'use client';

import { useState, useEffect } from 'react';
import {
    LLMConfig,
    LLMProvider,
    PROVIDER_MODELS,
    PROVIDER_NAMES,
    useLLMConfig,
} from '@/hooks/useLLMConfig';

interface LLMSettingsProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function LLMSettings({ isOpen, onClose }: LLMSettingsProps) {
    const { config, saveConfig, clearConfig } = useLLMConfig();
    
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
        onClose();
    };

    const handleClear = () => {
        clearConfig();
        setApiKey('');
        setModel(PROVIDER_MODELS[provider].default);
        setIsVerified(false);
        setVerifyError(null);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-theme-card rounded-xl shadow-2xl w-full max-w-md mx-4">
                <div className="flex items-center justify-between p-4 border-b border-theme">
                    <h2 className="text-lg font-semibold text-theme">
                        Configure LLM Provider
                    </h2>
                    <button
                        onClick={onClose}
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
                            className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme focus:ring-2 focus:ring-primary focus:border-primary"
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
                            className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme focus:ring-2 focus:ring-primary focus:border-primary"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-theme-secondary mb-1">
                            Model <span className="text-theme-muted">(optional)</span>
                        </label>
                        <select
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                            className="w-full px-3 py-2 border border-theme bg-theme rounded-lg text-theme focus:ring-2 focus:ring-primary focus:border-primary"
                        >
                            {PROVIDER_MODELS[provider].options.map((m) => (
                                <option key={m} value={m}>{m}</option>
                            ))}
                        </select>
                        <p className="mt-1 text-xs text-theme-muted">
                            Default: {PROVIDER_MODELS[provider].default} (cheapest)
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={handleVerify}
                            disabled={isVerifying || !apiKey.trim()}
                            className="px-4 py-2 bg-theme-secondary text-theme rounded-lg hover:opacity-80 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
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
                            <span className="text-green-500 flex items-center gap-1">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Key verified
                            </span>
                        )}
                    </div>

                    {verifyError && (
                        <p className="text-sm text-red-500">{verifyError}</p>
                    )}
                </div>

                <div className="flex items-center justify-between p-4 border-t border-theme bg-theme-secondary rounded-b-xl">
                    {config && (
                        <button
                            onClick={handleClear}
                            className="px-4 py-2 text-red-500 hover:bg-red-500/10 rounded-lg"
                        >
                            Clear Config
                        </button>
                    )}
                    <div className="flex gap-2 ml-auto">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-theme-secondary hover:bg-theme rounded-lg"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={!isVerified}
                            className="px-4 py-2 bg-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Save Configuration
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
