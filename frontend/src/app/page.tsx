'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import StockSearch from '@/components/StockSearch';
import LLMSettings from '@/components/LLMSettings';
import DarkModeToggle from '@/components/DarkModeToggle';
import { StockSearchResult } from '@/lib/api';

const RECENT_SEARCHES_KEY = 'investingiq_recent_searches';

const TICKER_TAPE = [
    { sym: 'AAPL', chg: '+1.24%', up: true },
    { sym: 'MSFT', chg: '+0.62%', up: true },
    { sym: 'NVDA', chg: '+3.08%', up: true },
    { sym: 'TSLA', chg: '-2.11%', up: false },
    { sym: 'AMZN', chg: '+0.47%', up: true },
    { sym: 'META', chg: '+1.83%', up: true },
    { sym: 'GOOGL', chg: '-0.34%', up: false },
    { sym: 'JPM', chg: '+0.91%', up: true },
    { sym: 'V', chg: '+0.18%', up: true },
    { sym: 'WMT', chg: '-0.55%', up: false },
];

const EDITION_DATE = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
});

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
            {/* ===== Ticker Tape ===== */}
            <div className="ticker-mask border-b border-theme bg-theme-secondary/60 overflow-hidden">
                <div className="flex w-max animate-ticker">
                    {[...TICKER_TAPE, ...TICKER_TAPE].map((t, i) => (
                        <span
                            key={i}
                            className="flex items-center gap-2 px-5 py-2 font-mono text-xs whitespace-nowrap border-r border-theme/60"
                        >
                            <span className="font-semibold text-theme tracking-wide">{t.sym}</span>
                            <span className={t.up ? 'text-gain' : 'text-loss'}>
                                {t.up ? '▲' : '▼'} {t.chg}
                            </span>
                        </span>
                    ))}
                </div>
            </div>

            {/* ===== Masthead ===== */}
            <header className="container mx-auto px-6 pt-7">
                <div className="flex items-center justify-between text-theme-muted">
                    <span className="font-mono text-[0.65rem] uppercase tracking-[0.2em] hidden sm:block">
                        Vol. MMXXVI · No. 01
                    </span>
                    <span className="font-mono text-[0.65rem] uppercase tracking-[0.2em] hidden md:block">
                        {EDITION_DATE}
                    </span>
                    <div className="flex items-center gap-3 ml-auto md:ml-0">
                        <span className="font-mono text-[0.65rem] uppercase tracking-[0.2em] hidden lg:block">
                            Price: 1 Analysis
                        </span>
                        <DarkModeToggle />
                    </div>
                </div>

                <hr className="rule-gold mt-4" />

                <div className="text-center pt-8">
                    <p className="eyebrow mb-3 animate-fade-up">An AI Bureau of Market Intelligence</p>
                    <h1 className="font-display font-black text-theme leading-[0.86] tracking-tight animate-fade-up"
                        style={{ animationDelay: '0.05s', fontSize: 'clamp(3.25rem, 11vw, 8.5rem)' }}>
                        InvestingIQ
                    </h1>
                </div>

                <hr className="rule-gold mt-7" />
            </header>

            {/* ===== Lede + Search ===== */}
            <section className="container mx-auto px-6">
                <div className="max-w-3xl mx-auto text-center pt-10">
                    <p className="font-display italic text-theme-secondary mb-9 animate-fade-up"
                        style={{ animationDelay: '0.12s', fontSize: 'clamp(1.15rem, 2.6vw, 1.6rem)' }}>
                        &ldquo;Instant insight on any ticker — statistical forecasts, machine
                        sentiment, and an AI analyst&rsquo;s read, set in plain type.&rdquo;
                    </p>

                    <div className="animate-fade-up" style={{ animationDelay: '0.2s' }}>
                        <StockSearch onRecentSearchesChange={setRecentSearches} />
                    </div>

                    {/* Feature columns — like newspaper bylines */}
                    <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-px bg-theme border border-theme animate-fade-up"
                        style={{ animationDelay: '0.28s' }}>
                        {[
                            ['Real-time', 'Live market analysis'],
                            ['AI-Powered', 'LLM-driven insight'],
                            ['Sentiment', 'News tone scoring'],
                            ['Global', 'Any stock worldwide'],
                        ].map(([head, sub]) => (
                            <div key={head} className="bg-theme-card px-4 py-5 text-center">
                                <p className="font-display font-semibold text-theme text-base">{head}</p>
                                <p className="text-theme-muted text-xs mt-1">{sub}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ===== Recent Searches ===== */}
            {recentSearches.length > 0 && (
                <section className="container mx-auto px-6 pt-16">
                    <div className="max-w-3xl mx-auto">
                        <div className="flex items-end justify-between mb-4">
                            <h2 className="eyebrow !text-theme-secondary">From Your Desk</h2>
                            <button
                                onClick={clearRecentSearches}
                                className="font-mono text-[0.65rem] uppercase tracking-[0.18em] text-theme-muted hover:text-loss transition-colors"
                            >
                                Clear all
                            </button>
                        </div>
                        <hr className="rule-gold mb-5" />
                        <div className="flex flex-wrap gap-2.5">
                            {recentSearches.map((stock: StockSearchResult) => (
                                <button
                                    key={stock.ticker}
                                    onClick={() => handleRecentClick(stock.ticker)}
                                    className="group inline-flex items-center gap-2 px-4 py-2 bg-theme-card border border-theme hover:border-accent transition-colors"
                                >
                                    <span className="font-mono font-semibold text-theme text-sm group-hover:text-primary">
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

            {/* ===== Popular Stocks — "Most Watched" index ===== */}
            <section className="container mx-auto px-6 py-16">
                <div className="max-w-4xl mx-auto">
                    <div className="text-center mb-2">
                        <h2 className="eyebrow !text-theme-secondary">The Watchlist Index</h2>
                    </div>
                    <p className="font-display text-center text-theme-muted italic text-sm mb-6">
                        Most-followed issues, selected by the bureau
                    </p>
                    <hr className="rule-gold mb-7" />
                    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-px bg-theme border border-theme">
                        {['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JPM', 'V', 'WMT', 'JNJ', 'UNH'].map(
                            (ticker, i) => (
                                <button
                                    key={ticker}
                                    onClick={() => handleRecentClick(ticker)}
                                    className="group bg-theme-card px-3 py-5 hover:bg-primary transition-colors duration-200"
                                >
                                    <span className="block font-mono text-[0.6rem] text-theme-muted group-hover:text-white/70 mb-1">
                                        {String(i + 1).padStart(2, '0')}
                                    </span>
                                    <span className="block font-display font-bold text-theme text-lg group-hover:text-white transition-colors">
                                        {ticker}
                                    </span>
                                </button>
                            )
                        )}
                    </div>
                </div>
            </section>

            {/* ===== Colophon footer ===== */}
            <footer className="border-t border-theme">
                <div className="container mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-theme-muted">
                    <span className="font-mono text-[0.65rem] uppercase tracking-[0.18em]">
                        InvestingIQ Bureau
                    </span>
                    <span className="font-display italic text-sm">
                        Not financial advice. Read the figures, make your own call.
                    </span>
                </div>
            </footer>

            <LLMSettings />
        </main>
    );
}
