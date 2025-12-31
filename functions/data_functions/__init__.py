"""Data processing Azure Functions - handles stock and news data fetching."""
import json
import logging
import os
from datetime import datetime, timedelta

import azure.functions as func
import yfinance as yf
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(msg: func.ServiceBusMessage, outputSbMsg: func.Out[str]):
    """
    Process data queue messages - fetch stock data or news.
    
    Triggered by: data-queue
    Outputs to: llm-queue (for sentiment/summary) and embed-queue (for embeddings)
    """
    from shared.webpubsub_utils import send_progress
    
    try:
        # Parse message
        message_body = msg.get_body().decode('utf-8')
        message = json.loads(message_body)
        
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        
        logger.info(f"Processing {task_type} for {ticker}, task_id: {task_id}")
        send_progress(task_id, 10, f"Fetching {task_type.replace('fetch_', '')}")
        
        if task_type == "fetch_stock_data":
            result = fetch_stock_data(ticker)
            output_message = {
                "task_type": "stock_data_ready",
                "task_id": task_id,
                "ticker": ticker,
                "data": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        elif task_type == "fetch_news":
            result = fetch_news(ticker)
            output_message = {
                "task_type": "news_ready",
                "task_id": task_id,
                "ticker": ticker,
                "data": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            logger.error(f"Unknown task type: {task_type}")
            return
        
        # Send to aggregate queue for collection
        outputSbMsg.set(json.dumps(output_message))
        logger.info(f"Completed {task_type} for {ticker}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise


def fetch_stock_data(ticker: str) -> dict:
    """Fetch stock data from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        
        # Get historical data (30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        history = stock.history(start=start_date, end=end_date)
        
        # Convert to list of dicts
        price_data = []
        for date, row in history.iterrows():
            price_data.append({
                "date": date.isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            })
        
        # Get company info
        info = stock.info
        company_info = {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "description": info.get("longBusinessSummary", ""),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
        }
        
        return {
            "ticker": ticker,
            "price_history": price_data,
            "company_info": company_info,
            "current_price": price_data[-1]["close"] if price_data else None,
        }
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {ticker}: {e}")
        return {
            "ticker": ticker,
            "price_history": [],
            "company_info": {"name": ticker},
            "error": str(e),
        }


def fetch_news(ticker: str, max_articles: int = 10) -> list:
    """Fetch news articles from News API."""
    api_key = os.environ.get("NEWS_API_KEY")
    
    if not api_key:
        logger.warning("NEWS_API_KEY not set, returning empty news")
        return []
    
    try:
        # Get company name for better search
        stock = yf.Ticker(ticker)
        company_name = stock.info.get("longName", ticker)
        
        # Search for news
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": f"{ticker} OR {company_name}",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max_articles,
            "apiKey": api_key,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
            })
        
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []
