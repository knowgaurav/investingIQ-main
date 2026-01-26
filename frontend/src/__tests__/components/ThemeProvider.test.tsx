import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import * as fc from 'fast-check'
import { ThemeProvider, useTheme } from '@/components/ThemeProvider'

describe('ThemeProvider', () => {
    let mockStorage: Record<string, string> = {}

    beforeEach(() => {
        mockStorage = {}
        vi.spyOn(window.localStorage, 'getItem').mockImplementation((key) => mockStorage[key] || null)
        vi.spyOn(window.localStorage, 'setItem').mockImplementation((key, value) => {
            mockStorage[key] = value
        })
        // Reset document class
        document.documentElement.classList.remove('dark')
    })

    it('provides default light theme', async () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider,
        })

        await vi.waitFor(() => {
            expect(result.current.mounted).toBe(true)
        })

        expect(result.current.theme).toBe('light')
    })

    it('loads theme from localStorage', async () => {
        mockStorage['theme'] = 'dark'

        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider,
        })

        await vi.waitFor(() => {
            expect(result.current.mounted).toBe(true)
        })

        expect(result.current.theme).toBe('dark')
    })

    it('toggleTheme changes theme from light to dark', async () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider,
        })

        await vi.waitFor(() => {
            expect(result.current.mounted).toBe(true)
        })

        act(() => {
            result.current.toggleTheme()
        })

        expect(result.current.theme).toBe('dark')
    })

    it('toggleTheme changes theme from dark to light', async () => {
        mockStorage['theme'] = 'dark'

        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider,
        })

        await vi.waitFor(() => {
            expect(result.current.mounted).toBe(true)
        })

        act(() => {
            result.current.toggleTheme()
        })

        expect(result.current.theme).toBe('light')
    })

    it('persists theme to localStorage on change', async () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider,
        })

        await vi.waitFor(() => {
            expect(result.current.mounted).toBe(true)
        })

        act(() => {
            result.current.toggleTheme()
        })

        expect(mockStorage['theme']).toBe('dark')
    })

    // Property 1: Theme Toggle Round Trip
    // **Validates: Requirements 2.3**
    it('Property 1: Theme Toggle Round Trip', async () => {
        await fc.assert(
            fc.asyncProperty(
                fc.constantFrom('light', 'dark'),
                async (initialTheme) => {
                    mockStorage = {}
                    mockStorage['theme'] = initialTheme
                    document.documentElement.classList.remove('dark')

                    const { result } = renderHook(() => useTheme(), {
                        wrapper: ThemeProvider,
                    })

                    await vi.waitFor(() => {
                        expect(result.current.mounted).toBe(true)
                    })

                    const startTheme = result.current.theme

                    // Toggle twice
                    act(() => {
                        result.current.toggleTheme()
                    })
                    act(() => {
                        result.current.toggleTheme()
                    })

                    // Should return to original state
                    expect(result.current.theme).toBe(startTheme)
                }
            ),
            { numRuns: 100 }
        )
    })
})
