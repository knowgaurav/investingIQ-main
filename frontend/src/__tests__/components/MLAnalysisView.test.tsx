import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '../utils/test-utils'
import MLAnalysisView from '@/components/MLAnalysisView'

// Mock ForecastChart
vi.mock('@/components/ForecastChart', () => ({
    default: () => <div data-testid="forecast-chart">Forecast Chart</div>,
}))

const mockPrediction = {
    forecast_7d: 155,
    forecast_7d_change: 3.33,
    forecast_30d: 165,
    forecast_30d_change: 10,
    trend: 'upward',
    confidence: 0.75,
    current_price: 150,
    models_used: 'ARIMA + Prophet',
    reasoning: ['Strong momentum indicators', 'Positive earnings trend'],
    daily_forecast: [151, 152, 153, 154, 155, 156, 157],
    arima_forecast: { '7d': 154, '30d': 163, daily: [151, 152, 153] },
    prophet_forecast: { '7d': 156, '30d': 167, daily: [152, 153, 154] },
    ets_forecast: { '7d': 155, '30d': 165, daily: [151.5, 152.5, 153.5] },
    rf_signal: {
        signal: 'buy' as const,
        buy_probability: 0.72,
        precision: 0.68,
        accuracy: 0.71,
        top_features: ['RSI', 'MACD', 'Volume'],
    },
}

const mockTechnical = {
    rsi: 45,
    rsi_signal: 'neutral',
    macd: 0.5,
    macd_signal: 'bullish',
    macd_histogram: 0.2,
    bollinger_upper: 160,
    bollinger_middle: 150,
    bollinger_lower: 140,
    bollinger_position: 'middle',
    support_levels: [145, 140],
    resistance_levels: [155, 160],
    volume_signal: 'normal',
    volume_ratio: 1.2,
}

const mockSentiment = {
    overall_score: 0.6,
    label: 'positive',
    positive_pct: 60,
    neutral_pct: 25,
    negative_pct: 15,
    details: [
        { headline: 'Strong earnings report', score: 0.8, label: 'positive' },
        { headline: 'Market uncertainty', score: -0.2, label: 'negative' },
    ],
}

describe('MLAnalysisView', () => {
    it('renders overall signal card', () => {
        render(<MLAnalysisView prediction={mockPrediction} technical={mockTechnical} sentiment={mockSentiment} />)
        expect(screen.getByText('ML Analysis Signal')).toBeInTheDocument()
    })

    it('shows BUY signal for positive indicators', () => {
        const strongPrediction = { ...mockPrediction, forecast_30d_change: 8 }
        render(<MLAnalysisView prediction={strongPrediction} technical={mockTechnical} sentiment={mockSentiment} />)
        // Multiple BUY elements may exist - use getAllByText
        const buyElements = screen.getAllByText('BUY')
        expect(buyElements.length).toBeGreaterThan(0)
    })

    it('shows HOLD signal for mixed indicators', () => {
        const neutralPrediction = { ...mockPrediction, forecast_30d_change: 1 }
        const neutralTechnical = { ...mockTechnical, macd_signal: 'neutral', rsi_signal: 'neutral' }
        const neutralSentiment = { ...mockSentiment, overall_score: 0.1 }
        render(<MLAnalysisView prediction={neutralPrediction} technical={neutralTechnical} sentiment={neutralSentiment} />)
        expect(screen.getByText('HOLD')).toBeInTheDocument()
    })

    it('shows SELL signal for negative indicators', () => {
        const negativePrediction = { ...mockPrediction, forecast_30d_change: -8 }
        const negativeTechnical = { ...mockTechnical, macd_signal: 'bearish', rsi_signal: 'overbought', bollinger_position: 'upper' }
        const negativeSentiment = { ...mockSentiment, overall_score: -0.5 }
        render(<MLAnalysisView prediction={negativePrediction} technical={negativeTechnical} sentiment={negativeSentiment} />)
        expect(screen.getByText('SELL')).toBeInTheDocument()
    })

    it('renders price forecast section', () => {
        render(<MLAnalysisView prediction={mockPrediction} />)
        expect(screen.getByText('Price Forecast')).toBeInTheDocument()
        expect(screen.getByText('7-Day Forecast (Combined)')).toBeInTheDocument()
        expect(screen.getByText('30-Day Forecast (Combined)')).toBeInTheDocument()
    })

    it('renders forecast chart when daily data available', () => {
        render(<MLAnalysisView prediction={mockPrediction} />)
        expect(screen.getByTestId('forecast-chart')).toBeInTheDocument()
    })

    it('renders model summary cards', () => {
        render(<MLAnalysisView prediction={mockPrediction} />)
        expect(screen.getByText('ARIMA')).toBeInTheDocument()
        expect(screen.getByText('Prophet')).toBeInTheDocument()
        expect(screen.getByText('ETS (Holt-Winters)')).toBeInTheDocument()
    })

    it('renders Random Forest signal card', () => {
        render(<MLAnalysisView prediction={mockPrediction} />)
        expect(screen.getByText('Random Forest Signal')).toBeInTheDocument()
        expect(screen.getByText('72%')).toBeInTheDocument() // Buy probability
    })

    it('renders trend and confidence', () => {
        render(<MLAnalysisView prediction={mockPrediction} />)
        expect(screen.getByText('Overall Trend')).toBeInTheDocument()
        expect(screen.getByText('↗ Upward')).toBeInTheDocument()
        expect(screen.getByText('75%')).toBeInTheDocument() // Confidence
    })

    it('renders ML reasoning', () => {
        render(<MLAnalysisView prediction={mockPrediction} />)
        expect(screen.getByText('🔍 Model Analysis Reasoning')).toBeInTheDocument()
        expect(screen.getByText('Strong momentum indicators')).toBeInTheDocument()
    })

    it('renders technical indicators section', () => {
        render(<MLAnalysisView technical={mockTechnical} />)
        expect(screen.getByText('Technical Indicators')).toBeInTheDocument()
        expect(screen.getByText('RSI (Relative Strength Index)')).toBeInTheDocument()
        expect(screen.getByText('MACD (Trend Direction)')).toBeInTheDocument()
        expect(screen.getByText('Bollinger Bands')).toBeInTheDocument()
    })

    it('renders support and resistance levels', () => {
        render(<MLAnalysisView technical={mockTechnical} />)
        expect(screen.getByText('Key Price Levels')).toBeInTheDocument()
        expect(screen.getByText('Support (Buy Zones)')).toBeInTheDocument()
        expect(screen.getByText('Resistance (Sell Zones)')).toBeInTheDocument()
        expect(screen.getByText('$145.00')).toBeInTheDocument()
        expect(screen.getByText('$155.00')).toBeInTheDocument()
    })

    it('renders sentiment analysis section', () => {
        render(<MLAnalysisView sentiment={mockSentiment} />)
        expect(screen.getByText('News Sentiment Analysis')).toBeInTheDocument()
        expect(screen.getByText('📈 Bullish')).toBeInTheDocument()
        // Multiple 60% elements may exist - use getAllByText
        const scoreElements = screen.getAllByText('60%')
        expect(scoreElements.length).toBeGreaterThan(0)
    })

    it('renders sentiment breakdown', () => {
        render(<MLAnalysisView sentiment={mockSentiment} />)
        expect(screen.getByText('Positive')).toBeInTheDocument()
        expect(screen.getByText('Neutral')).toBeInTheDocument()
        expect(screen.getByText('Negative')).toBeInTheDocument()
    })

    it('renders analyzed headlines', () => {
        render(<MLAnalysisView sentiment={mockSentiment} />)
        expect(screen.getByText('Analyzed Headlines')).toBeInTheDocument()
        expect(screen.getByText('Strong earnings report')).toBeInTheDocument()
    })

    it('renders disclaimer', () => {
        render(<MLAnalysisView />)
        expect(screen.getByText(/Disclaimer:/)).toBeInTheDocument()
    })

    it('shows loading state for missing prediction', () => {
        render(<MLAnalysisView />)
        expect(screen.getByText('Loading predictions...')).toBeInTheDocument()
    })

    it('shows loading state for missing technical', () => {
        render(<MLAnalysisView prediction={mockPrediction} />)
        expect(screen.getByText('Loading technical analysis...')).toBeInTheDocument()
    })

    it('shows loading state for missing sentiment', () => {
        render(<MLAnalysisView prediction={mockPrediction} technical={mockTechnical} />)
        expect(screen.getByText('Loading sentiment analysis...')).toBeInTheDocument()
    })

    it('renders investment projection', () => {
        render(<MLAnalysisView prediction={mockPrediction} />)
        expect(screen.getByText('Investment Projection (30 days)')).toBeInTheDocument()
        expect(screen.getByText('If you invest:')).toBeInTheDocument()
        expect(screen.getByText('$1,000')).toBeInTheDocument()
    })

    it('handles strong upward trend', () => {
        const strongUpPrediction = { ...mockPrediction, trend: 'strong_upward' }
        render(<MLAnalysisView prediction={strongUpPrediction} />)
        expect(screen.getByText('⬆ Strong Upward')).toBeInTheDocument()
    })

    it('handles downward trend', () => {
        const downPrediction = { ...mockPrediction, trend: 'downward', forecast_30d_change: -5 }
        render(<MLAnalysisView prediction={downPrediction} />)
        expect(screen.getByText('↘ Downward')).toBeInTheDocument()
    })

    it('handles sideways trend', () => {
        const sidewaysPrediction = { ...mockPrediction, trend: 'sideways' }
        render(<MLAnalysisView prediction={sidewaysPrediction} />)
        expect(screen.getByText('→ Sideways')).toBeInTheDocument()
    })
})
