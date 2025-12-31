"""Aggregate Azure Function - combines results and sends to frontend."""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import azure.functions as func
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = "redis://localhost:6379/0"
TASK_TTL = 3600  # 1 hour


def get_redis():
    """Get Redis client."""
    return redis.from_url(REDIS_URL)


def get_task_results(r: redis.Redis, task_id: str) -> Dict[str, Any]:
    """Load task results from Redis."""
    data = r.get(f"task:{task_id}")
    if data:
        return json.loads(data)
    return {"stock_data": None, "news": None, "sentiment": None, "summary": None, "insights": None}


def update_task_results(r: redis.Redis, task_id: str, results: Dict[str, Any]):
    """Save partial results to Redis."""
    r.setex(f"task:{task_id}", TASK_TTL, json.dumps(results))


def main(msg: func.ServiceBusMessage, outputSbMsg: func.Out[str]):
    """Aggregate partial results and proceed to next phase when ready."""
    try:
        message_body = msg.get_body().decode('utf-8')
        message = json.loads(message_body)
        
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        data = message.get("data")
        
        logger.info(f"Aggregating {task_type} for {ticker}, task_id: {task_id}")
        
        r = get_redis()
        results = get_task_results(r, task_id)
        results["ticker"] = ticker
        
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
        
        update_task_results(r, task_id, results)
        
        next_message = check_and_proceed(r, task_id, results)
        if next_message:
            outputSbMsg.set(json.dumps(next_message))
        
    except Exception as e:
        logger.error(f"Error in aggregate function: {e}")
        raise


def check_and_proceed(r: redis.Redis, task_id: str, results: Dict) -> Optional[Dict]:
    """Check if we have enough data to proceed to next phase."""
    from shared.webpubsub_utils import send_progress
    ticker = results["ticker"]
    
    # Phase 1: Stock data + news ready -> trigger sentiment analysis
    if results["stock_data"] is not None and results["news"] is not None and results["sentiment"] is None:
        logger.info(f"Phase 1 complete for {ticker}, triggering LLM analysis")
        send_progress(task_id, 20, "Analyzing sentiment...")
        
        headlines = [a.get("title", "") for a in (results["news"] or [])]
        return {
            "task_type": "analyze_sentiment",
            "task_id": task_id,
            "ticker": ticker,
            "data": {"headlines": headlines, "stock_data": results["stock_data"]},
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    # Phase 2: Sentiment + summary ready -> generate insights
    if results["sentiment"] is not None and results["summary"] is not None and results["insights"] is None:
        logger.info(f"Phase 2 complete for {ticker}, generating insights")
        send_progress(task_id, 70, "Generating insights...")
        
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
    
    # All phases complete -> send results to frontend via SSE
    if all([results.get(k) is not None for k in ["stock_data", "news", "sentiment", "summary", "insights"]]):
        logger.info(f"All phases complete for {ticker}, sending results")
        from shared.webpubsub_utils import send_completed_with_data
        send_completed_with_data(task_id, ticker, results)
        r.delete(f"task:{task_id}")  # Clean up
        return None
    
    return None
