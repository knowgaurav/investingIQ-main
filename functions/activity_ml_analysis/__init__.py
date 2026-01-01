"""Activity: Run all ML-based analysis (prediction, technical, sentiment)."""
import logging

logger = logging.getLogger(__name__)


def main(input_data: dict) -> dict:
    from shared.webpubsub_utils import send_progress
    from shared.ml_models import ml_prediction, ml_technical, ml_sentiment
    
    ticker = input_data["ticker"]
    task_id = input_data["task_id"]
    stock_data = input_data["stock_data"]
    news_data = input_data["news_data"]
    
    price_history = stock_data.get("price_history", [])
    headlines = [{"title": a.get("title", "")} for a in news_data]
    
    # ML Prediction
    send_progress(task_id, 25, "Running price predictions")
    prediction_result = ml_prediction(price_history)
    
    # ML Technical
    send_progress(task_id, 35, "Calculating technical indicators")
    technical_result = ml_technical(price_history)
    
    # ML Sentiment
    send_progress(task_id, 45, "Analyzing news sentiment")
    sentiment_result = ml_sentiment(headlines)
    
    logger.info(f"ML analysis completed for {ticker}")
    
    return {
        "type": "ml_analysis",
        "data": {
            "prediction": prediction_result,
            "technical": technical_result,
            "sentiment": sentiment_result,
        }
    }
