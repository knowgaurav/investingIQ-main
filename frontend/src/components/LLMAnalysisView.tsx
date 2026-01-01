'use client';

import ReactMarkdown from 'react-markdown';

interface LLMAnalysisViewProps {
    hasLLMConfig: boolean;
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
    newsSummary,
    sentiment,
    aiInsights,
    isLoading = false,
}: LLMAnalysisViewProps) {
    if (!hasLLMConfig) {
        return (
            <div className="bg-theme-card rounded-xl shadow-md p-8 text-center">
                <div className="w-16 h-16 bg-theme-secondary rounded-full flex items-center justify-center mx-auto mb-4">
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
                <p className="text-sm text-theme-secondary">
                    Click the settings button in the bottom right corner to configure.
                </p>
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
            <div className="bg-theme-card rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>📰</span> News Summary (LLM Generated)
                </h3>
                {newsSummary ? (
                    <div className="space-y-3 text-theme-secondary text-sm leading-relaxed
                        [&>p]:mb-3 [&>p]:leading-relaxed
                        [&_strong]:text-theme [&_strong]:font-semibold">
                        <ReactMarkdown>{newsSummary}</ReactMarkdown>
                    </div>
                ) : (
                    <p className="text-theme-muted">No summary available yet.</p>
                )}
            </div>

            {/* AI Sentiment */}
            <div className="bg-theme-card rounded-xl shadow-md p-6">
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
                                <div className="bg-gray-500/20 rounded-lg p-2">
                                    <p className="text-lg font-semibold text-gray-400">{sentiment.breakdown.neutral}</p>
                                    <p className="text-xs text-gray-400">Neutral</p>
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
                                <div className="space-y-2 max-h-60 overflow-y-auto">
                                    {sentiment.details.map((detail, i) => (
                                        <div key={i} className={`flex items-start gap-3 p-3 rounded-lg ${detail.sentiment.toLowerCase() === 'bullish' ? 'bg-green-500/10' :
                                            detail.sentiment.toLowerCase() === 'bearish' ? 'bg-red-500/10' : 'bg-gray-500/20'
                                            }`}>
                                            <span className={`px-2 py-1 rounded text-xs font-bold shrink-0 ${detail.sentiment.toLowerCase() === 'bullish' ? 'bg-green-500 text-white' :
                                                detail.sentiment.toLowerCase() === 'bearish' ? 'bg-red-500 text-white' :
                                                    'bg-gray-500 text-white'
                                                }`}>
                                                {detail.sentiment.toLowerCase() === 'bullish' ? '↑' :
                                                    detail.sentiment.toLowerCase() === 'bearish' ? '↓' : '−'} {(detail.confidence * 100).toFixed(0)}%
                                            </span>
                                            <div className="flex-1">
                                                <p className="text-sm font-medium text-theme">{detail.headline}</p>
                                                <p className="text-xs text-theme-secondary mt-1">{detail.reasoning}</p>
                                            </div>
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
            <div className="bg-theme-card rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>💡</span> AI Investment Insights
                </h3>
                {aiInsights ? (
                    <div className="space-y-4 text-theme-secondary text-sm leading-relaxed
                        [&>h3]:text-theme [&>h3]:font-semibold [&>h3]:text-base [&>h3]:mt-6 [&>h3]:mb-2
                        [&>h4]:text-theme [&>h4]:font-semibold [&>h4]:text-sm [&>h4]:mt-5 [&>h4]:mb-2
                        [&>p]:mb-3 [&>p]:leading-relaxed
                        [&_strong]:text-theme [&_strong]:font-semibold
                        [&>ul]:list-disc [&>ul]:pl-6 [&>ul]:my-3 [&>ul]:space-y-2
                        [&>ol]:list-decimal [&>ol]:pl-6 [&>ol]:my-3 [&>ol]:space-y-2
                        [&_li]:pl-1">
                        <ReactMarkdown>{aiInsights}</ReactMarkdown>
                    </div>
                ) : (
                    <p className="text-theme-muted">No insights available yet.</p>
                )}
            </div>

            {/* Disclaimer */}
            <div className="bg-amber-50 dark:bg-yellow-500/10 border border-amber-300 dark:border-yellow-500/30 rounded-lg p-4">
                <p className="text-sm text-amber-700 dark:text-yellow-400">
                    <strong>Disclaimer:</strong> This is AI-generated analysis and should not be considered financial advice.
                    Always consult with a qualified financial advisor before making investment decisions.
                </p>
            </div>
        </div>
    );
}

function LoadingCard({ title }: { title: string }) {
    return (
        <div className="bg-theme-card rounded-xl shadow-md p-6">
            <h3 className="text-lg font-semibold text-theme mb-4">{title}</h3>
            <div className="animate-pulse space-y-3">
                <div className="h-4 bg-theme-secondary rounded w-3/4"></div>
                <div className="h-4 bg-theme-secondary rounded w-full"></div>
                <div className="h-4 bg-theme-secondary rounded w-5/6"></div>
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
