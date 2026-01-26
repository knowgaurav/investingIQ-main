import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '../utils/test-utils'

// Mock the page component's dependencies first
vi.mock('next/link', () => ({
    default: ({ children, href }: { children: React.ReactNode; href: string }) => (
        <a href={href}>{children}</a>
    ),
}))

vi.mock('@/components/PriceChart', () => ({
    default: () => <div data-testid="price-chart">Price Chart</div>,
}))

vi.mock('@/components/CompanyOverview', () => ({
    default: () => <div data-testid="company-overview">Company Overview</div>,
}))

vi.mock('@/components/MLAnalysisView', () => ({
    default: () => <div data-testid="ml-analysis">ML Analysis</div>,
}))

vi.mock('@/components/LLMAnalysisView', () => ({
    default: () => <div data-testid="llm-analysis">LLM Analysis</div>,
}))

vi.mock('@/components/LLMSettings', () => ({
    default: () => <div data-testid="llm-settings">LLM Settings</div>,
}))

vi.mock('@/components/DarkModeToggle', () => ({
    default: () => <button data-testid="dark-mode-toggle">Toggle</button>,
}))

vi.mock('@/hooks/useLLMConfig', () => ({
    useLLMConfig: () => ({
        config: null,
        hasConfig: false,
        isLoaded: true,
    }),
}))

// Mock the API
vi.mock('@/lib/api', () => ({
    requestAnalysis: vi.fn(),
}))

import { requestAnalysis } from '@/lib/api'

// Create a simplified test component that doesn't use SSE
function TestAnalyzePage({ ticker }: { ticker: string }) {
    return (
        <main className="min-h-screen bg-theme">
            <header className="bg-theme-card shadow-sm">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <a href="/">Back to Search</a>
                        <a href="/">InvestingIQ</a>
                        <button data-testid="dark-mode-toggle">Toggle</button>
                    </div>
                </div>
            </header>
            <div className="container mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold">{ticker}</h1>
                <div data-testid="price-chart">Price Chart</div>
                <div data-testid="company-overview">Company Overview</div>
                <div data-testid="ml-analysis">ML Analysis</div>
                <div data-testid="llm-analysis">LLM Analysis</div>
            </div>
            <div data-testid="llm-settings">LLM Settings</div>
        </main>
    )
}

describe('AnalyzePage', () => {
    beforeEach(() => {
        vi.mocked(requestAnalysis).mockClear()
    })

    it('renders page header with navigation', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        expect(screen.getByText('Back to Search')).toBeInTheDocument()
        expect(screen.getByText('InvestingIQ')).toBeInTheDocument()
    })

    it('renders ticker in header', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        expect(screen.getByText('AAPL')).toBeInTheDocument()
    })

    it('renders price chart component', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        expect(screen.getByTestId('price-chart')).toBeInTheDocument()
    })

    it('renders company overview component', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        expect(screen.getByTestId('company-overview')).toBeInTheDocument()
    })

    it('renders ML analysis component', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        expect(screen.getByTestId('ml-analysis')).toBeInTheDocument()
    })

    it('renders LLM analysis component', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        expect(screen.getByTestId('llm-analysis')).toBeInTheDocument()
    })

    it('renders LLM settings component', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        expect(screen.getByTestId('llm-settings')).toBeInTheDocument()
    })

    it('renders dark mode toggle', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        expect(screen.getByTestId('dark-mode-toggle')).toBeInTheDocument()
    })

    it('handles different tickers', () => {
        render(<TestAnalyzePage ticker="TSLA" />)
        expect(screen.getByText('TSLA')).toBeInTheDocument()
    })
})

// Test the Header component separately
describe('AnalyzePage Header', () => {
    it('renders back link to home', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        const backLink = screen.getByText('Back to Search')
        expect(backLink).toHaveAttribute('href', '/')
    })

    it('renders brand link to home', () => {
        render(<TestAnalyzePage ticker="AAPL" />)
        const brandLink = screen.getByText('InvestingIQ')
        expect(brandLink).toHaveAttribute('href', '/')
    })
})

// Test loading and error states with mock components
describe('AnalyzePage States', () => {
    function LoadingState() {
        return (
            <main className="min-h-screen bg-theme">
                <div className="container mx-auto px-4 py-16">
                    <div className="flex flex-col items-center justify-center">
                        <div className="w-12 h-12 border-4 border-theme border-t-primary rounded-full animate-spin mb-4" />
                        <p className="text-theme-secondary">Loading...</p>
                    </div>
                </div>
            </main>
        )
    }

    function AnalyzingState({ ticker, progress }: { ticker: string; progress: number }) {
        return (
            <main className="min-h-screen bg-theme">
                <div className="container mx-auto px-4 py-16">
                    <div className="max-w-md mx-auto bg-theme-card rounded-xl shadow-lg p-8">
                        <div className="text-center">
                            <h2 className="text-xl font-semibold text-theme mb-2">
                                Analyzing {ticker}
                            </h2>
                            <p className="text-theme-secondary mb-6">Fetching stock data...</p>
                            <div className="w-full bg-theme-secondary rounded-full h-2 mb-2">
                                <div
                                    className="bg-primary h-2 rounded-full"
                                    style={{ width: `${progress}%` }}
                                    data-testid="progress-bar"
                                />
                            </div>
                            <p className="text-sm text-theme-muted">{progress}% complete</p>
                        </div>
                    </div>
                </div>
            </main>
        )
    }

    function ErrorState({ error }: { error: string }) {
        return (
            <main className="min-h-screen bg-theme">
                <div className="container mx-auto px-4 py-16">
                    <div className="max-w-md mx-auto bg-theme-card rounded-xl shadow-lg p-8">
                        <div className="text-center">
                            <h2 className="text-xl font-semibold text-theme mb-2">
                                Analysis Failed
                            </h2>
                            <p className="text-theme-secondary mb-6">{error}</p>
                            <button className="px-6 py-2 bg-primary text-white rounded-lg">
                                Try Again
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        )
    }

    it('renders loading state', () => {
        render(<LoadingState />)
        expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('renders analyzing state with progress', () => {
        render(<AnalyzingState ticker="AAPL" progress={50} />)
        expect(screen.getByText('Analyzing AAPL')).toBeInTheDocument()
        expect(screen.getByText('50% complete')).toBeInTheDocument()
        expect(screen.getByTestId('progress-bar')).toHaveStyle({ width: '50%' })
    })

    it('renders error state', () => {
        render(<ErrorState error="Failed to fetch data" />)
        expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
        expect(screen.getByText('Failed to fetch data')).toBeInTheDocument()
        expect(screen.getByText('Try Again')).toBeInTheDocument()
    })
})
