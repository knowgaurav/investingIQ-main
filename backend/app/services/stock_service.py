"""Stock data service using yfinance with caching and circuit breaker."""
import logging
from typing import List, Optional
from datetime import datetime, timedelta

import yfinance as yf

from app.models.schemas import StockSearchResult, PriceDataPoint
from app.utils.cache import cached, CacheService
from app.utils.circuit_breaker import get_circuit, CircuitOpenError as CBOpenError

logger = logging.getLogger(__name__)

# Circuit breaker for yfinance API
yfinance_circuit = get_circuit("yfinance", failure_threshold=5, recovery_timeout=60)



# Common stock exchanges for reference
MAJOR_EXCHANGES = {
    "NYSE": "New York Stock Exchange",
    "NASDAQ": "NASDAQ",
    "AMEX": "American Stock Exchange",
}


def validate_ticker(ticker: str) -> bool:
    """
    Validate that a ticker symbol exists using yfinance.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        True if ticker is valid and has data, False otherwise
    """
    try:
        stock = yf.Ticker(ticker.upper())
        # Try to get basic info - if ticker is invalid, this will be empty or raise
        info = stock.info
        
        # Check if we got meaningful data back
        # Invalid tickers often return empty dict or dict with only 'trailingPegRatio'
        if not info:
            return False
            
        # Check for key fields that indicate a valid ticker
        # Valid tickers typically have 'regularMarketPrice' or 'previousClose'
        has_price = info.get('regularMarketPrice') or info.get('previousClose')
        has_name = info.get('shortName') or info.get('longName')
        
        return bool(has_price or has_name)
        
    except Exception as e:
        logger.warning(f"Error validating ticker {ticker}: {e}")
        return False


def autocomplete(query: str, limit: int = 10) -> List[StockSearchResult]:
    """
    Search for stocks by partial ticker or company name.
    
    Note: yfinance doesn't have a native autocomplete API, so we use
    a workaround by attempting to fetch ticker info directly.
    For production, consider using a dedicated search API.
    
    Args:
        query: Search query (partial ticker or company name)
        limit: Maximum number of results to return
        
    Returns:
        List of StockSearchResult matching the query
    """
    results: List[StockSearchResult] = []
    query = query.upper().strip()
    
    if not query or len(query) < 1:
        return results
    
    # Try the query as a direct ticker first
    try:
        stock = yf.Ticker(query)
        info = stock.info
        
        if info and (info.get('regularMarketPrice') or info.get('previousClose')):
            name = info.get('shortName') or info.get('longName') or query
            exchange = info.get('exchange', 'UNKNOWN')
            quote_type = info.get('quoteType', 'EQUITY').lower()
            
            # Map quote types to our schema
            stock_type = 'etf' if quote_type == 'etf' else 'stock'
            
            results.append(StockSearchResult(
                ticker=query,
                name=name,
                exchange=exchange,
                type=stock_type
            ))
    except Exception as e:
        logger.debug(f"Direct ticker lookup failed for {query}: {e}")
    
    # For better autocomplete, we could integrate with a search API
    # For now, try some common variations
    common_suffixes = ['', '.L', '.TO', '.AX']  # US, London, Toronto, Australia
    
    if len(results) < limit and len(query) >= 2:
        for suffix in common_suffixes:
            if len(results) >= limit:
                break
                
            test_ticker = f"{query}{suffix}"
            if test_ticker == query:  # Already tried this
                continue
                
            try:
                stock = yf.Ticker(test_ticker)
                info = stock.info
                
                if info and (info.get('regularMarketPrice') or info.get('previousClose')):
                    name = info.get('shortName') or info.get('longName') or test_ticker
                    exchange = info.get('exchange', 'UNKNOWN')
                    quote_type = info.get('quoteType', 'EQUITY').lower()
                    stock_type = 'etf' if quote_type == 'etf' else 'stock'
                    
                    # Avoid duplicates
                    if not any(r.ticker == test_ticker for r in results):
                        results.append(StockSearchResult(
                            ticker=test_ticker,
                            name=name,
                            exchange=exchange,
                            type=stock_type
                        ))
            except Exception as e:
                logger.debug(f"Suffix lookup failed for {test_ticker}: {e}")
    
    return results[:limit]


@cached("stock_data", ttl=CacheService.TTL_MEDIUM)  # Cache for 5 minutes
def fetch_stock_data(ticker: str, period: str = "1y") -> dict:
    """
    Fetch stock price history and company information from yfinance.
    
    Results are cached for 5 minutes to reduce API calls.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period for historical data (default: '1y')
                Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        
    Returns:
        dict containing:
            - ticker: The ticker symbol
            - company_info: Company metadata (name, sector, industry, etc.)
            - price_history: List of PriceDataPoint dicts
            - current_price: Current/latest price
            - status: 'success' or 'error'
            - error: Error message if status is 'error'
    """
    result = {
        "ticker": ticker.upper(),
        "company_info": {},
        "price_history": [],
        "current_price": None,
        "status": "success",
        "error": None
    }
    
    try:
        stock = yf.Ticker(ticker.upper())
        
        # Fetch company info
        info = stock.info
        if not info or not (info.get('regularMarketPrice') or info.get('previousClose')):
            result["status"] = "error"
            result["error"] = f"Invalid ticker symbol: {ticker}"
            return result
        
        result["company_info"] = {
            "name": info.get('shortName') or info.get('longName'),
            "long_name": info.get('longName'),
            "sector": info.get('sector'),
            "industry": info.get('industry'),
            "country": info.get('country'),
            "website": info.get('website'),
            "description": info.get('longBusinessSummary'),
            "market_cap": info.get('marketCap'),
            "employees": info.get('fullTimeEmployees'),
            "exchange": info.get('exchange'),
            "currency": info.get('currency', 'USD'),
            "quote_type": info.get('quoteType'),
            "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
            "fifty_two_week_low": info.get('fiftyTwoWeekLow'),
            "dividend_yield": info.get('dividendYield'),
            "pe_ratio": info.get('trailingPE'),
            "eps": info.get('trailingEps'),
        }
        
        result["current_price"] = info.get('regularMarketPrice') or info.get('previousClose')
        
        # Fetch historical price data
        history = stock.history(period=period)
        
        if history.empty:
            logger.warning(f"No historical data found for {ticker}")
        else:
            price_history: List[dict] = []
            
            for date, row in history.iterrows():
                # Convert pandas Timestamp to datetime
                if hasattr(date, 'to_pydatetime'):
                    dt = date.to_pydatetime()
                else:
                    dt = datetime.fromisoformat(str(date))
                
                # Remove timezone info for consistency
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                
                price_point = PriceDataPoint(
                    date=dt,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
                price_history.append(price_point.model_dump())
            
            result["price_history"] = price_history
            
        logger.info(f"Successfully fetched data for {ticker}: {len(result['price_history'])} price points")
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {ticker}: {e}")
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


def get_current_price(ticker: str) -> Optional[float]:
    """
    Get the current/latest price for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Current price as float, or None if unavailable
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        return info.get('regularMarketPrice') or info.get('previousClose')
    except Exception as e:
        logger.error(f"Error getting current price for {ticker}: {e}")
        return None
