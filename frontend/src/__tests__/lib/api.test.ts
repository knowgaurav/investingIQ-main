import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import * as fc from 'fast-check'
import { ApiError, searchStocks, requestAnalysis, getAnalysisStatus, getAnalysisReport, sendChatMessage } from '@/lib/api'

describe('ApiError', () => {
    it('constructs with message and status', () => {
        const error = new ApiError('Not found', 404)
        expect(error.message).toBe('Not found')
        expect(error.status).toBe(404)
        expect(error.detail).toBeUndefined()
        expect(error.name).toBe('ApiError')
    })

    it('constructs with message, status, and detail', () => {
        const error = new ApiError('Bad request', 400, 'Invalid ticker symbol')
        expect(error.message).toBe('Bad request')
        expect(error.status).toBe(400)
        expect(error.detail).toBe('Invalid ticker symbol')
    })

    it('is an instance of Error', () => {
        const error = new ApiError('Server error', 500)
        expect(error).toBeInstanceOf(Error)
    })

    // Property 3: API Error Construction Preserves Values
    // **Validates: Requirements 6.3**
    it('Property 3: API Error Construction Preserves Values', () => {
        fc.assert(
            fc.property(
                fc.string({ minLength: 1 }),
                fc.integer({ min: 100, max: 599 }),
                fc.option(fc.string(), { nil: undefined }),
                (message, status, detail) => {
                    const error = new ApiError(message, status, detail)
                    expect(error.message).toBe(message)
                    expect(error.status).toBe(status)
                    expect(error.detail).toBe(detail)
                }
            ),
            { numRuns: 100 }
        )
    })
})

describe('searchStocks', () => {
    const originalFetch = global.fetch

    beforeEach(() => {
        global.fetch = vi.fn()
    })

    afterEach(() => {
        global.fetch = originalFetch
    })

    it('calls API with correct URL parameters', async () => {
        const mockResponse = {
            query: 'AAPL',
            results: [{ ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' }],
            count: 1,
        }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        await searchStocks('AAPL', 10)

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/stocks/search?q=AAPL&limit=10'),
            expect.any(Object)
        )
    })

    it('uses default limit of 10', async () => {
        const mockResponse = { query: 'TSLA', results: [], count: 0 }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        await searchStocks('TSLA')

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('limit=10'),
            expect.any(Object)
        )
    })

    it('throws ApiError on non-ok response', async () => {
        ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
            ok: false,
            status: 404,
            json: () => Promise.resolve({ detail: 'Stock not found' }),
        })

        await expect(searchStocks('INVALID')).rejects.toThrow(ApiError)
    })

    // Property 4: Search Query URL Formatting
    // **Validates: Requirements 6.2**
    it('Property 4: Search Query URL Formatting', async () => {
        // Use alphanumeric strings to avoid URL encoding edge cases
        await fc.assert(
            fc.asyncProperty(
                fc.stringMatching(/^[a-zA-Z0-9]{1,10}$/),
                fc.integer({ min: 1, max: 100 }),
                async (query, limit) => {
                    const mockFetch = vi.fn().mockResolvedValueOnce({
                        ok: true,
                        json: () => Promise.resolve({ query, results: [], count: 0 }),
                    })
                    global.fetch = mockFetch

                    await searchStocks(query, limit)

                    expect(mockFetch).toHaveBeenCalled()
                    const calledUrl = mockFetch.mock.calls[0][0] as string
                    const url = new URL(calledUrl)
                    expect(url.searchParams.get('q')).toBe(query)
                    expect(url.searchParams.get('limit')).toBe(String(limit))
                }
            ),
            { numRuns: 100 }
        )
    })
})

describe('requestAnalysis', () => {
    const originalFetch = global.fetch

    beforeEach(() => {
        global.fetch = vi.fn()
    })

    afterEach(() => {
        global.fetch = originalFetch
    })

    it('sends POST request with ticker', async () => {
        const mockResponse = { task_id: '123', status: 'pending', message: 'Analysis started' }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        const result = await requestAnalysis('AAPL')

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/analysis/request'),
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ ticker: 'AAPL' }),
            })
        )
        expect(result).toEqual(mockResponse)
    })

    it('includes LLM config when provided', async () => {
        const mockResponse = { task_id: '123', status: 'pending', message: 'Analysis started' }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        const llmConfig = { provider: 'openai', api_key: 'test-key', model: 'gpt-4' }
        await requestAnalysis('AAPL', llmConfig)

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/analysis/request'),
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({
                    ticker: 'AAPL',
                    llm_config: { provider: 'openai', api_key: 'test-key', model: 'gpt-4' },
                }),
            })
        )
    })

    it('handles null model in LLM config', async () => {
        const mockResponse = { task_id: '123', status: 'pending', message: 'Analysis started' }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        const llmConfig = { provider: 'openai', api_key: 'test-key' }
        await requestAnalysis('AAPL', llmConfig)

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    ticker: 'AAPL',
                    llm_config: { provider: 'openai', api_key: 'test-key', model: null },
                }),
            })
        )
    })
})

describe('getAnalysisStatus', () => {
    const originalFetch = global.fetch

    beforeEach(() => {
        global.fetch = vi.fn()
    })

    afterEach(() => {
        global.fetch = originalFetch
    })

    it('fetches status for task ID', async () => {
        const mockResponse = {
            task_id: '123',
            ticker: 'AAPL',
            status: 'completed',
            progress: 100,
            current_step: null,
            error_message: null,
        }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        const result = await getAnalysisStatus('123')

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/analysis/status/123'),
            expect.any(Object)
        )
        expect(result).toEqual(mockResponse)
    })
})

describe('getAnalysisReport', () => {
    const originalFetch = global.fetch

    beforeEach(() => {
        global.fetch = vi.fn()
    })

    afterEach(() => {
        global.fetch = originalFetch
    })

    it('fetches report for ticker', async () => {
        const mockResponse = {
            id: '123',
            ticker: 'AAPL',
            company_name: 'Apple Inc.',
            analyzed_at: '2024-01-01',
            price_data: [],
            news_summary: null,
            sentiment_score: null,
            sentiment_breakdown: null,
            sentiment_details: null,
            ai_insights: null,
        }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        const result = await getAnalysisReport('AAPL')

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/analysis/report/AAPL'),
            expect.any(Object)
        )
        expect(result).toEqual(mockResponse)
    })

    it('throws ApiError when report not found', async () => {
        ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
            ok: false,
            status: 404,
            json: () => Promise.resolve({ detail: 'Report not found' }),
        })

        await expect(getAnalysisReport('INVALID')).rejects.toThrow(ApiError)
    })
})

describe('sendChatMessage', () => {
    const originalFetch = global.fetch

    beforeEach(() => {
        global.fetch = vi.fn()
    })

    afterEach(() => {
        global.fetch = originalFetch
    })

    it('sends chat message and returns response', async () => {
        const mockResponse = {
            response: 'Apple is a tech company.',
            sources: ['news1', 'news2'],
            conversation_id: 'conv-123',
        }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        const result = await sendChatMessage({
            message: 'Tell me about Apple',
            ticker: 'AAPL',
        })

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/chat'),
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ message: 'Tell me about Apple', ticker: 'AAPL' }),
            })
        )
        expect(result).toEqual(mockResponse)
    })

    it('includes conversation_id when provided', async () => {
        const mockResponse = {
            response: 'More info about Apple.',
            sources: null,
            conversation_id: 'conv-123',
        }
            ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse),
            })

        await sendChatMessage({
            message: 'Tell me more',
            ticker: 'AAPL',
            conversation_id: 'conv-123',
        })

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                body: JSON.stringify({
                    message: 'Tell me more',
                    ticker: 'AAPL',
                    conversation_id: 'conv-123',
                }),
            })
        )
    })
})

describe('fetchApi error handling', () => {
    const originalFetch = global.fetch

    beforeEach(() => {
        global.fetch = vi.fn()
    })

    afterEach(() => {
        global.fetch = originalFetch
    })

    it('handles non-JSON error response', async () => {
        ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: () => Promise.reject(new Error('Invalid JSON')),
        })

        await expect(searchStocks('AAPL')).rejects.toThrow(ApiError)
    })

    it('uses HTTP status in error message when no detail', async () => {
        ; (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
            ok: false,
            status: 503,
            json: () => Promise.resolve({}),
        })

        try {
            await searchStocks('AAPL')
        } catch (error) {
            expect(error).toBeInstanceOf(ApiError)
            expect((error as ApiError).message).toContain('503')
        }
    })
})
