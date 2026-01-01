"""Stock search service using Alpha Vantage API.

Note: Stock data fetching is handled by Azure Functions, not the backend.
This service only handles search/autocomplete for the search bar.
"""
import logging
from typing import List
import requests

from app.models.schemas import StockSearchResult
from app.config import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "https://www.alphavantage.co/query"


def _get_api_key() -> str:
    """Get Alpha Vantage API key from settings."""
    settings = get_settings()
    key = settings.alpha_vantage_api_key
    if not key:
        raise ValueError("ALPHA_VANTAGE_API_KEY not configured")
    return key


def autocomplete(query: str, limit: int = 10) -> List[StockSearchResult]:
    """Search for stocks using Alpha Vantage SYMBOL_SEARCH."""
    results: List[StockSearchResult] = []
    query = query.upper().strip()
    
    if not query or len(query) < 1:
        return results
    
    try:
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": query,
            "apikey": _get_api_key(),
        }
        
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if "Note" in data or "Information" in data:
            logger.warning(f"Alpha Vantage rate limit hit for search")
            return results
        
        matches = data.get("bestMatches", [])
        
        for match in matches[:limit]:
            symbol = match.get("1. symbol", "")
            name = match.get("2. name", symbol)
            stock_type = match.get("3. type", "Equity")
            region = match.get("4. region", "")
            
            results.append(StockSearchResult(
                ticker=symbol,
                name=name,
                exchange=region,
                type="etf" if "ETF" in stock_type.upper() else "stock"
            ))
            
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
    
    return results


def validate_ticker(ticker: str) -> bool:
    """Validate that a ticker symbol exists by checking if search returns it."""
    try:
        results = autocomplete(ticker, limit=5)
        return any(r.ticker.upper() == ticker.upper() for r in results)
    except Exception as e:
        logger.warning(f"Error validating ticker {ticker}: {e}")
        return False


# Backward compatibility aliases
def search_stocks(query: str, limit: int = 10) -> List[StockSearchResult]:
    """Alias for autocomplete."""
    return autocomplete(query, limit)
