"""ML Prediction Azure Function - ARIMA + Prophet forecasting."""
import json
import logging
from datetime import datetime, timedelta
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

import azure.functions as func
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(msg: func.ServiceBusMessage, outputSbMsg: func.Out[str]):
    """
    Process ML prediction tasks using ARIMA and Prophet.
    
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
        send_progress(task_id, 25, "Running price predictions (ARIMA + Prophet)")
        
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
    """Run ARIMA, Prophet, ETS predictions + Random Forest buy/sell signal."""
    logger.info(f"run_predictions called with {len(price_history) if price_history else 0} price records")
    
    if not price_history or len(price_history) < 10:
        logger.warning(f"Insufficient price data: {len(price_history) if price_history else 0} records (need 10+)")
        return empty_result()
    
    df = pd.DataFrame(price_history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    prices = df['close'].values
    current_price = float(prices[-1])
    
    arima_result = None
    prophet_result = None
    ets_result = None
    rf_signal = None
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_arima, prices): 'arima',
            executor.submit(run_prophet, df): 'prophet',
            executor.submit(run_ets, prices): 'ets',
            executor.submit(run_random_forest_signal, df): 'rf_signal',
        }
        
        for future in as_completed(futures):
            model_name = futures[future]
            try:
                result = future.result(timeout=60)
                if model_name == 'arima':
                    arima_result = result
                elif model_name == 'prophet':
                    prophet_result = result
                elif model_name == 'ets':
                    ets_result = result
                else:
                    rf_signal = result
            except Exception as e:
                logger.error(f"{model_name} error: {e}")
    
    return combine_predictions(current_price, arima_result, prophet_result, ets_result, rf_signal)


def run_arima(prices: np.ndarray) -> dict:
    """Run ARIMA model for 30-day daily forecasts with smoothing."""
    try:
        current_price = float(prices[-1])
        logger.info(f"ARIMA: Starting with {len(prices)} prices, current: ${current_price:.2f}")
        
        # Use simple ARIMA(1,1,0) or (0,1,1) which are more stable for stock data
        best_forecast = None
        best_order = None
        
        # Simpler orders that don't produce oscillations
        orders_to_try = [(1, 1, 0), (0, 1, 1), (1, 1, 1)]
        
        for order in orders_to_try:
            try:
                model = ARIMA(prices, order=order)
                fitted = model.fit()
                forecast = fitted.forecast(steps=30)
                
                # Check if forecast is stable (not oscillating wildly)
                forecast_std = np.std(forecast)
                forecast_mean = np.mean(forecast)
                
                # If standard deviation is less than 10% of mean, it's stable
                if forecast_std < forecast_mean * 0.1:
                    best_forecast = forecast
                    best_order = order
                    break
            except:
                continue
        
        if best_forecast is None:
            # Fallback: use simple linear extrapolation
            logger.warning("ARIMA unstable, using linear trend")
            slope = (prices[-1] - prices[-5]) / 5 if len(prices) >= 5 else 0
            best_forecast = np.array([current_price + slope * (i + 1) for i in range(30)])
            best_order = "linear"
        
        logger.info(f"ARIMA: Using order {best_order}")
        
        # Cap predictions to +/- 15% of current price (conservative for 30 days)
        max_price = current_price * 1.15
        min_price = current_price * 0.85
        
        daily_forecast = []
        for f in best_forecast:
            capped = max(min_price, min(max_price, float(f)))
            daily_forecast.append(round(capped, 2))
        
        logger.info(f"ARIMA: 7d=${daily_forecast[6]:.2f}, 30d=${daily_forecast[-1]:.2f}")
        
        return {
            "forecast_7d": daily_forecast[6],
            "forecast_30d": daily_forecast[-1],
            "daily": daily_forecast,
        }
    except Exception as e:
        logger.error(f"ARIMA fitting error: {e}", exc_info=True)
        return None


def run_random_forest_signal(df: pd.DataFrame) -> dict:
    """Random Forest classifier for buy/sell signal prediction."""
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import precision_score
        
        logger.info(f"RF: Starting with {len(df)} records")
        data = df.copy()
        
        # Create target: 1 if tomorrow's close > today's close
        data['tomorrow'] = data['close'].shift(-1)
        data['target'] = (data['tomorrow'] > data['close']).astype(int)
        
        # Feature engineering for better accuracy
        # Price-based features
        data['return_1d'] = data['close'].pct_change(1)
        data['return_5d'] = data['close'].pct_change(5)
        data['return_10d'] = data['close'].pct_change(10)
        
        # Moving averages
        data['sma_5'] = data['close'].rolling(5).mean()
        data['sma_10'] = data['close'].rolling(10).mean()
        data['sma_20'] = data['close'].rolling(20).mean()
        
        # Price relative to MAs
        data['close_to_sma5'] = data['close'] / data['sma_5']
        data['close_to_sma10'] = data['close'] / data['sma_10']
        data['close_to_sma20'] = data['close'] / data['sma_20']
        
        # Volatility
        data['volatility_5d'] = data['return_1d'].rolling(5).std()
        data['volatility_10d'] = data['return_1d'].rolling(10).std()
        
        # Volume features (if available)
        if 'volume' in data.columns:
            data['volume_sma5'] = data['volume'].rolling(5).mean()
            data['volume_ratio'] = data['volume'] / data['volume_sma5']
        
        # High-Low range
        if 'high' in data.columns and 'low' in data.columns:
            data['hl_range'] = (data['high'] - data['low']) / data['close']
            data['hl_range_sma5'] = data['hl_range'].rolling(5).mean()
        
        # RSI-like momentum
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Drop NaN rows
        data = data.dropna()
        
        if len(data) < 50:
            logger.warning("Insufficient data for Random Forest after feature engineering")
            return None
        
        # Select features
        feature_cols = [
            'return_1d', 'return_5d', 'return_10d',
            'close_to_sma5', 'close_to_sma10', 'close_to_sma20',
            'volatility_5d', 'volatility_10d', 'rsi'
        ]
        
        # Add optional features if available
        if 'volume_ratio' in data.columns:
            feature_cols.append('volume_ratio')
        if 'hl_range' in data.columns:
            feature_cols.extend(['hl_range', 'hl_range_sma5'])
        
        X = data[feature_cols]
        y = data['target']
        
        # Train/test split - use last 20% for testing
        split_idx = int(len(data) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Train Random Forest with tuned hyperparameters
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Get predictions and probabilities
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)
        
        # Calculate precision
        precision = precision_score(y_test, y_pred, zero_division=0)
        
        # Predict tomorrow using latest data
        latest_features = X.iloc[-1:].values
        tomorrow_pred = model.predict(latest_features)[0]
        tomorrow_proba = model.predict_proba(latest_features)[0]
        
        # Buy probability (probability of price going up)
        buy_probability = float(tomorrow_proba[1])
        
        # Historical accuracy from backtest
        accuracy = float((y_pred == y_test).mean())
        
        # Feature importance
        importance = dict(zip(feature_cols, model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]
        
        result = {
            "signal": "buy" if tomorrow_pred == 1 else "hold",
            "buy_probability": round(buy_probability, 3),
            "precision": round(precision, 3),
            "accuracy": round(accuracy, 3),
            "top_features": [f[0] for f in top_features],
        }
        logger.info(f"RF: Success - signal={result['signal']}, prob={buy_probability:.2f}, acc={accuracy:.2f}")
        return result
        
    except Exception as e:
        logger.error(f"Random Forest error: {e}", exc_info=True)
        return None


def run_ets(prices: np.ndarray) -> dict:
    """Run Exponential Smoothing (Holt-Winters) for 30-day forecasts."""
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        
        current_price = float(prices[-1])
        logger.info(f"ETS: Starting with {len(prices)} prices, current: ${current_price:.2f}")
        
        # Use additive trend, no seasonality for daily stock data
        model = ExponentialSmoothing(
            prices,
            trend='add',
            seasonal=None,
            damped_trend=True,
            initialization_method='estimated',
        )
        fitted = model.fit(optimized=True)
        forecast = fitted.forecast(steps=30)
        
        # Cap predictions to +/- 25% (ETS is conservative)
        max_price = current_price * 1.25
        min_price = current_price * 0.75
        
        daily_forecast = []
        for f in forecast:
            capped = max(min_price, min(max_price, float(f)))
            daily_forecast.append(capped)
        
        logger.info(f"ETS: Success - 30d forecast: ${daily_forecast[-1]:.2f}")
        return {
            "forecast_7d": daily_forecast[6],
            "forecast_30d": daily_forecast[-1],
            "daily": daily_forecast,
        }
    except Exception as e:
        logger.error(f"ETS fitting error: {e}", exc_info=True)
        return None


def run_prophet(df: pd.DataFrame) -> dict:
    """Run Prophet model for 30-day daily forecasts using historical data."""
    try:
        from prophet import Prophet
        import warnings
        warnings.filterwarnings('ignore')
        
        logger.info(f"Prophet: Starting with {len(df)} days of historical data")
        
        if len(df) < 30:
            logger.warning("Prophet: Not enough data (need 30+ days)")
            return None
        
        prophet_df = df[['date', 'close']].copy()
        prophet_df.columns = ['ds', 'y']
        
        current_price = float(prophet_df['y'].iloc[-1])
        
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False,  # Keep simple
            changepoint_prior_scale=0.05,
            seasonality_mode='additive',
            interval_width=0.8,
        )
        model.fit(prophet_df)
        
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)
        
        # Get daily forecasts (last 30 rows are future predictions)
        daily_raw = forecast['yhat'].tail(30).tolist()
        
        # Validate and cap predictions to +/- 50% of current price
        max_price = current_price * 1.5
        min_valid = current_price * 0.5
        
        daily_forecast = [max(min_valid, min(max_price, float(f))) for f in daily_raw]
        
        forecast_7d = daily_forecast[6]
        forecast_30d = daily_forecast[-1]
        
        # If predictions are invalid, return None
        if forecast_7d <= 0 or forecast_30d <= 0:
            logger.warning(f"Prophet produced invalid predictions")
            return None
        
        logger.info(f"Prophet: Success - 7d=${forecast_7d:.2f}, 30d=${forecast_30d:.2f}")
        
        return {
            "forecast_7d": forecast_7d,
            "forecast_30d": forecast_30d,
            "daily": daily_forecast,
        }
    except Exception as e:
        logger.error(f"Prophet fitting error: {e}", exc_info=True)
        return None


def combine_predictions(current_price: float, arima: dict, prophet: dict, ets: dict = None, rf_signal: dict = None) -> dict:
    """Combine ARIMA, Prophet, ETS predictions + Random Forest signal."""
    
    reasoning = []
    daily_forecast = []
    arima_daily = []
    prophet_daily = []
    ets_daily = []
    
    # Count successful models
    models = []
    if arima:
        models.append(('arima', arima, 0.3))
        arima_daily = arima.get('daily', [])
        logger.info(f"ARIMA added to ensemble: 30d=${arima['forecast_30d']:.2f}")
    else:
        logger.warning("ARIMA returned None")
        
    if prophet:
        models.append(('prophet', prophet, 0.4))
        prophet_daily = prophet.get('daily', [])
        logger.info(f"Prophet added to ensemble: 30d=${prophet['forecast_30d']:.2f}")
    else:
        logger.warning("Prophet returned None")
        
    if ets:
        models.append(('ets', ets, 0.3))
        ets_daily = ets.get('daily', [])
        logger.info(f"ETS added to ensemble: 30d=${ets['forecast_30d']:.2f}")
    else:
        logger.warning("ETS returned None")
    
    logger.info(f"Models in ensemble: {len(models)}")
    
    if not models:
        logger.error("All prediction models failed!")
        return empty_result(current_price)
    
    # Normalize weights
    total_weight = sum(w for _, _, w in models)
    models = [(n, m, w / total_weight) for n, m, w in models]
    
    # Calculate weighted forecasts
    forecast_7d = sum(m['forecast_7d'] * w for _, m, w in models)
    forecast_30d = sum(m['forecast_30d'] * w for _, m, w in models)
    
    # Combine daily forecasts
    if len(models) > 0:
        max_len = max(len(m.get('daily', [])) for _, m, _ in models)
        daily_forecast = []
        for i in range(max_len):
            day_sum = 0
            for name, m, w in models:
                daily = m.get('daily', [])
                if i < len(daily):
                    day_sum += daily[i] * w
            daily_forecast.append(round(day_sum, 2))
    
    # Build models_used string and check agreement
    model_names = [n.upper() for n, _, _ in models]
    models_used = " + ".join(model_names)
    
    # Check model agreement for confidence
    directions = []
    for name, m, _ in models:
        direction = "up" if m['forecast_30d'] > current_price else "down"
        directions.append((name, direction))
    
    unique_directions = set(d for _, d in directions)
    
    if len(models) >= 2:
        if len(unique_directions) == 1:
            direction = directions[0][1]
            reasoning.append(f"All {len(models)} models agree on {direction}ward movement")
            confidence = 0.85
        else:
            up_count = sum(1 for _, d in directions if d == 'up')
            down_count = len(directions) - up_count
            majority = "up" if up_count > down_count else "down"
            reasoning.append(f"Models disagree: {up_count} bullish, {down_count} bearish - majority {majority}ward")
            confidence = 0.65
    elif len(models) == 1:
        model_name = models[0][0].upper()
        reasoning.append(f"Using {model_name} model only (other models failed)")
        confidence = 0.55
    
    forecast_7d_change = (forecast_7d - current_price) / current_price * 100
    forecast_30d_change = (forecast_30d - current_price) / current_price * 100
    
    # Determine trend and add reasoning
    if forecast_30d_change > 5:
        trend = "strong_upward"
        reasoning.append(f"Strong bullish signal: +{forecast_30d_change:.1f}% predicted in 30 days")
    elif forecast_30d_change > 2:
        trend = "upward"
        reasoning.append(f"Moderate bullish signal: +{forecast_30d_change:.1f}% predicted in 30 days")
    elif forecast_30d_change < -5:
        trend = "strong_downward"
        reasoning.append(f"Strong bearish signal: {forecast_30d_change:.1f}% predicted in 30 days")
    elif forecast_30d_change < -2:
        trend = "downward"
        reasoning.append(f"Moderate bearish signal: {forecast_30d_change:.1f}% predicted in 30 days")
    else:
        trend = "sideways"
        reasoning.append("Price expected to remain stable with minimal movement")
    
    # Add methodology explanation
    if arima:
        reasoning.append("ARIMA: Captures short-term momentum from recent price patterns")
    if prophet:
        reasoning.append("Prophet: Identifies weekly/seasonal trends and changepoints")
    if ets:
        reasoning.append("ETS: Exponential smoothing for trend extrapolation")
    if rf_signal:
        reasoning.append(f"Random Forest: ML classifier predicts '{rf_signal['signal']}' with {rf_signal['buy_probability']*100:.0f}% confidence")
    
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
        "arima_forecast": {
            "7d": round(arima['forecast_7d'], 2) if arima else None,
            "30d": round(arima['forecast_30d'], 2) if arima else None,
            "daily": [round(f, 2) for f in arima_daily] if arima_daily else None,
        } if arima else None,
        "prophet_forecast": {
            "7d": round(prophet['forecast_7d'], 2) if prophet else None,
            "30d": round(prophet['forecast_30d'], 2) if prophet else None,
            "daily": [round(f, 2) for f in prophet_daily] if prophet_daily else None,
        } if prophet else None,
        "ets_forecast": {
            "7d": round(ets['forecast_7d'], 2) if ets else None,
            "30d": round(ets['forecast_30d'], 2) if ets else None,
            "daily": [round(f, 2) for f in ets_daily] if ets_daily else None,
        } if ets else None,
        "rf_signal": rf_signal,
    }


def empty_result(current_price: float = None) -> dict:
    """Return empty prediction result."""
    return {
        "current_price": round(current_price, 2) if current_price else None,
        "forecast_7d": None,
        "forecast_7d_change": None,
        "forecast_30d": None,
        "forecast_30d_change": None,
        "trend": "insufficient_data",
        "confidence": 0.0,
        "models_used": None,
        "arima_forecast": None,
        "prophet_forecast": None,
    }
