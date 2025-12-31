"""Embedding tasks - runs on embed_queue workers."""
import logging

from app.tasks.celery_app import celery_app
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue="embed_queue", max_retries=3)
def embed_documents_task(
    self, 
    ticker: str, 
    stock_data: dict, 
    news_articles: list
) -> str:
    """
    Generate embeddings and store in vector database.
    
    Uses the RAG service to chunk documents, generate embeddings via
    OpenAI embeddings API (through OhMyGPT), and store them in PostgreSQL
    with pgvector for semantic search.
    
    Args:
        ticker: Stock ticker symbol
        stock_data: Stock price and company data
        news_articles: List of news articles
        
    Returns:
        Embedding batch ID
    """
    try:
        logger.info(f"Starting embedding task for {ticker}")
        
        rag_service = get_rag_service()
        
        batch_id = rag_service.embed_documents(
            ticker=ticker,
            stock_data=stock_data,
            news_articles=news_articles
        )
        
        logger.info(f"Completed embedding task for {ticker}, batch_id: {batch_id}")
        return batch_id
        
    except Exception as e:
        logger.error(f"Embedding task failed for {ticker}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
