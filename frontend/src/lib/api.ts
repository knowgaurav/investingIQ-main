/**
 * API client for InvestingIQ backend services.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Stock search result from autocomplete.
 */
export interface StockSearchResult {
    ticker: string;
    name: string;
    exchange: string;
}

/**
 * Stock search response.
 */
export interface StockSearchResponse {
    query: string;
    results: StockSearchResult[];
    count: number;
}

/**
 * Analysis task response after requesting analysis.
 */
export interface AnalysisTaskResponse {
    task_id: string;
    status: string;
    message: string;
}

/**
 * Analysis task status.
 */
export interface AnalysisTaskStatus {
    task_id: string;
    ticker: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_step: string | null;
    error_message: string | null;
}

/**
 * Price data point for charts.
 */
export interface PriceDataPoint {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

/**
 * Sentiment result for individual news items (LLM).
 */
export interface SentimentResult {
    headline: string;
    sentiment: string;
    confidence: number;
    reasoning: string;
}

/**
 * ML Prediction result.
 */
export interface MLPrediction {
    forecast_7d: number | null;
    forecast_7d_change: number | null;
    forecast_30d: number | null;
    forecast_30d_change: number | null;
    trend: string;
    confidence: number;
    current_price?: number;
}

/**
 * ML Technical indicators.
 */
export interface MLTechnical {
    rsi: number | null;
    rsi_signal: string;
    macd: number | null;
    macd_signal: string;
    macd_histogram: number | null;
    bollinger_upper: number | null;
    bollinger_middle: number | null;
    bollinger_lower: number | null;
    bollinger_position: string;
    support_levels: number[];
    resistance_levels: number[];
    volume_signal: string;
}

/**
 * ML Sentiment result (VADER/TextBlob).
 */
export interface MLSentiment {
    overall_score: number;
    label: string;
    positive_pct: number;
    neutral_pct: number;
    negative_pct: number;
    details: Array<{ headline: string; score: number; label: string }>;
}

/**
 * Combined ML analysis results.
 */
export interface MLAnalysisResult {
    prediction?: MLPrediction;
    technical?: MLTechnical;
    sentiment?: MLSentiment;
}

/**
 * Company information from Alpha Vantage.
 */
export interface CompanyInfo {
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

/**
 * News article with sentiment from Alpha Vantage.
 */
export interface NewsArticle {
    title: string;
    summary?: string;
    url?: string;
    source?: string;
    published_at?: string;
    overall_sentiment_score?: number;
    overall_sentiment_label?: string;
    ticker_sentiment_score?: number;
    ticker_sentiment_label?: string;
    relevance_score?: number;
}

/**
 * Earnings data from Alpha Vantage.
 */
export interface EarningsData {
    annual_earnings?: Array<{ fiscal_year: string; eps: number | null }>;
    quarterly_earnings?: Array<{
        fiscal_quarter: string;
        reported_eps: number | null;
        estimated_eps: number | null;
        surprise: number | null;
        surprise_pct: number | null;
    }>;
}

/**
 * LLM Configuration.
 */
export interface LLMConfig {
    provider: string;
    api_key: string;
    model?: string;
}

/**
 * Complete analysis report.
 */
export interface AnalysisReport {
    id: string;
    ticker: string;
    company_name: string;
    analyzed_at: string;
    price_data: PriceDataPoint[];
    current_price?: number;
    // Static company data (from Alpha Vantage)
    company_info?: CompanyInfo;
    news?: NewsArticle[];
    earnings?: EarningsData;
    // ML Analysis (always available)
    ml_analysis?: MLAnalysisResult;
    // LLM Analysis (requires API key)
    news_summary: string | null;
    sentiment_score: number | null;
    sentiment_breakdown: {
        positive: number;
        negative: number;
        neutral: number;
    } | null;
    sentiment_details: SentimentResult[] | null;
    ai_insights: string | null;
}

/**
 * Chat request payload.
 */
export interface ChatRequest {
    message: string;
    ticker: string;
    conversation_id?: string;
}

/**
 * Chat response from the API.
 */
export interface ChatResponse {
    response: string;
    sources: string[] | null;
    conversation_id: string;
}

/**
 * API error class.
 */
export class ApiError extends Error {
    constructor(
        message: string,
        public status: number,
        public detail?: string
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

/**
 * Generic fetch wrapper with error handling.
 */
async function fetchApi<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;

    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
            errorData.detail || `HTTP error ${response.status}`,
            response.status,
            errorData.detail
        );
    }

    return response.json();
}

/**
 * Search for stocks by ticker or company name.
 * @param query - Search query string
 * @param limit - Maximum number of results (default: 10)
 */
export async function searchStocks(
    query: string,
    limit: number = 10
): Promise<StockSearchResponse> {
    const params = new URLSearchParams({
        q: query,
        limit: limit.toString(),
    });

    return fetchApi<StockSearchResponse>(`/api/stocks/search?${params}`);
}

/**
 * Request a new stock analysis.
 * @param ticker - Stock ticker symbol
 * @param llmConfig - Optional LLM configuration for AI analysis
 */
export async function requestAnalysis(
    ticker: string,
    llmConfig?: LLMConfig | null
): Promise<AnalysisTaskResponse> {
    const body: Record<string, unknown> = { ticker };
    if (llmConfig) {
        body.llm_config = {
            provider: llmConfig.provider,
            api_key: llmConfig.api_key,
            model: llmConfig.model || null,
        };
    }
    return fetchApi<AnalysisTaskResponse>('/api/analysis/request', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

/**
 * Get the status of an analysis task.
 * @param taskId - UUID of the analysis task
 */
export async function getAnalysisStatus(
    taskId: string
): Promise<AnalysisTaskStatus> {
    return fetchApi<AnalysisTaskStatus>(`/api/analysis/status/${taskId}`);
}

/**
 * Get the analysis report for a ticker.
 * @param ticker - Stock ticker symbol
 */
export async function getAnalysisReport(
    ticker: string
): Promise<AnalysisReport> {
    return fetchApi<AnalysisReport>(`/api/analysis/report/${ticker}`);
}

/**
 * Send a chat message and get an AI response.
 * @param request - Chat request with message, ticker, and optional conversation_id
 */
export async function sendChatMessage(
    request: ChatRequest
): Promise<ChatResponse> {
    return fetchApi<ChatResponse>('/api/chat', {
        method: 'POST',
        body: JSON.stringify(request),
    });
}
