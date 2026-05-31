'use client';

import { useState } from 'react';
import {
    LLMConfig,
    LLMProvider,
    PROVIDER_MODELS,
    PROVIDER_NAMES,
} from '@/hooks/useLLMConfig';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AnalysisSetupModalProps {
    ticker?: string;
    initialConfig: LLMConfig | null;
    onStart: (config: LLMConfig) => void;
    onCancel: () => void;
    mode?: 'analyze' | 'settings';
}

export default function AnalysisSetupModal({
    ticker,
    initialConfig,
    onStart,
    onCancel,
    mode = 'analyze',
}: AnalysisSetupModalProps) {
    const [alphaVantageKey, setAlphaVantageKey] = useState(initialConfig?.alphaVantageKey || '');
    const [provider, setProvider] = useState<LLMProvider>(initialConfig?.provider || 'openai');
    const [apiKey, setApiKey] = useState(initialConfig?.apiKey || '');
    const [model, setModel] = useState(
        initialConfig?.model || PROVIDER_MODELS[initialConfig?.provider || 'openai'].default
    );
    const [isVerifying, setIsVerifying] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const isSettings = mode === 'settings';

    const handleProviderChange = (next: LLMProvider) => {
        setProvider(next);
        setModel(PROVIDER_MODELS[next].default);
        setError(null);
    };

    const handleStart = async () => {
        if (!alphaVantageKey.trim()) {
            setError('Alpha Vantage API key is required');
            return;
        }
        if (!apiKey.trim()) {
            setError('LLM API key is required');
            return;
        }

        setIsVerifying(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}/api/v1/llm/verify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, api_key: apiKey, model: model || null }),
            });
            const data = await response.json();

            if (!data.valid) {
                setError(data.error || 'LLM key verification failed');
                return;
            }

            onStart({
                provider,
                apiKey,
                model,
                alphaVantageKey: alphaVantageKey.trim(),
            });
        } catch {
            setError('Failed to verify the LLM key. Check your connection.');
        } finally {
            setIsVerifying(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onCancel}
            />

            {/* Modal */}
            <div className="relative w-full max-w-md animate-fade-up">
                <div className="card-paper shadow-2xl overflow-hidden">
                    <div className="flex items-center justify-between p-4 border-b border-theme bg-theme-secondary/50">
                        <div>
                            <span className="eyebrow">{isSettings ? 'API Keys' : 'Analysis Setup'}</span>
                            <h2 className="font-display text-lg font-bold text-theme mt-1">
                                {isSettings ? (
                                    'Update API Keys'
                                ) : (
                                    <>Analyze <span className="font-mono text-primary">{ticker}</span></>
                                )}
                            </h2>
                        </div>
                        <button
                            onClick={onCancel}
                            className="p-1 hover:text-loss rounded text-theme-secondary transition-colors"
                            aria-label="Close"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    <div className="p-4 space-y-4">
                        <p className="text-xs text-theme-secondary leading-relaxed">
                            {isSettings
                                ? 'Update the API keys used for analysis. Keys are stored only in your browser.'
                                : 'Provide your own API keys to run the analysis. Keys are stored only in your browser and sent directly with this request.'}
                        </p>

                        {/* Alpha Vantage Key */}
                        <div>
                            <label className="block text-xs font-medium text-theme-secondary mb-1.5">
                                Alpha Vantage API Key
                            </label>
                            <input
                                type="password"
                                value={alphaVantageKey}
                                onChange={(e) => {
                                    setAlphaVantageKey(e.target.value);
                                    setError(null);
                                }}
                                placeholder="Enter your Alpha Vantage key"
                                className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme text-sm font-mono focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all"
                            />
                            <a
                                href="https://www.alphavantage.co/support/#api-key"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="mt-1 inline-block text-xs text-primary hover:underline"
                            >
                                Get a free key →
                            </a>
                        </div>

                        {/* Provider */}
                        <div>
                            <label className="block text-xs font-medium text-theme-secondary mb-1.5">
                                LLM Provider
                            </label>
                            <select
                                value={provider}
                                onChange={(e) => handleProviderChange(e.target.value as LLMProvider)}
                                className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme text-sm focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all"
                            >
                                {Object.entries(PROVIDER_NAMES).map(([key, name]) => (
                                    <option key={key} value={key}>{name}</option>
                                ))}
                            </select>
                        </div>

                        {/* LLM Key */}
                        <div>
                            <label className="block text-xs font-medium text-theme-secondary mb-1.5">
                                LLM API Key
                            </label>
                            <input
                                type="password"
                                value={apiKey}
                                onChange={(e) => {
                                    setApiKey(e.target.value);
                                    setError(null);
                                }}
                                placeholder="Enter your LLM API key"
                                className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme text-sm font-mono focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all"
                            />
                        </div>

                        {/* Model */}
                        <div>
                            <label className="block text-xs font-medium text-theme-secondary mb-1.5">
                                Model
                            </label>
                            <select
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                                className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme text-sm focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all"
                            >
                                {PROVIDER_MODELS[provider].options.map((m) => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                        </div>

                        {error && <p className="text-sm text-loss">{error}</p>}
                    </div>

                    <div className="flex items-center justify-end gap-2 p-3 border-t border-theme bg-theme-secondary">
                        <button
                            onClick={onCancel}
                            className="px-3 py-1.5 rounded-lg text-sm font-medium text-theme-secondary hover:text-theme transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleStart}
                            disabled={isVerifying || !alphaVantageKey.trim() || !apiKey.trim()}
                            className="px-4 py-1.5 rounded-lg text-sm font-medium bg-primary text-white hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
                        >
                            {isVerifying ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/60 border-t-transparent rounded-full animate-spin" />
                                    Verifying...
                                </>
                            ) : (
                                isSettings ? 'Save Keys' : 'Start Analysis'
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
