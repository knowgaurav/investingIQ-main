"""ML Technical Analysis Azure Function - RSI, MACD, Bollinger Bands."""
import json
import logging
from datetime import datetime

import azure.functions as func
import pandas as pd
import ta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(msg: func.ServiceBusMessage, outputSbMsg: func.Out[str]):
    """
    Process technical analysis using ta library.
    
    Triggered by: ml-queue (task_type: ml_technical)
    Outputs to: aggregate-queue
    """
    from shared.webpubsub_utils import send_progress
    
    try:
        message = json.loads(msg.get_body().decode('utf-8'))
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        price_history = message.get("data", {}).get("price_history", [])
        
        logger.info(f"Running technical analysis for {ticker}, task_id: {task_id}")
        send_progress(task_id, 30, "Calculating technical indicators")
        
        result = calculate_technical_indicators(price_history)
        
        output_message = {
            "task_type": "ml_technical_ready",
            "task_id": task_id,
            "ticker": ticker,
            "data": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        outputSbMsg.set(json.dumps(output_message))
        logger.info(f"Completed technical analysis for {ticker}")
        
    except Exception as e:
        logger.error(f"Technical analysis error: {e}")
        raise


def calculate_technical_indicators(price_history: list) -> dict:
    """Calculate all technical indicators."""
    if not price_history or len(price_history) < 14:
        return empty_technical_result()
    
    df = pd.DataFrame(price_history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    result = {
        **calculate_rsi(df),
        **calculate_macd(df),
        **calculate_bollinger(df),
        **calculate_support_resistance(df),
        **calculate_volume_signal(df),
    }
    
    return result


def calculate_rsi(df: pd.DataFrame) -> dict:
    """Calculate RSI indicator."""
    try:
        rsi = ta.momentum.RSIIndicator(df['close'], window=14)
        rsi_value = rsi.rsi().iloc[-1]
        
        if pd.isna(rsi_value):
            return {"rsi": None, "rsi_signal": "unknown"}
        
        rsi_value = round(rsi_value, 2)
        
        if rsi_value > 70:
            signal = "overbought"
        elif rsi_value < 30:
            signal = "oversold"
        else:
            signal = "neutral"
        
        return {"rsi": rsi_value, "rsi_signal": signal}
    except Exception as e:
        logger.error(f"RSI error: {e}")
        return {"rsi": None, "rsi_signal": "error"}


def calculate_macd(df: pd.DataFrame) -> dict:
    """Calculate MACD indicator."""
    try:
        macd = ta.trend.MACD(df['close'])
        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]
        histogram = macd.macd_diff().iloc[-1]
        
        if pd.isna(macd_line):
            return {"macd": None, "macd_signal": "unknown", "macd_histogram": None}
        
        if macd_line > signal_line:
            signal = "bullish"
        elif macd_line < signal_line:
            signal = "bearish"
        else:
            signal = "neutral"
        
        return {
            "macd": round(macd_line, 4),
            "macd_signal": signal,
            "macd_histogram": round(histogram, 4) if not pd.isna(histogram) else None,
        }
    except Exception as e:
        logger.error(f"MACD error: {e}")
        return {"macd": None, "macd_signal": "error", "macd_histogram": None}


def calculate_bollinger(df: pd.DataFrame) -> dict:
    """Calculate Bollinger Bands."""
    try:
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        
        upper = bb.bollinger_hband().iloc[-1]
        middle = bb.bollinger_mavg().iloc[-1]
        lower = bb.bollinger_lband().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if pd.isna(upper):
            return {
                "bollinger_upper": None,
                "bollinger_middle": None,
                "bollinger_lower": None,
                "bollinger_position": "unknown",
            }
        
        if current_price >= upper:
            position = "upper"
        elif current_price <= lower:
            position = "lower"
        else:
            position = "middle"
        
        return {
            "bollinger_upper": round(upper, 2),
            "bollinger_middle": round(middle, 2),
            "bollinger_lower": round(lower, 2),
            "bollinger_position": position,
        }
    except Exception as e:
        logger.error(f"Bollinger error: {e}")
        return {
            "bollinger_upper": None,
            "bollinger_middle": None,
            "bollinger_lower": None,
            "bollinger_position": "error",
        }


def calculate_support_resistance(df: pd.DataFrame) -> dict:
    """Calculate support and resistance levels."""
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        resistance_levels = []
        support_levels = []
        
        for i in range(2, len(df) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                resistance_levels.append(round(highs[i], 2))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                support_levels.append(round(lows[i], 2))
        
        current_price = closes[-1]
        resistance_levels = sorted([r for r in resistance_levels if r > current_price])[:3]
        support_levels = sorted([s for s in support_levels if s < current_price], reverse=True)[:3]
        
        return {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
        }
    except Exception as e:
        logger.error(f"Support/Resistance error: {e}")
        return {"support_levels": [], "resistance_levels": []}


def calculate_volume_signal(df: pd.DataFrame) -> dict:
    """Calculate volume signal."""
    try:
        volumes = df['volume'].values
        avg_volume = volumes[-20:].mean() if len(volumes) >= 20 else volumes.mean()
        current_volume = volumes[-1]
        
        ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        if ratio > 2:
            signal = "unusual_spike"
        elif ratio > 1.5:
            signal = "high"
        elif ratio < 0.5:
            signal = "low"
        else:
            signal = "normal"
        
        return {"volume_signal": signal, "volume_ratio": round(ratio, 2)}
    except Exception as e:
        logger.error(f"Volume error: {e}")
        return {"volume_signal": "error", "volume_ratio": None}


def empty_technical_result() -> dict:
    """Return empty technical result."""
    return {
        "rsi": None,
        "rsi_signal": "insufficient_data",
        "macd": None,
        "macd_signal": "insufficient_data",
        "macd_histogram": None,
        "bollinger_upper": None,
        "bollinger_middle": None,
        "bollinger_lower": None,
        "bollinger_position": "insufficient_data",
        "support_levels": [],
        "resistance_levels": [],
        "volume_signal": "insufficient_data",
    }
