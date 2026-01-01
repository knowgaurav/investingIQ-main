'use client';

interface CompanyInfo {
    name: string;
    sector?: string;
    industry?: string;
    description?: string;
    market_cap?: number;
    pe_ratio?: number;
    peg_ratio?: number;
    book_value?: number;
    dividend_yield?: number;
    eps?: number;
    revenue_ttm?: number;
    profit_margin?: number;
    '52_week_high'?: number;
    '52_week_low'?: number;
    '50_day_ma'?: number;
    '200_day_ma'?: number;
    analyst_target?: number;
}

interface NewsArticle {
    title: string;
    summary?: string;
    url?: string;
    source?: string;
    published_at?: string;
    overall_sentiment_label?: string;
    ticker_sentiment_score?: number;
}

interface EarningsData {
    annual_earnings?: Array<{ fiscal_year: string; eps: number | null }>;
    quarterly_earnings?: Array<{
        fiscal_quarter: string;
        reported_eps: number | null;
        estimated_eps: number | null;
        surprise: number | null;
        surprise_pct: number | null;
    }>;
}

interface CompanyOverviewProps {
    ticker: string;
    companyInfo?: CompanyInfo;
    currentPrice?: number;
    news?: NewsArticle[];
    earnings?: EarningsData;
}

export default function CompanyOverview({ ticker, companyInfo, currentPrice, news, earnings }: CompanyOverviewProps) {
    return (
        <div className="space-y-6">
            {/* Company Profile */}
            <div className="bg-theme-card rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>🏢</span> Company Profile
                </h3>

                {companyInfo ? (
                    <div className="space-y-4">
                        <div className="flex flex-wrap gap-2 mb-4">
                            {companyInfo.sector && (
                                <span className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm font-medium">
                                    {companyInfo.sector}
                                </span>
                            )}
                            {companyInfo.industry && (
                                <span className="px-3 py-1 bg-theme-secondary text-theme-secondary rounded-full text-sm font-medium">
                                    {companyInfo.industry}
                                </span>
                            )}
                        </div>

                        {companyInfo.description && (
                            <p className="text-theme-secondary text-sm leading-relaxed">
                                {companyInfo.description}
                            </p>
                        )}
                    </div>
                ) : (
                    <p className="text-theme-muted">Company information loading...</p>
                )}
            </div>

            {/* Key Metrics */}
            <div className="bg-theme-card rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>📈</span> Key Metrics
                </h3>

                {companyInfo ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <MetricCard label="Market Cap" value={formatLargeNumber(companyInfo.market_cap)} />
                        <MetricCard label="Current Price" value={currentPrice ? `$${currentPrice.toFixed(2)}` : 'N/A'} />
                        <MetricCard label="P/E Ratio" value={companyInfo.pe_ratio?.toFixed(2)} />
                        <MetricCard label="EPS" value={companyInfo.eps ? `$${companyInfo.eps.toFixed(2)}` : undefined} />
                        <MetricCard label="PEG Ratio" value={companyInfo.peg_ratio?.toFixed(2)} />
                        <MetricCard label="Book Value" value={companyInfo.book_value ? `$${companyInfo.book_value.toFixed(2)}` : undefined} />
                        <MetricCard label="Dividend Yield" value={companyInfo.dividend_yield ? `${(companyInfo.dividend_yield * 100).toFixed(2)}%` : undefined} />
                        <MetricCard label="Profit Margin" value={companyInfo.profit_margin ? `${(companyInfo.profit_margin * 100).toFixed(2)}%` : undefined} />
                    </div>
                ) : (
                    <p className="text-theme-muted">Loading metrics...</p>
                )}
            </div>

            {/* Price Ranges & Moving Averages */}
            <div className="bg-theme-card rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                    <span>📊</span> Price Analysis
                </h3>

                {companyInfo ? (
                    <div className="space-y-5">
                        {/* 52-Week Range */}
                        <div className="bg-theme-secondary/50 rounded-lg p-4">
                            <p className="text-sm font-medium text-theme mb-3">52-Week Range</p>
                            <div className="flex items-center gap-3">
                                <div className="text-center min-w-[70px]">
                                    <p className="text-xs text-theme-muted mb-1">Low</p>
                                    <p className="text-sm font-semibold text-red-400">
                                        ${companyInfo['52_week_low']?.toFixed(2) || 'N/A'}
                                    </p>
                                </div>
                                <div className="flex-1 relative py-3">
                                    <div className="h-2 bg-gradient-to-r from-red-500/30 via-gray-500/30 to-green-500/30 rounded-full" />
                                    {companyInfo['52_week_low'] && companyInfo['52_week_high'] && currentPrice && (
                                        <>
                                            <div
                                                className="absolute h-5 w-5 bg-primary rounded-full top-1/2 -translate-y-1/2 border-2 border-white shadow-lg shadow-primary/30 z-10"
                                                style={{
                                                    left: `calc(${Math.min(Math.max(((currentPrice - companyInfo['52_week_low']) / (companyInfo['52_week_high'] - companyInfo['52_week_low'])) * 100, 0), 100)}% - 10px)`,
                                                }}
                                            />
                                            <div
                                                className="absolute -top-5 text-xs font-semibold text-primary whitespace-nowrap"
                                                style={{
                                                    left: `calc(${Math.min(Math.max(((currentPrice - companyInfo['52_week_low']) / (companyInfo['52_week_high'] - companyInfo['52_week_low'])) * 100, 0), 100)}% - 20px)`,
                                                }}
                                            >
                                                ${currentPrice.toFixed(2)}
                                            </div>
                                        </>
                                    )}
                                </div>
                                <div className="text-center min-w-[70px]">
                                    <p className="text-xs text-theme-muted mb-1">High</p>
                                    <p className="text-sm font-semibold text-green-400">
                                        ${companyInfo['52_week_high']?.toFixed(2) || 'N/A'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Moving Averages */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className={`rounded-lg p-4 border ${currentPrice && companyInfo['50_day_ma']
                                    ? currentPrice > companyInfo['50_day_ma']
                                        ? 'bg-green-500/10 border-green-500/30'
                                        : 'bg-red-500/10 border-red-500/30'
                                    : 'bg-theme-secondary border-transparent'
                                }`}>
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-sm text-theme-muted">50-Day MA</p>
                                    {currentPrice && companyInfo['50_day_ma'] && (
                                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${currentPrice > companyInfo['50_day_ma']
                                                ? 'bg-green-500 text-white'
                                                : 'bg-red-500 text-white'
                                            }`}>
                                            {currentPrice > companyInfo['50_day_ma'] ? '↑ Above' : '↓ Below'}
                                        </span>
                                    )}
                                </div>
                                <p className="text-xl font-bold text-theme">
                                    ${companyInfo['50_day_ma']?.toFixed(2) || 'N/A'}
                                </p>
                            </div>
                            <div className={`rounded-lg p-4 border ${currentPrice && companyInfo['200_day_ma']
                                    ? currentPrice > companyInfo['200_day_ma']
                                        ? 'bg-green-500/10 border-green-500/30'
                                        : 'bg-red-500/10 border-red-500/30'
                                    : 'bg-theme-secondary border-transparent'
                                }`}>
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-sm text-theme-muted">200-Day MA</p>
                                    {currentPrice && companyInfo['200_day_ma'] && (
                                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${currentPrice > companyInfo['200_day_ma']
                                                ? 'bg-green-500 text-white'
                                                : 'bg-red-500 text-white'
                                            }`}>
                                            {currentPrice > companyInfo['200_day_ma'] ? '↑ Above' : '↓ Below'}
                                        </span>
                                    )}
                                </div>
                                <p className="text-xl font-bold text-theme">
                                    ${companyInfo['200_day_ma']?.toFixed(2) || 'N/A'}
                                </p>
                            </div>
                        </div>

                        {/* Analyst Target */}
                        {companyInfo.analyst_target && (
                            <div className={`rounded-lg p-4 border ${currentPrice
                                    ? companyInfo.analyst_target > currentPrice
                                        ? 'bg-green-500/10 border-green-500/30'
                                        : 'bg-red-500/10 border-red-500/30'
                                    : 'bg-theme-secondary border-transparent'
                                }`}>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-theme-muted mb-1">Analyst Target Price</p>
                                        <p className="text-xl font-bold text-theme">
                                            ${companyInfo.analyst_target.toFixed(2)}
                                        </p>
                                    </div>
                                    {currentPrice && (
                                        <div className="text-right">
                                            <span className={`text-sm font-bold px-3 py-1 rounded ${companyInfo.analyst_target > currentPrice
                                                    ? 'bg-green-500 text-white'
                                                    : 'bg-red-500 text-white'
                                                }`}>
                                                {companyInfo.analyst_target > currentPrice ? '↑' : '↓'} {Math.abs((companyInfo.analyst_target - currentPrice) / currentPrice * 100).toFixed(1)}%
                                            </span>
                                            <p className={`text-xs mt-1 ${companyInfo.analyst_target > currentPrice ? 'text-green-400' : 'text-red-400'
                                                }`}>
                                                {companyInfo.analyst_target > currentPrice ? 'Upside potential' : 'Downside risk'}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-theme-muted">Loading price data...</p>
                )}
            </div>

            {/* Earnings History */}
            {earnings && (earnings.quarterly_earnings?.length || earnings.annual_earnings?.length) ? (
                <div className="bg-theme-card rounded-xl shadow-md p-6">
                    <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                        <span>💰</span> Earnings History
                    </h3>

                    {earnings.quarterly_earnings && earnings.quarterly_earnings.length > 0 && (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-theme">
                                        <th className="text-left py-2 text-theme-muted font-medium">Quarter</th>
                                        <th className="text-right py-2 text-theme-muted font-medium">Reported EPS</th>
                                        <th className="text-right py-2 text-theme-muted font-medium">Estimated EPS</th>
                                        <th className="text-right py-2 text-theme-muted font-medium">Surprise</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {earnings.quarterly_earnings.slice(0, 4).map((q, i) => (
                                        <tr key={i} className="border-b border-theme">
                                            <td className="py-2 text-theme">{q.fiscal_quarter}</td>
                                            <td className="py-2 text-right text-theme">
                                                {q.reported_eps !== null ? `$${q.reported_eps.toFixed(2)}` : 'N/A'}
                                            </td>
                                            <td className="py-2 text-right text-theme-secondary">
                                                {q.estimated_eps !== null ? `$${q.estimated_eps.toFixed(2)}` : 'N/A'}
                                            </td>
                                            <td className={`py-2 text-right ${q.surprise_pct !== null
                                                ? q.surprise_pct >= 0 ? 'text-green-500' : 'text-red-500'
                                                : 'text-theme-muted'
                                                }`}>
                                                {q.surprise_pct !== null ? `${q.surprise_pct >= 0 ? '+' : ''}${q.surprise_pct.toFixed(1)}%` : 'N/A'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            ) : null}

            {/* Recent News */}
            {news && news.length > 0 && (
                <div className="bg-theme-card rounded-xl shadow-md p-6">
                    <h3 className="text-lg font-semibold text-theme mb-4 flex items-center gap-2">
                        <span>📰</span> Recent News
                    </h3>

                    <div className="space-y-4 max-h-96 overflow-y-auto">
                        {news.slice(0, 10).map((article, i) => (
                            <div key={i} className="border-b border-theme pb-4 last:border-0 last:pb-0">
                                <div className="flex items-start justify-between gap-2">
                                    <div className="flex-1">
                                        {article.url ? (
                                            <a
                                                href={article.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-sm font-medium text-theme hover:text-primary transition-colors"
                                            >
                                                {article.title}
                                            </a>
                                        ) : (
                                            <p className="text-sm font-medium text-theme">{article.title}</p>
                                        )}
                                        {article.summary && (
                                            <p className="text-xs text-theme-secondary mt-1 line-clamp-2">{article.summary}</p>
                                        )}
                                        <div className="flex items-center gap-2 mt-2">
                                            {article.source && (
                                                <span className="text-xs text-theme-muted">{article.source}</span>
                                            )}
                                            {article.published_at && (
                                                <span className="text-xs text-theme-muted">
                                                    {formatDate(article.published_at)}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    {article.overall_sentiment_label && (
                                        <span className={`px-2 py-1 rounded text-xs font-medium shrink-0 ${article.overall_sentiment_label.toLowerCase().includes('bullish') ? 'bg-green-500/20 text-green-500' :
                                            article.overall_sentiment_label.toLowerCase().includes('bearish') ? 'bg-red-500/20 text-red-500' :
                                                'bg-gray-500/20 text-gray-400'
                                            }`}>
                                            {article.overall_sentiment_label}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function MetricCard({ label, value }: { label: string; value?: string }) {
    return (
        <div className="bg-theme-secondary rounded-lg p-4">
            <p className="text-sm text-theme-muted mb-1">{label}</p>
            <p className="text-lg font-semibold text-theme">{value || 'N/A'}</p>
        </div>
    );
}

function formatLargeNumber(num?: number): string {
    if (num === undefined || num === null) return 'N/A';
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
}

function formatDate(dateStr: string): string {
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}
