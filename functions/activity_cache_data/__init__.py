"""Activity: Cache data in Redis for LLM tool access."""
import logging

logger = logging.getLogger(__name__)


def main(input_data: dict) -> bool:
    from shared.cache import get_stock_cache
    
    ticker = input_data["ticker"]
    stock_data = input_data["stock_data"]
    news_data = input_data["news_data"]
    
    cache = get_stock_cache()
    
    cache.set_prices(ticker, stock_data.get("price_history", []))
    if stock_data.get("company_info"):
        cache.set_company_info(ticker, stock_data.get("company_info", {}))
    if stock_data.get("earnings"):
        cache.set_earnings(ticker, stock_data.get("earnings", {}))
    cache.set_news(ticker, news_data)
    
    logger.info(f"Cached all data for {ticker} in Redis")
    return True
