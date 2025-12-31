"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# Stock Search
class StockSearchResult(BaseModel):
    """Stock search autocomplete result."""
    ticker: str
    name: str
    exchange: str
    type: str = "stock"  # stock, etf, etc.


# Analysis
class AnalysisRequest(BaseModel):
    """Request to analyze a stock."""
    ticker: str = Field(..., min_length=1, max_length=10)


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
    news_summary: Optional[str]
    sentiment_score: Optional[float]
    sentiment_breakdown: Optional[dict]
    sentiment_details: Optional[List[SentimentResult]]
    ai_insights: Optional[str]
    
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
