'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import StockSearch from '@/components/StockSearch';
import LLMSettings from '@/components/LLMSettings';
import DarkModeToggle from '@/components/DarkModeToggle';
import { StockSearchResult } from '@/lib/api';

const RECENT_SEARCHES_KEY = 'investingiq_recent_searches';

const TICKER_TAPE = [
    { sym: 'AAPL', px: '212.48', chg: '+1.24%', up: true },
    { sym: 'MSFT', px: '438.10', chg: '+0.62%', up: true },
    { sym: 'NVDA', px: '131.26', chg: '+3.08%', up: true },
    { sym: 'TSLA', px: '248.50', chg: '-2.11%', up: false },
    { sym: 'AMZN', px: '197.12', chg: '+0.47%', up: true },
    { sym: 'META', px: '563.27', chg: '+1.83%', up: true },
    { sym: 'GOOGL', px: '178.35', chg: '-0.34%', up: false },
    { sym: 'JPM', px: '243.91', chg: '+0.91%', up: true },
    { sym: 'V', px: '312.18', chg: '+0.18%', up: true },
    { sym: 'WMT', px: '91.44', chg: '-0.55%', up: false },
];

const CAPABILITIES = [
    {
        tag: 'Forecasting',
        title: 'ML Price Models',
        body: 'Ensemble ARIMA, Prophet, and gradient-boosted signals project 7- and 30-day price paths with confidence bands.',
    },
    {
        tag: 'NLP',
        title: 'Sentiment Engine',
        body: 'Transformer-based scoring reads the news tape headline-by-headline, surfacing bullish and bearish pressure in real time.',
    },
    {
        tag: 'LLM',
        title: 'AI Analyst Desk',
        body: 'Large language models synthesize fundamentals, technicals, and filings into a plain-English research note.',
    },
    {
        tag: 'Technicals',
        title: 'Signal Coverage',
        body: 'RSI, MACD, Bollinger bands, and support/resistance computed continuously across every covered name.',
    },
];

const WATCHLIST = [
    { sym: 'AAPL', name: 'Apple Inc.' },
    { sym: 'MSFT', name: 'Microsoft Corp.' },
    { sym: 'GOOGL', name: 'Alphabet Inc.' },
    { sym: 'AMZN', name: 'Amazon.com Inc.' },
    { sym: 'NVDA', name: 'NVIDIA Corp.' },
    { sym: 'TSLA', name: 'Tesla Inc.' },
    { sym: 'META', name: 'Meta Platforms' },
    { sym: 'JPM', name: 'JPMorgan Chase' },
    { sym: 'V', name: 'Visa Inc.' },
    { sym: 'WMT', name: 'Walmart Inc.' },
    { sym: 'JNJ', name: 'Johnson & Johnson' },
    { sym: 'UNH', name: 'UnitedHealth Grp.' },
];

export default function Home() {
    const router = useRouter();
    const [recentSearches, setRecentSearches] = useState<StockSearchResult[]>([]);

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
        <main className="min-h-screen bg-theme overflow-hidden">
            {/* ===== Top Nav ===== */}
            <nav className="border-b border-theme">
                <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                        <Logo />
                        <span className="font-display font-extrabold text-lg tracking-tight text-theme">
                            InvestingIQ
                        </span>
                    </div>
                    <div className="hidden md:flex items-center gap-7 font-mono text-xs uppercase tracking-[0.12em] text-theme-muted">
                        <span className="hover:text-theme transition-colors cursor-default">Research</span>
                        <span className="hover:text-theme transition-colors cursor-default">Models</span>
                        <span className="hover:text-theme transition-colors cursor-default">Coverage</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="ai-badge hidden sm:inline-flex">
                            <span className="dot" /> Live
                        </span>
                        <DarkModeToggle />
                    </div>
                </div>
            </nav>

            {/* ===== Ticker Tape ===== */}
            <div className="ticker-mask border-b border-theme bg-theme-secondary/50 overflow-hidden">
                <div className="flex w-max animate-ticker">
                    {[...TICKER_TAPE, ...TICKER_TAPE].map((t, i) => (
                        <span
                            key={i}
                            className="flex items-center gap-2 px-5 py-2 font-mono text-xs whitespace-nowrap"
                        >
                            <span className="font-semibold text-theme tracking-wide">{t.sym}</span>
                            <span className="text-theme-muted">{t.px}</span>
                            <span className={t.up ? 'text-gain' : 'text-loss'}>
                                {t.up ? '▲' : '▼'} {t.chg}
                            </span>
                            <span className="text-theme/20 pl-3">|</span>
                        </span>
                    ))}
                </div>
            </div>

            {/* ===== Hero ===== */}
            <section className="container mx-auto px-6 pt-20 pb-16">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="animate-fade-up">
                        <span className="ai-badge">
                            <span className="dot" /> AI · ML Research Platform
                        </span>
                    </div>

                    <h1 className="font-display font-extrabold text-theme tracking-tight mt-7 leading-[1.02] animate-fade-up"
                        style={{ animationDelay: '0.05s', fontSize: 'clamp(2.5rem, 6vw, 4.75rem)' }}>
                        Every stock, decoded
                        <br className="hidden sm:block" /> by <span className="text-primary">machine intelligence</span>
                    </h1>

                    <p className="mt-6 text-theme-secondary max-w-2xl mx-auto leading-relaxed animate-fade-up"
                        style={{ animationDelay: '0.12s', fontSize: 'clamp(1rem, 1.6vw, 1.18rem)' }}>
                        Where quantitative models meet generative AI — price forecasts, live
                        sentiment, and analyst-grade insight on any ticker, in seconds.
                    </p>

                    <div className="mt-10 animate-fade-up" style={{ animationDelay: '0.2s' }}>
                        <StockSearch onRecentSearchesChange={setRecentSearches} />
                    </div>

                    <div className="mt-6 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 font-mono text-xs text-theme-muted animate-fade-up"
                        style={{ animationDelay: '0.28s' }}>
                        <span className="flex items-center gap-2"><Check /> Real-time data</span>
                        <span className="flex items-center gap-2"><Check /> 4 ML model families</span>
                        <span className="flex items-center gap-2"><Check /> Global coverage</span>
                    </div>
                </div>
            </section>

            {/* ===== Capabilities ===== */}
            <section className="container mx-auto px-6 pb-20">
                <div className="max-w-6xl mx-auto">
                    <div className="flex items-end justify-between mb-7">
                        <div>
                            <span className="eyebrow">The Engine</span>
                            <h2 className="font-display font-bold text-2xl text-theme mt-2">
                                Four models, one verdict
                            </h2>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {CAPABILITIES.map((c, i) => (
                            <div
                                key={c.title}
                                className="card-paper p-6 group hover:border-primary/60 transition-colors animate-fade-up"
                                style={{ animationDelay: `${0.05 * i}s` }}
                            >
                                <span className="font-mono text-[0.65rem] uppercase tracking-[0.16em] text-accent">
                                    {c.tag}
                                </span>
                                <h3 className="font-display font-bold text-lg text-theme mt-3 mb-2">
                                    {c.title}
                                </h3>
                                <p className="text-sm text-theme-secondary leading-relaxed">
                                    {c.body}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ===== Recent Searches ===== */}
            {recentSearches.length > 0 && (
                <section className="container mx-auto px-6 pb-16">
                    <div className="max-w-6xl mx-auto">
                        <div className="flex items-center justify-between mb-4">
                            <span className="eyebrow">Recent Activity</span>
                            <button
                                onClick={clearRecentSearches}
                                className="font-mono text-[0.65rem] uppercase tracking-[0.14em] text-theme-muted hover:text-loss transition-colors"
                            >
                                Clear
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2.5">
                            {recentSearches.map((stock: StockSearchResult) => (
                                <button
                                    key={stock.ticker}
                                    onClick={() => handleRecentClick(stock.ticker)}
                                    className="group inline-flex items-center gap-2 px-4 py-2 card-paper hover:border-primary/60 transition-colors"
                                >
                                    <span className="font-mono font-semibold text-theme text-sm group-hover:text-primary transition-colors">
                                        {stock.ticker}
                                    </span>
                                    <span className="text-xs text-theme-muted">
                                        {stock.name.length > 22 ? `${stock.name.substring(0, 22)}…` : stock.name}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                </section>
            )}

            {/* ===== Coverage / Watchlist ===== */}
            <section className="container mx-auto px-6 pb-24">
                <div className="max-w-6xl mx-auto">
                    <div className="mb-7">
                        <span className="eyebrow">Coverage Universe</span>
                        <h2 className="font-display font-bold text-2xl text-theme mt-2">
                            Most-followed names
                        </h2>
                    </div>
                    <div className="card-paper overflow-hidden">
                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4">
                            {WATCHLIST.map((s, i) => (
                                <button
                                    key={s.sym}
                                    onClick={() => handleRecentClick(s.sym)}
                                    className={`group flex items-center justify-between gap-3 px-5 py-4 text-left hover:bg-theme-secondary transition-colors border-theme
                                        ${i % 4 !== 3 ? 'lg:border-r' : ''} ${i % 3 !== 2 ? 'sm:border-r lg:border-r-0' : ''} ${i % 2 !== 1 ? 'border-r sm:border-r-0' : ''}
                                        ${i < WATCHLIST.length - (WATCHLIST.length % 4 || 4) ? 'border-b' : ''}`}
                                >
                                    <div className="min-w-0">
                                        <span className="block font-mono font-semibold text-theme group-hover:text-primary transition-colors">
                                            {s.sym}
                                        </span>
                                        <span className="block text-xs text-theme-muted truncate">{s.name}</span>
                                    </div>
                                    <svg className="w-4 h-4 text-theme-muted group-hover:text-primary transition-colors shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* ===== Footer ===== */}
            <footer className="border-t border-theme">
                <div className="container mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                        <Logo />
                        <span className="font-display font-bold text-theme">InvestingIQ</span>
                    </div>
                    <p className="font-mono text-[0.7rem] text-theme-muted text-center">
                        For informational purposes only · Not investment advice
                    </p>
                </div>
            </footer>

            <LLMSettings />
        </main>
    );
}

function Logo() {
    return (
        <span className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-primary text-white shadow-sm">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M4 18L9 11l4 4 7-9" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M16 6h4v4" />
            </svg>
        </span>
    );
}

function Check() {
    return (
        <svg className="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
        </svg>
    );
}
