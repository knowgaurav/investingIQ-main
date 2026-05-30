"""Shared ML models for the analysis pipeline: prediction, technical, sentiment.

Consolidates the classical/statistical analysis used by the Durable activity
functions (ARIMA/Prophet/ETS forecasting, RSI/MACD/Bollinger technical
indicators, and VADER/TextBlob/keyword sentiment).
"""
import logging
import re
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prediction (ARIMA + Prophet + ETS + Random Forest)
# ---------------------------------------------------------------------------

def ml_prediction(price_history: list) -> dict:
    """Run ARIMA, Prophet, ETS predictions plus a Random Forest buy/hold signal."""
    if not price_history or len(price_history) < 10:
        return _empty_prediction()

    df = pd.DataFrame(price_history)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    prices = df["close"].values
    current_price = float(prices[-1])

    arima_result = prophet_result = ets_result = rf_signal = None

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_run_arima, prices): "arima",
            executor.submit(_run_prophet, df): "prophet",
            executor.submit(_run_ets, prices): "ets",
            executor.submit(_run_random_forest_signal, df): "rf_signal",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result(timeout=60)
            except Exception as e:
                logger.error(f"{name} error: {e}")
                continue
            if name == "arima":
                arima_result = result
            elif name == "prophet":
                prophet_result = result
            elif name == "ets":
                ets_result = result
            else:
                rf_signal = result

    return _combine_predictions(current_price, arima_result, prophet_result, ets_result, rf_signal)


def _run_arima(prices: np.ndarray) -> dict:
    from statsmodels.tsa.arima.model import ARIMA

    try:
        current_price = float(prices[-1])
        best_forecast = None
        for order in [(1, 1, 0), (0, 1, 1), (1, 1, 1)]:
            try:
                fitted = ARIMA(prices, order=order).fit()
                forecast = fitted.forecast(steps=30)
                if np.std(forecast) < np.mean(forecast) * 0.1:
                    best_forecast = forecast
                    break
            except Exception:
                continue
        if best_forecast is None:
            slope = (prices[-1] - prices[-5]) / 5 if len(prices) >= 5 else 0
            best_forecast = np.array([current_price + slope * (i + 1) for i in range(30)])

        max_price, min_price = current_price * 1.15, current_price * 0.85
        daily = [round(max(min_price, min(max_price, float(f))), 2) for f in best_forecast]
        return {"forecast_7d": daily[6], "forecast_30d": daily[-1], "daily": daily}
    except Exception as e:
        logger.error(f"ARIMA error: {e}")
        return None


def _run_ets(prices: np.ndarray) -> dict:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    try:
        current_price = float(prices[-1])
        fitted = ExponentialSmoothing(
            prices, trend="add", seasonal=None, damped_trend=True,
            initialization_method="estimated",
        ).fit(optimized=True)
        forecast = fitted.forecast(steps=30)
        max_price, min_price = current_price * 1.25, current_price * 0.75
        daily = [max(min_price, min(max_price, float(f))) for f in forecast]
        return {"forecast_7d": daily[6], "forecast_30d": daily[-1], "daily": daily}
    except Exception as e:
        logger.error(f"ETS error: {e}")
        return None


def _run_prophet(df: pd.DataFrame) -> dict:
    try:
        from prophet import Prophet

        if len(df) < 30:
            return None
        prophet_df = df[["date", "close"]].copy()
        prophet_df.columns = ["ds", "y"]
        current_price = float(prophet_df["y"].iloc[-1])

        model = Prophet(
            daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=False,
            changepoint_prior_scale=0.05, seasonality_mode="additive", interval_width=0.8,
        )
        model.fit(prophet_df)
        forecast = model.predict(model.make_future_dataframe(periods=30))
        daily_raw = forecast["yhat"].tail(30).tolist()

        max_price, min_valid = current_price * 1.5, current_price * 0.5
        daily = [max(min_valid, min(max_price, float(f))) for f in daily_raw]
        if daily[6] <= 0 or daily[-1] <= 0:
            return None
        return {"forecast_7d": daily[6], "forecast_30d": daily[-1], "daily": daily}
    except Exception as e:
        logger.error(f"Prophet error: {e}")
        return None


def _run_random_forest_signal(df: pd.DataFrame) -> dict:
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import precision_score

        data = df.copy()
        data["tomorrow"] = data["close"].shift(-1)
        data["target"] = (data["tomorrow"] > data["close"]).astype(int)

        data["return_1d"] = data["close"].pct_change(1)
        data["return_5d"] = data["close"].pct_change(5)
        data["return_10d"] = data["close"].pct_change(10)
        data["sma_5"] = data["close"].rolling(5).mean()
        data["sma_10"] = data["close"].rolling(10).mean()
        data["sma_20"] = data["close"].rolling(20).mean()
        data["close_to_sma5"] = data["close"] / data["sma_5"]
        data["close_to_sma10"] = data["close"] / data["sma_10"]
        data["close_to_sma20"] = data["close"] / data["sma_20"]
        data["volatility_5d"] = data["return_1d"].rolling(5).std()
        data["volatility_10d"] = data["return_1d"].rolling(10).std()

        if "volume" in data.columns:
            data["volume_sma5"] = data["volume"].rolling(5).mean()
            data["volume_ratio"] = data["volume"] / data["volume_sma5"]
        if "high" in data.columns and "low" in data.columns:
            data["hl_range"] = (data["high"] - data["low"]) / data["close"]
            data["hl_range_sma5"] = data["hl_range"].rolling(5).mean()

        delta = data["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        data["rsi"] = 100 - (100 / (1 + gain / (loss + 1e-10)))

        data = data.dropna()
        if len(data) < 50:
            return None

        feature_cols = [
            "return_1d", "return_5d", "return_10d",
            "close_to_sma5", "close_to_sma10", "close_to_sma20",
            "volatility_5d", "volatility_10d", "rsi",
        ]
        if "volume_ratio" in data.columns:
            feature_cols.append("volume_ratio")
        if "hl_range" in data.columns:
            feature_cols.extend(["hl_range", "hl_range_sma5"])

        X, y = data[feature_cols], data["target"]
        split_idx = int(len(data) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        model = RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_split=20,
            min_samples_leaf=10, random_state=42, n_jobs=-1,
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        precision = precision_score(y_test, y_pred, zero_division=0)

        latest_features = X.iloc[-1:].values
        tomorrow_pred = model.predict(latest_features)[0]
        buy_probability = float(model.predict_proba(latest_features)[0][1])
        accuracy = float((y_pred == y_test).mean())

        importance = dict(zip(feature_cols, model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "signal": "buy" if tomorrow_pred == 1 else "hold",
            "buy_probability": round(buy_probability, 3),
            "precision": round(precision, 3),
            "accuracy": round(accuracy, 3),
            "top_features": [f[0] for f in top_features],
        }
    except Exception as e:
        logger.error(f"Random Forest error: {e}")
        return None


def _combine_predictions(current_price, arima, prophet, ets, rf_signal) -> dict:
    reasoning = []
    models = []
    if arima:
        models.append(("arima", arima, 0.3))
    if prophet:
        models.append(("prophet", prophet, 0.4))
    if ets:
        models.append(("ets", ets, 0.3))

    if not models:
        return _empty_prediction(current_price)

    total_weight = sum(w for _, _, w in models)
    models = [(n, m, w / total_weight) for n, m, w in models]

    forecast_7d = sum(m["forecast_7d"] * w for _, m, w in models)
    forecast_30d = sum(m["forecast_30d"] * w for _, m, w in models)

    max_len = max(len(m.get("daily", [])) for _, m, _ in models)
    daily_forecast = []
    for i in range(max_len):
        day_sum = sum(m["daily"][i] * w for _, m, w in models if i < len(m.get("daily", [])))
        daily_forecast.append(round(day_sum, 2))

    models_used = " + ".join(n.upper() for n, _, _ in models)

    directions = [("up" if m["forecast_30d"] > current_price else "down") for _, m, _ in models]
    if len(models) >= 2:
        if len(set(directions)) == 1:
            reasoning.append(f"All {len(models)} models agree on {directions[0]}ward movement")
            confidence = 0.85
        else:
            up = directions.count("up")
            reasoning.append(f"Models disagree: {up} bullish, {len(directions) - up} bearish")
            confidence = 0.65
    else:
        reasoning.append(f"Using {models[0][0].upper()} model only")
        confidence = 0.55

    forecast_7d_change = (forecast_7d - current_price) / current_price * 100
    forecast_30d_change = (forecast_30d - current_price) / current_price * 100

    if forecast_30d_change > 5:
        trend = "strong_upward"
    elif forecast_30d_change > 2:
        trend = "upward"
    elif forecast_30d_change < -5:
        trend = "strong_downward"
    elif forecast_30d_change < -2:
        trend = "downward"
    else:
        trend = "sideways"

    if rf_signal:
        reasoning.append(
            f"Random Forest predicts '{rf_signal['signal']}' "
            f"({rf_signal['buy_probability'] * 100:.0f}% buy probability)"
        )

    return {
        "current_price": round(current_price, 2),
        "forecast_7d": round(forecast_7d, 2),
        "forecast_7d_change": round(forecast_7d_change, 2),
        "forecast_30d": round(forecast_30d, 2),
        "forecast_30d_change": round(forecast_30d_change, 2),
        "trend": trend,
        "confidence": round(confidence, 2),
        "models_used": models_used,
        "reasoning": reasoning,
        "daily_forecast": daily_forecast,
        "arima_forecast": _model_summary(arima),
        "prophet_forecast": _model_summary(prophet),
        "ets_forecast": _model_summary(ets),
        "rf_signal": rf_signal,
    }


def _model_summary(model: dict) -> dict:
    if not model:
        return None
    return {
        "7d": round(model["forecast_7d"], 2),
        "30d": round(model["forecast_30d"], 2),
        "daily": [round(f, 2) for f in model.get("daily", [])] or None,
    }


def _empty_prediction(current_price: float = None) -> dict:
    return {
        "current_price": round(current_price, 2) if current_price else None,
        "forecast_7d": None, "forecast_7d_change": None,
        "forecast_30d": None, "forecast_30d_change": None,
        "trend": "insufficient_data", "confidence": 0.0,
        "models_used": None, "reasoning": [], "daily_forecast": [],
        "arima_forecast": None, "prophet_forecast": None,
        "ets_forecast": None, "rf_signal": None,
    }


# ---------------------------------------------------------------------------
# Technical indicators (RSI, MACD, Bollinger, support/resistance, volume)
# ---------------------------------------------------------------------------

def ml_technical(price_history: list) -> dict:
    """Calculate technical indicators from price history."""
    if not price_history or len(price_history) < 14:
        return _empty_technical()

    import ta

    df = pd.DataFrame(price_history)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    return {
        **_calc_rsi(df, ta),
        **_calc_macd(df, ta),
        **_calc_bollinger(df, ta),
        **_calc_support_resistance(df),
        **_calc_volume_signal(df),
    }


def _calc_rsi(df, ta) -> dict:
    try:
        rsi_value = ta.momentum.RSIIndicator(df["close"], window=14).rsi().iloc[-1]
        if pd.isna(rsi_value):
            return {"rsi": None, "rsi_signal": "unknown"}
        rsi_value = round(rsi_value, 2)
        signal = "overbought" if rsi_value > 70 else "oversold" if rsi_value < 30 else "neutral"
        return {"rsi": rsi_value, "rsi_signal": signal}
    except Exception as e:
        logger.error(f"RSI error: {e}")
        return {"rsi": None, "rsi_signal": "error"}


def _calc_macd(df, ta) -> dict:
    try:
        macd = ta.trend.MACD(df["close"])
        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]
        histogram = macd.macd_diff().iloc[-1]
        if pd.isna(macd_line):
            return {"macd": None, "macd_signal": "unknown", "macd_histogram": None}
        signal = "bullish" if macd_line > signal_line else "bearish" if macd_line < signal_line else "neutral"
        return {
            "macd": round(macd_line, 4),
            "macd_signal": signal,
            "macd_histogram": round(histogram, 4) if not pd.isna(histogram) else None,
        }
    except Exception as e:
        logger.error(f"MACD error: {e}")
        return {"macd": None, "macd_signal": "error", "macd_histogram": None}


def _calc_bollinger(df, ta) -> dict:
    try:
        bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
        upper = bb.bollinger_hband().iloc[-1]
        middle = bb.bollinger_mavg().iloc[-1]
        lower = bb.bollinger_lband().iloc[-1]
        current_price = df["close"].iloc[-1]
        if pd.isna(upper):
            return {
                "bollinger_upper": None, "bollinger_middle": None,
                "bollinger_lower": None, "bollinger_position": "unknown",
            }
        position = "upper" if current_price >= upper else "lower" if current_price <= lower else "middle"
        return {
            "bollinger_upper": round(upper, 2),
            "bollinger_middle": round(middle, 2),
            "bollinger_lower": round(lower, 2),
            "bollinger_position": position,
        }
    except Exception as e:
        logger.error(f"Bollinger error: {e}")
        return {
            "bollinger_upper": None, "bollinger_middle": None,
            "bollinger_lower": None, "bollinger_position": "error",
        }


def _calc_support_resistance(df) -> dict:
    try:
        highs, lows, closes = df["high"].values, df["low"].values, df["close"].values
        resistance_levels, support_levels = [], []
        for i in range(2, len(df) - 2):
            if highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 1] and highs[i] > highs[i + 2]:
                resistance_levels.append(round(highs[i], 2))
            if lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 1] and lows[i] < lows[i + 2]:
                support_levels.append(round(lows[i], 2))
        current_price = closes[-1]
        resistance_levels = sorted([r for r in resistance_levels if r > current_price])[:3]
        support_levels = sorted([s for s in support_levels if s < current_price], reverse=True)[:3]
        return {"support_levels": support_levels, "resistance_levels": resistance_levels}
    except Exception as e:
        logger.error(f"Support/Resistance error: {e}")
        return {"support_levels": [], "resistance_levels": []}


def _calc_volume_signal(df) -> dict:
    try:
        volumes = df["volume"].values
        avg_volume = volumes[-20:].mean() if len(volumes) >= 20 else volumes.mean()
        ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
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


def _empty_technical() -> dict:
    return {
        "rsi": None, "rsi_signal": "insufficient_data",
        "macd": None, "macd_signal": "insufficient_data", "macd_histogram": None,
        "bollinger_upper": None, "bollinger_middle": None,
        "bollinger_lower": None, "bollinger_position": "insufficient_data",
        "support_levels": [], "resistance_levels": [],
        "volume_signal": "insufficient_data",
    }


# ---------------------------------------------------------------------------
# Sentiment (VADER + TextBlob + keyword/phrase analysis)
# ---------------------------------------------------------------------------

_BULLISH_KEYWORDS = {
    "surge", "soar", "rally", "gain", "rise", "jump", "climb", "boost",
    "record", "high", "growth", "profit", "beat", "exceed", "strong",
    "upgrade", "buy", "bullish", "outperform", "positive", "upside",
    "breakout", "momentum", "winner", "success", "boom", "skyrocket",
    "optimistic", "recovery", "rebound", "opportunity", "overweight",
}

_BEARISH_KEYWORDS = {
    "fall", "drop", "decline", "plunge", "crash", "loss", "miss", "weak",
    "downgrade", "sell", "bearish", "underperform", "negative", "risk",
    "concern", "warning", "cut", "slash", "layoff", "recession",
    "slip", "slips", "slipped", "slide", "slides", "tumble", "sink",
    "fear", "worry", "trouble", "struggle", "fails", "failure", "down",
    "loses", "losing", "lost", "underweight", "avoid", "cautious",
    "thins", "thin", "slump", "plummets", "tanks", "dumps", "selloff",
}

_BEARISH_PHRASES = [
    "sell rating", "maintains sell", "downgrade", "price target cut",
    "stock slips", "shares fall", "stock drops", "loses ground",
    "trading thins", "year-end selling", "profit taking",
]

_BULLISH_PHRASES = [
    "buy rating", "maintains buy", "upgrade", "price target raised",
    "stock surges", "shares rise", "stock jumps", "gains ground",
    "all-time high", "record high", "strong buy",
]

_vader_analyzer = None


def _get_vader():
    global _vader_analyzer
    if _vader_analyzer is None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _vader_analyzer = SentimentIntensityAnalyzer()
    return _vader_analyzer


def ml_sentiment(headlines: list) -> dict:
    """Analyze headline sentiment using VADER, TextBlob, and keyword analysis."""
    if not headlines:
        return _empty_sentiment()

    details = []
    for headline in headlines:
        text = headline.get("title", "") if isinstance(headline, dict) else str(headline)
        if not text:
            continue
        combined = (
            _analyze_vader(text) * 0.4
            + _analyze_textblob(text) * 0.3
            + _analyze_keywords(text) * 0.3
        )
        details.append({
            "headline": text[:200],
            "score": round(combined, 3),
            "label": _score_to_label(combined),
        })

    if not details:
        return _empty_sentiment()

    overall_score = sum(d["score"] for d in details) / len(details)
    total = len(details)
    positive = sum(1 for d in details if d["label"] == "positive")
    negative = sum(1 for d in details if d["label"] == "negative")
    neutral = sum(1 for d in details if d["label"] == "neutral")

    return {
        "overall_score": round(overall_score, 3),
        "label": _score_to_label(overall_score),
        "positive_pct": round(positive / total * 100, 1),
        "neutral_pct": round(neutral / total * 100, 1),
        "negative_pct": round(negative / total * 100, 1),
        "details": details,
    }


def _analyze_vader(text: str) -> float:
    try:
        return _get_vader().polarity_scores(text)["compound"]
    except Exception:
        return 0.0


def _analyze_textblob(text: str) -> float:
    try:
        from textblob import TextBlob
        return TextBlob(text).sentiment.polarity
    except Exception:
        return 0.0


def _analyze_keywords(text: str) -> float:
    text_lower = text.lower()
    phrase_score = 0.0
    for phrase in _BEARISH_PHRASES:
        if phrase in text_lower:
            phrase_score -= 0.5
    for phrase in _BULLISH_PHRASES:
        if phrase in text_lower:
            phrase_score += 0.5
    if phrase_score != 0:
        return max(-1.0, min(1.0, phrase_score))

    words = set(re.findall(r"\b\w+\b", text_lower))
    bullish = len(words & _BULLISH_KEYWORDS)
    bearish = len(words & _BEARISH_KEYWORDS)
    total = bullish + bearish
    if total == 0:
        return 0.0
    return (bullish - bearish) / total


def _score_to_label(score: float) -> str:
    if score > 0.05:
        return "positive"
    if score < -0.05:
        return "negative"
    return "neutral"


def _empty_sentiment() -> dict:
    return {
        "overall_score": 0.0, "label": "neutral",
        "positive_pct": 0.0, "neutral_pct": 100.0, "negative_pct": 0.0,
        "details": [],
    }
