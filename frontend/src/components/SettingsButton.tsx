'use client';

import { useState } from 'react';
import { useLLMConfig } from '@/hooks/useLLMConfig';
import AnalysisSetupModal from '@/components/AnalysisSetupModal';

/**
 * Floating bottom-right gear that lets the user view/update their API keys
 * (Alpha Vantage + LLM) anytime. Persists the keys to localStorage.
 */
export default function SettingsButton() {
    const { config, saveConfig, hasConfig } = useLLMConfig();
    const [isOpen, setIsOpen] = useState(false);

    return (
        <>
            <button
                onClick={() => setIsOpen(true)}
                title="Update API keys"
                className={`fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-105 ${hasConfig ? 'bg-green-500 hover:brightness-110' : 'bg-primary hover:brightness-110'
                    }`}
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

            {isOpen && (
                <AnalysisSetupModal
                    mode="settings"
                    initialConfig={config}
                    onStart={(stored) => {
                        saveConfig(stored);
                        setIsOpen(false);
                    }}
                    onCancel={() => setIsOpen(false)}
                />
            )}
        </>
    );
}
