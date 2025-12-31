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
    const lineColor = isPositive ? '#10B981' : '#EF4444';
    const gradientId = isPositive ? 'colorPositive' : 'colorNegative';

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
                            <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorNegative" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12, fill: '#6B7280' }}
                        tickLine={false}
                        axisLine={{ stroke: '#E5E7EB' }}
                        interval="preserveStartEnd"
                        minTickGap={50}
                    />
                    <YAxis
                        domain={[minPrice - padding, maxPrice + padding]}
                        tick={{ fontSize: 12, fill: '#6B7280' }}
                        tickLine={false}
                        axisLine={{ stroke: '#E5E7EB' }}
                        tickFormatter={(value: number) => `$${value.toFixed(0)}`}
                        width={60}
                    />
                    <Tooltip
                        content={<CustomTooltip />}
                        cursor={{ stroke: '#9CA3AF', strokeDasharray: '5 5' }}
                    />
                    <Area
                        type="monotone"
                        dataKey="close"
                        stroke={lineColor}
                        strokeWidth={2}
                        fill={`url(#${gradientId})`}
                        dot={false}
                        activeDot={{
                            r: 6,
                            fill: lineColor,
                            stroke: '#fff',
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
        <div className="bg-theme-card rounded-lg shadow-lg p-3">
            <p className="text-sm font-medium text-theme mb-1">{label}</p>
            <div className="space-y-1 text-sm">
                <p className="text-theme-secondary">
                    Close: <span className="font-medium text-theme">${data.close.toFixed(2)}</span>
                </p>
                <p className="text-theme-secondary">
                    High: <span className="font-medium text-theme">${data.high.toFixed(2)}</span>
                </p>
                <p className="text-theme-secondary">
                    Low: <span className="font-medium text-theme">${data.low.toFixed(2)}</span>
                </p>
                <p className="text-theme-secondary">
                    Volume: <span className="font-medium text-theme">{formatVolume(data.volume)}</span>
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
