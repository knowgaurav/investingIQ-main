"""Data fetching tasks - runs on data_queue workers."""
import logging

from celery.exceptions import MaxRetriesExceededError

from app.tasks.celery_app import celery_app
from app.services.news_service import fetch_news, RateLimitError
from app.services import stock_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue="data_queue", max_retries=3)
def fetch_stock_data_task(self, ticker: str, period: str = "1y") -> dict:
    """
    Fetch stock price history and company info from yfinance.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period for historical data (default: '1y')
        
    Returns:
        dict with price_history, company_info, current_price, and status
    """
    try:
        logger.info(f"Fetching stock data for {ticker} (period: {period})")
        
        # Use the stock service to fetch data
        result = stock_service.fetch_stock_data(ticker, period=period)
        
        if result["status"] == "error":
            logger.error(f"Failed to fetch stock data for {ticker}: {result['error']}")
            # Retry on failure
            raise self.retry(
                exc=Exception(result["error"]),
                countdown=60  # Wait 60 seconds before retry
            )
        
        logger.info(f"Successfully fetched stock data for {ticker}: {len(result['price_history'])} price points")
        return result
        
    except MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for fetching stock data: {ticker}")
        return {
            "ticker": ticker,
            "price_history": [],
            "company_info": {},
            "current_price": None,
            "status": "error",
            "error": f"Failed to fetch stock data after {self.max_retries} retries"
        }
    except Exception as e:
        logger.error(f"Error in fetch_stock_data_task for {ticker}: {e}")
        try:
            raise self.retry(exc=e, countdown=60)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for fetching stock data: {ticker}")
            return {
                "ticker": ticker,
                "price_history": [],
                "company_info": {},
                "current_price": None,
                "status": "error",
                "error": str(e)
            }


@celery_app.task(bind=True, queue="data_queue", max_retries=3)
def fetch_news_task(self, ticker: str, limit: int = 20) -> list:
    """
    Fetch recent news articles for a stock.
    
    Uses the news_service to fetch articles from NewsAPI.
    Handles rate limiting with automatic retries.
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of articles to fetch (default: 20)
        
    Returns:
        List of news article dicts with keys:
        - title: Article title
        - description: Article description/summary
        - url: Link to full article
        - published_at: Publication timestamp
        - source: News source name
    """
    try:
        logger.info(f"Fetching news for ticker: {ticker}")
        articles = fetch_news(ticker, limit=limit)
        logger.info(f"Successfully fetched {len(articles)} articles for {ticker}")
        return articles
        
    except RateLimitError as e:
        # Retry with exponential backoff on rate limit
        logger.warning(f"Rate limited fetching news for {ticker}, scheduling retry")
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for news fetch: {ticker}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        # Return empty list on error - don't fail the entire task
        return []
