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
            <header className="bg-theme-card shadow-sm">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <Link
                            href="/"
                            className="flex items-center gap-2 text-theme-secondary hover:text-theme transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                            Back to Search
                        </Link>
                        <Link href="/" className="text-xl font-bold text-primary">
                            InvestingIQ
                        </Link>
                        <div className="flex items-center gap-2">
                            <DarkModeToggle />
                            <button
                                onClick={startNewConversation}
                                className="text-sm text-theme-muted hover:text-theme"
                            >
                                New Chat
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Chat Area */}
            <div className="flex-1 container mx-auto px-4 py-6 flex flex-col max-w-3xl">
                {/* Ticker Input */}
                <div className="mb-4">
                    <label className="block text-sm font-medium text-theme-secondary mb-1">
                        Stock Ticker
                    </label>
                    <input
                        type="text"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        placeholder="Enter ticker (e.g., AAPL)"
                        className="w-full max-w-xs px-4 py-2 bg-theme-secondary text-theme rounded-lg focus:ring-2 focus:ring-primary focus:outline-none"
                    />
                </div>

                {/* Messages Container */}
                <div className="flex-1 bg-theme-card rounded-xl shadow-md flex flex-col min-h-[500px]">
                    {/* Messages */}
                    <div className="flex-1 p-6 overflow-y-auto">
                        {messages.length === 0 ? (
                            <div className="text-center text-theme-muted mt-20">
                                <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                    </svg>
                                </div>
                                <p className="text-lg font-medium text-theme">AI Financial Assistant</p>
                                <p className="text-sm mt-2 max-w-md mx-auto">
                                    Ask me anything about stocks! I can help with analysis, news summaries,
                                    sentiment insights, and more.
                                </p>
                                <div className="mt-6 flex flex-wrap justify-center gap-2">
                                    {[
                                        `What's the outlook for ${ticker || 'AAPL'}?`,
                                        `Why did ${ticker || 'TSLA'} move today?`,
                                        `Summarize recent news for ${ticker || 'NVDA'}`,
                                    ].map((suggestion, i) => (
                                        <button
                                            key={i}
                                            onClick={() => setInput(suggestion)}
                                            className="px-3 py-1.5 text-sm bg-theme-secondary text-theme rounded-full hover:opacity-80 transition-opacity"
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
                                            className={`max-w-[80%] rounded-2xl px-4 py-3 ${message.role === 'user'
                                                    ? 'bg-primary text-white'
                                                    : 'bg-theme-secondary text-theme'
                                                }`}
                                        >
                                            <p className="whitespace-pre-wrap">{message.content}</p>
                                            {message.sources && message.sources.length > 0 && (
                                                <div className="mt-3 pt-3 border-t border-white/20">
                                                    <p className="text-xs text-theme-muted mb-1">Sources:</p>
                                                    <div className="flex flex-wrap gap-1">
                                                        {message.sources.map((source, i) => (
                                                            <span
                                                                key={i}
                                                                className="text-xs bg-theme text-theme-secondary px-2 py-0.5 rounded"
                                                            >
                                                                {source}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                                {isLoading && (
                                    <div className="flex justify-start">
                                        <div className="bg-theme-secondary rounded-2xl px-4 py-3">
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
                    <div className="border-t border-theme/30 p-4">
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder={ticker ? `Ask about ${ticker}...` : 'Enter a ticker first...'}
                                disabled={!ticker.trim() || isLoading}
                                className="flex-1 px-4 py-3 bg-theme-secondary rounded-xl text-theme focus:ring-2 focus:ring-primary focus:outline-none disabled:opacity-50"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || !ticker.trim() || isLoading}
                                className="bg-primary text-white px-6 py-3 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
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
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </main>
        }>
            <ChatContent />
        </Suspense>
    );
}
