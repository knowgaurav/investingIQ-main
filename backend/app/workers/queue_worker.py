"""
Queue Worker - Processes messages from Azure Service Bus queues.

This worker runs locally and processes messages from all queues,
similar to how Azure Functions would process them in production.
"""
import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.exceptions import ServiceBusError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.config import get_settings
from app.services.stock_service import get_stock_data, search_stocks
from app.services.news_service import fetch_news
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from app.models.database import SessionLocal, AnalysisReport, AnalysisTask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Queue names
QUEUE_DATA = "data-queue"
QUEUE_LLM = "llm-queue"
QUEUE_EMBED = "embed-queue"
QUEUE_AGGREGATE = "aggregate-queue"

# In-memory store for partial results (per task_id)
partial_results: Dict[str, Dict[str, Any]] = {}


class QueueWorker:
    """Worker that processes messages from Service Bus queues."""
    
    def __init__(self):
        settings = get_settings()
        self._connection_string = settings.azure_servicebus_connection_string
        self._client: Optional[ServiceBusClient] = None
        self._running = False
    
    def _get_client(self) -> ServiceBusClient:
        """Get or create Service Bus client."""
        if self._client is None:
            self._client = ServiceBusClient.from_connection_string(
                self._connection_string
            )
        return self._client
    
    def start(self):
        """Start processing messages from all queues."""
        self._running = True
        logger.info("Starting queue worker...")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            asyncio.run(self._process_all_queues())
        except KeyboardInterrupt:
            logger.info("Worker interrupted")
        finally:
            self.stop()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._running = False
    
    def stop(self):
        """Stop the worker and clean up."""
        self._running = False
        if self._client:
            self._client.close()
            self._client = None
        logger.info("Worker stopped")
    
    async def _process_all_queues(self):
        """Process messages from all queues concurrently."""
        tasks = [
            self._process_queue(QUEUE_DATA, self._handle_data_message),
            self._process_queue(QUEUE_LLM, self._handle_llm_message),
            self._process_queue(QUEUE_EMBED, self._handle_embed_message),
            self._process_queue(QUEUE_AGGREGATE, self._handle_aggregate_message),
        ]
        
        await asyncio.gather(*tasks)
    
    async def _process_queue(self, queue_name: str, handler):
        """Process messages from a specific queue."""
        logger.info(f"Starting to process queue: {queue_name}")
        
        client = self._get_client()
        
        while self._running:
            try:
                with client.get_queue_receiver(queue_name, max_wait_time=5) as receiver:
                    for msg in receiver:
                        try:
                            message_body = str(msg)
                            message = json.loads(message_body)
                            
                            logger.info(f"Processing message from {queue_name}: {message.get('task_type')}")
                            
                            # Process the message
                            await handler(message)
                            
                            # Complete the message
                            receiver.complete_message(msg)
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in message: {e}")
                            receiver.dead_letter_message(msg, reason="InvalidJSON")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            # Message will be retried or dead-lettered based on config
                            
            except ServiceBusError as e:
                logger.error(f"Service Bus error on {queue_name}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error(f"Unexpected error on {queue_name}: {e}")
                await asyncio.sleep(5)
    
    async def _handle_data_message(self, message: Dict):
        """Handle data queue messages (stock data, news fetching)."""
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        
        if task_type == "fetch_stock_data":
            result = await self._fetch_stock_data(ticker)
            await self._send_to_aggregate(task_id, ticker, "stock_data", result)
            
        elif task_type == "fetch_news":
            result = await self._fetch_news(ticker)
            await self._send_to_aggregate(task_id, ticker, "news", result)
    
    async def _handle_llm_message(self, message: Dict):
        """Handle LLM queue messages (sentiment, summary, insights)."""
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        data = message.get("data", {})
        
        llm_service = get_llm_service()
        
        if task_type == "analyze_sentiment":
            headlines = data.get("headlines", [])
            result = llm_service.analyze_sentiment(headlines)
            
            # Convert to expected format
            sentiment_result = self._format_sentiment_result(result)
            await self._send_to_aggregate(task_id, ticker, "sentiment", sentiment_result)
            
        elif task_type == "generate_summary":
            articles = data.get("articles", [])
            result = llm_service.summarize_news(articles, ticker)
            await self._send_to_aggregate(task_id, ticker, "summary", result)
            
        elif task_type == "generate_insights":
            stock_data = data.get("stock_data", {})
            sentiment = data.get("sentiment", {})
            summary = data.get("summary", "")
            
            result = llm_service.generate_insights(ticker, stock_data, sentiment, summary)
            await self._send_to_aggregate(task_id, ticker, "insights", result)
    
    async def _handle_embed_message(self, message: Dict):
        """Handle embedding queue messages."""
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        stock_data = message.get("stock_data", {})
        news_articles = message.get("news_articles", [])
        
        rag_service = get_rag_service()
        
        try:
            batch_id = rag_service.embed_documents(ticker, stock_data, news_articles)
            await self._send_to_aggregate(task_id, ticker, "embedding", batch_id)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            await self._send_to_aggregate(task_id, ticker, "embedding", None)
    
    async def _handle_aggregate_message(self, message: Dict):
        """Handle aggregate queue messages - combine results and trigger next steps."""
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        data = message.get("data")
        result_type = message.get("result_type")
        
        # Initialize partial results for this task
        if task_id not in partial_results:
            partial_results[task_id] = {
                "ticker": ticker,
                "stock_data": None,
                "news": None,
                "sentiment": None,
                "summary": None,
                "insights": None,
                "embedding": None,
            }
        
        results = partial_results[task_id]
        
        # Store the result
        if result_type:
            results[result_type] = data
        
        # Check what to do next
        await self._check_and_proceed(task_id, results)
    
    async def _check_and_proceed(self, task_id: str, results: Dict):
        """Check if we can proceed to next phase."""
        ticker = results["ticker"]
        
        # Phase 1 complete: Stock data and news ready -> trigger LLM tasks
        if results["stock_data"] and results["news"] and not results["sentiment"]:
            logger.info(f"Phase 1 complete for {ticker}, triggering LLM tasks")
            
            # Update task progress
            self._update_task_progress(task_id, 30, "Analyzing sentiment and generating summary")
            
            # Send sentiment analysis task
            headlines = [article.get("title", "") for article in results["news"]]
            await self._send_to_llm(task_id, ticker, "analyze_sentiment", {"headlines": headlines})
            
            # Send summary task
            await self._send_to_llm(task_id, ticker, "generate_summary", {"articles": results["news"]})
            
            # Send embedding task
            await self._send_to_embed(task_id, ticker, results["stock_data"], results["news"])
        
        # Phase 2 complete: Sentiment and summary ready -> trigger insights
        elif (results["stock_data"] and results["sentiment"] and 
              results["summary"] and not results["insights"]):
            logger.info(f"Phase 2 complete for {ticker}, triggering insights")
            
            self._update_task_progress(task_id, 70, "Generating AI insights")
            
            await self._send_to_llm(task_id, ticker, "generate_insights", {
                "stock_data": results["stock_data"],
                "sentiment": results["sentiment"],
                "summary": results["summary"],
            })
        
        # All phases complete -> save report
        elif all([
            results["stock_data"],
            results["news"],
            results["sentiment"],
            results["summary"],
            results["insights"],
        ]):
            logger.info(f"All phases complete for {ticker}, saving report")
            
            self._update_task_progress(task_id, 90, "Saving analysis report")
            
            await self._save_report(task_id, results)
            
            # Clean up
            del partial_results[task_id]
    
    async def _fetch_stock_data(self, ticker: str) -> Dict:
        """Fetch stock data from yfinance."""
        try:
            return get_stock_data(ticker)
        except Exception as e:
            logger.error(f"Error fetching stock data for {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}
    
    async def _fetch_news(self, ticker: str) -> list:
        """Fetch news articles."""
        try:
            return fetch_news(ticker)
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []
    
    def _format_sentiment_result(self, results: list) -> Dict:
        """Format sentiment analysis results."""
        if not results:
            return {
                "overall_score": 0.0,
                "breakdown": {"positive": 0, "negative": 0, "neutral": 0},
                "details": [],
            }
        
        scores = {"bullish": 1, "bearish": -1, "neutral": 0}
        breakdown = {"positive": 0, "negative": 0, "neutral": 0}
        total_score = 0
        
        for r in results:
            sentiment = r.get("sentiment", "neutral").lower()
            total_score += scores.get(sentiment, 0)
            if sentiment == "bullish":
                breakdown["positive"] += 1
            elif sentiment == "bearish":
                breakdown["negative"] += 1
            else:
                breakdown["neutral"] += 1
        
        overall_score = total_score / len(results) if results else 0
        
        return {
            "overall_score": overall_score,
            "breakdown": breakdown,
            "details": results,
        }
    
    async def _send_to_aggregate(self, task_id: str, ticker: str, result_type: str, data: Any):
        """Send result to aggregate queue."""
        message = {
            "task_type": "aggregate_result",
            "result_type": result_type,
            "task_id": task_id,
            "ticker": ticker,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._send_message(QUEUE_AGGREGATE, message)
    
    async def _send_to_llm(self, task_id: str, ticker: str, task_type: str, data: Dict):
        """Send task to LLM queue."""
        message = {
            "task_type": task_type,
            "task_id": task_id,
            "ticker": ticker,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._send_message(QUEUE_LLM, message)
    
    async def _send_to_embed(self, task_id: str, ticker: str, stock_data: Dict, news: list):
        """Send task to embed queue."""
        message = {
            "task_type": "embed_documents",
            "task_id": task_id,
            "ticker": ticker,
            "stock_data": stock_data,
            "news_articles": news,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._send_message(QUEUE_EMBED, message)
    
    async def _send_message(self, queue_name: str, message: Dict):
        """Send a message to a queue."""
        try:
            client = self._get_client()
            with client.get_queue_sender(queue_name) as sender:
                sender.send_messages(ServiceBusMessage(
                    body=json.dumps(message),
                    content_type="application/json",
                ))
        except Exception as e:
            logger.error(f"Error sending message to {queue_name}: {e}")
    
    def _update_task_progress(self, task_id: str, progress: int, step: str):
        """Update task progress in database."""
        try:
            db = SessionLocal()
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if task:
                task.progress = progress
                task.current_step = step
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Error updating task progress: {e}")
    
    async def _save_report(self, task_id: str, results: Dict):
        """Save the complete analysis report to database."""
        try:
            db = SessionLocal()
            
            ticker = results["ticker"]
            stock_data = results["stock_data"]
            
            # Create report
            report = AnalysisReport(
                ticker=ticker,
                company_name=stock_data.get("company_info", {}).get("name", ticker),
                analyzed_at=datetime.utcnow(),
                price_data=stock_data.get("price_history", []),
                news_summary=results["summary"],
                sentiment_score=results["sentiment"].get("overall_score", 0),
                sentiment_breakdown=results["sentiment"].get("breakdown", {}),
                sentiment_details=results["sentiment"].get("details", []),
                ai_insights=results["insights"],
            )
            
            db.add(report)
            
            # Update task status
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if task:
                task.status = "completed"
                task.progress = 100
                task.current_step = "Analysis complete"
                task.report_id = report.id
                task.completed_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Saved report for {ticker}, report_id: {report.id}")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")


def main():
    """Main entry point for the worker."""
    worker = QueueWorker()
    worker.start()


if __name__ == "__main__":
    main()
