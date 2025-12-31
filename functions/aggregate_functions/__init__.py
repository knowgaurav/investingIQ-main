"""Aggregate Azure Function - combines ML and LLM results."""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import azure.functions as func
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = "redis://localhost:6379/0"
TASK_TTL = 3600


def get_redis():
    """Get Redis client."""
    return redis.from_url(REDIS_URL)


def get_task_results(r: redis.Redis, task_id: str) -> Dict[str, Any]:
    """Load task results from Redis."""
    data = r.get(f"task:{task_id}")
    if data:
        return json.loads(data)
    return {
        "stock_data": None, 
        "news": None,
        "ml_prediction": None,
        "ml_technical": None,
        "ml_sentiment": None,
        "llm_sentiment": None,
        "llm_summary": None,
        "llm_insights": None,
        "llm_config": None,
    }


def update_task_results(r: redis.Redis, task_id: str, results: Dict[str, Any]):
    """Save partial results to Redis."""
    r.setex(f"task:{task_id}", TASK_TTL, json.dumps(results))


def main(msg: func.ServiceBusMessage):
    """Aggregate partial results from ML and LLM functions."""
    from shared.webpubsub_utils import send_progress
    
    try:
        message = json.loads(msg.get_body().decode('utf-8'))
        
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        data = message.get("data")
        llm_config = message.get("llm_config")
        
        logger.info(f"Aggregating {task_type} for {ticker}, task_id: {task_id}")
        
        r = get_redis()
        results = get_task_results(r, task_id)
        results["ticker"] = ticker
        
        if llm_config:
            results["llm_config"] = llm_config
        
        if task_type == "stock_data_ready":
            results["stock_data"] = data
        elif task_type == "news_ready":
            results["news"] = data
        elif task_type == "ml_prediction_ready":
            results["ml_prediction"] = data
            send_progress(task_id, 40, "ML predictions complete")
        elif task_type == "ml_technical_ready":
            results["ml_technical"] = data
            send_progress(task_id, 45, "Technical analysis complete")
        elif task_type == "ml_sentiment_ready":
            results["ml_sentiment"] = data
            send_progress(task_id, 50, "Sentiment analysis complete")
        elif task_type == "llm_sentiment_ready":
            results["llm_sentiment"] = data
            send_progress(task_id, 60, "LLM sentiment complete")
        elif task_type == "llm_summary_ready":
            results["llm_summary"] = data
            send_progress(task_id, 70, "News summary complete")
        elif task_type == "llm_insights_ready":
            results["llm_insights"] = data
            send_progress(task_id, 90, "AI insights complete")
        
        update_task_results(r, task_id, results)
        check_completion(r, task_id, results)
        
    except Exception as e:
        logger.error(f"Error in aggregate function: {e}")
        raise


def check_completion(r: redis.Redis, task_id: str, results: Dict):
    """Check if analysis is complete and send results."""
    from shared.webpubsub_utils import send_completed_with_data
    
    ticker = results.get("ticker")
    has_llm_config = results.get("llm_config") is not None
    
    ml_complete = all([
        results.get("stock_data") is not None,
        results.get("news") is not None,
        results.get("ml_prediction") is not None,
        results.get("ml_technical") is not None,
        results.get("ml_sentiment") is not None,
    ])
    
    if has_llm_config:
        llm_complete = all([
            results.get("llm_sentiment") is not None,
            results.get("llm_summary") is not None,
            results.get("llm_insights") is not None,
        ])
        all_complete = ml_complete and llm_complete
    else:
        all_complete = ml_complete
    
    if all_complete:
        logger.info(f"Analysis complete for {ticker}")
        send_completed_with_data(task_id, ticker, results)
        r.delete(f"task:{task_id}")
    else:
        missing = []
        if not results.get("stock_data"):
            missing.append("stock_data")
        if not results.get("ml_prediction"):
            missing.append("ml_prediction")
        if not results.get("ml_technical"):
            missing.append("ml_technical")
        if not results.get("ml_sentiment"):
            missing.append("ml_sentiment")
        if has_llm_config:
            if not results.get("llm_sentiment"):
                missing.append("llm_sentiment")
            if not results.get("llm_summary"):
                missing.append("llm_summary")
            if not results.get("llm_insights"):
                missing.append("llm_insights")
        logger.info(f"Waiting for: {missing}")
