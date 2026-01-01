'use client';

import { useState, useEffect, useCallback } from 'react';

export type LLMProvider = 'openai' | 'anthropic' | 'google' | 'ohmygpt' | 'openrouter';

export interface LLMConfig {
    provider: LLMProvider;
    apiKey: string;
    model?: string;
}

const STORAGE_KEY = 'investingiq_llm_config';

export const PROVIDER_MODELS: Record<LLMProvider, { default: string; options: string[] }> = {
    openai: {
        default: 'gpt-4o-mini',
        options: ['gpt-4o-mini', 'gpt-5-nano', 'gpt-5-mini', 'gpt-5', 'gpt-5.1', 'gpt-5.2', 'gpt-4.1-nano', 'gpt-4.1-mini', 'gpt-4.1', 'gpt-4o'],
    },
    anthropic: {
        default: 'claude-haiku-4-5-latest',
        options: ['claude-haiku-4-5-latest', 'claude-sonnet-4-5-latest', 'claude-3-5-haiku-20241022', 'claude-3-5-sonnet-20241022'],
    },
    google: {
        default: 'gemini-2.5-flash',
        options: ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash'],
    },
    ohmygpt: {
        default: 'gpt-4o-mini',
        options: ['gpt-4o-mini', 'gpt-4o', 'claude-3-5-sonnet-20241022'],
    },
    openrouter: {
        default: 'xiaomi/mimo-v2-flash:free',
        options: [
            'xiaomi/mimo-v2-flash:free',
            'mistralai/devstral-2512:free',
            'kwaipilot/kat-coder-pro:free',
            'deepseek/deepseek-r1-0528:free',
            'qwen/qwen3-coder:free',
            'meta-llama/llama-3.3-70b-instruct:free',
            'google/gemma-3-27b-it:free',
            'openai/gpt-oss-120b:free',
            'moonshotai/kimi-k2:free',
            'google/gemini-2.0-flash-exp:free',
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
