'use client';

import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
} from 'recharts';
import { PriceDataPoint } from '@/lib/api';

interface PriceChartProps {
    data: PriceDataPoint[];
    height?: number;
}

export default function PriceChart({ data, height = 300 }: PriceChartProps) {
    if (!data || data.length === 0) {
        return (
            <div
                className="flex items-center justify-center bg-theme-secondary rounded-lg"
                style={{ height }}
            >
                <p className="text-theme-muted">No price data available</p>
            </div>
        );
    }

    // Format data for the chart
    const chartData = data.map((point) => ({
        date: formatDate(point.date),
        close: point.close,
        high: point.high,
        low: point.low,
        volume: point.volume,
    }));

    // Calculate price change for color
    const firstPrice = data[0]?.close || 0;
    const lastPrice = data[data.length - 1]?.close || 0;
    const isPositive = lastPrice >= firstPrice;
    const lineColor = isPositive ? '#177a54' : '#b8322c';
    const gradientId = isPositive ? 'colorPositive' : 'colorNegative';

    // Theme-aware chart chrome via CSS variables (set in globals.css)
    const gridColor = 'var(--chart-grid)';
    const axisText = 'var(--chart-axis-text)';

    // Calculate min/max for Y axis with padding
    const prices = data.map((d) => d.close);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const padding = (maxPrice - minPrice) * 0.1;

    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer>
                <AreaChart
                    data={chartData}
                    margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                >
                    <defs>
                        <linearGradient id="colorPositive" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#177a54" stopOpacity={0.28} />
                            <stop offset="95%" stopColor="#177a54" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorNegative" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#b8322c" stopOpacity={0.28} />
                            <stop offset="95%" stopColor="#b8322c" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="2 4" stroke={gridColor} />
                    <XAxis
                        dataKey="date"
                        tick={{ fontSize: 11, fill: axisText, fontFamily: 'var(--font-plex-mono)' }}
                        tickLine={false}
                        axisLine={{ stroke: gridColor }}
                        interval="preserveStartEnd"
                        minTickGap={50}
                    />
                    <YAxis
                        domain={[minPrice - padding, maxPrice + padding]}
                        tick={{ fontSize: 11, fill: axisText, fontFamily: 'var(--font-plex-mono)' }}
                        tickLine={false}
                        axisLine={{ stroke: gridColor }}
                        tickFormatter={(value: number) => `$${value.toFixed(0)}`}
                        width={60}
                    />
                    <Tooltip
                        content={<CustomTooltip />}
                        cursor={{ stroke: lineColor, strokeDasharray: '4 4', strokeOpacity: 0.5 }}
                    />
                    <Area
                        type="monotone"
                        dataKey="close"
                        stroke={lineColor}
                        strokeWidth={2}
                        fill={`url(#${gradientId})`}
                        dot={false}
                        activeDot={{
                            r: 5,
                            fill: lineColor,
                            stroke: 'var(--chart-tooltip-bg)',
                            strokeWidth: 2,
                        }}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}

interface TooltipProps {
    active?: boolean;
    payload?: Array<{ payload: { close: number; high: number; low: number; volume: number } }>;
    label?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
    if (!active || !payload || !payload.length) {
        return null;
    }

    const data = payload[0].payload;

    return (
        <div className="card-paper p-3 font-mono text-xs">
            <p className="font-semibold text-theme mb-1.5 tracking-wide">{label}</p>
            <div className="space-y-1">
                <p className="text-theme-secondary flex justify-between gap-4">
                    Close <span className="font-semibold text-theme">${data.close.toFixed(2)}</span>
                </p>
                <p className="text-theme-secondary flex justify-between gap-4">
                    High <span className="font-semibold text-gain">${data.high.toFixed(2)}</span>
                </p>
                <p className="text-theme-secondary flex justify-between gap-4">
                    Low <span className="font-semibold text-loss">${data.low.toFixed(2)}</span>
                </p>
                <p className="text-theme-secondary flex justify-between gap-4">
                    Vol <span className="font-semibold text-theme">{formatVolume(data.volume)}</span>
                </p>
            </div>
        </div>
    );
}

function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
    });
}

function formatVolume(volume: number): string {
    if (volume >= 1_000_000_000) {
        return `${(volume / 1_000_000_000).toFixed(1)}B`;
    }
    if (volume >= 1_000_000) {
        return `${(volume / 1_000_000).toFixed(1)}M`;
    }
    if (volume >= 1_000) {
        return `${(volume / 1_000).toFixed(1)}K`;
    }
    return volume.toString();
}
