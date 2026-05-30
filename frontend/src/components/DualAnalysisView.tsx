'use client';

import { MLAnalysisResult, DualComparison } from '@/lib/api';

interface DualAnalysisViewProps {
    ml?: MLAnalysisResult;
    llm?: {
        outlook?: string | null;
        sentiment_score?: number | null;
        insight?: string | null;
    };
    llmStatus?: string | null;
    comparison?: DualComparison | null;
}

const SIGNAL_STYLES: Record<string, string> = {
    bullish: 'bg-green-500/20 text-green-500',
    bearish: 'bg-red-500/20 text-red-500',
    neutral: 'bg-yellow-500/20 text-yellow-500',
};

function signalClass(signal?: string | null): string {
    if (!signal) return 'bg-gray-500/20 text-theme-secondary';
    return SIGNAL_STYLES[signal.toLowerCase()] || SIGNAL_STYLES.neutral;
}

function mlDirection(ml?: MLAnalysisResult): string | null {
    const trend = ml?.prediction?.trend;
    if (!trend) return null;
    if (trend.includes('upward')) return 'bullish';
    if (trend.includes('downward')) return 'bearish';
    if (trend === 'sideways') return 'neutral';
    return null;
}

export default function DualAnalysisView({ ml, llm, llmStatus, comparison }: DualAnalysisViewProps) {
    const llmAvailable = llmStatus === 'ok' && !!llm;
    const mlSignal = comparison?.ml_signal || mlDirection(ml);
    const llmSignal = comparison?.llm_signal || llm?.outlook || null;

    return (
        <div className="space-y-6">
            {/* Agreement banner */}
            {comparison ? (
                <div
                    className={`rounded-xl p-5 border-2 ${comparison.agreement
                            ? 'bg-green-50 dark:bg-green-500/10 border-green-300 dark:border-green-500/30'
                            : 'bg-amber-50 dark:bg-yellow-500/10 border-amber-300 dark:border-yellow-500/30'
                        }`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-theme-secondary">Model Consensus</p>
                            <p className="text-xl font-bold text-theme">
                                {comparison.agreement
                                    ? `Both models agree: ${comparison.ml_signal}`
                                    : 'Models disagree'}
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className={`px-3 py-1.5 rounded-full text-sm font-semibold capitalize ${signalClass(comparison.ml_signal)}`}>
                                ML: {comparison.ml_signal}
                            </span>
                            <span className={`px-3 py-1.5 rounded-full text-sm font-semibold capitalize ${signalClass(comparison.llm_signal)}`}>
                                LLM: {comparison.llm_signal}
                            </span>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="rounded-xl p-5 border-2 border-dashed border-theme/30 bg-theme-secondary/40">
                    <p className="text-sm text-theme-secondary">
                        Side-by-side consensus is available when both the statistical model and the LLM produce a directional signal.
                    </p>
                </div>
            )}

            {/* Two columns */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* ML column */}
                <div className="bg-theme-card rounded-xl shadow-md p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-theme flex items-center gap-2">
                            <span>📊</span> Statistical (ML)
                        </h3>
                        {mlSignal && (
                            <span className={`px-3 py-1 rounded-full text-sm font-semibold capitalize ${signalClass(mlSignal)}`}>
                                {mlSignal}
                            </span>
                        )}
                    </div>
                    {ml ? (
                        <dl className="space-y-3 text-sm">
                            <Row label="30-day forecast change">
                                {ml.prediction?.forecast_30d_change != null
                                    ? `${ml.prediction.forecast_30d_change >= 0 ? '+' : ''}${ml.prediction.forecast_30d_change.toFixed(2)}%`
                                    : 'N/A'}
                            </Row>
                            <Row label="Trend">{ml.prediction?.trend ?? 'N/A'}</Row>
                            <Row label="RSI signal">{ml.technical?.rsi_signal ?? 'N/A'}</Row>
                            <Row label="MACD signal">{ml.technical?.macd_signal ?? 'N/A'}</Row>
                            <Row label="Bollinger position">{ml.technical?.bollinger_position ?? 'N/A'}</Row>
                            <Row label="News sentiment">
                                {ml.sentiment ? `${ml.sentiment.label} (${ml.sentiment.overall_score.toFixed(2)})` : 'N/A'}
                            </Row>
                        </dl>
                    ) : (
                        <p className="text-theme-muted text-sm">ML analysis unavailable.</p>
                    )}
                </div>

                {/* LLM column */}
                <div className="bg-theme-card rounded-xl shadow-md p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-theme flex items-center gap-2">
                            <span>🤖</span> AI (LLM)
                        </h3>
                        {llmAvailable && llmSignal && (
                            <span className={`px-3 py-1 rounded-full text-sm font-semibold capitalize ${signalClass(llmSignal)}`}>
                                {llmSignal}
                            </span>
                        )}
                    </div>
                    {llmAvailable ? (
                        <div className="space-y-3 text-sm">
                            <Row label="Outlook">{llm?.outlook ?? 'N/A'}</Row>
                            <Row label="Sentiment score">
                                {llm?.sentiment_score != null ? llm.sentiment_score.toFixed(2) : 'N/A'}
                            </Row>
                            {llm?.insight && (
                                <div>
                                    <p className="text-theme-secondary mb-1">Insight</p>
                                    <p className="text-theme whitespace-pre-wrap">{llm.insight}</p>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="rounded-lg bg-theme-secondary/50 p-4">
                            <p className="text-sm font-medium text-theme">LLM analysis not run</p>
                            <p className="text-sm text-theme-muted mt-1">
                                Add an LLM API key in settings to see the AI-based analysis alongside the statistical model.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="flex items-center justify-between border-b border-theme/10 pb-2">
            <dt className="text-theme-secondary">{label}</dt>
            <dd className="font-medium text-theme capitalize">{children}</dd>
        </div>
    );
}
