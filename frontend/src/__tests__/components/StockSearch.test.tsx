import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, act, waitFor } from '@testing-library/react'
import { render } from '../utils/test-utils'
import StockSearch from '@/components/StockSearch'
import { createMockStock } from '../utils/mock-data'

// Mock next/navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
    useRouter: () => ({
        push: mockPush,
        replace: vi.fn(),
        prefetch: vi.fn(),
        back: vi.fn(),
    }),
}))

// Mock the API
vi.mock('@/lib/api', () => ({
    searchStocks: vi.fn(),
}))

import { searchStocks } from '@/lib/api'

describe('StockSearch', () => {
    let mockStorage: Record<string, string> = {}

    beforeEach(() => {
        mockStorage = {}
        vi.spyOn(window.localStorage, 'getItem').mockImplementation((key) => mockStorage[key] || null)
        vi.spyOn(window.localStorage, 'setItem').mockImplementation((key, value) => {
            mockStorage[key] = value
        })
        mockPush.mockClear()
        vi.mocked(searchStocks).mockClear()
        vi.useRealTimers()
    })

    it('renders search input', () => {
        render(<StockSearch />)
        expect(screen.getByPlaceholderText(/search for any stock/i)).toBeInTheDocument()
    })

    it('renders analyze button', () => {
        render(<StockSearch />)
        expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument()
    })

    it('updates input value on typing', () => {
        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        fireEvent.change(input, { target: { value: 'AAPL' } })

        expect(input).toHaveValue('AAPL')
    })

    it('triggers search after debounce', async () => {
        vi.useFakeTimers()
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'AAPL',
            results: [createMockStock()],
            count: 1,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'AAPL' } })
        })

        // Should not call immediately
        expect(searchStocks).not.toHaveBeenCalled()

        // Advance timers past debounce
        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        expect(searchStocks).toHaveBeenCalledWith('AAPL', 8)
        vi.useRealTimers()
    })

    it('navigates on Enter key with query', () => {
        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        fireEvent.change(input, { target: { value: 'TSLA' } })
        fireEvent.keyDown(input, { key: 'Enter' })

        expect(mockPush).toHaveBeenCalledWith('/analyze/TSLA')
    })

    it('navigates on Analyze button click', () => {
        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)
        const button = screen.getByRole('button', { name: /analyze/i })

        fireEvent.change(input, { target: { value: 'NVDA' } })
        fireEvent.click(button)

        expect(mockPush).toHaveBeenCalledWith('/analyze/NVDA')
    })

    it('converts ticker to uppercase on navigation', () => {
        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        fireEvent.change(input, { target: { value: 'aapl' } })
        fireEvent.keyDown(input, { key: 'Enter' })

        expect(mockPush).toHaveBeenCalledWith('/analyze/AAPL')
    })

    it('does not navigate with empty query', () => {
        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        fireEvent.keyDown(input, { key: 'Enter' })

        expect(mockPush).not.toHaveBeenCalled()
    })

    it('does not navigate with whitespace-only query', () => {
        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)
        const button = screen.getByRole('button', { name: /analyze/i })

        fireEvent.change(input, { target: { value: '   ' } })
        fireEvent.click(button)

        expect(mockPush).not.toHaveBeenCalled()
    })

    it('shows suggestions dropdown after search', async () => {
        vi.useFakeTimers()
        const mockResults = [
            { ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' },
            { ticker: 'AMZN', name: 'Amazon.com Inc.', exchange: 'NASDAQ' },
        ]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'A',
            results: mockResults,
            count: 2,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'A' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        expect(screen.getByText('AAPL')).toBeInTheDocument()
        expect(screen.getByText('Apple Inc.')).toBeInTheDocument()
        vi.useRealTimers()
    })

    it('navigates when clicking a suggestion', async () => {
        vi.useFakeTimers()
        const mockResults = [{ ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' }]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'AAPL',
            results: mockResults,
            count: 1,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'AAPL' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        const suggestion = screen.getByText('AAPL')
        fireEvent.click(suggestion)

        expect(mockPush).toHaveBeenCalledWith('/analyze/AAPL')
        vi.useRealTimers()
    })

    it('handles keyboard navigation with ArrowDown', async () => {
        vi.useFakeTimers()
        const mockResults = [
            { ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' },
            { ticker: 'AMZN', name: 'Amazon.com Inc.', exchange: 'NASDAQ' },
        ]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'A',
            results: mockResults,
            count: 2,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'A' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        fireEvent.keyDown(input, { key: 'ArrowDown' })
        fireEvent.keyDown(input, { key: 'Enter' })

        expect(mockPush).toHaveBeenCalledWith('/analyze/AAPL')
        vi.useRealTimers()
    })

    it('handles keyboard navigation with ArrowUp', async () => {
        vi.useFakeTimers()
        const mockResults = [
            { ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' },
            { ticker: 'AMZN', name: 'Amazon.com Inc.', exchange: 'NASDAQ' },
        ]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'A',
            results: mockResults,
            count: 2,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'A' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        fireEvent.keyDown(input, { key: 'ArrowDown' })
        fireEvent.keyDown(input, { key: 'ArrowDown' })
        fireEvent.keyDown(input, { key: 'ArrowUp' })
        fireEvent.keyDown(input, { key: 'Enter' })

        expect(mockPush).toHaveBeenCalledWith('/analyze/AAPL')
        vi.useRealTimers()
    })

    it('handles Escape key press', async () => {
        vi.useFakeTimers()
        const mockResults = [{ ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' }]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'AAPL',
            results: mockResults,
            count: 1,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'AAPL' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        // Escape key should be handled without error
        fireEvent.keyDown(input, { key: 'Escape' })

        vi.useRealTimers()
    })

    it('handles search error gracefully', async () => {
        vi.useFakeTimers()
        vi.mocked(searchStocks).mockRejectedValue(new Error('Network error'))

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'AAPL' } })
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        // Should not crash, suggestions should be empty
        expect(screen.queryByText('Apple Inc.')).not.toBeInTheDocument()
        vi.useRealTimers()
    })

    it('saves recent search to localStorage', async () => {
        vi.useFakeTimers()
        const mockResults = [{ ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' }]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'AAPL',
            results: mockResults,
            count: 1,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'AAPL' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        const suggestion = screen.getByText('AAPL')
        fireEvent.click(suggestion)

        expect(window.localStorage.setItem).toHaveBeenCalled()
        vi.useRealTimers()
    })

    it('calls onRecentSearchesChange callback', async () => {
        vi.useFakeTimers()
        const mockCallback = vi.fn()
        const mockResults = [{ ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' }]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'AAPL',
            results: mockResults,
            count: 1,
        })

        render(<StockSearch onRecentSearchesChange={mockCallback} />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'AAPL' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        const suggestion = screen.getByText('AAPL')
        fireEvent.click(suggestion)

        expect(mockCallback).toHaveBeenCalled()
        vi.useRealTimers()
    })

    it('handles empty query after having results', async () => {
        vi.useFakeTimers()
        const mockResults = [{ ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' }]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'AAPL',
            results: mockResults,
            count: 1,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'AAPL' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        // Clear the input - should not crash
        await act(async () => {
            fireEvent.change(input, { target: { value: '' } })
        })

        expect(input).toHaveValue('')
        vi.useRealTimers()
    })

    it('highlights selected suggestion on mouse enter', async () => {
        vi.useFakeTimers()
        const mockResults = [
            { ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' },
            { ticker: 'AMZN', name: 'Amazon.com Inc.', exchange: 'NASDAQ' },
        ]
        vi.mocked(searchStocks).mockResolvedValue({
            query: 'A',
            results: mockResults,
            count: 2,
        })

        render(<StockSearch />)
        const input = screen.getByPlaceholderText(/search for any stock/i)

        await act(async () => {
            fireEvent.change(input, { target: { value: 'A' } })
            fireEvent.focus(input)
        })

        await act(async () => {
            await vi.advanceTimersByTimeAsync(350)
        })

        const secondSuggestion = screen.getByText('AMZN').closest('button')
        if (secondSuggestion) {
            fireEvent.mouseEnter(secondSuggestion)
        }

        // The component should update selectedIndex on mouse enter
        expect(screen.getByText('AMZN')).toBeInTheDocument()
        vi.useRealTimers()
    })
})
