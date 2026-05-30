'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { searchStocks, StockSearchResult } from '@/lib/api';

const RECENT_SEARCHES_KEY = 'investingiq_recent_searches';
const MAX_RECENT_SEARCHES = 5;

interface StockSearchProps {
    onRecentSearchesChange?: (searches: StockSearchResult[]) => void;
}

export default function StockSearch({ onRecentSearchesChange }: StockSearchProps) {
    const router = useRouter();
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState<StockSearchResult[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const inputRef = useRef<HTMLInputElement>(null);
    const suggestionsRef = useRef<HTMLDivElement>(null);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Load recent searches from localStorage
    const getRecentSearches = useCallback((): StockSearchResult[] => {
        if (typeof window === 'undefined') return [];
        try {
            const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch {
            return [];
        }
    }, []);

    // Save recent search to localStorage
    const saveRecentSearch = useCallback((stock: StockSearchResult) => {
        const recent = getRecentSearches();
        // Remove if already exists
        const filtered = recent.filter((s: StockSearchResult) => s.ticker !== stock.ticker);
        // Add to beginning
        const updated = [stock, ...filtered].slice(0, MAX_RECENT_SEARCHES);
        localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
        onRecentSearchesChange?.(updated);
    }, [getRecentSearches, onRecentSearchesChange]);

    // Debounced search
    useEffect(() => {
        if (debounceRef.current) {
            clearTimeout(debounceRef.current);
        }

        if (!query.trim()) {
            setSuggestions([]);
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        debounceRef.current = setTimeout(async () => {
            try {
                const response = await searchStocks(query, 8);
                setSuggestions(response.results);
            } catch (error) {
                console.error('Search error:', error);
                setSuggestions([]);
            } finally {
                setIsLoading(false);
            }
        }, 300);

        return () => {
            if (debounceRef.current) {
                clearTimeout(debounceRef.current);
            }
        };
    }, [query]);

    // Handle stock selection
    const handleSelect = (stock: StockSearchResult) => {
        saveRecentSearch(stock);
        setQuery('');
        setSuggestions([]);
        setShowSuggestions(false);
        router.push(`/analyze/${stock.ticker}`);
    };

    // Handle keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (!showSuggestions || suggestions.length === 0) {
            if (e.key === 'Enter' && query.trim()) {
                // Navigate directly with the query as ticker
                router.push(`/analyze/${query.trim().toUpperCase()}`);
            }
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex((prev) =>
                    prev < suggestions.length - 1 ? prev + 1 : prev
                );
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
                    handleSelect(suggestions[selectedIndex]);
                } else if (query.trim()) {
                    router.push(`/analyze/${query.trim().toUpperCase()}`);
                }
                break;
            case 'Escape':
                setShowSuggestions(false);
                setSelectedIndex(-1);
                break;
        }
    };

    // Close suggestions when clicking outside
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (
                suggestionsRef.current &&
                !suggestionsRef.current.contains(e.target as Node) &&
                inputRef.current &&
                !inputRef.current.contains(e.target as Node)
            ) {
                setShowSuggestions(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className="relative w-full max-w-xl mx-auto">
            <div className="relative flex items-center bg-theme-card border-2 border-theme focus-within:border-primary transition-colors">
                {/* Magnifier */}
                <span className="pl-4 text-theme-muted shrink-0">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M21 21l-4.35-4.35m1.35-5.4a6.75 6.75 0 11-13.5 0 6.75 6.75 0 0113.5 0z" />
                    </svg>
                </span>
                <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => {
                        setQuery(e.target.value);
                        setShowSuggestions(true);
                        setSelectedIndex(-1);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    onKeyDown={handleKeyDown}
                    placeholder="Search for any stock (e.g., AAPL, TSLA, NVDA)..."
                    className="flex-1 min-w-0 px-3 py-4 text-base md:text-lg bg-transparent text-theme placeholder:text-theme-muted focus:outline-none font-mono"
                    autoComplete="off"
                />
                <div className="flex items-center gap-2 pr-2 shrink-0">
                    {isLoading && (
                        <div className="w-5 h-5 border-2 border-theme border-t-primary rounded-full animate-spin" />
                    )}
                    <button
                        onClick={() => {
                            if (query.trim()) {
                                router.push(`/analyze/${query.trim().toUpperCase()}`);
                            }
                        }}
                        className="bg-primary text-white px-5 md:px-7 py-2.5 font-mono text-sm uppercase tracking-[0.15em] hover:bg-accent transition-colors"
                    >
                        Analyze
                    </button>
                </div>
            </div>

            {/* Suggestions dropdown */}
            {showSuggestions && suggestions.length > 0 && (
                <div
                    ref={suggestionsRef}
                    className="absolute z-50 w-full mt-1.5 bg-theme-card border border-theme shadow-2xl overflow-hidden text-left"
                >
                    <div className="px-4 py-2 border-b border-theme bg-theme-secondary/60">
                        <span className="eyebrow !text-theme-muted">Matching Issues</span>
                    </div>
                    {suggestions.map((stock: StockSearchResult, index: number) => (
                        <button
                            key={stock.ticker}
                            onClick={() => handleSelect(stock)}
                            onMouseEnter={() => setSelectedIndex(index)}
                            className={`w-full px-4 py-3 text-left flex items-center justify-between border-b border-theme/50 last:border-0 transition-colors ${index === selectedIndex ? 'bg-primary/10' : 'hover:bg-theme-secondary'
                                }`}
                        >
                            <div className="flex items-baseline gap-3 min-w-0">
                                <span className="font-mono font-semibold text-primary shrink-0">
                                    {stock.ticker}
                                </span>
                                <span className="text-theme-secondary truncate">
                                    {stock.name}
                                </span>
                            </div>
                            <span className="font-mono text-xs text-theme-muted uppercase tracking-wider shrink-0 ml-3">
                                {stock.exchange}
                            </span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
