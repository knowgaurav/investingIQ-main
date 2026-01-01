"""Pydantic schemas for API request/response models."""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# Stock Search
class StockSearchResult(BaseModel):
    """Stock search autocomplete result."""
    ticker: str
    name: str
    exchange: str
    type: str = "stock"


# LLM Configuration
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OHMYGPT = "ohmygpt"
    OPENROUTER = "openrouter"


class LLMConfig(BaseModel):
    """User's LLM provider configuration."""
    provider: LLMProvider
    api_key: str = Field(..., min_length=1)
    model: Optional[str] = None


class LLMVerifyRequest(BaseModel):
    """Request to verify an LLM API key."""
    provider: LLMProvider
    api_key: str = Field(..., min_length=1)
    model: Optional[str] = None


class LLMVerifyResponse(BaseModel):
    """Response from LLM key verification."""
    valid: bool
    error: Optional[str] = None


# ML Analysis Results (Non-LLM)
class PredictionResult(BaseModel):
    """Prophet/ARIMA prediction results."""
    forecast_7d: Optional[float] = None
    forecast_7d_change: Optional[float] = None
    forecast_30d: Optional[float] = None
    forecast_30d_change: Optional[float] = None
    trend: str = "sideways"
    confidence: float = 0.0


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators."""
    rsi: Optional[float] = None
    rsi_signal: str = "neutral"
    macd: Optional[float] = None
    macd_signal: str = "neutral"
    macd_histogram: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    bollinger_position: str = "middle"
    support_levels: List[float] = []
    resistance_levels: List[float] = []
    volume_signal: str = "normal"


class MLSentimentDetail(BaseModel):
    """Single headline sentiment from VADER/TextBlob."""
    headline: str
    score: float
    label: str


class MLSentimentResult(BaseModel):
    """VADER + TextBlob sentiment analysis."""
    overall_score: float = 0.0
    label: str = "neutral"
    positive_pct: float = 0.0
    neutral_pct: float = 0.0
    negative_pct: float = 0.0
    details: List[MLSentimentDetail] = []


class MLAnalysisResult(BaseModel):
    """Combined ML analysis results."""
    prediction: Optional[PredictionResult] = None
    technical: Optional[TechnicalIndicators] = None
    sentiment: Optional[MLSentimentResult] = None


# Analysis
class AnalysisRequest(BaseModel):
    """Request to analyze a stock."""
    ticker: str = Field(..., min_length=1, max_length=10)
    llm_config: Optional[LLMConfig] = None


class AnalysisTaskStatus(BaseModel):
    """Status of an analysis task."""
    task_id: UUID
    ticker: str
    status: str  # pending, processing, completed, failed
    progress: int = 0
    current_step: Optional[str] = None
    error_message: Optional[str] = None


class AnalysisTaskResponse(BaseModel):
    """Response when creating an analysis task."""
    task_id: UUID
    status: str = "pending"
    message: str = "Analysis task created"


class PriceDataPoint(BaseModel):
    """Single price data point."""
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class SentimentResult(BaseModel):
    """Sentiment analysis result for a headline."""
    headline: str
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str


class AnalysisReportResponse(BaseModel):
    """Complete analysis report response."""
    id: UUID
    ticker: str
    company_name: Optional[str]
    analyzed_at: datetime
    price_data: List[PriceDataPoint]
    # ML Analysis (always available)
    ml_analysis: Optional[MLAnalysisResult] = None
    # LLM Analysis (requires API key)
    news_summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_breakdown: Optional[dict] = None
    sentiment_details: Optional[List[SentimentResult]] = None
    ai_insights: Optional[str] = None
    
    class Config:
        from_attributes = True


# Chat
class ChatRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1)
    ticker: str = Field(..., min_length=1, max_length=10)
    conversation_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    """Chat message response."""
    response: str
    sources: List[str] = []
    conversation_id: UUID


class ChatMessageResponse(BaseModel):
    """Single chat message."""
    id: UUID
    role: str
    content: str
    sources: Optional[List[str]] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Error Response
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[dict] = None
    request_id: Optional[str] = None
