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
            <header className="border-b border-theme bg-theme-card/80 backdrop-blur-sm">
                <div className="container mx-auto px-6 py-3.5">
                    <div className="flex items-center justify-between">
                        <Link
                            href="/"
                            className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.15em] text-theme-secondary hover:text-accent transition-colors"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                            Back
                        </Link>
                        <Link href="/" className="font-display font-black text-xl text-theme tracking-tight">
                            InvestingIQ
                        </Link>
                        <div className="flex items-center gap-3">
                            <DarkModeToggle />
                            <button
                                onClick={startNewConversation}
                                className="font-mono text-[0.65rem] uppercase tracking-[0.15em] text-theme-muted hover:text-accent transition-colors"
                            >
                                New Chat
                            </button>
                        </div>
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
                        className="w-full max-w-xs px-4 py-2.5 bg-theme-card border border-theme text-theme font-mono focus:outline-none focus:border-primary"
                    />
                </div>

                {/* Messages Container */}
                <div className="flex-1 card-paper flex flex-col min-h-[500px]">
                    {/* Messages */}
                    <div className="flex-1 p-6 overflow-y-auto">
                        {messages.length === 0 ? (
                            <div className="text-center text-theme-muted mt-16">
                                <p className="eyebrow mb-4">The Correspondent</p>
                                <p className="font-display text-2xl font-semibold text-theme">AI Financial Assistant</p>
                                <p className="font-display italic text-sm mt-3 max-w-md mx-auto text-theme-secondary">
                                    Ask anything about a stock — analysis, news summaries,
                                    sentiment, and more, answered in plain type.
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
                                            className="px-3 py-1.5 text-sm bg-theme-secondary border border-theme text-theme hover:border-accent transition-colors"
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
                                            className={`max-w-[80%] px-4 py-3 ${message.role === 'user'
                                                ? 'bg-primary text-white'
                                                : 'bg-theme-secondary text-theme border-l-2 border-accent'
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
                                        <div className="bg-theme-secondary border-l-2 border-accent px-4 py-3">
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
                                className="flex-1 px-4 py-3 bg-theme-secondary border border-theme text-theme focus:outline-none focus:border-primary disabled:opacity-50"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || !ticker.trim() || isLoading}
                                className="bg-primary text-white px-6 py-3 hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
