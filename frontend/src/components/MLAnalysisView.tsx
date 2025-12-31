'use client';

interface MLAnalysisViewProps {
    prediction?: {
        forecast_7d: number | null;
        forecast_7d_change: number | null;
        forecast_30d: number | null;
        forecast_30d_change: number | null;
        trend: string;
        confidence: number;
        current_price?: number;
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

export default function MLAnalysisView({ prediction, technical, sentiment }: MLAnalysisViewProps) {
    return (
        <div className="space-y-6">
            {/* Predictions Section */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span>🔮</span> ML Predictions (Prophet/ARIMA)
                </h3>
                
                {prediction ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <PredictionCard
                            label="7-Day Forecast"
                            value={prediction.forecast_7d}
                            change={prediction.forecast_7d_change}
                        />
                        <PredictionCard
                            label="30-Day Forecast"
                            value={prediction.forecast_30d}
                            change={prediction.forecast_30d_change}
                        />
                        <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-500 mb-1">Trend</p>
                            <p className={`text-lg font-semibold capitalize ${getTrendColor(prediction.trend)}`}>
                                {prediction.trend}
                            </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-500 mb-1">Confidence</p>
                            <p className="text-lg font-semibold text-gray-900">
                                {(prediction.confidence * 100).toFixed(0)}%
                            </p>
                        </div>
                    </div>
                ) : (
                    <p className="text-gray-500">Loading predictions...</p>
                )}
            </div>

            {/* Technical Indicators */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span>📊</span> Technical Indicators
                </h3>
                
                {technical ? (
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <IndicatorCard
                                label="RSI"
                                value={technical.rsi?.toFixed(1) || 'N/A'}
                                signal={technical.rsi_signal}
                            />
                            <IndicatorCard
                                label="MACD"
                                value={technical.macd?.toFixed(4) || 'N/A'}
                                signal={technical.macd_signal}
                            />
                            <IndicatorCard
                                label="Bollinger"
                                value={technical.bollinger_position}
                                signal={technical.bollinger_position === 'upper' ? 'overbought' : technical.bollinger_position === 'lower' ? 'oversold' : 'neutral'}
                            />
                            <IndicatorCard
                                label="Volume"
                                value={technical.volume_signal}
                                signal={technical.volume_signal === 'unusual_spike' ? 'alert' : technical.volume_signal}
                            />
                        </div>
                        
                        {(technical.support_levels.length > 0 || technical.resistance_levels.length > 0) && (
                            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                                <div>
                                    <p className="text-sm font-medium text-gray-700 mb-2">Support Levels</p>
                                    <div className="flex flex-wrap gap-2">
                                        {technical.support_levels.map((level, i) => (
                                            <span key={i} className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">
                                                ${level.toFixed(2)}
                                            </span>
                                        ))}
                                        {technical.support_levels.length === 0 && (
                                            <span className="text-gray-400 text-sm">None detected</span>
                                        )}
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-gray-700 mb-2">Resistance Levels</p>
                                    <div className="flex flex-wrap gap-2">
                                        {technical.resistance_levels.map((level, i) => (
                                            <span key={i} className="px-2 py-1 bg-red-100 text-red-700 rounded text-sm">
                                                ${level.toFixed(2)}
                                            </span>
                                        ))}
                                        {technical.resistance_levels.length === 0 && (
                                            <span className="text-gray-400 text-sm">None detected</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-gray-500">Loading technical analysis...</p>
                )}
            </div>

            {/* ML Sentiment */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span>💬</span> Sentiment Analysis (VADER + TextBlob)
                </h3>
                
                {sentiment ? (
                    <div className="space-y-4">
                        <div className="flex items-center gap-6">
                            <div>
                                <p className="text-sm text-gray-500">Overall Score</p>
                                <p className={`text-2xl font-bold ${getSentimentColor(sentiment.label)}`}>
                                    {sentiment.overall_score.toFixed(2)}
                                </p>
                                <p className={`text-sm font-medium capitalize ${getSentimentColor(sentiment.label)}`}>
                                    {sentiment.label}
                                </p>
                            </div>
                            
                            <div className="flex-1 space-y-2">
                                <SentimentBar label="Positive" pct={sentiment.positive_pct} color="bg-green-500" />
                                <SentimentBar label="Neutral" pct={sentiment.neutral_pct} color="bg-gray-400" />
                                <SentimentBar label="Negative" pct={sentiment.negative_pct} color="bg-red-500" />
                            </div>
                        </div>
                        
                        {sentiment.details.length > 0 && (
                            <div className="pt-4 border-t">
                                <p className="text-sm font-medium text-gray-700 mb-2">Headlines</p>
                                <div className="space-y-2 max-h-48 overflow-y-auto">
                                    {sentiment.details.slice(0, 5).map((detail, i) => (
                                        <div key={i} className="flex items-start gap-2 text-sm">
                                            <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                                                detail.label === 'positive' ? 'bg-green-100 text-green-700' :
                                                detail.label === 'negative' ? 'bg-red-100 text-red-700' :
                                                'bg-gray-100 text-gray-700'
                                            }`}>
                                                {detail.score.toFixed(2)}
                                            </span>
                                            <span className="text-gray-700">{detail.headline}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-gray-500">Loading sentiment analysis...</p>
                )}
            </div>
        </div>
    );
}

function PredictionCard({ label, value, change }: { label: string; value: number | null; change: number | null }) {
    const isPositive = change !== null && change >= 0;
    
    return (
        <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500 mb-1">{label}</p>
            {value !== null ? (
                <>
                    <p className="text-lg font-semibold text-gray-900">${value.toFixed(2)}</p>
                    {change !== null && (
                        <p className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                            {isPositive ? '+' : ''}{change.toFixed(2)}%
                        </p>
                    )}
                </>
            ) : (
                <p className="text-gray-400">N/A</p>
            )}
        </div>
    );
}

function IndicatorCard({ label, value, signal }: { label: string; value: string; signal: string }) {
    const signalColors: Record<string, string> = {
        bullish: 'text-green-600',
        bearish: 'text-red-600',
        overbought: 'text-red-600',
        oversold: 'text-green-600',
        neutral: 'text-gray-600',
        normal: 'text-gray-600',
        high: 'text-yellow-600',
        unusual_spike: 'text-red-600',
        alert: 'text-red-600',
    };
    
    return (
        <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500 mb-1">{label}</p>
            <p className="text-lg font-semibold text-gray-900 capitalize">{value}</p>
            <p className={`text-sm capitalize ${signalColors[signal.toLowerCase()] || 'text-gray-600'}`}>
                {signal}
            </p>
        </div>
    );
}

function SentimentBar({ label, pct, color }: { label: string; pct: number; color: string }) {
    return (
        <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 w-16">{label}</span>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs text-gray-700 w-10 text-right">{pct.toFixed(0)}%</span>
        </div>
    );
}

function getTrendColor(trend: string): string {
    switch (trend.toLowerCase()) {
        case 'upward': return 'text-green-600';
        case 'downward': return 'text-red-600';
        default: return 'text-gray-600';
    }
}

function getSentimentColor(label: string): string {
    switch (label.toLowerCase()) {
        case 'positive': return 'text-green-600';
        case 'negative': return 'text-red-600';
        default: return 'text-gray-600';
    }
}
