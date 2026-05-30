import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '../utils/test-utils'
import DualAnalysisView from '@/components/DualAnalysisView'

const mockMl = {
    prediction: {
        forecast_7d: 155,
        forecast_7d_change: 3.33,
        forecast_30d: 165,
        forecast_30d_change: 10,
        trend: 'upward',
        confidence: 0.75,
    },
    technical: {
        rsi: 45,
        rsi_signal: 'neutral',
        macd: 0.5,
        macd_signal: 'bullish',
        macd_histogram: 0.2,
        bollinger_upper: 160,
        bollinger_middle: 150,
        bollinger_lower: 140,
        bollinger_position: 'middle',
        support_levels: [145],
        resistance_levels: [160],
        volume_signal: 'normal',
    },
    sentiment: {
        overall_score: 0.6,
        label: 'positive',
        positive_pct: 60,
        neutral_pct: 25,
        negative_pct: 15,
        details: [],
    },
}

const mockLlm = {
    outlook: 'bullish',
    sentiment_score: 0.7,
    insight: 'Strong revenue growth supports an upward outlook.',
}

describe('DualAnalysisView', () => {
    it('renders both ML and LLM columns', () => {
        render(<DualAnalysisView ml={mockMl} llm={mockLlm} llmStatus="ok" comparison={{ ml_signal: 'bullish', llm_signal: 'bullish', agreement: true }} />)
        expect(screen.getByText('Statistical (ML)')).toBeInTheDocument()
        expect(screen.getByText('AI (LLM)')).toBeInTheDocument()
    })

    it('shows agreement chip when both signals agree', () => {
        render(<DualAnalysisView ml={mockMl} llm={mockLlm} llmStatus="ok" comparison={{ ml_signal: 'bullish', llm_signal: 'bullish', agreement: true }} />)
        expect(screen.getByText(/Both models agree/i)).toBeInTheDocument()
    })

    it('shows disagreement when signals differ', () => {
        render(<DualAnalysisView ml={mockMl} llm={{ ...mockLlm, outlook: 'bearish' }} llmStatus="ok" comparison={{ ml_signal: 'bullish', llm_signal: 'bearish', agreement: false }} />)
        expect(screen.getByText(/Models disagree/i)).toBeInTheDocument()
    })

    it('shows LLM not run state when LLM absent', () => {
        render(<DualAnalysisView ml={mockMl} llmStatus="not_run" />)
        expect(screen.getByText('LLM analysis not run')).toBeInTheDocument()
    })

    it('renders LLM insight when available', () => {
        render(<DualAnalysisView ml={mockMl} llm={mockLlm} llmStatus="ok" comparison={null} />)
        expect(screen.getByText(/Strong revenue growth/i)).toBeInTheDocument()
    })
})
