"""News fetching service for InvestingIQ."""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import time

import requests
from requests.exceptions import RequestException, Timeout

from app.config import get_settings

logger = logging.getLogger(__name__)

# Rate limiting configuration
_last_request_time: float = 0
_min_request_interval: float = 0.5  # Minimum 500ms between requests


class NewsServiceError(Exception):
    """Custom exception for news service errors."""
    pass


class RateLimitError(NewsServiceError):
    """Raised when rate limit is exceeded."""
    pass


def _rate_limit_wait() -> None:
    """Enforce rate limiting between API requests."""
    global _last_request_time
    
    current_time = time.time()
    elapsed = current_time - _last_request_time
    
    if elapsed < _min_request_interval:
        sleep_time = _min_request_interval - elapsed
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def _parse_newsapi_article(article: dict) -> dict:
    """
    Parse a NewsAPI article into our standard format.
    
    Args:
        article: Raw article dict from NewsAPI
        
    Returns:
        Standardized article dict
    """
    return {
        "title": article.get("title", ""),
        "description": article.get("description", ""),
        "url": article.get("url", ""),
        "published_at": article.get("publishedAt", ""),
        "source": article.get("source", {}).get("name", "Unknown")
    }


def fetch_news(ticker: str, limit: int = 20) -> List[dict]:
    """
    Fetch news articles for a given stock ticker.
    
    Uses NewsAPI to fetch recent news articles related to the stock.
    Handles rate limiting and errors gracefully.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        limit: Maximum number of articles to return (default: 20)
        
    Returns:
        List of dicts with keys: title, description, url, published_at, source
        Returns empty list if no news available or on error.
    """
    settings = get_settings()
    
    # Check if API key is configured
    if not settings.news_api_key:
        logger.warning("NEWS_API_KEY not configured, returning empty news list")
        return []
    
    # Build search query - use ticker and common company name patterns
    # NewsAPI works better with company names, so we'll search for the ticker
    search_query = f"{ticker} stock"
    
    # Calculate date range (last 7 days)
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=7)
    
    # NewsAPI endpoint
    url = "https://newsapi.org/v2/everything"
    
    params = {
        "q": search_query,
        "apiKey": settings.news_api_key,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(limit, 100),  # NewsAPI max is 100
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
    }
    
    try:
        # Apply rate limiting
        _rate_limit_wait()
        
        logger.info(f"Fetching news for ticker: {ticker}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={"User-Agent": "InvestingIQ/1.0"}
        )
        
        # Handle rate limiting from API
        if response.status_code == 429:
            logger.warning(f"NewsAPI rate limit exceeded for ticker: {ticker}")
            raise RateLimitError("NewsAPI rate limit exceeded")
        
        # Handle unauthorized (invalid API key)
        if response.status_code == 401:
            logger.error("Invalid NewsAPI key")
            return []
        
        # Handle other HTTP errors
        if response.status_code != 200:
            logger.error(f"NewsAPI returned status {response.status_code}: {response.text}")
            return []
        
        data = response.json()
        
        # Check API response status
        if data.get("status") != "ok":
            error_message = data.get("message", "Unknown error")
            logger.error(f"NewsAPI error: {error_message}")
            return []
        
        # Parse articles
        articles = data.get("articles", [])
        
        if not articles:
            logger.info(f"No news articles found for ticker: {ticker}")
            return []
        
        # Parse and return articles
        parsed_articles = [
            _parse_newsapi_article(article)
            for article in articles[:limit]
        ]
        
        logger.info(f"Fetched {len(parsed_articles)} news articles for ticker: {ticker}")
        return parsed_articles
        
    except RateLimitError:
        # Re-raise rate limit errors for caller to handle
        raise
        
    except Timeout:
        logger.error(f"Timeout fetching news for ticker: {ticker}")
        return []
        
    except RequestException as e:
        logger.error(f"Request error fetching news for ticker {ticker}: {e}")
        return []
        
    except Exception as e:
        logger.error(f"Unexpected error fetching news for ticker {ticker}: {e}")
        return []


def fetch_news_with_retry(
    ticker: str,
    limit: int = 20,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> List[dict]:
    """
    Fetch news with automatic retry on rate limit errors.
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of articles to return
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries (exponential backoff applied)
        
    Returns:
        List of news article dicts
    """
    last_error: Optional[Exception] = None
    
    for attempt in range(max_retries):
        try:
            return fetch_news(ticker, limit)
            
        except RateLimitError as e:
            last_error = e
            if attempt < max_retries - 1:
                # Exponential backoff
                sleep_time = retry_delay * (2 ** attempt)
                logger.info(f"Rate limited, retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)
            else:
                logger.error(f"Max retries exceeded for ticker: {ticker}")
    
    # Return empty list after all retries exhausted
    return []
