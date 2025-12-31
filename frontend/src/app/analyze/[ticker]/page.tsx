'use client';

import { useState, useEffect, useCallback, use } from 'react';
import Link from 'next/link';
import {
    requestAnalysis,
    AnalysisReport,
    AnalysisTaskStatus,
    SentimentResult,
} from '@/lib/api';
import PriceChart from '@/components/PriceChart';

interface AnalyzePageProps {
    params: Promise<{ ticker: string }>;
}

type PageState = 'loading' | 'analyzing' | 'complete' | 'error';

export default function AnalyzePage({ params }: AnalyzePageProps) {
    const { ticker: rawTicker } = use(params);
    const ticker = rawTicker.toUpperCase();
    const [pageState, setPageState] = useState<PageState>('loading');
    const [taskStatus, setTaskStatus] = useState<AnalysisTaskStatus | null>(null);
    const [report, setReport] = useState<AnalysisReport | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Connect to SSE for real-time updates
    const connectSSE = useCallback((taskId: string) => {
        const eventSource = new EventSource(`http://localhost:8000/api/v1/events/${taskId}`);
        
        eventSource.addEventListener('connected', () => {
            console.log('SSE connected for task:', taskId);
        });
        
        eventSource.addEventListener('progress', (event) => {
            const data = JSON.parse(event.data);
            setTaskStatus({
                task_id: data.task_id,
                ticker: data.ticker,
                status: data.status,
                progress: data.progress,
                current_step: data.current_step,
            });
            
            if (data.status === 'completed' && data.data) {
                // Got analysis results directly from SSE
                const analysisData = data.data;
                setReport({
                    id: taskId,
                    ticker: data.ticker,
                    company_name: analysisData.stock_data?.company_info?.name || data.ticker,
                    analyzed_at: new Date().toISOString(),
                    price_data: analysisData.stock_data?.price_history || [],
                    news_summary: analysisData.summary || '',
                    sentiment_score: analysisData.sentiment?.overall_score || 0,
                    sentiment_breakdown: analysisData.sentiment?.breakdown || { positive: 0, negative: 0, neutral: 0 },
                    sentiment_details: analysisData.sentiment?.details || [],
                    ai_insights: analysisData.insights || '',
                });
                setPageState('complete');
                eventSource.close();
            } else if (data.status === 'failed') {
                setError(data.error || 'Analysis failed');
                setPageState('error');
                eventSource.close();
            }
        });
        
        eventSource.addEventListener('error', () => {
            console.error('SSE connection error');
            eventSource.close();
        });
        
        return eventSource;
    }, []);

    // Start analysis on mount
    useEffect(() => {
        let eventSource: EventSource | null = null;
        
        const startAnalysis = async () => {
            try {
                // Always request fresh analysis (no caching)
                setPageState('analyzing');
                const response = await requestAnalysis(ticker);
                eventSource = connectSSE(response.task_id);
            } catch (err: any) {
                console.error('Error starting analysis:', err);
                setError(err.message || 'Failed to start analysis');
                setPageState('error');
            }
        };

        startAnalysis();
        
        return () => {
            if (eventSource) {
                eventSource.close();
            }
        };
    }, [ticker, connectSSE]);

    // Loading state
    if (pageState === 'loading') {
        return (
            <main className="min-h-screen bg-gray-50">
                <div className="container mx-auto px-4 py-16">
                    <div className="flex flex-col items-center justify-center">
                        <div className="w-12 h-12 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin mb-4" />
                        <p className="text-gray-600">Loading...</p>
                    </div>
                </div>
            </main>
        );
    }

    // Analyzing state
    if (pageState === 'analyzing') {
        return (
            <main className="min-h-screen bg-gray-50">
                <Header ticker={ticker} />
                <div className="container mx-auto px-4 py-16">
                    <div className="max-w-md mx-auto bg-white rounded-xl shadow-lg p-8">
                        <div className="text-center">
                            <div className="w-16 h-16 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin mx-auto mb-6" />
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">
                                Analyzing {ticker}
                            </h2>
                            <p className="text-gray-600 mb-6">
                                {taskStatus?.current_step || 'Initializing analysis...'}
                            </p>

                            {/* Progress bar */}
                            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                                <div
                                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${taskStatus?.progress || 0}%` }}
                                />
                            </div>
                            <p className="text-sm text-gray-500">
                                {taskStatus?.progress || 0}% complete
                            </p>
                        </div>
                    </div>
                </div>
            </main>
        );
    }

    // Error state
    if (pageState === 'error') {
        return (
            <main className="min-h-screen bg-gray-50">
                <Header ticker={ticker} />
                <div className="container mx-auto px-4 py-16">
                    <div className="max-w-md mx-auto bg-white rounded-xl shadow-lg p-8">
                        <div className="text-center">
                            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                <svg
                                    className="w-8 h-8 text-red-500"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </div>
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">
                                Analysis Failed
                            </h2>
                            <p className="text-gray-600 mb-6">{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        );
    }

    // Complete state - show report
    if (!report) {
        return null;
    }

    return (
        <main className="min-h-screen bg-gray-50">
            <Header ticker={ticker} companyName={report.company_name} />

            <div className="container mx-auto px-4 py-8">
                {/* Company Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-4 mb-2">
                        <h1 className="text-3xl font-bold text-gray-900">
                            {report.company_name || ticker}
                        </h1>
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-semibold">
                            {ticker}
                        </span>
                    </div>
                    <p className="text-gray-500">
                        Last analyzed: {new Date(report.analyzed_at).toLocaleString()}
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Price Chart */}
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">
                            Price History
                        </h2>
                        <PriceChart data={report.price_data} height={300} />
                    </div>

                    {/* Sentiment Analysis */}
                    <div className="bg-white rounded-xl shadow-sm p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">
                            Sentiment Analysis
                        </h2>
                        <SentimentDisplay
                            score={report.sentiment_score}
                            breakdown={report.sentiment_breakdown}
                        />
                    </div>

                    {/* News Summary */}
                    <div className="bg-white rounded-xl shadow-sm p-6 lg:col-span-2">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">
                            News Summary
                        </h2>
                        {report.news_summary ? (
                            <div className="prose prose-gray max-w-none">
                                <p className="text-gray-700 whitespace-pre-wrap">
                                    {report.news_summary}
                                </p>
                            </div>
                        ) : (
                            <p className="text-gray-500">No news summary available.</p>
                        )}
                    </div>

                    {/* AI Insights */}
                    <div className="bg-white rounded-xl shadow-sm p-6 lg:col-span-2">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">
                            <span className="inline-flex items-center gap-2">
                                <svg
                                    className="w-6 h-6 text-purple-500"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                                    />
                                </svg>
                                AI Insights
                            </span>
                        </h2>
                        {report.ai_insights ? (
                            <div className="prose prose-gray max-w-none">
                                <p className="text-gray-700 whitespace-pre-wrap">
                                    {report.ai_insights}
                                </p>
                            </div>
                        ) : (
                            <p className="text-gray-500">No AI insights available.</p>
                        )}
                    </div>

                    {/* Sentiment Details */}
                    {report.sentiment_details && report.sentiment_details.length > 0 && (
                        <div className="bg-white rounded-xl shadow-sm p-6 lg:col-span-2">
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">
                                News Sentiment Details
                            </h2>
                            <div className="space-y-3">
                                {report.sentiment_details.map((detail: SentimentResult, index: number) => (
                                    <div
                                        key={index}
                                        className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                                    >
                                        <SentimentBadge sentiment={detail.sentiment} />
                                        <div className="flex-1">
                                            <p className="font-medium text-gray-900">
                                                {detail.headline}
                                            </p>
                                            {detail.reasoning && (
                                                <p className="text-sm text-gray-600 mt-1">
                                                    {detail.reasoning}
                                                </p>
                                            )}
                                        </div>
                                        <span className="text-sm text-gray-500">
                                            {(detail.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Chat CTA */}
                <div className="mt-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 text-white">
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-xl font-semibold mb-2">
                                Have questions about {ticker}?
                            </h3>
                            <p className="text-blue-100">
                                Chat with our AI assistant for deeper insights and analysis.
                            </p>
                        </div>
                        <Link
                            href={`/chat?ticker=${ticker}`}
                            className="px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
                        >
                            Start Chat
                        </Link>
                    </div>
                </div>
            </div>
        </main>
    );
}

function Header({ ticker, companyName }: { ticker: string; companyName?: string }) {
    return (
        <header className="bg-white border-b border-gray-200">
            <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between">
                    <Link
                        href="/"
                        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
                    >
                        <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10 19l-7-7m0 0l7-7m-7 7h18"
                            />
                        </svg>
                        Back to Search
                    </Link>
                    <Link href="/" className="text-xl font-bold text-blue-600">
                        InvestingIQ
                    </Link>
                </div>
            </div>
        </header>
    );
}

function SentimentDisplay({
    score,
    breakdown,
}: {
    score: number | null;
    breakdown: { positive: number; negative: number; neutral: number } | null;
}) {
    if (score === null) {
        return (
            <div className="flex items-center justify-center h-48">
                <p className="text-gray-500">No sentiment data available</p>
            </div>
        );
    }

    // Score is typically -1 to 1, convert to 0-100 for display
    const normalizedScore = ((score + 1) / 2) * 100;
    const sentimentLabel =
        score > 0.2 ? 'Positive' : score < -0.2 ? 'Negative' : 'Neutral';
    const sentimentColor =
        score > 0.2
            ? 'text-green-600'
            : score < -0.2
                ? 'text-red-600'
                : 'text-gray-600';
    const bgColor =
        score > 0.2
            ? 'bg-green-500'
            : score < -0.2
                ? 'bg-red-500'
                : 'bg-gray-500';

    return (
        <div className="space-y-6">
            {/* Main Score */}
            <div className="text-center">
                <div className="relative w-32 h-32 mx-auto mb-4">
                    <svg className="w-full h-full transform -rotate-90">
                        <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="#E5E7EB"
                            strokeWidth="12"
                            fill="none"
                        />
                        <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke={score > 0.2 ? '#10B981' : score < -0.2 ? '#EF4444' : '#6B7280'}
                            strokeWidth="12"
                            fill="none"
                            strokeDasharray={`${normalizedScore * 3.52} 352`}
                            strokeLinecap="round"
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-2xl font-bold ${sentimentColor}`}>
                            {score.toFixed(2)}
                        </span>
                    </div>
                </div>
                <p className={`text-lg font-semibold ${sentimentColor}`}>
                    {sentimentLabel}
                </p>
            </div>

            {/* Breakdown */}
            {breakdown && (
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Positive</span>
                        <div className="flex items-center gap-2">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-green-500 h-2 rounded-full"
                                    style={{ width: `${breakdown.positive}%` }}
                                />
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-12 text-right">
                                {breakdown.positive}%
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Neutral</span>
                        <div className="flex items-center gap-2">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-gray-500 h-2 rounded-full"
                                    style={{ width: `${breakdown.neutral}%` }}
                                />
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-12 text-right">
                                {breakdown.neutral}%
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Negative</span>
                        <div className="flex items-center gap-2">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-red-500 h-2 rounded-full"
                                    style={{ width: `${breakdown.negative}%` }}
                                />
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-12 text-right">
                                {breakdown.negative}%
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
    const colors: Record<string, string> = {
        positive: 'bg-green-100 text-green-700',
        negative: 'bg-red-100 text-red-700',
        neutral: 'bg-gray-100 text-gray-700',
    };

    return (
        <span
            className={`px-2 py-1 rounded text-xs font-medium ${colors[sentiment.toLowerCase()] || colors.neutral
                }`}
        >
            {sentiment}
        </span>
    );
}
