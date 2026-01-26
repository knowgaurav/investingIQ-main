import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '../utils/test-utils'
import LLMAnalysisView from '@/components/LLMAnalysisView'

const mockSentiment = {
    overall_score: 0.65,
    breakdown: { positive: 60, negative: 20, neutral: 20 },
    details: [
        {
            headline: 'Company reports strong earnings',
            sentiment: 'Bullish',
            confidence: 0.85,
            reasoning: 'Earnings beat expectations by 15%',
        },
        {
            headline: 'New product launch announced',
            sentiment: 'Bullish',
            confidence: 0.75,
            reasoning: 'Market expansion expected',
        },
    ],
}

describe('LLMAnalysisView', () => {
    it('renders locked state when no LLM config', () => {
        render(<LLMAnalysisView hasLLMConfig={false} />)
        expect(screen.getByText('LLM Analysis Locked')).toBeInTheDocument()
        expect(screen.getByText(/Configure your LLM API key/)).toBeInTheDocument()
        expect(screen.getByText('• AI news summarization')).toBeInTheDocument()
    })

    it('renders loading state', () => {
        render(<LLMAnalysisView hasLLMConfig={true} isLoading={true} />)
        expect(screen.getByText('News Summary')).toBeInTheDocument()
        expect(screen.getByText('AI Sentiment')).toBeInTheDocument()
        expect(screen.getByText('Investment Insights')).toBeInTheDocument()
    })

    it('renders news summary when provided', () => {
        render(
            <LLMAnalysisView
                hasLLMConfig={true}
                newsSummary="The company showed strong performance this quarter."
            />
        )
        expect(screen.getByText('News Summary (LLM Generated)')).toBeInTheDocument()
        expect(screen.getByText('The company showed strong performance this quarter.')).toBeInTheDocument()
    })

    it('renders no summary message when empty', () => {
        render(<LLMAnalysisView hasLLMConfig={true} />)
        expect(screen.getByText('No summary available yet.')).toBeInTheDocument()
    })

    it('renders sentiment analysis with score', () => {
        render(<LLMAnalysisView hasLLMConfig={true} sentiment={mockSentiment} />)
        expect(screen.getByText('AI Sentiment Analysis')).toBeInTheDocument()
        // Score may be split - check for the value
        expect(screen.getByText(/0\.65/)).toBeInTheDocument()
        // Multiple Bullish elements may exist
        const bullishElements = screen.getAllByText('Bullish')
        expect(bullishElements.length).toBeGreaterThan(0)
    })

    it('renders sentiment breakdown', () => {
        render(<LLMAnalysisView hasLLMConfig={true} sentiment={mockSentiment} />)
        // Check for breakdown values - may be multiple
        const positiveElements = screen.getAllByText('60')
        expect(positiveElements.length).toBeGreaterThan(0)
    })

    it('renders sentiment details', () => {
        render(<LLMAnalysisView hasLLMConfig={true} sentiment={mockSentiment} />)
        expect(screen.getByText('Company reports strong earnings')).toBeInTheDocument()
        expect(screen.getByText('Earnings beat expectations by 15%')).toBeInTheDocument()
    })

    it('renders AI insights when provided', () => {
        render(
            <LLMAnalysisView
                hasLLMConfig={true}
                aiInsights="Based on the analysis, the stock shows strong fundamentals."
            />
        )
        expect(screen.getByText('AI Investment Insights')).toBeInTheDocument()
        expect(screen.getByText('Based on the analysis, the stock shows strong fundamentals.')).toBeInTheDocument()
    })

    it('renders no insights message when empty', () => {
        render(<LLMAnalysisView hasLLMConfig={true} />)
        expect(screen.getByText('No insights available yet.')).toBeInTheDocument()
    })

    it('renders disclaimer', () => {
        render(<LLMAnalysisView hasLLMConfig={true} />)
        expect(screen.getByText(/Disclaimer:/)).toBeInTheDocument()
        expect(screen.getByText(/should not be considered financial advice/)).toBeInTheDocument()
    })

    it('handles neutral sentiment score', () => {
        const neutralSentiment = {
            ...mockSentiment,
            overall_score: 0.1,
        }
        render(<LLMAnalysisView hasLLMConfig={true} sentiment={neutralSentiment} />)
        // Multiple Neutral elements may exist - use getAllByText
        const neutralElements = screen.getAllByText('Neutral')
        expect(neutralElements.length).toBeGreaterThan(0)
    })

    it('handles negative sentiment score', () => {
        const negativeSentiment = {
            ...mockSentiment,
            overall_score: -0.5,
            details: [
                {
                    headline: 'Company faces challenges',
                    sentiment: 'Bearish',
                    confidence: 0.8,
                    reasoning: 'Revenue decline expected',
                },
            ],
        }
        render(<LLMAnalysisView hasLLMConfig={true} sentiment={negativeSentiment} />)
        // Multiple Bearish elements may exist - use getAllByText
        const bearishElements = screen.getAllByText('Bearish')
        expect(bearishElements.length).toBeGreaterThan(0)
    })
})
