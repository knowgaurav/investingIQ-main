'use client';

import ForecastChart from './ForecastChart';

interface MLAnalysisViewProps {
    prediction?: {
        forecast_7d: number | null;
        forecast_7d_change: number | null;
        forecast_30d: number | null;
        forecast_30d_change: number | null;
        trend: string;
        confidence: number;
        current_price?: number;
        models_used?: string;
        reasoning?: string[];
        daily_forecast?: number[];
        arima_forecast?: { '7d': number | null; '30d': number | null; daily?: number[] | null } | null;
        prophet_forecast?: { '7d': number | null; '30d': number | null; daily?: number[] | null } | null;
        ets_forecast?: { '7d': number | null; '30d': number | null; daily?: number[] | null } | null;
        rf_signal?: {
            signal: 'buy' | 'hold';
            buy_probability: number;
            precision: number;
            accuracy: number;
            top_features: string[];
        } | null;
    };
    technical?: {
        rsi: number | null;
        rsi_signal: string;
        macd: number | null;
        macd_signal: string;
        macd_histogram: number | null;
        bollinger_upper: number | null;
        bollinger_middle: number | null;
        bollinger_lower: number | null;
        bollinger_position: string;
        support_levels: number[];
        resistance_levels: number[];
        volume_signal: string;
        volume_ratio?: number;
    };
    sentiment?: {
        overall_score: number;
        label: string;
        positive_pct: number;
        neutral_pct: number;
        negative_pct: number;
        details: Array<{ headline: string; score: number; label: string }>;
    };
}

function calculateOverallSignal(prediction?: MLAnalysisViewProps['prediction'], technical?: MLAnalysisViewProps['technical'], sentiment?: MLAnalysisViewProps['sentiment']): { signal: 'BUY' | 'HOLD' | 'SELL'; score: number; reasons: string[] } {
    let score = 0;
    const reasons: string[] = [];
    
    // Prediction signals (weight: 40%)
    if (prediction?.forecast_30d_change !== null && prediction?.forecast_30d_change !== undefined) {
        if (prediction.forecast_30d_change > 5) { score += 2; reasons.push('Strong upward price prediction'); }
        else if (prediction.forecast_30d_change > 2) { score += 1; reasons.push('Moderate upward price prediction'); }
        else if (prediction.forecast_30d_change < -5) { score -= 2; reasons.push('Strong downward price prediction'); }
        else if (prediction.forecast_30d_change < -2) { score -= 1; reasons.push('Moderate downward price prediction'); }
    }
    
    // Technical signals (weight: 40%)
    if (technical) {
        if (technical.rsi_signal === 'oversold') { score += 1; reasons.push('Momentum indicator (RSI) shows oversold - potential buying opportunity'); }
        else if (technical.rsi_signal === 'overbought') { score -= 1; reasons.push('Momentum indicator (RSI) shows overbought - price may decline'); }
        
        if (technical.macd_signal === 'bullish') { score += 1; reasons.push('Trend indicator (MACD) shows upward momentum'); }
        else if (technical.macd_signal === 'bearish') { score -= 1; reasons.push('Trend indicator (MACD) shows downward momentum'); }
        
        if (technical.bollinger_position === 'lower') { score += 1; reasons.push('Price near support level - potential bounce up'); }
        else if (technical.bollinger_position === 'upper') { score -= 1; reasons.push('Price near resistance level - potential pullback'); }
    }
    
    // Sentiment signals (weight: 20%)
    if (sentiment) {
        if (sentiment.overall_score > 0.3) { score += 1; reasons.push('Positive news sentiment'); }
        else if (sentiment.overall_score < -0.3) { score -= 1; reasons.push('Negative news sentiment'); }
    }
    
    const signal: 'BUY' | 'HOLD' | 'SELL' = score >= 2 ? 'BUY' : score <= -2 ? 'SELL' : 'HOLD';
    return { signal, score, reasons };
}

export default function MLAnalysisView({ prediction, technical, sentiment }: MLAnalysisViewProps) {
    const { signal, score, reasons } = calculateOverallSignal(prediction, technical, sentiment);
    
    return (
        <div className="space-y-6">
            {/* Overall Signal Card */}
            <div className={`rounded-xl shadow-sm p-6 ${
                signal === 'BUY' ? 'bg-green-500/10 border-2 border-green-500/30' :
                signal === 'SELL' ? 'bg-red-500/10 border-2 border-red-500/30' :
                'bg-yellow-500/10 border-2 border-yellow-500/30'
            }`}>
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-theme">ML Analysis Signal</h3>
                    <span className={`px-4 py-2 rounded-full text-lg font-bold ${
                        signal === 'BUY' ? 'bg-green-500/100 text-white' :
                        signal === 'SELL' ? 'bg-red-500/100 text-white' :
                        'bg-yellow-500/100 text-white'
                    }`}>
                        {signal}
                    </span>
                </div>
                
                <div className="grid md:grid-cols-2 gap-4">
                    <div>
                        <p className="text-sm text-theme-secondary mb-2">Signal Strength: <span className="font-semibold">{Math.abs(score)}/6</span></p>
                        <div className="space-y-1">
                            {reasons.length > 0 ? reasons.map((reason, i) => (
                                <p key={i} className="text-sm text-theme-secondary flex items-start gap-2">
                                    <span className="text-green-500">•</span> {reason}
                                </p>
                            )) : (
                                <p className="text-sm text-theme-muted">No strong signals detected - indicators are mixed</p>
                            )}
                        </div>
                    </div>
                    
                    {/* Profit Projection */}
                    {prediction?.current_price && prediction?.forecast_30d_change !== null && (
                        <div className="bg-theme-card/50 rounded-lg p-4">
                            <p className="text-sm text-theme-secondary mb-2">Investment Projection (30 days)</p>
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <span className="text-theme-secondary">If you invest:</span>
                                    <span className="font-semibold">$1,000</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-theme-secondary">Predicted value:</span>
                                    <span className={`font-semibold ${prediction.forecast_30d_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                        ${(1000 * (1 + prediction.forecast_30d_change / 100)).toFixed(2)}
                                    </span>
                                </div>
                                <div className="flex justify-between border-t pt-2">
                                    <span className="text-theme-secondary">Projected {prediction.forecast_30d_change >= 0 ? 'profit' : 'loss'}:</span>
                                    <span className={`font-bold ${prediction.forecast_30d_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                        {prediction.forecast_30d_change >= 0 ? '+' : ''}{(1000 * prediction.forecast_30d_change / 100).toFixed(2)} ({prediction.forecast_30d_change >= 0 ? '+' : ''}{prediction.forecast_30d_change.toFixed(2)}%)
                                    </span>
                                </div>
                            </div>
                            <p className="text-xs text-theme-muted mt-2">*Based on {prediction.models_used || 'combined'} prediction. Not financial advice.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Price Predictions */}
            <div className="bg-theme-card rounded-xl shadow-sm p-6 border border-theme">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>📈</span> Price Forecast
                    {prediction?.models_used && (
                        <span className="text-xs bg-blue-100 text-blue-400 px-2 py-1 rounded-full">
                            {prediction.models_used}
                        </span>
                    )}
                </h3>
                
                {prediction ? (
                    <div className="space-y-4">
                        {/* Combined Forecast */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <ForecastCard
                                label="7-Day Forecast (Combined)"
                                currentPrice={prediction.current_price}
                                forecastPrice={prediction.forecast_7d}
                                change={prediction.forecast_7d_change}
                            />
                            <ForecastCard
                                label="30-Day Forecast (Combined)"
                                currentPrice={prediction.current_price}
                                forecastPrice={prediction.forecast_30d}
                                change={prediction.forecast_30d_change}
                            />
                        </div>
                        
                        {/* Forecast Chart */}
                        {prediction.daily_forecast && prediction.daily_forecast.length > 0 && prediction.current_price && (
                            <div className="border-t pt-4">
                                <p className="text-sm font-medium text-theme mb-3">30-Day Price Forecast</p>
                                <ForecastChart
                                    currentPrice={prediction.current_price}
                                    dailyForecast={prediction.daily_forecast}
                                    arimaDaily={prediction.arima_forecast?.daily}
                                    prophetDaily={prediction.prophet_forecast?.daily}
                                    etsDaily={prediction.ets_forecast?.daily}
                                />
                            </div>
                        )}
                        
                        {/* Model Summary Cards */}
                        {(prediction.arima_forecast || prediction.prophet_forecast || prediction.ets_forecast) && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                {/* ARIMA */}
                                <div className="bg-blue-500/10 rounded-lg p-3">
                                    <p className="text-xs font-semibold text-blue-400 mb-2">ARIMA</p>
                                    {prediction.arima_forecast ? (
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-xs">
                                                <span className="text-theme-muted">7-Day:</span>
                                                <span className="font-medium">${prediction.arima_forecast['7d']?.toFixed(2) || 'N/A'}</span>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span className="text-theme-secondary">30-Day:</span>
                                                <span className="font-semibold">${prediction.arima_forecast['30d']?.toFixed(2) || 'N/A'}</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <p className="text-xs text-theme-muted">Failed</p>
                                    )}
                                </div>
                                
                                {/* Prophet */}
                                <div className="bg-purple-500/10 rounded-lg p-3">
                                    <p className="text-xs font-semibold text-purple-400 mb-2">Prophet</p>
                                    {prediction.prophet_forecast ? (
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-xs">
                                                <span className="text-theme-muted">7-Day:</span>
                                                <span className="font-medium">${prediction.prophet_forecast['7d']?.toFixed(2) || 'N/A'}</span>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span className="text-theme-secondary">30-Day:</span>
                                                <span className="font-semibold">${prediction.prophet_forecast['30d']?.toFixed(2) || 'N/A'}</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <p className="text-xs text-theme-muted">Failed</p>
                                    )}
                                </div>
                                
                                {/* ETS */}
                                <div className="bg-green-500/10 rounded-lg p-3">
                                    <p className="text-xs font-semibold text-green-500 mb-2">ETS (Holt-Winters)</p>
                                    {prediction.ets_forecast ? (
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-xs">
                                                <span className="text-theme-muted">7-Day:</span>
                                                <span className="font-medium">${prediction.ets_forecast['7d']?.toFixed(2) || 'N/A'}</span>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span className="text-theme-secondary">30-Day:</span>
                                                <span className="font-semibold">${prediction.ets_forecast['30d']?.toFixed(2) || 'N/A'}</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <p className="text-xs text-theme-muted">Failed</p>
                                    )}
                                </div>
                            </div>
                        )}
                        
                        {/* Random Forest Signal Card */}
                        {prediction.rf_signal && (
                            <div className={`rounded-lg p-4 border-2 ${
                                prediction.rf_signal.signal === 'buy' 
                                    ? 'bg-green-500/10 border-green-500/40' 
                                    : 'bg-yellow-500/10 border-yellow-500/40'
                            }`}>
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                        <span className="text-2xl">{prediction.rf_signal.signal === 'buy' ? '🌲' : '⏸️'}</span>
                                        <div>
                                            <p className="text-xs text-theme-muted uppercase tracking-wide">Random Forest Signal</p>
                                            <p className={`text-xl font-bold uppercase ${
                                                prediction.rf_signal.signal === 'buy' ? 'text-green-500' : 'text-yellow-400'
                                            }`}>
                                                {prediction.rf_signal.signal === 'buy' ? 'BUY' : 'HOLD'}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs text-theme-muted">Buy Probability</p>
                                        <p className="text-2xl font-bold text-theme">
                                            {(prediction.rf_signal.buy_probability * 100).toFixed(0)}%
                                        </p>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-3 text-sm">
                                    <div className="bg-theme-card/50 rounded p-2">
                                        <p className="text-xs text-theme-muted">Model Precision</p>
                                        <p className="font-semibold">{(prediction.rf_signal.precision * 100).toFixed(1)}%</p>
                                    </div>
                                    <div className="bg-theme-card/50 rounded p-2">
                                        <p className="text-xs text-theme-muted">Backtest Accuracy</p>
                                        <p className="font-semibold">{(prediction.rf_signal.accuracy * 100).toFixed(1)}%</p>
                                    </div>
                                </div>
                                {prediction.rf_signal.top_features && (
                                    <p className="text-xs text-theme-muted mt-2">
                                        Key factors: {prediction.rf_signal.top_features.join(', ')}
                                    </p>
                                )}
                            </div>
                        )}
                        
                        <div className="bg-theme-secondary rounded-lg p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-theme-muted">Overall Trend</p>
                                    <p className={`text-xl font-bold capitalize ${getTrendColor(prediction.trend)}`}>
                                        {prediction.trend === 'strong_upward' ? '⬆ Strong Upward' :
                                         prediction.trend === 'upward' ? '↗ Upward' : 
                                         prediction.trend === 'strong_downward' ? '⬇ Strong Downward' :
                                         prediction.trend === 'downward' ? '↘ Downward' : '→ Sideways'}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm text-theme-muted">Model Confidence</p>
                                    <p className="text-xl font-bold text-theme">{(prediction.confidence * 100).toFixed(0)}%</p>
                                </div>
                            </div>
                            <p className="text-sm text-theme-secondary mt-2">
                                {prediction.trend === 'strong_upward' 
                                    ? 'Both models strongly predict the price will increase significantly over the next 30 days.'
                                    : prediction.trend === 'upward' 
                                    ? 'The models predict the price will increase over the next 30 days.'
                                    : prediction.trend === 'strong_downward'
                                    ? 'Both models strongly predict the price will decrease significantly over the next 30 days.'
                                    : prediction.trend === 'downward'
                                    ? 'The models predict the price will decrease over the next 30 days.'
                                    : 'The models predict the price will remain relatively stable.'}
                            </p>
                        </div>
                        
                        {/* ML Reasoning */}
                        {prediction.reasoning && prediction.reasoning.length > 0 && (
                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                                <p className="text-sm font-semibold text-blue-400 mb-2">🔍 Model Analysis Reasoning</p>
                                <ul className="space-y-1">
                                    {prediction.reasoning.map((reason, i) => (
                                        <li key={i} className="text-sm text-blue-400 flex items-start gap-2">
                                            <span className="text-blue-400">•</span>
                                            {reason}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-theme-muted">Loading predictions...</p>
                )}
            </div>

            {/* Technical Indicators */}
            <div className="bg-theme-card rounded-xl shadow-sm p-6 border border-theme">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>📊</span> Technical Indicators
                </h3>
                
                {technical ? (
                    <div className="space-y-4">
                        {/* RSI */}
                        <TechnicalIndicatorRow
                            name="RSI (Relative Strength Index)"
                            value={technical.rsi !== null ? technical.rsi.toFixed(1) : 'N/A'}
                            signal={technical.rsi_signal}
                            explanation={
                                technical.rsi_signal === 'overbought' 
                                    ? `RSI at ${technical.rsi?.toFixed(0)} (above 70) suggests the stock may be overbought. Consider waiting for a pullback.`
                                    : technical.rsi_signal === 'oversold'
                                    ? `RSI at ${technical.rsi?.toFixed(0)} (below 30) suggests the stock may be oversold. Could be a buying opportunity.`
                                    : `RSI at ${technical.rsi?.toFixed(0)} is in neutral territory (30-70). No extreme buying or selling pressure.`
                            }
                        />
                        
                        {/* MACD */}
                        <TechnicalIndicatorRow
                            name="MACD (Trend Direction)"
                            value={technical.macd !== null ? technical.macd.toFixed(4) : 'N/A'}
                            signal={technical.macd_signal}
                            explanation={
                                technical.macd_signal === 'bullish'
                                    ? 'MACD shows the price trend is moving upward. This is a buy signal suggesting momentum is positive.'
                                    : technical.macd_signal === 'bearish'
                                    ? 'MACD shows the price trend is moving downward. This is a sell signal suggesting momentum is negative.'
                                    : 'MACD shows no clear trend direction. The market is indecisive.'
                            }
                        />
                        
                        {/* Bollinger Bands */}
                        <TechnicalIndicatorRow
                            name="Bollinger Bands"
                            value={technical.bollinger_position}
                            signal={technical.bollinger_position === 'upper' ? 'overbought' : technical.bollinger_position === 'lower' ? 'oversold' : 'neutral'}
                            explanation={
                                technical.bollinger_position === 'upper'
                                    ? 'Price is near the upper band, suggesting potential overbought conditions. May see a pullback.'
                                    : technical.bollinger_position === 'lower'
                                    ? 'Price is near the lower band, suggesting potential oversold conditions. May see a bounce.'
                                    : 'Price is within normal range between the bands.'
                            }
                        />
                        
                        {/* Volume */}
                        <TechnicalIndicatorRow
                            name="Trading Volume"
                            value={technical.volume_ratio ? `${technical.volume_ratio.toFixed(1)}x avg` : technical.volume_signal}
                            signal={technical.volume_signal === 'unusual_spike' ? 'alert' : technical.volume_signal === 'high' ? 'bullish' : 'neutral'}
                            explanation={
                                technical.volume_signal === 'unusual_spike'
                                    ? 'Unusual volume spike detected! This could indicate significant news or institutional activity.'
                                    : technical.volume_signal === 'high'
                                    ? 'Higher than average trading volume suggests increased interest in the stock.'
                                    : technical.volume_signal === 'low'
                                    ? 'Lower than average volume may indicate reduced interest or consolidation.'
                                    : 'Trading volume is at normal levels.'
                            }
                        />
                        
                        {/* Support/Resistance */}
                        {(technical.support_levels.length > 0 || technical.resistance_levels.length > 0) && (
                            <div className="pt-4 border-t">
                                <p className="text-sm font-medium text-theme mb-3">Key Price Levels</p>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-green-500/10 rounded-lg p-3">
                                        <p className="text-xs text-green-500 font-medium mb-2">Support (Buy Zones)</p>
                                        <p className="text-xs text-green-500 mb-2">Price tends to bounce up from these levels</p>
                                        <div className="flex flex-wrap gap-2">
                                            {technical.support_levels.length > 0 ? technical.support_levels.map((level, i) => (
                                                <span key={i} className="px-2 py-1 bg-green-500/100/20 text-green-500 rounded text-sm font-medium">
                                                    ${level.toFixed(2)}
                                                </span>
                                            )) : <span className="text-theme-muted text-xs">None nearby</span>}
                                        </div>
                                    </div>
                                    <div className="bg-red-500/10 rounded-lg p-3">
                                        <p className="text-xs text-red-500 font-medium mb-2">Resistance (Sell Zones)</p>
                                        <p className="text-xs text-red-500 mb-2">Price tends to face selling pressure here</p>
                                        <div className="flex flex-wrap gap-2">
                                            {technical.resistance_levels.length > 0 ? technical.resistance_levels.map((level, i) => (
                                                <span key={i} className="px-2 py-1 bg-red-500/100/20 text-red-500 rounded text-sm font-medium">
                                                    ${level.toFixed(2)}
                                                </span>
                                            )) : <span className="text-theme-muted text-xs">None nearby</span>}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-theme-muted">Loading technical analysis...</p>
                )}
            </div>

            {/* ML Sentiment */}
            <div className="bg-theme-card rounded-xl shadow-sm p-6 border border-theme">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>💬</span> News Sentiment Analysis
                </h3>
                
                {sentiment ? (
                    <div className="space-y-4">
                        {/* Sentiment Summary */}
                        <div className={`rounded-lg p-4 ${
                            sentiment.label === 'positive' ? 'bg-green-500/10' :
                            sentiment.label === 'negative' ? 'bg-red-500/10' : 'bg-theme-secondary'
                        }`}>
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <p className="text-sm text-theme-secondary">Market Sentiment</p>
                                    <p className={`text-2xl font-bold capitalize ${getSentimentColor(sentiment.label)}`}>
                                        {sentiment.label === 'positive' ? '📈 Bullish' : 
                                         sentiment.label === 'negative' ? '📉 Bearish' : '➡️ Neutral'}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm text-theme-secondary">Score</p>
                                    <p className={`text-2xl font-bold ${getSentimentColor(sentiment.label)}`}>
                                        {(sentiment.overall_score * 100).toFixed(0)}%
                                    </p>
                                </div>
                            </div>
                            <p className="text-sm text-theme-secondary">
                                {sentiment.label === 'positive' 
                                    ? `News sentiment is positive with ${sentiment.positive_pct.toFixed(0)}% of headlines showing bullish indicators. This suggests favorable market perception.`
                                    : sentiment.label === 'negative'
                                    ? `News sentiment is negative with ${sentiment.negative_pct.toFixed(0)}% of headlines showing bearish indicators. Exercise caution.`
                                    : 'News sentiment is mixed with no strong directional bias. The market appears undecided.'}
                            </p>
                        </div>
                        
                        {/* Sentiment Breakdown */}
                        <div className="grid grid-cols-3 gap-3">
                            <div className="bg-green-500/10 rounded-lg p-3 text-center">
                                <p className="text-2xl font-bold text-green-500">{sentiment.positive_pct.toFixed(0)}%</p>
                                <p className="text-xs text-green-500">Positive</p>
                            </div>
                            <div className="bg-theme-secondary rounded-lg p-3 text-center">
                                <p className="text-2xl font-bold text-theme-secondary">{sentiment.neutral_pct.toFixed(0)}%</p>
                                <p className="text-xs text-theme-secondary">Neutral</p>
                            </div>
                            <div className="bg-red-500/10 rounded-lg p-3 text-center">
                                <p className="text-2xl font-bold text-red-500">{sentiment.negative_pct.toFixed(0)}%</p>
                                <p className="text-xs text-red-500">Negative</p>
                            </div>
                        </div>
                        
                        {/* Headlines */}
                        {sentiment.details.length > 0 && (
                            <div className="pt-4 border-t">
                                <p className="text-sm font-medium text-theme mb-3">Analyzed Headlines</p>
                                <div className="space-y-2 max-h-60 overflow-y-auto">
                                    {sentiment.details.slice(0, 8).map((detail, i) => (
                                        <div key={i} className={`flex items-start gap-3 p-2 rounded-lg ${
                                            detail.label === 'positive' ? 'bg-green-500/10' :
                                            detail.label === 'negative' ? 'bg-red-500/10' : 'bg-theme-secondary'
                                        }`}>
                                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                                                detail.label === 'positive' ? 'bg-green-500/100 text-white' :
                                                detail.label === 'negative' ? 'bg-red-500/100 text-white' :
                                                'bg-gray-400 text-white'
                                            }`}>
                                                {detail.label === 'positive' ? '↑' : detail.label === 'negative' ? '↓' : '−'}
                                            </span>
                                            <span className="text-sm text-theme-secondary flex-1">{detail.headline}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-theme-muted">Loading sentiment analysis...</p>
                )}
            </div>
            
            {/* Disclaimer */}
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <p className="text-sm text-yellow-400">
                    <strong>Disclaimer:</strong> This ML analysis is for informational purposes only and should not be considered financial advice. 
                    Always do your own research and consult with a qualified financial advisor before making investment decisions.
                </p>
            </div>
        </div>
    );
}

function ForecastCard({ label, currentPrice, forecastPrice, change }: { 
    label: string; 
    currentPrice?: number;
    forecastPrice: number | null; 
    change: number | null;
}) {
    const isPositive = change !== null && change >= 0;
    
    return (
        <div className={`rounded-lg p-4 ${isPositive ? 'bg-green-500/10' : change !== null ? 'bg-red-500/10' : 'bg-theme-secondary'}`}>
            <p className="text-sm text-theme-secondary mb-2">{label}</p>
            {forecastPrice !== null && currentPrice ? (
                <div className="space-y-2">
                    <div className="flex items-baseline gap-2">
                        <span className="text-sm text-theme-muted">From</span>
                        <span className="text-lg font-medium text-theme-secondary">${currentPrice.toFixed(2)}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-sm text-theme-muted">To</span>
                        <span className={`text-2xl font-bold ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                            ${forecastPrice.toFixed(2)}
                        </span>
                    </div>
                    {change !== null && (
                        <p className={`text-sm font-semibold ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                            {isPositive ? '↑' : '↓'} {isPositive ? '+' : ''}{change.toFixed(2)}%
                        </p>
                    )}
                </div>
            ) : forecastPrice !== null ? (
                <p className="text-2xl font-bold text-theme">${forecastPrice.toFixed(2)}</p>
            ) : (
                <p className="text-theme-muted">Insufficient data</p>
            )}
        </div>
    );
}

function TechnicalIndicatorRow({ name, value, signal, explanation }: { 
    name: string; 
    value: string; 
    signal: string;
    explanation: string;
}) {
    const signalConfig: Record<string, { bg: string; text: string; label: string }> = {
        bullish: { bg: 'bg-green-500/100/20', text: 'text-green-500', label: 'Bullish' },
        bearish: { bg: 'bg-red-500/100/20', text: 'text-red-500', label: 'Bearish' },
        overbought: { bg: 'bg-red-500/100/20', text: 'text-red-500', label: 'Overbought' },
        oversold: { bg: 'bg-green-500/100/20', text: 'text-green-500', label: 'Oversold' },
        neutral: { bg: 'bg-theme-secondary', text: 'text-theme-secondary', label: 'Neutral' },
        normal: { bg: 'bg-theme-secondary', text: 'text-theme-secondary', label: 'Normal' },
        high: { bg: 'bg-yellow-100', text: 'text-yellow-400', label: 'High' },
        low: { bg: 'bg-blue-100', text: 'text-blue-400', label: 'Low' },
        alert: { bg: 'bg-red-500/100/20', text: 'text-red-500', label: 'Alert' },
    };
    
    const config = signalConfig[signal.toLowerCase()] || signalConfig.neutral;
    
    return (
        <div className="border-b border-theme pb-3 last:border-0 last:pb-0">
            <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-theme">{name}</span>
                <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold text-gray-800 capitalize">{value}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.text}`}>
                        {config.label}
                    </span>
                </div>
            </div>
            <p className="text-sm text-theme-secondary">{explanation}</p>
        </div>
    );
}

function getTrendColor(trend: string): string {
    switch (trend.toLowerCase()) {
        case 'strong_upward': return 'text-green-500';
        case 'upward': return 'text-green-500';
        case 'strong_downward': return 'text-red-500';
        case 'downward': return 'text-red-500';
        default: return 'text-theme-secondary';
    }
}

function getSentimentColor(label: string): string {
    switch (label.toLowerCase()) {
        case 'positive': return 'text-green-500';
        case 'negative': return 'text-red-500';
        default: return 'text-theme-secondary';
    }
}
