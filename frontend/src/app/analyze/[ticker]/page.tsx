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
import DualAnalysisView from '@/components/DualAnalysisView';
import LLMSettings from '@/components/LLMSettings';
import DarkModeToggle from '@/components/DarkModeToggle';
import { useLLMConfig } from '@/hooks/useLLMConfig';

interface AnalyzePageProps {
    params: Promise<{ ticker: string }>;
}

type PageState = 'loading' | 'analyzing' | 'complete' | 'error';
type AnalysisTab = 'overview' | 'dual' | 'ml' | 'llm';

export default function AnalyzePage({ params }: AnalyzePageProps) {
    const { ticker: rawTicker } = use(params);
    const ticker = rawTicker.toUpperCase();
    const [pageState, setPageState] = useState<PageState>('loading');
    const [taskStatus, setTaskStatus] = useState<AnalysisTaskStatus | null>(null);
    const [report, setReport] = useState<AnalysisReport | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<AnalysisTab>('overview');

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
                    sentiment_score: analysisData.llm_sentiment?.overall_score || analysisData.llm_sentiment?.score || analysisData.sentiment?.overall_score || null,
                    sentiment_breakdown: analysisData.llm_sentiment?.breakdown || analysisData.sentiment?.breakdown || null,
                    sentiment_details: analysisData.llm_sentiment?.details || analysisData.sentiment?.details || null,
                    ai_insights: analysisData.llm_insights || analysisData.insights || null,
                    llm_outlook: analysisData.llm_outlook || null,
                    llm_status: analysisData.llm_status || null,
                    dual_comparison: analysisData.dual_comparison || null,
                    financials_status: analysisData.financials_status || null,
                    financials_quarter: analysisData.financials_quarter || null,
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
                <div className="container mx-auto px-6 py-24">
                    <div className="flex flex-col items-center justify-center">
                        <div className="w-12 h-12 border-2 border-theme border-t-accent rounded-full animate-spin mb-5" />
                        <p className="eyebrow !text-theme-muted">Going to press…</p>
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
                <div className="container mx-auto px-6 py-20">
                    <div className="max-w-lg mx-auto card-paper p-10">
                        <div className="text-center">
                            <p className="eyebrow mb-3">Dispatch in Progress</p>
                            <h2 className="font-display font-bold text-3xl text-theme mb-3">
                                Analyzing <span className="font-mono">{ticker}</span>
                            </h2>
                            <p className="font-display italic text-theme-secondary mb-8">
                                {taskStatus?.current_step || 'Initializing analysis…'}
                            </p>

                            {/* Progress bar */}
                            <div className="w-full bg-theme-secondary h-1.5 mb-3 overflow-hidden">
                                <div
                                    className="bg-accent h-1.5 transition-all duration-500"
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
                            <p className="eyebrow !text-loss mb-3">Stop Press</p>
                            <h2 className="font-display font-bold text-3xl text-theme mb-3">
                                Analysis Failed
                            </h2>
                            <p className="font-display italic text-theme-secondary mb-8">{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="px-7 py-2.5 bg-primary text-white font-mono text-sm uppercase tracking-[0.15em] hover:bg-accent transition-colors"
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
                {/* Company Header — editorial dateline */}
                <div className="mb-8 animate-fade-up">
                    <p className="eyebrow mb-2">Company Dossier · {ticker}</p>
                    <div className="flex flex-wrap items-end gap-4">
                        <h1 className="font-display font-black text-theme tracking-tight leading-none"
                            style={{ fontSize: 'clamp(2.25rem, 6vw, 4rem)' }}>
                            {report.company_name || ticker}
                        </h1>
                        <span className="font-mono text-sm px-3 py-1.5 bg-primary text-white font-semibold tracking-wide mb-1">
                            {ticker}
                        </span>
                    </div>
                    <hr className="rule-gold mt-4" />
                    <p className="font-mono text-xs text-theme-muted mt-3 uppercase tracking-[0.15em]">
                        Filed: {new Date(report.analyzed_at).toLocaleString()}
                    </p>
                </div>

                {/* Price Chart — always visible */}
                <div className="card-paper p-6 mb-7 animate-fade-up" style={{ animationDelay: '0.08s' }}>
                    <h2 className="font-display font-semibold text-xl text-theme mb-1">
                        Price History
                    </h2>
                    <p className="eyebrow !text-theme-muted mb-4">Trailing market record</p>
                    <PriceChart data={report.price_data} height={300} />
                </div>

                {/* Analysis Tabs — section masthead */}
                <div className="mb-7 animate-fade-up" style={{ animationDelay: '0.14s' }}>
                    <div className="flex flex-wrap gap-x-1 gap-y-2 border-b-2 border-theme">
                        <TabButton active={activeTab === 'overview'} accent="primary" onClick={() => setActiveTab('overview')}>
                            Company Overview
                        </TabButton>
                        <TabButton active={activeTab === 'dual'} accent="primary" onClick={() => setActiveTab('dual')}>
                            ML vs LLM
                        </TabButton>
                        <TabButton active={activeTab === 'ml'} accent="gain" onClick={() => setActiveTab('ml')}>
                            ML Analysis
                        </TabButton>
                        <TabButton active={activeTab === 'llm'} accent="accent" onClick={() => setActiveTab('llm')}>
                            <span className="flex items-center gap-2">
                                LLM Analysis
                                {!hasLLMConfig && (
                                    <span className="px-1.5 py-0.5 bg-theme-secondary text-theme-muted font-mono text-[0.6rem] uppercase tracking-wider">
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

            {/* LLM Settings Floating Button */}
            <LLMSettings />
        </main>
    );
}

function TabButton({
    active,
    accent,
    onClick,
    children,
}: {
    active: boolean;
    accent: 'primary' | 'gain' | 'accent';
    onClick: () => void;
    children: React.ReactNode;
}) {
    const activeText =
        accent === 'gain' ? 'text-gain' : accent === 'accent' ? 'text-accent' : 'text-primary';
    const activeBorder =
        accent === 'gain' ? 'border-gain' : accent === 'accent' ? 'border-accent' : 'border-primary';
    return (
        <button
            onClick={onClick}
            className={`px-4 md:px-5 py-3 font-mono text-xs md:text-sm uppercase tracking-[0.12em] -mb-0.5 border-b-2 transition-colors ${active
                ? `${activeBorder} ${activeText}`
                : 'border-transparent text-theme-muted hover:text-theme'
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
        <header className="border-b border-theme bg-theme-card/80 backdrop-blur-sm sticky top-0 z-30">
            <div className="container mx-auto px-6 py-3.5">
                <div className="flex items-center justify-between">
                    <Link
                        href="/"
                        className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.15em] text-theme-secondary hover:text-accent transition-colors"
                    >
                        <svg
                            className="w-4 h-4"
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
                        Back
                    </Link>
                    <Link href="/" className="absolute left-1/2 -translate-x-1/2 font-display font-black text-xl text-theme tracking-tight">
                        InvestingIQ
                    </Link>
                    <DarkModeToggle />
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
