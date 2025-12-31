'use client';

import { useLLMConfig } from '@/hooks/useLLMConfig';

interface LLMAnalysisViewProps {
    hasLLMConfig: boolean;
    onConfigureClick: () => void;
    newsSummary?: string;
    sentiment?: {
        overall_score: number;
        breakdown: { positive: number; negative: number; neutral: number };
        details: Array<{
            headline: string;
            sentiment: string;
            confidence: number;
            reasoning: string;
        }>;
    };
    aiInsights?: string;
    isLoading?: boolean;
}

export default function LLMAnalysisView({
    hasLLMConfig,
    onConfigureClick,
    newsSummary,
    sentiment,
    aiInsights,
    isLoading = false,
}: LLMAnalysisViewProps) {
    if (!hasLLMConfig) {
        return (
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-8 text-center">
                <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-theme-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                </div>
                <h3 className="text-lg font-semibold text-theme mb-2">
                    LLM Analysis Locked
                </h3>
                <p className="text-theme-secondary mb-4 max-w-sm mx-auto">
                    Configure your LLM API key to unlock AI-powered insights:
                </p>
                <ul className="text-sm text-theme-muted mb-6 space-y-1">
                    <li>• AI news summarization</li>
                    <li>• Deep sentiment analysis with reasoning</li>
                    <li>• Investment insights & recommendations</li>
                </ul>
                <button
                    onClick={onConfigureClick}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    Configure LLM API Key
                </button>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="space-y-6">
                <LoadingCard title="News Summary" />
                <LoadingCard title="AI Sentiment" />
                <LoadingCard title="Investment Insights" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* News Summary */}
            <div className="bg-theme-card rounded-xl shadow-sm p-6 border border-theme">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>📰</span> News Summary (LLM Generated)
                </h3>
                {newsSummary ? (
                    <div className="prose prose-gray max-w-none">
                        <p className="text-theme-secondary whitespace-pre-wrap">{newsSummary}</p>
                    </div>
                ) : (
                    <p className="text-theme-muted">No summary available yet.</p>
                )}
            </div>

            {/* AI Sentiment */}
            <div className="bg-theme-card rounded-xl shadow-sm p-6 border border-theme">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>🧠</span> AI Sentiment Analysis
                </h3>
                {sentiment ? (
                    <div className="space-y-4">
                        <div className="flex items-center gap-4">
                            <div className="text-center">
                                <p className={`text-3xl font-bold ${getScoreColor(sentiment.overall_score)}`}>
                                    {sentiment.overall_score.toFixed(2)}
                                </p>
                                <p className={`text-sm font-medium ${getScoreColor(sentiment.overall_score)}`}>
                                    {getScoreLabel(sentiment.overall_score)}
                                </p>
                            </div>
                            <div className="flex-1 grid grid-cols-3 gap-2 text-center">
                                <div className="bg-green-500/10 rounded-lg p-2">
                                    <p className="text-lg font-semibold text-green-500">{sentiment.breakdown.positive}</p>
                                    <p className="text-xs text-green-500">Bullish</p>
                                </div>
                                <div className="bg-theme-secondary rounded-lg p-2">
                                    <p className="text-lg font-semibold text-theme-secondary">{sentiment.breakdown.neutral}</p>
                                    <p className="text-xs text-theme-secondary">Neutral</p>
                                </div>
                                <div className="bg-red-500/10 rounded-lg p-2">
                                    <p className="text-lg font-semibold text-red-500">{sentiment.breakdown.negative}</p>
                                    <p className="text-xs text-red-500">Bearish</p>
                                </div>
                            </div>
                        </div>

                        {sentiment.details.length > 0 && (
                            <div className="pt-4 border-t">
                                <p className="text-sm font-medium text-theme-secondary mb-3">Detailed Analysis</p>
                                <div className="space-y-3 max-h-64 overflow-y-auto">
                                    {sentiment.details.map((detail, i) => (
                                        <div key={i} className="bg-theme-secondary rounded-lg p-3">
                                            <div className="flex items-start justify-between gap-2 mb-1">
                                                <p className="text-sm font-medium text-theme">{detail.headline}</p>
                                                <span className={`px-2 py-0.5 rounded text-xs font-medium shrink-0 ${
                                                    detail.sentiment.toLowerCase() === 'bullish' ? 'bg-green-500/100/20 text-green-500' :
                                                    detail.sentiment.toLowerCase() === 'bearish' ? 'bg-red-500/100/20 text-red-500' :
                                                    'bg-theme-secondary text-theme-secondary'
                                                }`}>
                                                    {detail.sentiment} ({(detail.confidence * 100).toFixed(0)}%)
                                                </span>
                                            </div>
                                            <p className="text-xs text-theme-secondary">{detail.reasoning}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-theme-muted">No sentiment analysis available yet.</p>
                )}
            </div>

            {/* AI Insights */}
            <div className="bg-theme-card rounded-xl shadow-sm p-6 border border-theme">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>💡</span> AI Investment Insights
                </h3>
                {aiInsights ? (
                    <div className="prose prose-gray max-w-none">
                        <p className="text-theme-secondary whitespace-pre-wrap">{aiInsights}</p>
                    </div>
                ) : (
                    <p className="text-theme-muted">No insights available yet.</p>
                )}
                <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg">
                    <p className="text-xs text-yellow-400">
                        ⚠️ This is AI-generated analysis and should not be considered financial advice. 
                        Always consult with a qualified financial advisor before making investment decisions.
                    </p>
                </div>
            </div>
        </div>
    );
}

function LoadingCard({ title }: { title: string }) {
    return (
        <div className="bg-theme-card rounded-xl shadow-sm p-6 border border-theme">
            <h3 className="text-lg font-semibold text-theme mb-4">{title}</h3>
            <div className="animate-pulse space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-full"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
        </div>
    );
}

function getScoreColor(score: number): string {
    if (score > 0.3) return 'text-green-500';
    if (score < -0.3) return 'text-red-500';
    return 'text-theme-secondary';
}

function getScoreLabel(score: number): string {
    if (score > 0.3) return 'Bullish';
    if (score < -0.3) return 'Bearish';
    return 'Neutral';
}
