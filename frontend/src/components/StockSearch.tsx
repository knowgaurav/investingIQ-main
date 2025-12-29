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
            <div className="relative">
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
                    className="w-full px-6 py-4 text-lg border-2 border-gray-200 rounded-full focus:border-blue-500 focus:outline-none transition-colors"
                    autoComplete="off"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    {isLoading && (
                        <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
                    )}
                    <button
                        onClick={() => {
                            if (query.trim()) {
                                router.push(`/analyze/${query.trim().toUpperCase()}`);
                            }
                        }}
                        className="bg-blue-500 text-white px-6 py-2 rounded-full hover:bg-blue-600 transition-colors font-medium"
                    >
                        Analyze
                    </button>
                </div>
            </div>

            {/* Suggestions dropdown */}
            {showSuggestions && suggestions.length > 0 && (
                <div
                    ref={suggestionsRef}
                    className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden"
                >
                    {suggestions.map((stock: StockSearchResult, index: number) => (
                        <button
                            key={stock.ticker}
                            onClick={() => handleSelect(stock)}
                            onMouseEnter={() => setSelectedIndex(index)}
                            className={`w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-50 transition-colors ${index === selectedIndex ? 'bg-blue-50' : ''
                                }`}
                        >
                            <div>
                                <span className="font-semibold text-gray-900">
                                    {stock.ticker}
                                </span>
                                <span className="ml-2 text-gray-600">
                                    {stock.name}
                                </span>
                            </div>
                            <span className="text-sm text-gray-400">
                                {stock.exchange}
                            </span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
