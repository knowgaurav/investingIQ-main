"""
Simple parallel processing using Redis queues (local) or Azure Service Bus (production).
This replaces Durable Functions with a simpler approach.
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional
import redis
import httpx

logger = logging.getLogger(__name__)

# Redis for local queue-based parallel processing
REDIS_URL = "redis://localhost:6379"


class ParallelAnalyzer:
    """Runs analysis tasks in parallel using asyncio."""
    
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    
    async def run_analysis(self, ticker: str, task_id: str, db_url: str) -> dict:
        """Run all analysis tasks in parallel."""
        from app.services.scraper_service import fetch_stock_data_scraped, fetch_news_scraped
        from app.services.llm_service import get_llm_service
        from app.services.sentiment_service import get_sentiment_service
        from app.services.summarizer_service import get_summarizer_service
        
        # Update progress
        self._update_progress(task_id, 10, "Fetching data in parallel")
        
        # PHASE 1: Fetch data in parallel
        stock_task = asyncio.create_task(asyncio.to_thread(fetch_stock_data_scraped, ticker))
        news_task = asyncio.create_task(asyncio.to_thread(fetch_news_scraped, ticker, 10))
        
        stock_data, news_articles = await asyncio.gather(stock_task, news_task)
        
        self._update_progress(task_id, 40, "Processing in parallel")
        
        # PHASE 2: Process in parallel
        llm = get_llm_service()
        sentiment_svc = get_sentiment_service()
        summarizer = get_summarizer_service()
        
        async def analyze_sentiment():
            if not news_articles:
                return {"breakdown": {"bullish": 0, "bearish": 0, "neutral": 0}, "details": []}
            result = await asyncio.to_thread(sentiment_svc.analyze_articles, news_articles)
            return result
        
        async def generate_summary():
            if not news_articles:
                return f"No recent news for {ticker}."
            return await asyncio.to_thread(summarizer.summarize_news, news_articles, ticker)
        
        async def generate_insights():
            return await asyncio.to_thread(llm.generate_insights, ticker, stock_data, {}, "")
        
        sentiment_task = asyncio.create_task(analyze_sentiment())
        summary_task = asyncio.create_task(generate_summary())
        insights_task = asyncio.create_task(generate_insights())
        
        sentiment_result, news_summary, ai_insights = await asyncio.gather(
            sentiment_task, summary_task, insights_task
        )
        
        self._update_progress(task_id, 90, "Saving report")
        
        # Get breakdown and convert to percentages for frontend
        raw = sentiment_result.get("sentiment_breakdown", {"bullish": 0, "bearish": 0, "neutral": 0})
        total = sum(raw.values()) or 1
        sentiment_score = (raw.get("bullish", 0) - raw.get("bearish", 0)) / total
        breakdown = {
            "positive": round(raw.get("bullish", 0) / total * 100),
            "negative": round(raw.get("bearish", 0) / total * 100),
            "neutral": round(raw.get("neutral", 0) / total * 100),
        }
        
        return {
            "ticker": ticker,
            "task_id": task_id,
            "stock_data": stock_data,
            "news_articles": news_articles,
            "sentiment_result": {"breakdown": breakdown, "details": sentiment_result.get("details", [])},
            "sentiment_score": sentiment_score,
            "news_summary": news_summary,
            "ai_insights": ai_insights,
        }
    
    def _update_progress(self, task_id: str, progress: int, step: str):
        """Update task progress in Redis."""
        try:
            self.redis.hset(f"task:{task_id}", mapping={
                "progress": progress,
                "current_step": step,
                "updated_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")


async def run_parallel_analysis(ticker: str, task_id: str) -> dict:
    """Entry point for parallel analysis."""
    analyzer = ParallelAnalyzer()
    return await analyzer.run_analysis(ticker, task_id, "")
