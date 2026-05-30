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
        expect(screen.getByText(/An AI Bureau of Market Intelligence/)).toBeInTheDocument()
    })

    it('renders stock search component', () => {
        render(<Home />)
        expect(screen.getByTestId('stock-search')).toBeInTheDocument()
    })

    it('renders feature columns', () => {
        render(<Home />)
        expect(screen.getByText('Real-time')).toBeInTheDocument()
        expect(screen.getByText('AI-Powered')).toBeInTheDocument()
        expect(screen.getByText('Sentiment')).toBeInTheDocument()
        expect(screen.getByText('Global')).toBeInTheDocument()
    })

    it('renders watchlist index section', () => {
        render(<Home />)
        expect(screen.getByText('The Watchlist Index')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /AAPL/ })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /MSFT/ })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /GOOGL/ })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /TSLA/ })).toBeInTheDocument()
    })

    it('navigates to analyze page on popular stock click', () => {
        render(<Home />)
        fireEvent.click(screen.getByRole('button', { name: /AAPL/ }))
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
        expect(screen.queryByText('From Your Desk')).not.toBeInTheDocument()
    })
})
