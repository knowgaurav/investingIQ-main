import { StockSearchResult, PriceDataPoint } from '@/lib/api'

export function createMockStock(overrides?: Partial<StockSearchResult>): StockSearchResult {
    return {
        ticker: 'AAPL',
        name: 'Apple Inc.',
        exchange: 'NASDAQ',
        ...overrides,
    }
}

export function createMockPriceData(count: number = 5): PriceDataPoint[] {
    return Array.from({ length: count }, (_, i) => ({
        date: `2024-01-${String(i + 1).padStart(2, '0')}`,
        open: 150 + i,
        high: 155 + i,
        low: 148 + i,
        close: 152 + i,
        volume: 1000000 + i * 100000,
    }))
}
