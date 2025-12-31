"""ML Prediction Azure Function - ARIMA forecasting (fast, lightweight)."""
import json
import logging
from datetime import datetime
import warnings

import azure.functions as func
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(msg: func.ServiceBusMessage, outputSbMsg: func.Out[str]):
    """
    Process ML prediction tasks using ARIMA.
    
    Triggered by: ml-prediction-queue
    Outputs to: aggregate-queue
    """
    from shared.webpubsub_utils import send_progress
    
    try:
        message = json.loads(msg.get_body().decode('utf-8'))
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        price_history = message.get("data", {}).get("price_history", [])
        
        logger.info(f"Running ML prediction for {ticker}, task_id: {task_id}")
        send_progress(task_id, 25, "Running price predictions")
        
        result = run_predictions(price_history)
        
        output_message = {
            "task_type": "ml_prediction_ready",
            "task_id": task_id,
            "ticker": ticker,
            "data": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        outputSbMsg.set(json.dumps(output_message))
        logger.info(f"Completed ML prediction for {ticker}")
        
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        raise


def run_predictions(price_history: list) -> dict:
    """Run ARIMA predictions on price data."""
    if not price_history or len(price_history) < 10:
        return {
            "forecast_7d": None,
            "forecast_7d_change": None,
            "forecast_30d": None,
            "forecast_30d_change": None,
            "trend": "insufficient_data",
            "confidence": 0.0,
        }
    
    df = pd.DataFrame(price_history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    prices = df['close'].values
    current_price = prices[-1]
    
    try:
        model = ARIMA(prices, order=(2, 1, 2))
        fitted = model.fit()
        forecast = fitted.forecast(steps=30)
        
        forecast_7d = forecast[6]
        forecast_30d = forecast[-1]
        
        forecast_7d_change = (forecast_7d - current_price) / current_price * 100
        forecast_30d_change = (forecast_30d - current_price) / current_price * 100
        
        if forecast_30d_change > 2:
            trend = "upward"
        elif forecast_30d_change < -2:
            trend = "downward"
        else:
            trend = "sideways"
        
        recent_volatility = np.std(prices[-10:]) / np.mean(prices[-10:])
        confidence = max(0.4, min(0.85, 0.7 - recent_volatility))
        
        return {
            "forecast_7d": round(forecast_7d, 2),
            "forecast_7d_change": round(forecast_7d_change, 2),
            "forecast_30d": round(forecast_30d, 2),
            "forecast_30d_change": round(forecast_30d_change, 2),
            "trend": trend,
            "confidence": round(confidence, 2),
            "current_price": round(current_price, 2),
        }
        
    except Exception as e:
        logger.error(f"ARIMA error: {e}")
        return {
            "forecast_7d": None,
            "forecast_7d_change": None,
            "forecast_30d": None,
            "forecast_30d_change": None,
            "trend": "error",
            "confidence": 0.0,
            "current_price": round(current_price, 2),
        }
