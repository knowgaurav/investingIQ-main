'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import StockSearch from '@/components/StockSearch';
import LLMSettings from '@/components/LLMSettings';
import DarkModeToggle from '@/components/DarkModeToggle';
import { StockSearchResult } from '@/lib/api';
import { useLLMConfig, PROVIDER_NAMES } from '@/hooks/useLLMConfig';

const RECENT_SEARCHES_KEY = 'investingiq_recent_searches';

export default function Home() {
    const router = useRouter();
    const [recentSearches, setRecentSearches] = useState<StockSearchResult[]>([]);
    const [showLLMSettings, setShowLLMSettings] = useState(false);
    const { config: llmConfig, hasConfig: hasLLMConfig } = useLLMConfig();

    // Load recent searches on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
            if (stored) {
                setRecentSearches(JSON.parse(stored));
            }
        } catch {
            // Ignore localStorage errors
        }
    }, []);

    const handleRecentClick = (ticker: string) => {
        router.push(`/analyze/${ticker}`);
    };

    const clearRecentSearches = () => {
        localStorage.removeItem(RECENT_SEARCHES_KEY);
        setRecentSearches([]);
    };

    return (
        <main className="min-h-screen bg-theme">
            {/* Top Right Controls */}
            <div className="absolute top-4 right-4 flex items-center gap-2">
                <DarkModeToggle />
                <button
                    onClick={() => setShowLLMSettings(true)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                        hasLLMConfig
                            ? 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50'
                            : 'bg-theme-secondary text-theme-secondary hover:opacity-80'
                    }`}
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {hasLLMConfig ? (
                        <span className="text-sm font-medium">
                            {PROVIDER_NAMES[llmConfig!.provider]}
                        </span>
                    ) : (
                        <span className="text-sm">Configure LLM</span>
                    )}
                </button>
            </div>

            {/* Hero Section */}
            <div className="container mx-auto px-4 pt-20 pb-16">
                <div className="text-center">
                    {/* Logo/Brand */}
                    <div className="mb-6">
                        <span className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-2xl shadow-lg mb-4">
                            <svg
                                className="w-8 h-8 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                                />
                            </svg>
                        </span>
                    </div>

                    {/* Title */}
                    <h1 className="text-5xl font-bold text-theme mb-4">
                        InvestingIQ
                    </h1>
                    <p className="text-xl text-theme-secondary mb-10 max-w-2xl mx-auto">
                        AI-Powered Stock Analysis Platform. Get instant insights,
                        sentiment analysis, and intelligent recommendations for any stock.
                    </p>

                    {/* Stock Search */}
                    <StockSearch onRecentSearchesChange={setRecentSearches} />

                    {/* Features */}
                    <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm text-theme-muted">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            Real-time Analysis
                        </span>
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            AI-Powered Insights
                        </span>
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            Sentiment Analysis
                        </span>
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            Any Stock Worldwide
                        </span>
                    </div>
                </div>
            </div>

            {/* Recent Searches Section */}
            {recentSearches.length > 0 && (
                <div className="container mx-auto px-4 pb-16">
                    <div className="max-w-xl mx-auto">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-theme-secondary">
                                Recent Searches
                            </h2>
                            <button
                                onClick={clearRecentSearches}
                                className="text-sm text-theme-muted hover:text-theme transition-colors"
                            >
                                Clear all
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {recentSearches.map((stock: StockSearchResult) => (
                                <button
                                    key={stock.ticker}
                                    onClick={() => handleRecentClick(stock.ticker)}
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-theme-card border border-theme rounded-full hover:border-primary transition-colors group"
                                >
                                    <span className="font-semibold text-theme group-hover:text-primary">
                                        {stock.ticker}
                                    </span>
                                    <span className="text-sm text-theme-muted group-hover:text-primary">
                                        {stock.name.length > 20
                                            ? `${stock.name.substring(0, 20)}...`
                                            : stock.name}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Popular Stocks Section */}
            <div className="container mx-auto px-4 pb-20">
                <div className="max-w-3xl mx-auto">
                    <h2 className="text-lg font-semibold text-theme-secondary mb-4 text-center">
                        Popular Stocks
                    </h2>
                    <div className="flex flex-wrap justify-center gap-3">
                        {['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JPM', 'V', 'WMT', 'JNJ', 'UNH'].map(
                            (ticker) => (
                                <button
                                    key={ticker}
                                    onClick={() => handleRecentClick(ticker)}
                                    className="px-5 py-2.5 bg-theme-card border border-theme text-theme rounded-lg hover:bg-primary hover:text-white hover:border-primary transition-colors font-medium"
                                >
                                    {ticker}
                                </button>
                            )
                        )}
                    </div>
                </div>
            </div>

            {/* LLM Settings Modal */}
            <LLMSettings isOpen={showLLMSettings} onClose={() => setShowLLMSettings(false)} />
        </main>
    );
}
