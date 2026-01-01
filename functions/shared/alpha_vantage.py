"""Alpha Vantage API client with multi-key rotation."""
import os
import logging
from typing import Optional
import requests
import redis

logger = logging.getLogger(__name__)

BASE_URL = "https://www.alphavantage.co/query"
REDIS_URL = "redis://localhost:6379/0"

# Redis key for tracking which API key to use next
REDIS_KEY_INDEX = "alpha_vantage:key_index"


def _get_redis():
    """Get Redis client."""
    return redis.from_url(REDIS_URL, decode_responses=True)


def get_api_keys() -> list:
    """Get list of Alpha Vantage API keys from environment.
    
    Expects ALPHA_VANTAGE_API_KEYS as comma-separated values,
    or falls back to single ALPHA_VANTAGE_API_KEY.
    """
    keys_str = os.environ.get("ALPHA_VANTAGE_API_KEYS", "")
    if keys_str:
        return [k.strip() for k in keys_str.split(",") if k.strip()]
    
    # Fallback to single key
    single_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    return [single_key] if single_key else []


def get_api_key() -> str:
    """Get next API key using round-robin rotation."""
    keys = get_api_keys()
    if not keys:
        raise ValueError("No Alpha Vantage API keys configured")
    
    if len(keys) == 1:
        return keys[0]
    
    # Round-robin using Redis atomic increment
    try:
        r = _get_redis()
        index = r.incr(REDIS_KEY_INDEX) - 1
        key = keys[index % len(keys)]
        logger.debug(f"Using API key index {index % len(keys)}")
        return key
    except Exception as e:
        logger.warning(f"Redis error, using first key: {e}")
        return keys[0]


def safe_float(value) -> Optional[float]:
    """Safely convert value to float."""
    if value is None or value == "" or value == "None" or value == "-":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value) -> Optional[int]:
    """Safely convert value to int."""
    if value is None or value == "" or value == "None" or value == "-":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def fetch_daily_prices(ticker: str, outputsize: str = "compact", days: int = 100) -> dict:
    """Fetch daily price data from Alpha Vantage."""
    ticker = ticker.upper()
    
    try:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": outputsize,
            "apikey": get_api_key(),
        }
        
        resp = requests.get(BASE_URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        if "Error Message" in data:
            logger.error(f"Alpha Vantage error: {data['Error Message']}")
            return {"ticker": ticker, "price_history": [], "error": data["Error Message"]}
        
        if "Note" in data:
            logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            return {"ticker": ticker, "price_history": [], "_rate_limited": True}
        
        if "Information" in data:
            logger.warning(f"Alpha Vantage: {data['Information']}")
            return {"ticker": ticker, "price_history": [], "_rate_limited": True}
        
        time_series = data.get("Time Series (Daily)", {})
        if not time_series:
            return {"ticker": ticker, "price_history": [], "error": "No data"}
        
        price_history = []
        sorted_dates = sorted(time_series.items(), reverse=True)[:days]
        
        for date_str, values in sorted_dates:
            price_history.append({
                "date": date_str,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"]),
            })
        
        price_history.reverse()
        current_price = price_history[-1]["close"] if price_history else None
        
        logger.info(f"Alpha Vantage: {len(price_history)} days for {ticker}")
        return {"ticker": ticker, "price_history": price_history, "current_price": current_price}
        
    except Exception as e:
        logger.error(f"Alpha Vantage price error: {e}")
        return {"ticker": ticker, "price_history": [], "error": str(e)}


def fetch_company_overview(ticker: str) -> dict:
    """Fetch company overview from Alpha Vantage."""
    ticker = ticker.upper()
    
    try:
        params = {
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": get_api_key(),
        }
        
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if "Note" in data or "Information" in data:
            msg = data.get("Note") or data.get("Information")
            logger.warning(f"Alpha Vantage rate limit for {ticker}: {msg}")
            return {"name": ticker, "sector": None, "industry": None, "_rate_limited": True}
        
        if not data or "Symbol" not in data:
            logger.warning(f"No overview data for {ticker}")
            return {"name": ticker, "sector": None, "industry": None}
        
        result = {
            "name": data.get("Name", ticker),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "description": data.get("Description") or "",
            "market_cap": safe_int(data.get("MarketCapitalization")),
            "pe_ratio": safe_float(data.get("PERatio")),
            "peg_ratio": safe_float(data.get("PEGRatio")),
            "book_value": safe_float(data.get("BookValue")),
            "dividend_yield": safe_float(data.get("DividendYield")),
            "eps": safe_float(data.get("EPS")),
            "revenue_ttm": safe_int(data.get("RevenueTTM")),
            "profit_margin": safe_float(data.get("ProfitMargin")),
            "52_week_high": safe_float(data.get("52WeekHigh")),
            "52_week_low": safe_float(data.get("52WeekLow")),
            "50_day_ma": safe_float(data.get("50DayMovingAverage")),
            "200_day_ma": safe_float(data.get("200DayMovingAverage")),
            "analyst_target": safe_float(data.get("AnalystTargetPrice")),
        }
        
        logger.info(f"Alpha Vantage overview for {ticker}: sector={result['sector']}, industry={result['industry']}")
        return result
        
    except Exception as e:
        logger.error(f"Alpha Vantage overview error for {ticker}: {e}")
        return {"name": ticker, "sector": None, "industry": None, "_error": str(e)}


def fetch_earnings(ticker: str) -> dict:
    """Fetch earnings history from Alpha Vantage."""
    ticker = ticker.upper()
    
    try:
        params = {
            "function": "EARNINGS",
            "symbol": ticker,
            "apikey": get_api_key(),
        }
        
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if "Note" in data or "Information" in data:
            logger.warning(f"Alpha Vantage rate limit for earnings {ticker}")
            return {"annual_earnings": [], "quarterly_earnings": [], "_rate_limited": True}
        
        annual = data.get("annualEarnings", [])[:5]
        quarterly = data.get("quarterlyEarnings", [])[:8]
        
        return {
            "annual_earnings": [
                {"fiscal_year": e.get("fiscalDateEnding"), "eps": safe_float(e.get("reportedEPS"))}
                for e in annual
            ],
            "quarterly_earnings": [
                {
                    "fiscal_quarter": e.get("fiscalDateEnding"),
                    "reported_eps": safe_float(e.get("reportedEPS")),
                    "estimated_eps": safe_float(e.get("estimatedEPS")),
                    "surprise": safe_float(e.get("surprise")),
                    "surprise_pct": safe_float(e.get("surprisePercentage")),
                }
                for e in quarterly
            ],
        }
        
    except Exception as e:
        logger.error(f"Alpha Vantage earnings error for {ticker}: {e}")
        return {"annual_earnings": [], "quarterly_earnings": []}


def fetch_news_sentiment(ticker: str, limit: int = 50) -> list:
    """Fetch news articles with sentiment from Alpha Vantage."""
    try:
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "limit": limit,
            "apikey": get_api_key(),
        }
        
        logger.info(f"Fetching news for {ticker}...")
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if "Note" in data or "Information" in data:
            logger.warning(f"Alpha Vantage rate limit for news {ticker}")
            return []
        
        feed = data.get("feed", [])
        logger.info(f"Fetched {len(feed)} news articles for {ticker}")
        
        articles = []
        for item in feed:
            ticker_sentiment = {}
            for ts in item.get("ticker_sentiment", []):
                if ts.get("ticker") == ticker:
                    ticker_sentiment = ts
                    break
            
            articles.append({
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "source": item.get("source", "Unknown"),
                "published_at": item.get("time_published", ""),
                "overall_sentiment_score": safe_float(item.get("overall_sentiment_score")),
                "overall_sentiment_label": item.get("overall_sentiment_label", "Neutral"),
                "ticker_sentiment_score": safe_float(ticker_sentiment.get("ticker_sentiment_score")),
                "ticker_sentiment_label": ticker_sentiment.get("ticker_sentiment_label", "Neutral"),
                "relevance_score": safe_float(ticker_sentiment.get("relevance_score")),
            })
        
        return articles
        
    except Exception as e:
        logger.error(f"Alpha Vantage news error for {ticker}: {e}")
        return []


def fetch_stock_data(ticker: str) -> dict:
    """Fetch complete stock data: prices and company info."""
    ticker = ticker.upper()
    
    prices = fetch_daily_prices(ticker)
    company = fetch_company_overview(ticker)
    
    return {
        "ticker": ticker,
        "price_history": prices.get("price_history", []),
        "current_price": prices.get("current_price"),
        "company_info": company,
        "error": prices.get("error") or company.get("_error"),
    }


def fetch_news(ticker: str, limit: int = 20) -> list:
    """Fetch news articles from Alpha Vantage."""
    return fetch_news_sentiment(ticker.upper(), limit)
