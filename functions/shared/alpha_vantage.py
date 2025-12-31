"""Alpha Vantage API client for stock data, news, and company info."""
import os
import logging
from datetime import datetime
from typing import Optional
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.alphavantage.co/query"


def get_api_key() -> str:
    """Get Alpha Vantage API key from environment."""
    key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not key:
        raise ValueError("ALPHA_VANTAGE_API_KEY not set")
    return key


def fetch_daily_prices(ticker: str, outputsize: str = "compact") -> dict:
    """
    Fetch daily price data from Alpha Vantage.
    
    Args:
        ticker: Stock symbol (e.g., "AAPL")
        outputsize: "compact" (100 days) or "full" (20+ years)
    
    Returns:
        Dict with price_history, current_price, ticker
    """
    try:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": outputsize,
            "apikey": get_api_key(),
        }
        
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if "Error Message" in data:
            logger.error(f"Alpha Vantage error: {data['Error Message']}")
            return {"ticker": ticker, "price_history": [], "error": data["Error Message"]}
        
        if "Note" in data:
            logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            return {"ticker": ticker, "price_history": [], "error": "Rate limit exceeded"}
        
        time_series = data.get("Time Series (Daily)", {})
        
        price_history = []
        for date_str, values in sorted(time_series.items(), reverse=True)[:30]:
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
        
        return {
            "ticker": ticker,
            "price_history": price_history,
            "current_price": current_price,
        }
        
    except Exception as e:
        logger.error(f"Error fetching daily prices for {ticker}: {e}")
        return {"ticker": ticker, "price_history": [], "error": str(e)}


def fetch_company_overview(ticker: str) -> dict:
    """
    Fetch company information and key metrics from Alpha Vantage.
    
    Returns company name, sector, industry, description, market cap, PE ratio, etc.
    """
    try:
        params = {
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": get_api_key(),
        }
        
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if not data or "Symbol" not in data:
            return {"name": ticker, "error": "No data available"}
        
        return {
            "name": data.get("Name", ticker),
            "sector": data.get("Sector", "Unknown"),
            "industry": data.get("Industry", "Unknown"),
            "description": data.get("Description", ""),
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
        
    except Exception as e:
        logger.error(f"Error fetching company overview for {ticker}: {e}")
        return {"name": ticker, "error": str(e)}


def fetch_news_sentiment(ticker: str, limit: int = 50) -> list:
    """
    Fetch news articles with sentiment from Alpha Vantage.
    
    Returns list of articles with title, summary, url, source, sentiment scores.
    """
    try:
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "limit": limit,
            "apikey": get_api_key(),
        }
        
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if "Note" in data:
            logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            return []
        
        feed = data.get("feed", [])
        
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
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []


def fetch_earnings(ticker: str) -> dict:
    """
    Fetch earnings history and estimates from Alpha Vantage.
    """
    try:
        params = {
            "function": "EARNINGS",
            "symbol": ticker,
            "apikey": get_api_key(),
        }
        
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        annual = data.get("annualEarnings", [])[:5]
        quarterly = data.get("quarterlyEarnings", [])[:8]
        
        return {
            "annual_earnings": [
                {
                    "fiscal_year": e.get("fiscalDateEnding"),
                    "eps": safe_float(e.get("reportedEPS")),
                }
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
        logger.error(f"Error fetching earnings for {ticker}: {e}")
        return {"annual_earnings": [], "quarterly_earnings": []}


def fetch_stock_data(ticker: str) -> dict:
    """
    Fetch complete stock data: prices, company info, and earnings.
    
    Combines multiple API calls into one comprehensive result.
    """
    ticker = ticker.upper()
    
    prices = fetch_daily_prices(ticker)
    company = fetch_company_overview(ticker)
    
    return {
        "ticker": ticker,
        "price_history": prices.get("price_history", []),
        "current_price": prices.get("current_price"),
        "company_info": company,
        "error": prices.get("error") or company.get("error"),
    }


def fetch_news(ticker: str, limit: int = 20) -> list:
    """
    Fetch news articles for sentiment analysis.
    
    Returns list with title, summary, sentiment scores.
    """
    return fetch_news_sentiment(ticker.upper(), limit)


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
        return int(value)
    except (ValueError, TypeError):
        return None
