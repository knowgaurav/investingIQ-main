import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '../utils/test-utils'
import CompanyOverview from '@/components/CompanyOverview'

const mockCompanyInfo = {
    name: 'Apple Inc.',
    sector: 'Technology',
    industry: 'Consumer Electronics',
    description: 'Apple designs and manufactures consumer electronics.',
    market_cap: 3000000000000,
    pe_ratio: 28.5,
    peg_ratio: 2.1,
    book_value: 4.25,
    dividend_yield: 0.005,
    eps: 6.15,
    revenue_ttm: 380000000000,
    profit_margin: 0.25,
    '52_week_high': 200,
    '52_week_low': 150,
    '50_day_ma': 180,
    '200_day_ma': 175,
    analyst_target: 210,
}

const mockNews = [
    {
        title: 'Apple announces new product',
        summary: 'Apple revealed its latest innovation today.',
        url: 'https://example.com/news/1',
        source: 'TechNews',
        published_at: '2024-01-15T10:00:00Z',
        overall_sentiment_label: 'Bullish',
        ticker_sentiment_score: 0.8,
    },
]

const mockEarnings = {
    quarterly_earnings: [
        {
            fiscal_quarter: 'Q4 2024',
            reported_eps: 2.18,
            estimated_eps: 2.10,
            surprise: 0.08,
            surprise_pct: 3.8,
        },
    ],
    annual_earnings: [{ fiscal_year: '2024', eps: 6.15 }],
}

describe('CompanyOverview', () => {
    it('renders company profile section', () => {
        render(<CompanyOverview ticker="AAPL" companyInfo={mockCompanyInfo} />)
        expect(screen.getByText('Company Profile')).toBeInTheDocument()
        expect(screen.getByText('Technology')).toBeInTheDocument()
        expect(screen.getByText('Consumer Electronics')).toBeInTheDocument()
    })

    it('renders loading state when no company info', () => {
        render(<CompanyOverview ticker="AAPL" />)
        expect(screen.getByText('Company information loading...')).toBeInTheDocument()
    })

    it('renders key metrics with formatted values', () => {
        render(<CompanyOverview ticker="AAPL" companyInfo={mockCompanyInfo} currentPrice={185} />)
        expect(screen.getByText('Key Metrics')).toBeInTheDocument()
        // Market cap formatted as T (trillion)
        expect(screen.getByText(/3\.00T/)).toBeInTheDocument()
        // P/E ratio
        expect(screen.getByText('28.50')).toBeInTheDocument()
    })

    it('renders price analysis section', () => {
        render(<CompanyOverview ticker="AAPL" companyInfo={mockCompanyInfo} currentPrice={185} />)
        expect(screen.getByText('Price Analysis')).toBeInTheDocument()
        expect(screen.getByText('52-Week Range')).toBeInTheDocument()
        expect(screen.getByText('50-Day MA')).toBeInTheDocument()
        expect(screen.getByText('200-Day MA')).toBeInTheDocument()
    })

    it('shows above/below indicators for moving averages', () => {
        render(<CompanyOverview ticker="AAPL" companyInfo={mockCompanyInfo} currentPrice={185} />)
        // Price 185 is above both 50-day MA (180) and 200-day MA (175)
        const aboveLabels = screen.getAllByText('↑ Above')
        expect(aboveLabels.length).toBeGreaterThan(0)
    })

    it('renders analyst target with upside potential', () => {
        render(<CompanyOverview ticker="AAPL" companyInfo={mockCompanyInfo} currentPrice={185} />)
        expect(screen.getByText('Analyst Target Price')).toBeInTheDocument()
        expect(screen.getByText('$210.00')).toBeInTheDocument()
        expect(screen.getByText('Upside potential')).toBeInTheDocument()
    })

    it('renders earnings history when provided', () => {
        render(<CompanyOverview ticker="AAPL" companyInfo={mockCompanyInfo} earnings={mockEarnings} />)
        expect(screen.getByText('Earnings History')).toBeInTheDocument()
        expect(screen.getByText('Q4 2024')).toBeInTheDocument()
        expect(screen.getByText('+3.8%')).toBeInTheDocument()
    })

    it('renders news section when provided', () => {
        render(<CompanyOverview ticker="AAPL" companyInfo={mockCompanyInfo} news={mockNews} />)
        expect(screen.getByText('Recent News')).toBeInTheDocument()
        expect(screen.getByText('Apple announces new product')).toBeInTheDocument()
        expect(screen.getByText('Bullish')).toBeInTheDocument()
    })

    it('does not render news section when empty', () => {
        render(<CompanyOverview ticker="AAPL" companyInfo={mockCompanyInfo} news={[]} />)
        expect(screen.queryByText('Recent News')).not.toBeInTheDocument()
    })

    it('formats large numbers correctly', () => {
        const infoWithVariousMarketCaps = { ...mockCompanyInfo, market_cap: 500000000 }
        render(<CompanyOverview ticker="TEST" companyInfo={infoWithVariousMarketCaps} />)
        expect(screen.getByText(/500.*M/)).toBeInTheDocument()
    })

    it('handles missing optional fields gracefully', () => {
        const minimalInfo = { name: 'Test Corp' }
        render(<CompanyOverview ticker="TEST" companyInfo={minimalInfo} />)
        expect(screen.getByText('Company Profile')).toBeInTheDocument()
        // Should show N/A for missing metrics
        const naElements = screen.getAllByText('N/A')
        expect(naElements.length).toBeGreaterThan(0)
    })
})
