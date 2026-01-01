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
    """Load task results from Redis using HGETALL for atomic access."""
    key = f"task:{task_id}"
    data = r.hgetall(key)
    
    result = {
        "stock_data": None, 
        "news": None,
        "ml_prediction": None,
        "ml_technical": None,
        "ml_sentiment": None,
        "llm_sentiment": None,
        "llm_summary": None,
        "llm_insights": None,
        "llm_config": None,
        "ticker": None,
    }
    
    for field, value in data.items():
        field_str = field.decode() if isinstance(field, bytes) else field
        value_str = value.decode() if isinstance(value, bytes) else value
        try:
            result[field_str] = json.loads(value_str)
        except (json.JSONDecodeError, TypeError):
            result[field_str] = value_str
    
    return result


def update_task_field(r: redis.Redis, task_id: str, field: str, value: Any):
    """Atomically update a single field in task results."""
    key = f"task:{task_id}"
    r.hset(key, field, json.dumps(value))
    r.expire(key, TASK_TTL)


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
        
        # Always update ticker
        update_task_field(r, task_id, "ticker", ticker)
        
        # Update llm_config if present
        if llm_config:
            update_task_field(r, task_id, "llm_config", llm_config)
        
        # Atomically update only the specific field for this message
        if task_type == "stock_data_ready":
            update_task_field(r, task_id, "stock_data", data)
        elif task_type == "news_ready":
            update_task_field(r, task_id, "news", data)
        elif task_type == "ml_prediction_ready":
            update_task_field(r, task_id, "ml_prediction", data)
            send_progress(task_id, 40, "ML predictions complete")
        elif task_type == "ml_technical_ready":
            update_task_field(r, task_id, "ml_technical", data)
            send_progress(task_id, 45, "Technical analysis complete")
        elif task_type == "ml_sentiment_ready":
            update_task_field(r, task_id, "ml_sentiment", data)
            send_progress(task_id, 50, "Sentiment analysis complete")
        elif task_type == "llm_sentiment_ready":
            update_task_field(r, task_id, "llm_sentiment", data)
            send_progress(task_id, 60, "LLM sentiment complete")
        elif task_type == "llm_summary_ready":
            update_task_field(r, task_id, "llm_summary", data)
            send_progress(task_id, 70, "News summary complete")
        elif task_type == "llm_insights_ready":
            update_task_field(r, task_id, "llm_insights", data)
            send_progress(task_id, 90, "AI insights complete")
        
        # Re-read all fields to check completion
        results = get_task_results(r, task_id)
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
        stock_data = results.get('stock_data') or {}
        price_history = stock_data.get('price_history', []) if isinstance(stock_data, dict) else []
        logger.info(f"Stock data has {len(price_history)} price records")
        ml_pred = results.get('ml_prediction') or {}
        logger.info(f"ML prediction: {ml_pred.get('trend', 'N/A') if isinstance(ml_pred, dict) else 'N/A'}")
        logger.info(f"LLM results: sentiment={results.get('llm_sentiment') is not None}, summary={results.get('llm_summary') is not None}, insights={results.get('llm_insights') is not None}")
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
