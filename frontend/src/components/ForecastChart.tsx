'use client';

import { useMemo } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine,
} from 'recharts';

interface ChartDataPoint {
    day: number;
    date: string;
    combined: number;
    arima: number | null;
    prophet: number | null;
    ets: number | null;
    label: string;
}

interface ForecastChartProps {
    currentPrice: number;
    dailyForecast: number[];
    arimaDaily?: number[] | null;
    prophetDaily?: number[] | null;
    etsDaily?: number[] | null;
}

export default function ForecastChart({
    currentPrice,
    dailyForecast,
    arimaDaily,
    prophetDaily,
    etsDaily,
}: ForecastChartProps) {
    const chartData = useMemo((): ChartDataPoint[] => {
        if (!dailyForecast || dailyForecast.length === 0) return [];

        const today = new Date();
        
        // Add current price as day 0
        const data: ChartDataPoint[] = [
            {
                day: 0,
                date: today.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                combined: currentPrice,
                arima: currentPrice,
                prophet: currentPrice,
                ets: currentPrice,
                label: 'Today',
            },
        ];

        // Add forecast days
        for (let i = 0; i < dailyForecast.length; i++) {
            const forecastDate = new Date(today);
            forecastDate.setDate(today.getDate() + i + 1);
            
            data.push({
                day: i + 1,
                date: forecastDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                combined: dailyForecast[i],
                arima: arimaDaily ? arimaDaily[i] : null,
                prophet: prophetDaily ? prophetDaily[i] : null,
                ets: etsDaily ? etsDaily[i] : null,
                label: i === 6 ? '7 Days' : i === 29 ? '30 Days' : '',
            });
        }

        return data;
    }, [currentPrice, dailyForecast, arimaDaily, prophetDaily, etsDaily]);

    if (chartData.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center text-gray-500">
                No forecast data available
            </div>
        );
    }

    const prices = chartData.map(d => d.combined).filter(Boolean) as number[];
    const priceRange = Math.max(...prices) - Math.min(...prices);
    const padding = Math.max(priceRange * 0.15, 1); // 15% padding or at least $1
    const minPrice = Math.min(...prices) - padding;
    const maxPrice = Math.max(...prices) + padding;

    return (
        <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 11 }}
                        tickLine={false}
                        interval="preserveStartEnd"
                    />
                    <YAxis 
                        domain={[minPrice, maxPrice]}
                        tick={{ fontSize: 11 }}
                        tickFormatter={(value) => `$${value.toFixed(0)}`}
                        width={60}
                    />
                    <Tooltip
                        formatter={(value: number, name: string) => [
                            `$${value.toFixed(2)}`,
                            name === 'combined' ? 'Combined' : 
                            name === 'arima' ? 'ARIMA' : 
                            name === 'prophet' ? 'Prophet' : 'ETS'
                        ]}
                        labelFormatter={(label) => `Date: ${label}`}
                        contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #E5E7EB',
                            borderRadius: '8px',
                            fontSize: '12px',
                        }}
                    />
                    <Legend 
                        verticalAlign="top"
                        height={36}
                        formatter={(value) => 
                            value === 'combined' ? 'Combined Forecast' : 
                            value === 'arima' ? 'ARIMA' : 
                            value === 'prophet' ? 'Prophet' : 'ETS'
                        }
                    />
                    
                    {/* Reference line for current price */}
                    <ReferenceLine 
                        y={currentPrice} 
                        stroke="#9CA3AF" 
                        strokeDasharray="5 5"
                        label={{ value: 'Current', position: 'right', fontSize: 10, fill: '#6B7280' }}
                    />
                    
                    {/* Reference lines for 7-day and 30-day marks */}
                    <ReferenceLine x="7 Days" stroke="#D1D5DB" strokeDasharray="3 3" />
                    
                    {/* Combined forecast line */}
                    <Line
                        type="monotone"
                        dataKey="combined"
                        stroke="#3B82F6"
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6 }}
                    />
                    
                    {/* ARIMA line */}
                    {arimaDaily && (
                        <Line
                            type="monotone"
                            dataKey="arima"
                            stroke="#60A5FA"
                            strokeWidth={1.5}
                            strokeDasharray="5 5"
                            dot={false}
                        />
                    )}
                    
                    {/* Prophet line */}
                    {prophetDaily && (
                        <Line
                            type="monotone"
                            dataKey="prophet"
                            stroke="#A855F7"
                            strokeWidth={1.5}
                            strokeDasharray="5 5"
                            dot={false}
                        />
                    )}
                    
                    {/* ETS line */}
                    {etsDaily && (
                        <Line
                            type="monotone"
                            dataKey="ets"
                            stroke="#10B981"
                            strokeWidth={1.5}
                            strokeDasharray="5 5"
                            dot={false}
                        />
                    )}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
