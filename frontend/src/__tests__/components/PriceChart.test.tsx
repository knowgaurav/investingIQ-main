import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '../utils/test-utils'
import PriceChart from '@/components/PriceChart'
import { createMockPriceData } from '../utils/mock-data'

// Mock ResizeObserver for Recharts
class ResizeObserverMock {
    observe() { }
    unobserve() { }
    disconnect() { }
}
global.ResizeObserver = ResizeObserverMock

describe('PriceChart', () => {
    beforeEach(() => {
        vi.spyOn(window.localStorage, 'getItem').mockReturnValue(null)
        vi.spyOn(window.localStorage, 'setItem').mockImplementation(() => { })
    })

    it('shows empty state message when no data', () => {
        render(<PriceChart data={[]} />)
        expect(screen.getByText('No price data available')).toBeInTheDocument()
    })

    it('shows empty state message when data is undefined', () => {
        render(<PriceChart data={undefined as any} />)
        expect(screen.getByText('No price data available')).toBeInTheDocument()
    })

    it('renders chart container with data', () => {
        const mockData = createMockPriceData(10)
        const { container } = render(<PriceChart data={mockData} />)

        // Check that the chart wrapper div is rendered (not the empty state)
        expect(screen.queryByText('No price data available')).not.toBeInTheDocument()
        expect(container.firstChild).toHaveStyle({ width: '100%' })
    })

    it('applies custom height', () => {
        const mockData = createMockPriceData(5)
        const { container } = render(<PriceChart data={mockData} height={400} />)

        const wrapper = container.firstChild as HTMLElement
        expect(wrapper).toHaveStyle({ height: '400px' })
    })

    it('uses default height of 300', () => {
        const mockData = createMockPriceData(5)
        const { container } = render(<PriceChart data={mockData} />)

        const wrapper = container.firstChild as HTMLElement
        expect(wrapper).toHaveStyle({ height: '300px' })
    })

    it('renders with positive price change (green)', () => {
        // Create data where last price > first price
        const mockData = [
            { date: '2024-01-01', open: 100, high: 105, low: 95, close: 100, volume: 1000000 },
            { date: '2024-01-02', open: 102, high: 110, low: 100, close: 110, volume: 1200000 },
        ]
        const { container } = render(<PriceChart data={mockData} />)

        expect(screen.queryByText('No price data available')).not.toBeInTheDocument()
        expect(container.firstChild).toBeInTheDocument()
    })

    it('renders with negative price change (red)', () => {
        // Create data where last price < first price
        const mockData = [
            { date: '2024-01-01', open: 110, high: 115, low: 105, close: 110, volume: 1000000 },
            { date: '2024-01-02', open: 105, high: 108, low: 95, close: 100, volume: 1200000 },
        ]
        const { container } = render(<PriceChart data={mockData} />)

        expect(screen.queryByText('No price data available')).not.toBeInTheDocument()
        expect(container.firstChild).toBeInTheDocument()
    })

    it('handles single data point', () => {
        const mockData = [
            { date: '2024-01-01', open: 100, high: 105, low: 95, close: 100, volume: 1000000 },
        ]
        const { container } = render(<PriceChart data={mockData} />)

        expect(screen.queryByText('No price data available')).not.toBeInTheDocument()
        expect(container.firstChild).toBeInTheDocument()
    })

    it('handles data with equal first and last price', () => {
        const mockData = [
            { date: '2024-01-01', open: 100, high: 105, low: 95, close: 100, volume: 1000000 },
            { date: '2024-01-02', open: 98, high: 102, low: 96, close: 100, volume: 1100000 },
        ]
        const { container } = render(<PriceChart data={mockData} />)

        expect(screen.queryByText('No price data available')).not.toBeInTheDocument()
        expect(container.firstChild).toBeInTheDocument()
    })

    it('handles large volume numbers', () => {
        const mockData = [
            { date: '2024-01-01', open: 100, high: 105, low: 95, close: 100, volume: 5000000000 }, // 5B
            { date: '2024-01-02', open: 102, high: 110, low: 100, close: 105, volume: 1500000 }, // 1.5M
        ]
        const { container } = render(<PriceChart data={mockData} />)

        expect(container.firstChild).toBeInTheDocument()
    })

    it('handles small volume numbers', () => {
        const mockData = [
            { date: '2024-01-01', open: 100, high: 105, low: 95, close: 100, volume: 500 },
            { date: '2024-01-02', open: 102, high: 110, low: 100, close: 105, volume: 1500 },
        ]
        const { container } = render(<PriceChart data={mockData} />)

        expect(container.firstChild).toBeInTheDocument()
    })
})
