import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import * as fc from 'fast-check'
import { useLLMConfig, LLMConfig, LLMProvider } from '@/hooks/useLLMConfig'

const STORAGE_KEY = 'investingiq_llm_config'

describe('useLLMConfig', () => {
    let mockStorage: Record<string, string> = {}

    beforeEach(() => {
        mockStorage = {}
        vi.spyOn(window.localStorage, 'getItem').mockImplementation((key) => mockStorage[key] || null)
        vi.spyOn(window.localStorage, 'setItem').mockImplementation((key, value) => {
            mockStorage[key] = value
        })
        vi.spyOn(window.localStorage, 'removeItem').mockImplementation((key) => {
            delete mockStorage[key]
        })
    })

    it('returns null config initially when localStorage is empty', () => {
        const { result } = renderHook(() => useLLMConfig())
        expect(result.current.config).toBeNull()
    })

    it('sets isLoaded to true after mount', async () => {
        const { result } = renderHook(() => useLLMConfig())
        // Wait for useEffect to run
        await vi.waitFor(() => {
            expect(result.current.isLoaded).toBe(true)
        })
    })

    it('loads config from localStorage on mount', async () => {
        const storedConfig: LLMConfig = {
            provider: 'openai',
            apiKey: 'sk-test-key',
            model: 'gpt-4o-mini',
        }
        mockStorage[STORAGE_KEY] = JSON.stringify(storedConfig)

        const { result } = renderHook(() => useLLMConfig())

        await vi.waitFor(() => {
            expect(result.current.config).toEqual(storedConfig)
        })
    })

    it('saveConfig persists to localStorage', async () => {
        const { result } = renderHook(() => useLLMConfig())

        const newConfig: LLMConfig = {
            provider: 'anthropic',
            apiKey: 'sk-ant-test',
            model: 'claude-3-5-sonnet-20241022',
        }

        act(() => {
            result.current.saveConfig(newConfig)
        })

        expect(mockStorage[STORAGE_KEY]).toBe(JSON.stringify(newConfig))
        expect(result.current.config).toEqual(newConfig)
    })

    it('clearConfig removes from localStorage', async () => {
        const storedConfig: LLMConfig = {
            provider: 'openai',
            apiKey: 'sk-test-key',
        }
        mockStorage[STORAGE_KEY] = JSON.stringify(storedConfig)

        const { result } = renderHook(() => useLLMConfig())

        await vi.waitFor(() => {
            expect(result.current.config).toEqual(storedConfig)
        })

        act(() => {
            result.current.clearConfig()
        })

        expect(mockStorage[STORAGE_KEY]).toBeUndefined()
        expect(result.current.config).toBeNull()
    })

    it('hasConfig returns true when config exists with apiKey', async () => {
        const storedConfig: LLMConfig = {
            provider: 'openai',
            apiKey: 'sk-test-key',
        }
        mockStorage[STORAGE_KEY] = JSON.stringify(storedConfig)

        const { result } = renderHook(() => useLLMConfig())

        await vi.waitFor(() => {
            expect(result.current.hasConfig).toBe(true)
        })
    })

    it('hasConfig returns false when config is null', () => {
        const { result } = renderHook(() => useLLMConfig())
        expect(result.current.hasConfig).toBe(false)
    })

    // Property 2: LLM Config Persistence Round Trip
    // **Validates: Requirements 5.1**
    it('Property 2: LLM Config Persistence Round Trip', async () => {
        const providers: LLMProvider[] = ['openai', 'anthropic', 'google', 'ohmygpt', 'openrouter']

        await fc.assert(
            fc.asyncProperty(
                fc.record({
                    provider: fc.constantFrom(...providers),
                    apiKey: fc.string({ minLength: 1, maxLength: 100 }),
                    model: fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
                }),
                async (config) => {
                    mockStorage = {}

                    const { result, rerender } = renderHook(() => useLLMConfig())

                    act(() => {
                        result.current.saveConfig(config as LLMConfig)
                    })

                    // Simulate remount by creating new hook instance
                    const { result: result2 } = renderHook(() => useLLMConfig())

                    await vi.waitFor(() => {
                        expect(result2.current.isLoaded).toBe(true)
                    })

                    expect(result2.current.config).toEqual(config)
                }
            ),
            { numRuns: 100 }
        )
    })
})
