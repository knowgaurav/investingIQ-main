import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { render } from '../utils/test-utils'
import Home from '@/app/page'

// Mock next/navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
    useRouter: () => ({
        push: mockPush,
        replace: vi.fn(),
        prefetch: vi.fn(),
    }),
}))

// Mock components
vi.mock('@/components/StockSearch', () => ({
    default: ({ onRecentSearchesChange }: { onRecentSearchesChange?: (searches: any[]) => void }) => (
        <div data-testid="stock-search">Stock Search Component</div>
    ),
}))

vi.mock('@/components/LLMSettings', () => ({
    default: () => <div data-testid="llm-settings">LLM Settings</div>,
}))

vi.mock('@/components/DarkModeToggle', () => ({
    default: () => <button data-testid="dark-mode-toggle">Toggle</button>,
}))

describe('Home Page', () => {
    beforeEach(() => {
        vi.spyOn(window.localStorage, 'getItem').mockReturnValue(null)
        vi.spyOn(window.localStorage, 'setItem').mockImplementation(() => { })
        vi.spyOn(window.localStorage, 'removeItem').mockImplementation(() => { })
        mockPush.mockClear()
    })

    it('renders the main title', () => {
        render(<Home />)
        expect(screen.getByText('InvestingIQ')).toBeInTheDocument()
    })

    it('renders the tagline', () => {
        render(<Home />)
        expect(screen.getByText(/AI-Powered Stock Analysis Platform/)).toBeInTheDocument()
    })

    it('renders stock search component', () => {
        render(<Home />)
        expect(screen.getByTestId('stock-search')).toBeInTheDocument()
    })

    it('renders feature badges', () => {
        render(<Home />)
        expect(screen.getByText('Real-time Analysis')).toBeInTheDocument()
        expect(screen.getByText('AI-Powered Insights')).toBeInTheDocument()
        expect(screen.getByText('Sentiment Analysis')).toBeInTheDocument()
        expect(screen.getByText('Any Stock Worldwide')).toBeInTheDocument()
    })

    it('renders popular stocks section', () => {
        render(<Home />)
        expect(screen.getByText('Popular Stocks')).toBeInTheDocument()
        expect(screen.getByText('AAPL')).toBeInTheDocument()
        expect(screen.getByText('MSFT')).toBeInTheDocument()
        expect(screen.getByText('GOOGL')).toBeInTheDocument()
        expect(screen.getByText('TSLA')).toBeInTheDocument()
    })

    it('navigates to analyze page on popular stock click', () => {
        render(<Home />)
        fireEvent.click(screen.getByText('AAPL'))
        expect(mockPush).toHaveBeenCalledWith('/analyze/AAPL')
    })

    it('renders dark mode toggle', () => {
        render(<Home />)
        expect(screen.getByTestId('dark-mode-toggle')).toBeInTheDocument()
    })

    it('renders LLM settings component', () => {
        render(<Home />)
        expect(screen.getByTestId('llm-settings')).toBeInTheDocument()
    })

    it('does not render recent searches section when empty', () => {
        render(<Home />)
        expect(screen.queryByText('Recent Searches')).not.toBeInTheDocument()
    })
})
