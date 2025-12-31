'use client';

import { useState, useEffect, useCallback } from 'react';

export type LLMProvider = 'openai' | 'anthropic' | 'google' | 'openrouter' | 'megallm' | 'agentrouter';

export interface LLMConfig {
    provider: LLMProvider;
    apiKey: string;
    model?: string;
}

const STORAGE_KEY = 'investingiq_llm_config';

export const PROVIDER_MODELS: Record<LLMProvider, { default: string; options: string[] }> = {
    openai: {
        default: 'gpt-4o-mini',
        options: ['gpt-4o-mini', 'gpt-4.1-mini', 'gpt-4.1-nano', 'gpt-5-mini', 'gpt-5-nano'],
    },
    anthropic: {
        default: 'claude-haiku-4-5-latest',
        options: ['claude-haiku-4-5-latest', 'claude-sonnet-4-5-latest', 'claude-3-5-haiku-latest'],
    },
    google: {
        default: 'gemini-2.5-flash',
        options: ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-3-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite'],
    },
    openrouter: {
        default: 'openai/gpt-4o-mini',
        options: ['openai/gpt-4o-mini', 'anthropic/claude-3.5-haiku', 'google/gemini-2.0-flash-exp'],
    },
    megallm: {
        default: 'gpt-4o-mini',
        options: ['gpt-4o-mini', 'claude-haiku', 'gemini-flash'],
    },
    agentrouter: {
        default: 'gpt-4o-mini',
        options: ['gpt-4o-mini', 'claude-haiku', 'gemini-flash'],
    },
};

export const PROVIDER_NAMES: Record<LLMProvider, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    google: 'Google',
    openrouter: 'OpenRouter',
    megallm: 'MegaLLM',
    agentrouter: 'AgentRouter',
};

export function useLLMConfig() {
    const [config, setConfig] = useState<LLMConfig | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                setConfig(JSON.parse(stored));
            } catch {
                localStorage.removeItem(STORAGE_KEY);
            }
        }
        setIsLoaded(true);
    }, []);

    const saveConfig = useCallback((newConfig: LLMConfig) => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newConfig));
        setConfig(newConfig);
    }, []);

    const clearConfig = useCallback(() => {
        localStorage.removeItem(STORAGE_KEY);
        setConfig(null);
    }, []);

    const hasConfig = config !== null && config.apiKey.length > 0;

    return {
        config,
        isLoaded,
        hasConfig,
        saveConfig,
        clearConfig,
    };
}
