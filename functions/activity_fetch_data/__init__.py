"""Activity: Fetch stock data and news from Alpha Vantage."""
import logging

logger = logging.getLogger(__name__)


def main(input_data: dict) -> dict:
    from shared.alpha_vantage import fetch_stock_data, fetch_earnings, fetch_news
    from shared.webpubsub_utils import send_progress
    
    ticker = input_data["ticker"]
    task_id = input_data["task_id"]
    
    send_progress(task_id, 5, "Fetching stock data")
    stock_data = fetch_stock_data(ticker)
    
    send_progress(task_id, 8, "Fetching earnings data")
    earnings = fetch_earnings(ticker)
    stock_data["earnings"] = earnings
    
    send_progress(task_id, 12, "Fetching news")
    news_data = fetch_news(ticker, max_articles=20)
    
    logger.info(f"Fetched data for {ticker}: {len(stock_data.get('price_history', []))} prices, {len(news_data)} news")
    
    return {
        "stock_data": stock_data,
        "news_data": news_data,
    }
