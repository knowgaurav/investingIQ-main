'use client';

import { useState, useEffect } from 'react';
import {
    LLMConfig,
    LLMProvider,
    PROVIDER_MODELS,
    PROVIDER_NAMES,
    useLLMConfig,
} from '@/hooks/useLLMConfig';

export default function LLMSettings() {
    const { config, saveConfig, clearConfig, hasConfig } = useLLMConfig();
    const [isOpen, setIsOpen] = useState(false);
    
    const [provider, setProvider] = useState<LLMProvider>('openai');
    const [apiKey, setApiKey] = useState('');
    const [model, setModel] = useState('');
    const [isVerifying, setIsVerifying] = useState(false);
    const [isVerified, setIsVerified] = useState(false);
    const [verifyError, setVerifyError] = useState<string | null>(null);

    useEffect(() => {
        if (config) {
            setProvider(config.provider);
            setApiKey(config.apiKey);
            setModel(config.model || PROVIDER_MODELS[config.provider].default);
            setIsVerified(true);
        }
    }, [config]);

    useEffect(() => {
        setModel(PROVIDER_MODELS[provider].default);
        setIsVerified(false);
        setVerifyError(null);
    }, [provider]);

    const handleVerify = async () => {
        if (!apiKey.trim()) {
            setVerifyError('API key is required');
            return;
        }

        setIsVerifying(true);
        setVerifyError(null);

        try {
            const response = await fetch('http://localhost:8000/api/v1/llm/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider,
                    api_key: apiKey,
                    model: model || null,
                }),
            });

            const data = await response.json();

            if (data.valid) {
                setIsVerified(true);
                setVerifyError(null);
            } else {
                setIsVerified(false);
                setVerifyError(data.error || 'Verification failed');
            }
        } catch (err) {
            setIsVerified(false);
            setVerifyError('Failed to verify. Check your connection.');
        } finally {
            setIsVerifying(false);
        }
    };

    const handleSave = () => {
        if (!isVerified) return;
        
        saveConfig({
            provider,
            apiKey,
            model: model || undefined,
        });
        setIsOpen(false);
    };

    const handleClear = () => {
        clearConfig();
        setApiKey('');
        setModel(PROVIDER_MODELS[provider].default);
        setIsVerified(false);
        setVerifyError(null);
    };

    return (
        <>
            {/* Floating Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-105 ${
                    hasConfig
                        ? 'bg-green-500 hover:bg-green-600'
                        : 'bg-primary hover:bg-primary/90'
                }`}
                title={hasConfig ? `LLM: ${PROVIDER_NAMES[config!.provider]}` : 'Configure LLM'}
            >
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {hasConfig && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center">
                        <svg className="w-3 h-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                    </span>
                )}
            </button>

            {/* Modal Panel - Bottom Right */}
            {isOpen && (
                <div className="fixed bottom-24 right-6 z-50 w-full max-w-sm">
                    <div className="bg-theme-card rounded-xl shadow-2xl border border-theme overflow-hidden">
                        <div className="flex items-center justify-between p-3 border-b border-theme">
                            <h2 className="text-base font-semibold text-theme">
                                Configure LLM
                            </h2>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-1 hover:bg-theme-secondary rounded text-theme-secondary"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="p-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-theme-secondary mb-1">
                                    Provider
                                </label>
                                <select
                                    value={provider}
                                    onChange={(e) => setProvider(e.target.value as LLMProvider)}
                                    className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme text-sm focus:ring-2 focus:ring-primary focus:border-primary"
                                >
                                    {Object.entries(PROVIDER_NAMES).map(([key, name]) => (
                                        <option key={key} value={key}>{name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-theme-secondary mb-1">
                                    API Key
                                </label>
                                <input
                                    type="password"
                                    value={apiKey}
                                    onChange={(e) => {
                                        setApiKey(e.target.value);
                                        setIsVerified(false);
                                    }}
                                    placeholder="Enter your API key"
                                    className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme text-sm focus:ring-2 focus:ring-primary focus:border-primary"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-theme-secondary mb-1">
                                    Model <span className="text-theme-muted">(optional)</span>
                                </label>
                                <select
                                    value={model}
                                    onChange={(e) => setModel(e.target.value)}
                                    className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme text-sm focus:ring-2 focus:ring-primary focus:border-primary"
                                >
                                    {PROVIDER_MODELS[provider].options.map((m) => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                </select>
                                <p className="mt-1 text-xs text-theme-muted">
                                    Default: {PROVIDER_MODELS[provider].default}
                                </p>
                            </div>

                            <div className="flex items-center gap-3">
                                <button
                                    onClick={handleVerify}
                                    disabled={isVerifying || !apiKey.trim()}
                                    className="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                >
                                    {isVerifying ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-theme-muted border-t-transparent rounded-full animate-spin" />
                                            Verifying...
                                        </>
                                    ) : (
                                        'Verify Key'
                                    )}
                                </button>
                                
                                {isVerified && (
                                    <span className="text-green-500 text-sm flex items-center gap-1">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        Verified
                                    </span>
                                )}
                            </div>

                            {verifyError && (
                                <p className="text-sm text-red-500">{verifyError}</p>
                            )}
                        </div>

                        <div className="flex items-center justify-between p-3 border-t border-theme bg-theme-secondary">
                            {config && (
                                <button
                                    onClick={handleClear}
                                    className="px-3 py-1.5 text-sm text-red-500 hover:bg-red-500/10 rounded-lg"
                                >
                                    Clear
                                </button>
                            )}
                            <div className="flex gap-2 ml-auto">
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="px-3 py-1.5 text-sm text-theme-secondary hover:bg-theme rounded-lg"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={!isVerified}
                                    className="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Save
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
