import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '../utils/test-utils'
import ForecastChart from '@/components/ForecastChart'

// Mock recharts to avoid rendering issues in tests
vi.mock('recharts', () => ({
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="responsive-container">{children}</div>
    ),
    LineChart: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="line-chart">{children}</div>
    ),
    Line: () => <div data-testid="line" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: () => <div data-testid="y-axis" />,
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    Tooltip: () => <div data-testid="tooltip" />,
    Legend: () => <div data-testid="legend" />,
    ReferenceLine: () => <div data-testid="reference-line" />,
}))

describe('ForecastChart', () => {
    const defaultProps = {
        currentPrice: 150,
        dailyForecast: [151, 152, 153, 154, 155, 156, 157],
    }

    it('renders chart container with data', () => {
        render(<ForecastChart {...defaultProps} />)
        expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('renders empty state when no forecast data', () => {
        render(<ForecastChart currentPrice={150} dailyForecast={[]} />)
        expect(screen.getByText('No forecast data available')).toBeInTheDocument()
    })

    it('renders with ARIMA forecast data', () => {
        render(
            <ForecastChart
                {...defaultProps}
                arimaDaily={[151.5, 152.5, 153.5, 154.5, 155.5, 156.5, 157.5]}
            />
        )
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('renders with Prophet forecast data', () => {
        render(
            <ForecastChart
                {...defaultProps}
                prophetDaily={[150.5, 151.5, 152.5, 153.5, 154.5, 155.5, 156.5]}
            />
        )
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('renders with ETS forecast data', () => {
        render(
            <ForecastChart
                {...defaultProps}
                etsDaily={[151, 152, 153, 154, 155, 156, 157]}
            />
        )
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('renders with all forecast models', () => {
        render(
            <ForecastChart
                {...defaultProps}
                arimaDaily={[151.5, 152.5, 153.5, 154.5, 155.5, 156.5, 157.5]}
                prophetDaily={[150.5, 151.5, 152.5, 153.5, 154.5, 155.5, 156.5]}
                etsDaily={[151, 152, 153, 154, 155, 156, 157]}
            />
        )
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('handles 30-day forecast data', () => {
        const thirtyDayForecast = Array.from({ length: 30 }, (_, i) => 150 + i * 0.5)
        render(<ForecastChart currentPrice={150} dailyForecast={thirtyDayForecast} />)
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })
})
