"""LLM tasks - runs on llm_queue workers with rate limiting."""
import logging
from typing import List

from app.tasks.celery_app import celery_app
from app.services.llm_service import get_llm_service
from app.services.sentiment_service import get_sentiment_service
from app.services.summarizer_service import get_summarizer_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue="llm_queue", max_retries=3, rate_limit="10/m")
def analyze_sentiment_task(self, news_articles: list) -> dict:
    """
    Analyze sentiment of news articles using LLM.
    
    Args:
        news_articles: List of news article dicts with 'title' key
        
    Returns:
        dict with sentiment_score, sentiment_breakdown, details, and status
    """
    try:
        sentiment_service = get_sentiment_service()
        result = sentiment_service.analyze_articles(news_articles)
        
        logger.info(
            f"Sentiment analysis completed: score={result.get('sentiment_score')}, "
            f"breakdown={result.get('sentiment_breakdown')}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Sentiment analysis task failed: {e}")
        
        # Retry with exponential backoff
        retry_countdown = 2 ** self.request.retries * 60  # 1min, 2min, 4min
        raise self.retry(exc=e, countdown=retry_countdown)


@celery_app.task(bind=True, queue="llm_queue", max_retries=3, rate_limit="10/m")
def generate_summary_task(self, ticker: str, news_articles: list) -> str:
    """
    Generate news summary using LLM.
    
    Args:
        ticker: Stock ticker symbol
        news_articles: List of news article dicts
        
    Returns:
        Summary string
    """
    try:
        summarizer_service = get_summarizer_service()
        summary = summarizer_service.summarize_news(news_articles, ticker)
        
        logger.info(f"Summary generated for {ticker}: {len(summary)} characters")
        
        return summary
        
    except Exception as e:
        logger.error(f"Summary generation task failed for {ticker}: {e}")
        
        # Retry with exponential backoff
        retry_countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=e, countdown=retry_countdown)


@celery_app.task(bind=True, queue="llm_queue", max_retries=3, rate_limit="10/m")
def generate_insights_task(
    self, 
    ticker: str, 
    stock_data: dict, 
    sentiment: dict, 
    summary: str
) -> str:
    """
    Generate AI insights combining all analysis.
    
    Args:
        ticker: Stock ticker symbol
        stock_data: Stock price and company data
        sentiment: Sentiment analysis results
        summary: News summary
        
    Returns:
        AI insights string
    """
    try:
        llm_service = get_llm_service()
        insights = llm_service.generate_insights(
            ticker=ticker,
            stock_data=stock_data,
            sentiment=sentiment,
            summary=summary
        )
        
        logger.info(f"Insights generated for {ticker}: {len(insights)} characters")
        
        return insights
        
    except Exception as e:
        logger.error(f"Insights generation task failed for {ticker}: {e}")
        
        # Retry with exponential backoff
        retry_countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=e, countdown=retry_countdown)


@celery_app.task(bind=True, queue="llm_queue", max_retries=3, rate_limit="10/m")
def chat_completion_task(self, query: str, context: str = "") -> str:
    """
    Execute a chat completion using LLM.
    
    Args:
        query: User query/question
        context: Optional context to include
        
    Returns:
        LLM response string
    """
    try:
        llm_service = get_llm_service()
        response = llm_service.chat(query=query, context=context)
        
        logger.info(f"Chat completion: query_len={len(query)}, response_len={len(response)}")
        
        return response
        
    except Exception as e:
        logger.error(f"Chat completion task failed: {e}")
        
        # Retry with exponential backoff
        retry_countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=e, countdown=retry_countdown)
