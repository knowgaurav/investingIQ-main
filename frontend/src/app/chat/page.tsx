'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { sendChatMessage, ChatResponse } from '@/lib/api';
import DarkModeToggle from '@/components/DarkModeToggle';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: string[] | null;
    timestamp: Date;
}

function ChatContent() {
    const searchParams = useSearchParams();
    const initialTicker = searchParams.get('ticker') || '';

    const [ticker, setTicker] = useState(initialTicker);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || !ticker.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response: ChatResponse = await sendChatMessage({
                message: input,
                ticker: ticker.toUpperCase(),
                conversation_id: conversationId || undefined,
            });

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.response,
                sources: response.sources,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
            setConversationId(response.conversation_id);
        } catch (error: any) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: `Sorry, I encountered an error: ${error.message || 'Unknown error'}. Please try again.`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const startNewConversation = () => {
        setMessages([]);
        setConversationId(null);
    };

    return (
        <main className="min-h-screen bg-theme flex flex-col">
            {/* Header */}
            <header className="border-b border-theme bg-theme-card/80 backdrop-blur-md">
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
                    <Link href="/" className="flex items-center gap-2">
                        <span className="inline-flex items-center justify-center w-7 h-7 rounded-md bg-primary text-white">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M4 18L9 11l4 4 7-9" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M16 6h4v4" />
                            </svg>
                        </span>
                        <span className="font-display font-extrabold text-lg tracking-tight text-theme">InvestingIQ</span>
                    </Link>
                    <div className="flex items-center gap-3">
                        <DarkModeToggle />
                        <button
                            onClick={startNewConversation}
                            className="text-sm font-medium text-theme-muted hover:text-theme transition-colors"
                        >
                            New Chat
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Chat Area */}
            <div className="flex-1 container mx-auto px-6 py-8 flex flex-col max-w-3xl">
                {/* Ticker Input */}
                <div className="mb-5">
                    <label className="block font-mono text-[0.65rem] uppercase tracking-[0.18em] text-theme-muted mb-1.5">
                        Stock Ticker
                    </label>
                    <input
                        type="text"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        placeholder="Enter ticker (e.g., AAPL)"
                        className="w-full max-w-xs px-4 py-2.5 bg-theme-card border border-theme rounded-lg text-theme font-mono focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all"
                    />
                </div>

                {/* Messages Container */}
                <div className="flex-1 card-paper flex flex-col min-h-[500px]">
                    {/* Messages */}
                    <div className="flex-1 p-6 overflow-y-auto">
                        {messages.length === 0 ? (
                            <div className="text-center text-theme-muted mt-16">
                                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                    </svg>
                                </div>
                                <p className="font-display text-xl font-bold text-theme">AI Financial Assistant</p>
                                <p className="text-sm mt-2 max-w-md mx-auto text-theme-secondary leading-relaxed">
                                    Ask anything about a stock — analysis, news summaries,
                                    sentiment, and more.
                                </p>
                                <div className="mt-7 flex flex-wrap justify-center gap-2">
                                    {[
                                        `What's the outlook for ${ticker || 'AAPL'}?`,
                                        `Why did ${ticker || 'TSLA'} move today?`,
                                        `Summarize recent news for ${ticker || 'NVDA'}`,
                                    ].map((suggestion, i) => (
                                        <button
                                            key={i}
                                            onClick={() => setInput(suggestion)}
                                            className="px-3 py-1.5 text-sm bg-theme-secondary border border-theme rounded-lg text-theme hover:border-primary/50 transition-colors"
                                        >
                                            {suggestion}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {messages.map((message) => (
                                    <div
                                        key={message.id}
                                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div
                                            className={`max-w-[80%] px-4 py-3 rounded-2xl ${message.role === 'user'
                                                ? 'bg-primary text-white rounded-br-md'
                                                : 'bg-theme-secondary text-theme rounded-bl-md'
                                                }`}
                                        >
                                            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                                            {message.sources && message.sources.length > 0 && (
                                                <div className="mt-3 pt-3 border-t border-theme/40">
                                                    <p className="font-mono text-[0.6rem] uppercase tracking-[0.15em] text-theme-muted mb-1.5">Sources</p>
                                                    <div className="flex flex-wrap gap-1">
                                                        {message.sources.map((source, i) => {
                                                            const isFinancials = source.includes('·');
                                                            return (
                                                                <span
                                                                    key={i}
                                                                    className={`font-mono text-xs px-2 py-0.5 ${isFinancials
                                                                        ? 'bg-primary/15 text-primary font-medium'
                                                                        : 'bg-theme text-theme-secondary'
                                                                        }`}
                                                                >
                                                                    {isFinancials ? `📑 ${source}` : source}
                                                                </span>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                                {isLoading && (
                                    <div className="flex justify-start">
                                        <div className="bg-theme-secondary rounded-2xl rounded-bl-md px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 bg-theme-muted rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                                <div className="w-2 h-2 bg-theme-muted rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                                <div className="w-2 h-2 bg-theme-muted rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </div>

                    {/* Input */}
                    <div className="border-t border-theme p-4">
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder={ticker ? `Ask about ${ticker}...` : 'Enter a ticker first...'}
                                disabled={!ticker.trim() || isLoading}
                                className="flex-1 px-4 py-3 bg-theme-secondary border border-theme rounded-lg text-theme focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all disabled:opacity-50"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || !ticker.trim() || isLoading}
                                className="bg-primary text-white px-6 py-3 rounded-lg hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? (
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                ) : (
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                    </svg>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}


export default function ChatPage() {
    return (
        <Suspense fallback={
            <main className="min-h-screen bg-theme flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
            </main>
        }>
            <ChatContent />
        </Suspense>
    );
}
