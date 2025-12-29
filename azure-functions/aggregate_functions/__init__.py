"""Aggregate Azure Function - combines results and saves analysis report."""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

import azure.functions as func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory store for partial results (in production, use Redis or Cosmos DB)
# This is simplified - in production you'd use Azure Cache for Redis
_partial_results: Dict[str, Dict[str, Any]] = {}


def main(msg: func.ServiceBusMessage, outputSbMsg: func.Out[str]):
    """
    Aggregate partial results and save final report when complete.
    
    Triggered by: aggregate-queue
    Outputs to: llm-queue (for next steps) or saves to database
    """
    try:
        message_body = msg.get_body().decode('utf-8')
        message = json.loads(message_body)
        
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        data = message.get("data")
        
        logger.info(f"Aggregating {task_type} for {ticker}, task_id: {task_id}")
        
        # Initialize task results if not exists
        if task_id not in _partial_results:
            _partial_results[task_id] = {
                "ticker": ticker,
                "stock_data": None,
                "news": None,
                "sentiment": None,
                "summary": None,
                "insights": None,
                "embedding_id": None,
            }
        
        results = _partial_results[task_id]
        
        # Store the result based on type
        if task_type == "stock_data_ready":
            results["stock_data"] = data
            
        elif task_type == "news_ready":
            results["news"] = data
            
        elif task_type == "sentiment_ready":
            results["sentiment"] = data
            
        elif task_type == "summary_ready":
            results["summary"] = data
            
        elif task_type == "insights_ready":
            results["insights"] = data
            
        elif task_type == "embedding_ready":
            results["embedding_id"] = data
        
        # Check if we can proceed to next phase
        next_message = check_and_proceed(task_id, results, outputSbMsg)
        
        if next_message:
            outputSbMsg.set(json.dumps(next_message))
        
    except Exception as e:
        logger.error(f"Error in aggregate function: {e}")
        raise


def check_and_proceed(task_id: str, results: Dict, outputSbMsg) -> Optional[Dict]:
    """Check if we have enough data to proceed to next phase."""
    ticker = results["ticker"]
    
    # Phase 1 complete: Stock data and news ready -> trigger LLM tasks
    if results["stock_data"] and results["news"] and not results["sentiment"]:
        logger.info(f"Phase 1 complete for {ticker}, triggering LLM tasks")
        
        # Send sentiment analysis task
        headlines = [article.get("title", "") for article in results["news"]]
        
        # We need to send multiple messages - return the first one
        # In production, you'd use a Service Bus client to send multiple
        return {
            "task_type": "analyze_sentiment",
            "task_id": task_id,
            "ticker": ticker,
            "data": {"headlines": headlines},
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    # Phase 2 complete: Sentiment and summary ready -> trigger insights
    if (results["stock_data"] and results["sentiment"] and 
        results["summary"] and not results["insights"]):
        logger.info(f"Phase 2 complete for {ticker}, triggering insights")
        
        return {
            "task_type": "generate_insights",
            "task_id": task_id,
            "ticker": ticker,
            "data": {
                "stock_data": results["stock_data"],
                "sentiment": results["sentiment"],
                "summary": results["summary"],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    # All phases complete -> save report
    if all([
        results["stock_data"],
        results["news"],
        results["sentiment"],
        results["summary"],
        results["insights"],
    ]):
        logger.info(f"All phases complete for {ticker}, saving report")
        save_report(task_id, results)
        
        # Clean up
        del _partial_results[task_id]
        
        return None
    
    return None


def save_report(task_id: str, results: Dict):
    """Save the complete analysis report to database."""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL not set")
            return
        
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Import here to avoid circular imports
            from models import AnalysisReport, AnalysisTask
            
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
            
            session.add(report)
            
            # Update task status
            task = session.query(AnalysisTask).filter(
                AnalysisTask.id == task_id
            ).first()
            
            if task:
                task.status = "completed"
                task.progress = 100
                task.report_id = report.id
                task.completed_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Saved report for {ticker}, report_id: {report.id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        raise
