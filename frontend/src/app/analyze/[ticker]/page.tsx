'use client';

import { useState, useEffect, useCallback, use } from 'react';
import Link from 'next/link';
import {
    requestAnalysis,
    AnalysisReport,
    AnalysisTaskStatus,
    SentimentResult,
    LLMConfig,
} from '@/lib/api';
import PriceChart from '@/components/PriceChart';
import CompanyOverview from '@/components/CompanyOverview';
import MLAnalysisView from '@/components/MLAnalysisView';
import LLMAnalysisView from '@/components/LLMAnalysisView';
import LLMSettings from '@/components/LLMSettings';
import DarkModeToggle from '@/components/DarkModeToggle';
import { useLLMConfig } from '@/hooks/useLLMConfig';

interface AnalyzePageProps {
    params: Promise<{ ticker: string }>;
}

type PageState = 'loading' | 'analyzing' | 'complete' | 'error';
type AnalysisTab = 'overview' | 'ml' | 'llm';

export default function AnalyzePage({ params }: AnalyzePageProps) {
    const { ticker: rawTicker } = use(params);
    const ticker = rawTicker.toUpperCase();
    const [pageState, setPageState] = useState<PageState>('loading');
    const [taskStatus, setTaskStatus] = useState<AnalysisTaskStatus | null>(null);
    const [report, setReport] = useState<AnalysisReport | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<AnalysisTab>('overview');
    const [showLLMSettings, setShowLLMSettings] = useState(false);
    
    const { config: llmConfig, hasConfig: hasLLMConfig, isLoaded: llmConfigLoaded } = useLLMConfig();

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
                error_message: data.error_message || null,
            });
            
            if (data.status === 'completed' && data.data) {
                const analysisData = data.data;
                setReport({
                    id: taskId,
                    ticker: data.ticker,
                    company_name: analysisData.stock_data?.company_info?.name || data.ticker,
                    analyzed_at: new Date().toISOString(),
                    price_data: analysisData.stock_data?.price_history || [],
                    current_price: analysisData.stock_data?.current_price || null,
                    company_info: analysisData.stock_data?.company_info || null,
                    news: analysisData.news || [],
                    earnings: analysisData.stock_data?.earnings || null,
                    ml_analysis: {
                        prediction: analysisData.ml_prediction || null,
                        technical: analysisData.ml_technical || null,
                        sentiment: analysisData.ml_sentiment || null,
                    },
                    news_summary: analysisData.llm_summary || analysisData.summary || null,
                    sentiment_score: analysisData.llm_sentiment?.overall_score || analysisData.sentiment?.overall_score || null,
                    sentiment_breakdown: analysisData.llm_sentiment?.breakdown || analysisData.sentiment?.breakdown || null,
                    sentiment_details: analysisData.llm_sentiment?.details || analysisData.sentiment?.details || null,
                    ai_insights: analysisData.llm_insights || analysisData.insights || null,
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

    useEffect(() => {
        if (!llmConfigLoaded) return;
        
        let eventSource: EventSource | null = null;
        
        const startAnalysis = async () => {
            try {
                setPageState('analyzing');
                const llmConfigPayload: LLMConfig | null = llmConfig ? {
                    provider: llmConfig.provider,
                    api_key: llmConfig.apiKey,
                    model: llmConfig.model,
                } : null;
                const response = await requestAnalysis(ticker, llmConfigPayload);
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
    }, [ticker, connectSSE, llmConfig, llmConfigLoaded]);

    // Loading state
    if (pageState === 'loading') {
        return (
            <main className="min-h-screen bg-theme">
                <div className="container mx-auto px-4 py-16">
                    <div className="flex flex-col items-center justify-center">
                        <div className="w-12 h-12 border-4 border-theme border-t-primary rounded-full animate-spin mb-4" />
                        <p className="text-theme-secondary">Loading...</p>
                    </div>
                </div>
            </main>
        );
    }

    // Analyzing state
    if (pageState === 'analyzing') {
        return (
            <main className="min-h-screen bg-theme">
                <Header ticker={ticker} />
                <div className="container mx-auto px-4 py-16">
                    <div className="max-w-md mx-auto bg-theme-card rounded-xl shadow-lg p-8">
                        <div className="text-center">
                            <div className="w-16 h-16 border-4 border-theme border-t-primary rounded-full animate-spin mx-auto mb-6" />
                            <h2 className="text-xl font-semibold text-theme mb-2">
                                Analyzing {ticker}
                            </h2>
                            <p className="text-theme-secondary mb-6">
                                {taskStatus?.current_step || 'Initializing analysis...'}
                            </p>

                            {/* Progress bar */}
                            <div className="w-full bg-theme-secondary rounded-full h-2 mb-2">
                                <div
                                    className="bg-primary h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${taskStatus?.progress || 0}%` }}
                                />
                            </div>
                            <p className="text-sm text-theme-muted">
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
            <main className="min-h-screen bg-theme">
                <Header ticker={ticker} />
                <div className="container mx-auto px-4 py-16">
                    <div className="max-w-md mx-auto bg-theme-card rounded-xl shadow-lg p-8">
                        <div className="text-center">
                            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
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
                            <h2 className="text-xl font-semibold text-theme mb-2">
                                Analysis Failed
                            </h2>
                            <p className="text-theme-secondary mb-6">{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="px-6 py-2 bg-primary text-white rounded-lg hover:opacity-90 transition-opacity"
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
        <main className="min-h-screen bg-theme">
            <Header 
                ticker={ticker} 
                companyName={report.company_name} 
                onLLMSettingsClick={() => setShowLLMSettings(true)}
            />

            <div className="container mx-auto px-4 py-8">
                {/* Company Header */}
                <div className="mb-6">
                    <div className="flex items-center gap-4 mb-2">
                        <h1 className="text-3xl font-bold text-theme">
                            {report.company_name || ticker}
                        </h1>
                        <span className="px-3 py-1 bg-primary/20 text-primary rounded-full font-semibold">
                            {ticker}
                        </span>
                    </div>
                    <p className="text-theme-muted">
                        Last analyzed: {new Date(report.analyzed_at).toLocaleString()}
                    </p>
                </div>

                {/* Price Chart - Always visible */}
                <div className="bg-theme-card rounded-xl shadow-md p-6 mb-6">
                    <h2 className="text-xl font-semibold text-theme mb-4">
                        Price History
                    </h2>
                    <PriceChart data={report.price_data} height={300} />
                </div>

                {/* Analysis Tabs */}
                <div className="mb-6">
                    <div className="flex border-b border-theme/30">
                        <button
                            onClick={() => setActiveTab('overview')}
                            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                                activeTab === 'overview'
                                    ? 'border-primary text-primary'
                                    : 'border-transparent text-theme-muted hover:text-theme'
                            }`}
                        >
                            <span className="flex items-center gap-2">
                                <span>🏢</span> Company Overview
                            </span>
                        </button>
                        <button
                            onClick={() => setActiveTab('ml')}
                            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                                activeTab === 'ml'
                                    ? 'border-green-500 text-green-500'
                                    : 'border-transparent text-theme-muted hover:text-theme'
                            }`}
                        >
                            <span className="flex items-center gap-2">
                                <span>📊</span> ML Analysis
                            </span>
                        </button>
                        <button
                            onClick={() => setActiveTab('llm')}
                            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                                activeTab === 'llm'
                                    ? 'border-blue-400 text-blue-400'
                                    : 'border-transparent text-theme-muted hover:text-theme'
                            }`}
                        >
                            <span className="flex items-center gap-2">
                                <span>🤖</span> LLM Analysis
                                {!hasLLMConfig && (
                                    <span className="px-1.5 py-0.5 bg-theme-secondary text-theme-muted text-xs rounded">
                                        Locked
                                    </span>
                                )}
                            </span>
                        </button>
                    </div>
                </div>

                {/* Tab Content */}
                {activeTab === 'overview' && (
                    <CompanyOverview
                        ticker={ticker}
                        companyInfo={report.company_info}
                        currentPrice={report.current_price}
                        news={report.news}
                        earnings={report.earnings}
                    />
                )}
                {activeTab === 'ml' && (
                    <MLAnalysisView
                        prediction={report.ml_analysis?.prediction}
                        technical={report.ml_analysis?.technical}
                        sentiment={report.ml_analysis?.sentiment}
                    />
                )}
                {activeTab === 'llm' && (
                    <LLMAnalysisView
                        hasLLMConfig={hasLLMConfig}
                        onConfigureClick={() => setShowLLMSettings(true)}
                        newsSummary={report.news_summary || undefined}
                        sentiment={report.sentiment_score !== null ? {
                            overall_score: report.sentiment_score,
                            breakdown: report.sentiment_breakdown || { positive: 0, negative: 0, neutral: 0 },
                            details: report.sentiment_details || [],
                        } : undefined}
                        aiInsights={report.ai_insights || undefined}
                    />
                )}


            </div>

            {/* LLM Settings Modal */}
            <LLMSettings isOpen={showLLMSettings} onClose={() => setShowLLMSettings(false)} />
        </main>
    );
}

function Header({ 
    ticker, 
    companyName,
    onLLMSettingsClick 
}: { 
    ticker: string; 
    companyName?: string;
    onLLMSettingsClick?: () => void;
}) {
    return (
        <header className="bg-theme-card shadow-sm">
            <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between">
                    <Link
                        href="/"
                        className="flex items-center gap-2 text-theme-secondary hover:text-theme transition-colors"
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
                    <div className="flex items-center gap-4">
                        <DarkModeToggle />
                        {onLLMSettingsClick && (
                            <button
                                onClick={onLLMSettingsClick}
                                className="flex items-center gap-1 px-3 py-1.5 text-sm text-theme-secondary hover:text-theme hover:bg-theme-secondary rounded-lg transition-colors"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                </svg>
                                LLM
                            </button>
                        )}
                        <Link href="/" className="text-xl font-bold text-primary">
                            InvestingIQ
                        </Link>
                    </div>
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
                <p className="text-theme-muted">No sentiment data available</p>
            </div>
        );
    }

    // Score is typically -1 to 1, convert to 0-100 for display
    const normalizedScore = ((score + 1) / 2) * 100;
    const sentimentLabel =
        score > 0.2 ? 'Positive' : score < -0.2 ? 'Negative' : 'Neutral';
    const sentimentColor =
        score > 0.2
            ? 'text-green-500'
            : score < -0.2
                ? 'text-red-500'
                : 'text-theme-secondary';

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
                            className="stroke-gray-200 dark:stroke-gray-700"
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
                        <span className="text-sm text-theme-secondary">Positive</span>
                        <div className="flex items-center gap-2">
                            <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div
                                    className="bg-green-500 h-2 rounded-full"
                                    style={{ width: `${breakdown.positive}%` }}
                                />
                            </div>
                            <span className="text-sm font-medium text-theme w-12 text-right">
                                {breakdown.positive}%
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-theme-secondary">Neutral</span>
                        <div className="flex items-center gap-2">
                            <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div
                                    className="bg-gray-500 h-2 rounded-full"
                                    style={{ width: `${breakdown.neutral}%` }}
                                />
                            </div>
                            <span className="text-sm font-medium text-theme w-12 text-right">
                                {breakdown.neutral}%
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-theme-secondary">Negative</span>
                        <div className="flex items-center gap-2">
                            <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div
                                    className="bg-red-500 h-2 rounded-full"
                                    style={{ width: `${breakdown.negative}%` }}
                                />
                            </div>
                            <span className="text-sm font-medium text-theme w-12 text-right">
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
        positive: 'bg-green-500/20 text-green-500',
        negative: 'bg-red-500/20 text-red-500',
        neutral: 'bg-gray-500/20 text-theme-secondary',
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
