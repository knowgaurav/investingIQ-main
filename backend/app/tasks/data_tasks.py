"""Data fetching tasks - runs on data_queue workers."""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, queue="data_queue", max_retries=3)
def fetch_stock_data_task(self, ticker: str) -> dict:
    """
    Fetch stock price history and company info from yfinance.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        dict with price_history and company_info
    """
    # Will be implemented in Task 3
    return {
        "ticker": ticker,
        "price_history": [],
        "company_info": {},
        "status": "placeholder"
    }


@celery_app.task(bind=True, queue="data_queue", max_retries=3)
def fetch_news_task(self, ticker: str) -> list:
    """
    Fetch recent news articles for a stock.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List of news article dicts
    """
    # Will be implemented in Task 4
    return []
