'use client';

import { useState, useEffect, useCallback } from 'react';

export type LLMProvider = 'openai' | 'anthropic' | 'google' | 'ohmygpt' | 'openrouter';

export interface LLMConfig {
    provider: LLMProvider;
    apiKey: string;
    model?: string;
    alphaVantageKey?: string;
}

const STORAGE_KEY = 'investingiq_llm_config';

export const PROVIDER_MODELS: Record<LLMProvider, { default: string; options: string[] }> = {
    openai: {
        default: 'gpt-5.4-mini',
        options: ['gpt-5.4-mini', 'gpt-5.4-nano', 'gpt-5.4', 'gpt-5.5', 'gpt-5.5-pro'],
    },
    anthropic: {
        default: 'claude-haiku-4-5',
        options: ['claude-haiku-4-5', 'claude-sonnet-4-5', 'claude-sonnet-4-6', 'claude-opus-4-7', 'claude-opus-4-8'],
    },
    google: {
        default: 'gemini-3.1-flash-lite',
        options: ['gemini-3.1-flash-lite', 'gemini-2.5-pro', 'gemini-3-flash-preview', 'gemini-3.5-flash', 'gemini-3.1-pro-preview'],
    },
    ohmygpt: {
        default: 'gpt-5.4-mini',
        options: ['gpt-5.4-mini', 'gpt-5.5', 'claude-haiku-4-5', 'claude-sonnet-4-6', 'gemini-3.5-flash'],
    },
    openrouter: {
        default: 'moonshotai/kimi-k2.6:free',
        options: [
            'moonshotai/kimi-k2.6:free',
            'deepseek/deepseek-v4-flash:free',
            'qwen/qwen3-coder:free',
            'qwen/qwen3-next-80b-a3b-instruct:free',
            'minimax/minimax-m2.5:free',
            'z-ai/glm-4.5-air:free',
            'nvidia/nemotron-3-super-120b-a12b:free',
            'openai/gpt-oss-120b:free',
            'meta-llama/llama-3.3-70b-instruct:free',
            'google/gemma-4-31b-it:free',
        ],
    },
};

export const PROVIDER_NAMES: Record<LLMProvider, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    google: 'Google',
    ohmygpt: 'OHMYGPT',
    openrouter: 'OpenRouter',
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
