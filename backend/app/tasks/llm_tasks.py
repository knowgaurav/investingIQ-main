"""LLM tasks - runs on llm_queue workers with rate limiting."""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, queue="llm_queue", max_retries=3, rate_limit="10/m")
def analyze_sentiment_task(self, news_articles: list) -> dict:
    """
    Analyze sentiment of news articles using LLM.
    
    Args:
        news_articles: List of news article dicts
        
    Returns:
        dict with sentiment results
    """
    # Will be implemented in Task 5
    return {
        "sentiment_score": 0.0,
        "sentiment_breakdown": {"bullish": 0, "bearish": 0, "neutral": 0},
        "details": [],
        "status": "placeholder"
    }


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
    # Will be implemented in Task 5
    return f"News summary for {ticker} - placeholder"


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
    # Will be implemented in Task 5
    return f"AI insights for {ticker} - placeholder"
