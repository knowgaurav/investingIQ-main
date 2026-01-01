"""Data fetching tasks - DEPRECATED.

Note: Data fetching is now handled by Azure Functions.
This file is kept for backward compatibility but tasks are not used.
"""
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue="data_queue")
def fetch_stock_data_task(self, ticker: str, period: str = "1y") -> dict:
    """DEPRECATED: Stock data fetching is handled by Azure Functions."""
    logger.warning("fetch_stock_data_task is deprecated - use Azure Functions")
    return {"ticker": ticker, "status": "error", "error": "Use Azure Functions"}


@celery_app.task(bind=True, queue="data_queue")
def fetch_news_task(self, ticker: str, limit: int = 20) -> list:
    """DEPRECATED: News fetching is handled by Azure Functions."""
    logger.warning("fetch_news_task is deprecated - use Azure Functions")
    return []
