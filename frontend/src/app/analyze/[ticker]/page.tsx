'use client';

import { useState, useCallback, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
import DualAnalysisView from '@/components/DualAnalysisView';
import AnalysisSetupModal from '@/components/AnalysisSetupModal';
import DarkModeToggle from '@/components/DarkModeToggle';
import { useLLMConfig, LLMConfig as StoredLLMConfig } from '@/hooks/useLLMConfig';

interface AnalyzePageProps {
    params: Promise<{ ticker: string }>;
}

type PageState = 'setup' | 'analyzing' | 'complete' | 'error';
type AnalysisTab = 'overview' | 'dual' | 'ml' | 'llm';

export default function AnalyzePage({ params }: AnalyzePageProps) {
    const { ticker: rawTicker } = use(params);
    const ticker = rawTicker.toUpperCase();
    const router = useRouter();
    const [pageState, setPageState] = useState<PageState>('setup');
    const [taskStatus, setTaskStatus] = useState<AnalysisTaskStatus | null>(null);
    const [report, setReport] = useState<AnalysisReport | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<AnalysisTab>('overview');
    const [showSettings, setShowSettings] = useState(false);

    const { config: llmConfig, hasConfig: hasLLMConfig, isLoaded: llmConfigLoaded, saveConfig } = useLLMConfig();

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
                    sentiment_score: analysisData.llm_sentiment?.overall_score || analysisData.llm_sentiment?.score || analysisData.sentiment?.overall_score || null,
                    sentiment_breakdown: analysisData.llm_sentiment?.breakdown || analysisData.sentiment?.breakdown || null,
                    sentiment_details: analysisData.llm_sentiment?.details || analysisData.sentiment?.details || null,
                    ai_insights: analysisData.llm_insights || analysisData.insights || null,
                    llm_outlook: analysisData.llm_outlook || null,
                    llm_status: analysisData.llm_status || null,
                    dual_comparison: analysisData.dual_comparison || null,
                    financials_status: analysisData.financials_status || null,
                    financials_quarter: analysisData.financials_quarter || null,
                    rate_limited: analysisData.stock_data?.rate_limited || false,
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

    const startAnalysis = useCallback((stored: StoredLLMConfig) => {
        // Persist for next time, then kick off the analysis with the provided keys.
        saveConfig(stored);
        setPageState('analyzing');
        setError(null);

        const llmConfigPayload: LLMConfig = {
            provider: stored.provider,
            api_key: stored.apiKey,
            model: stored.model,
        };

        requestAnalysis(ticker, llmConfigPayload, stored.alphaVantageKey)
            .then((response) => {
                connectSSE(response.task_id);
            })
            .catch((err: any) => {
                console.error('Error starting analysis:', err);
                setError(err.message || 'Failed to start analysis');
                setPageState('error');
            });
    }, [ticker, connectSSE, saveConfig]);

    // Setup state - collect API keys before running analysis
    if (pageState === 'setup') {
        return (
            <main className="min-h-screen bg-theme">
                <Header ticker={ticker} />
                {llmConfigLoaded && (
                    <AnalysisSetupModal
                        ticker={ticker}
                        initialConfig={llmConfig}
                        onStart={startAnalysis}
                        onCancel={() => router.push('/')}
                    />
                )}
            </main>
        );
    }

    // Analyzing state
    if (pageState === 'analyzing') {
        return (
            <main className="min-h-screen bg-theme">
                <Header ticker={ticker} />
                <div className="container mx-auto px-6 py-20">
                    <div className="max-w-lg mx-auto card-paper p-10">
                        <div className="text-center">
                            <span className="ai-badge mb-5"><span className="dot" /> Running Models</span>
                            <h2 className="font-display font-bold text-3xl text-theme mb-2 mt-2">
                                Analyzing <span className="font-mono text-primary">{ticker}</span>
                            </h2>
                            <p className="text-theme-secondary mb-8">
                                {taskStatus?.current_step || 'Initializing analysis…'}
                            </p>

                            {/* Progress bar */}
                            <div className="w-full bg-theme-secondary rounded-full h-2 mb-3 overflow-hidden">
                                <div
                                    className="bg-primary h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${taskStatus?.progress || 0}%` }}
                                />
                            </div>
                            <p className="font-mono text-xs text-theme-muted tracking-wider">
                                {taskStatus?.progress || 0}% COMPLETE
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
                <div className="container mx-auto px-6 py-20">
                    <div className="max-w-lg mx-auto card-paper p-10">
                        <div className="text-center">
                            <div className="w-12 h-12 rounded-full bg-loss/10 flex items-center justify-center mx-auto mb-5">
                                <svg className="w-6 h-6 text-loss" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                                </svg>
                            </div>
                            <h2 className="font-display font-bold text-2xl text-theme mb-2">
                                Analysis Failed
                            </h2>
                            <p className="text-theme-secondary mb-8">{error}</p>
                            <button
                                onClick={() => { setError(null); setPageState('setup'); }}
                                className="px-6 py-2.5 bg-primary text-white rounded-lg font-medium text-sm hover:brightness-110 transition-all"
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
            />

            <div className="container mx-auto px-6 py-10">
                {/* Company Header */}
                <div className="mb-8 animate-fade-up">
                    <span className="eyebrow">Equity Research · {ticker}</span>
                    <div className="flex flex-wrap items-center gap-3 mt-3">
                        <h1 className="font-display font-extrabold text-theme tracking-tight leading-none"
                            style={{ fontSize: 'clamp(2rem, 5vw, 3.25rem)' }}>
                            {report.company_name || ticker}
                        </h1>
                        <span className="font-mono text-sm px-2.5 py-1 rounded-md bg-primary/10 text-primary font-semibold tracking-wide border border-primary/20">
                            {ticker}
                        </span>
                    </div>
                    <p className="font-mono text-xs text-theme-muted mt-3">
                        Last analyzed {new Date(report.analyzed_at).toLocaleString()}
                    </p>
                </div>

                {/* Price Chart — always visible */}
                <div className="card-paper p-6 mb-7 animate-fade-up" style={{ animationDelay: '0.08s' }}>
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="font-display font-bold text-lg text-theme">
                            Price History
                        </h2>
                        <span className="ai-badge"><span className="dot" /> Live</span>
                    </div>
                    {report.rate_limited && report.price_data.length === 0 ? (
                        <RateLimitNotice onUpdateKeys={() => setShowSettings(true)} />
                    ) : (
                        <PriceChart data={report.price_data} height={300} />
                    )}
                </div>

                {/* Analysis Tabs */}
                <div className="mb-7 animate-fade-up" style={{ animationDelay: '0.14s' }}>
                    <div className="flex flex-wrap gap-1 p-1 card-paper !rounded-xl">
                        <TabButton active={activeTab === 'overview'} onClick={() => setActiveTab('overview')}>
                            Overview
                        </TabButton>
                        <TabButton active={activeTab === 'dual'} onClick={() => setActiveTab('dual')}>
                            ML vs LLM
                        </TabButton>
                        <TabButton active={activeTab === 'ml'} onClick={() => setActiveTab('ml')}>
                            ML Analysis
                        </TabButton>
                        <TabButton active={activeTab === 'llm'} onClick={() => setActiveTab('llm')}>
                            <span className="flex items-center gap-2">
                                LLM Analysis
                                {!hasLLMConfig && (
                                    <span className="px-1.5 py-0.5 rounded bg-theme-secondary text-theme-muted font-mono text-[0.6rem] uppercase tracking-wider">
                                        Locked
                                    </span>
                                )}
                            </span>
                        </TabButton>
                    </div>
                </div>

                {/* Tab Content */}
                <div className="animate-fade-in" key={activeTab}>
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
                    {activeTab === 'dual' && (
                        <DualAnalysisView
                            ml={report.ml_analysis}
                            llm={{
                                outlook: report.llm_outlook,
                                sentiment_score: report.sentiment_score,
                                insight: report.ai_insights,
                            }}
                            llmStatus={report.llm_status}
                            comparison={report.dual_comparison}
                        />
                    )}
                    {activeTab === 'llm' && (
                        <LLMAnalysisView
                            hasLLMConfig={hasLLMConfig}
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
            </div>

            {/* Floating settings gear — update keys anytime */}
            <SettingsButton onClick={() => setShowSettings(true)} />

            {showSettings && (
                <AnalysisSetupModal
                    ticker={ticker}
                    initialConfig={llmConfig}
                    onStart={(stored) => {
                        setShowSettings(false);
                        startAnalysis(stored);
                    }}
                    onCancel={() => setShowSettings(false)}
                />
            )}
        </main>
    );
}

function SettingsButton({ onClick }: { onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            title="Update API keys"
            className="fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full shadow-lg flex items-center justify-center bg-primary hover:brightness-110 transition-all hover:scale-105"
        >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
        </button>
    );
}

function RateLimitNotice({ onUpdateKeys }: { onUpdateKeys: () => void }) {
    return (
        <div className="flex flex-col items-center justify-center text-center py-12 px-6 bg-theme-secondary rounded-lg">
            <div className="w-12 h-12 rounded-full bg-yellow-500/10 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
            </div>
            <p className="font-display font-bold text-theme mb-1">Alpha Vantage rate limit reached</p>
            <p className="text-sm text-theme-secondary max-w-md leading-relaxed mb-4">
                Your Alpha Vantage API key has hit its daily request limit, so price data
                couldn&apos;t be fetched. This is an upstream provider limit, not an app error.
                Try again later or update your key.
            </p>
            <button
                onClick={onUpdateKeys}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-primary text-white hover:brightness-110 transition-all"
            >
                Update API Keys
            </button>
        </div>
    );
}

function TabButton({
    active,
    onClick,
    children,
}: {
    active: boolean;
    onClick: () => void;
    children: React.ReactNode;
}) {
    return (
        <button
            onClick={onClick}
            className={`px-4 md:px-5 py-2.5 rounded-lg text-sm font-medium transition-colors ${active
                ? 'bg-primary text-white shadow-sm'
                : 'text-theme-secondary hover:text-theme hover:bg-theme-secondary'
                }`}
        >
            {children}
        </button>
    );
}

function Header({
    ticker,
    companyName,
}: {
    ticker: string;
    companyName?: string;
}) {
    return (
        <header className="border-b border-theme bg-theme-card/80 backdrop-blur-md sticky top-0 z-30">
            <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                <Link
                    href="/"
                    className="flex items-center gap-2 text-sm font-medium text-theme-secondary hover:text-theme transition-colors"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    Back
                </Link>
                <Link href="/" className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2">
                    <span className="inline-flex items-center justify-center w-7 h-7 rounded-md bg-primary text-white">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M4 18L9 11l4 4 7-9" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M16 6h4v4" />
                        </svg>
                    </span>
                    <span className="font-display font-extrabold text-lg tracking-tight text-theme">InvestingIQ</span>
                </Link>
                <DarkModeToggle />
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
                            className="stroke-gray-200 dark:stroke-slate-700"
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
                            <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
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
                            <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
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
                            <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
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
