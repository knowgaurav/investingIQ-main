"""Data processing Azure Functions - handles stock and news data fetching."""
import json
import logging
from datetime import datetime

import azure.functions as func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(msg: func.ServiceBusMessage):
    """
    Process data queue messages - fetch stock data or news.
    Then route to ML queue (always) and LLM queue (if configured).
    
    Triggered by: data-queue
    Outputs to: ml-queue (always), llm-queue (if llm_config present), aggregate-queue
    """
    from shared.webpubsub_utils import send_progress
    from azure.servicebus import ServiceBusClient, ServiceBusMessage as SBMessage
    from shared.config import get_settings
    
    try:
        message = json.loads(msg.get_body().decode('utf-8'))
        
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        llm_config = message.get("llm_config")
        
        logger.info(f"Processing {task_type} for {ticker}, task_id: {task_id}")
        send_progress(task_id, 10, f"Fetching {task_type.replace('fetch_', '')}")
        
        settings = get_settings()
        messages_to_send = []
        
        if task_type == "fetch_stock_data":
            result = fetch_stock_data(ticker)
            
            messages_to_send.append({
                "queue": "aggregate-queue",
                "message": {
                    "task_type": "stock_data_ready",
                    "task_id": task_id,
                    "ticker": ticker,
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            })
            
            messages_to_send.append({
                "queue": "ml-prediction-queue",
                "message": {
                    "task_type": "ml_prediction",
                    "task_id": task_id,
                    "ticker": ticker,
                    "data": {"price_history": result.get("price_history", [])},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            })
            
            messages_to_send.append({
                "queue": "ml-technical-queue",
                "message": {
                    "task_type": "ml_technical",
                    "task_id": task_id,
                    "ticker": ticker,
                    "data": {"price_history": result.get("price_history", [])},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            })
            
        elif task_type == "fetch_news":
            result = fetch_news(ticker)
            headlines = [{"title": a.get("title", "")} for a in result]
            
            messages_to_send.append({
                "queue": "aggregate-queue",
                "message": {
                    "task_type": "news_ready",
                    "task_id": task_id,
                    "ticker": ticker,
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            })
            
            messages_to_send.append({
                "queue": "ml-sentiment-queue",
                "message": {
                    "task_type": "ml_sentiment",
                    "task_id": task_id,
                    "ticker": ticker,
                    "data": {"headlines": headlines},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            })
            
            if llm_config:
                messages_to_send.append({
                    "queue": "llm-queue",
                    "message": {
                        "task_type": "analyze_sentiment",
                        "task_id": task_id,
                        "ticker": ticker,
                        "data": {"headlines": result},
                        "llm_config": llm_config,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                })
        else:
            logger.error(f"Unknown task type: {task_type}")
            return
        
        with ServiceBusClient.from_connection_string(settings.servicebus_connection) as client:
            for item in messages_to_send:
                with client.get_queue_sender(item["queue"]) as sender:
                    sender.send_messages(SBMessage(json.dumps(item["message"])))
                    logger.info(f"Sent {item['message']['task_type']} to {item['queue']}")
        
        logger.info(f"Completed {task_type} for {ticker}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise


def fetch_stock_data(ticker: str) -> dict:
    """Fetch stock data and earnings from Alpha Vantage."""
    from shared.alpha_vantage import fetch_stock_data as av_fetch_stock, fetch_earnings
    
    stock_data = av_fetch_stock(ticker)
    earnings = fetch_earnings(ticker)
    stock_data["earnings"] = earnings
    return stock_data


def fetch_news(ticker: str, max_articles: int = 20) -> list:
    """Fetch news with sentiment from Alpha Vantage."""
    from shared.alpha_vantage import fetch_news as av_fetch_news
    return av_fetch_news(ticker, max_articles)
