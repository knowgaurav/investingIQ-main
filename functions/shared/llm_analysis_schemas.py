"""Pydantic schemas for LLM analysis structured outputs.

These schemas define the expected output format from LLM analysis,
ensuring consistent and type-safe responses.
"""
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class TrendDirection(str, Enum):
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class ValuationStatus(str, Enum):
    OVERVALUED = "overvalued"
    FAIRLY_VALUED = "fairly_valued"
    UNDERVALUED = "undervalued"


class SentimentLevel(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class RecommendationAction(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TechnicalAnalysis(BaseModel):
    """Technical analysis output from LLM."""
    trend: TrendDirection = Field(description="Overall trend direction based on price action")
    trend_strength: float = Field(ge=0, le=1, description="Strength of the trend (0-1)")
    support_levels: List[float] = Field(default_factory=list, description="Key support price levels")
    resistance_levels: List[float] = Field(default_factory=list, description="Key resistance price levels")
    volume_analysis: str = Field(description="Interpretation of volume patterns")
    patterns_identified: List[str] = Field(default_factory=list, description="Chart patterns identified (e.g., head and shoulders, double top)")
    key_observations: List[str] = Field(description="Key technical observations")


class FundamentalAnalysis(BaseModel):
    """Fundamental analysis output from LLM."""
    valuation: ValuationStatus = Field(description="Overall valuation assessment")
    valuation_reasoning: str = Field(description="Reasoning for valuation assessment")
    pe_assessment: str = Field(description="P/E ratio analysis compared to sector/market")
    growth_assessment: str = Field(description="Revenue and earnings growth trajectory")
    financial_health: str = Field(description="Assessment of balance sheet and cash flow")
    competitive_position: str = Field(description="Company's competitive advantages or weaknesses")
    key_metrics: dict = Field(default_factory=dict, description="Key fundamental metrics highlighted")


class SentimentAnalysis(BaseModel):
    """Sentiment analysis output from LLM."""
    overall_sentiment: SentimentLevel = Field(description="Overall market sentiment")
    sentiment_score: float = Field(ge=-1, le=1, description="Sentiment score (-1 to 1)")
    news_summary: str = Field(description="Summary of recent news and events")
    key_events: List[str] = Field(default_factory=list, description="Key events affecting the stock")
    market_mood: str = Field(description="General market mood interpretation")
    catalysts: List[str] = Field(default_factory=list, description="Potential upcoming catalysts")


class PricePrediction(BaseModel):
    """Price prediction output from LLM."""
    current_price: float = Field(description="Current stock price")
    target_7d: float = Field(description="7-day price target")
    target_7d_change_pct: float = Field(description="Expected 7-day change percentage")
    target_30d: float = Field(description="30-day price target")
    target_30d_change_pct: float = Field(description="Expected 30-day change percentage")
    confidence: float = Field(ge=0, le=1, description="Confidence in prediction (0-1)")
    prediction_reasoning: List[str] = Field(description="Reasoning behind price predictions")
    upside_scenario: str = Field(description="Bull case scenario")
    downside_scenario: str = Field(description="Bear case scenario")


class InvestmentRecommendation(BaseModel):
    """Investment recommendation output from LLM."""
    action: RecommendationAction = Field(description="Recommended action")
    confidence: float = Field(ge=0, le=1, description="Confidence in recommendation (0-1)")
    risk_level: RiskLevel = Field(description="Risk level assessment")
    time_horizon: str = Field(description="Recommended holding period")
    entry_price: Optional[float] = Field(default=None, description="Suggested entry price")
    stop_loss: Optional[float] = Field(default=None, description="Suggested stop loss level")
    take_profit: Optional[float] = Field(default=None, description="Suggested take profit level")
    key_reasons: List[str] = Field(description="Key reasons for the recommendation")
    risks: List[str] = Field(description="Key risks to consider")


class LLMAnalysisResult(BaseModel):
    """Complete LLM analysis result combining all analyses."""
    ticker: str = Field(description="Stock ticker symbol")
    analysis_timestamp: str = Field(description="ISO timestamp of analysis")
    technical: TechnicalAnalysis = Field(description="Technical analysis results")
    fundamental: FundamentalAnalysis = Field(description="Fundamental analysis results")
    sentiment: SentimentAnalysis = Field(description="Sentiment analysis results")
    prediction: PricePrediction = Field(description="Price prediction results")
    recommendation: InvestmentRecommendation = Field(description="Investment recommendation")
    disclaimer: str = Field(
        default="This analysis is for informational purposes only and should not be considered financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions.",
        description="Legal disclaimer"
    )


# JSON Schema for OpenAI structured output
LLM_ANALYSIS_JSON_SCHEMA = {
    "name": "stock_analysis",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "analysis_timestamp": {"type": "string"},
            "technical": {
                "type": "object",
                "properties": {
                    "trend": {"type": "string", "enum": ["strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"]},
                    "trend_strength": {"type": "number"},
                    "support_levels": {"type": "array", "items": {"type": "number"}},
                    "resistance_levels": {"type": "array", "items": {"type": "number"}},
                    "volume_analysis": {"type": "string"},
                    "patterns_identified": {"type": "array", "items": {"type": "string"}},
                    "key_observations": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["trend", "trend_strength", "support_levels", "resistance_levels", "volume_analysis", "patterns_identified", "key_observations"],
                "additionalProperties": False
            },
            "fundamental": {
                "type": "object",
                "properties": {
                    "valuation": {"type": "string", "enum": ["overvalued", "fairly_valued", "undervalued"]},
                    "valuation_reasoning": {"type": "string"},
                    "pe_assessment": {"type": "string"},
                    "growth_assessment": {"type": "string"},
                    "financial_health": {"type": "string"},
                    "competitive_position": {"type": "string"},
                    "key_metrics": {"type": "object", "additionalProperties": True}
                },
                "required": ["valuation", "valuation_reasoning", "pe_assessment", "growth_assessment", "financial_health", "competitive_position", "key_metrics"],
                "additionalProperties": False
            },
            "sentiment": {
                "type": "object",
                "properties": {
                    "overall_sentiment": {"type": "string", "enum": ["very_positive", "positive", "neutral", "negative", "very_negative"]},
                    "sentiment_score": {"type": "number"},
                    "news_summary": {"type": "string"},
                    "key_events": {"type": "array", "items": {"type": "string"}},
                    "market_mood": {"type": "string"},
                    "catalysts": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["overall_sentiment", "sentiment_score", "news_summary", "key_events", "market_mood", "catalysts"],
                "additionalProperties": False
            },
            "prediction": {
                "type": "object",
                "properties": {
                    "current_price": {"type": "number"},
                    "target_7d": {"type": "number"},
                    "target_7d_change_pct": {"type": "number"},
                    "target_30d": {"type": "number"},
                    "target_30d_change_pct": {"type": "number"},
                    "confidence": {"type": "number"},
                    "prediction_reasoning": {"type": "array", "items": {"type": "string"}},
                    "upside_scenario": {"type": "string"},
                    "downside_scenario": {"type": "string"}
                },
                "required": ["current_price", "target_7d", "target_7d_change_pct", "target_30d", "target_30d_change_pct", "confidence", "prediction_reasoning", "upside_scenario", "downside_scenario"],
                "additionalProperties": False
            },
            "recommendation": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["strong_buy", "buy", "hold", "sell", "strong_sell"]},
                    "confidence": {"type": "number"},
                    "risk_level": {"type": "string", "enum": ["low", "moderate", "high", "very_high"]},
                    "time_horizon": {"type": "string"},
                    "entry_price": {"type": ["number", "null"]},
                    "stop_loss": {"type": ["number", "null"]},
                    "take_profit": {"type": ["number", "null"]},
                    "key_reasons": {"type": "array", "items": {"type": "string"}},
                    "risks": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["action", "confidence", "risk_level", "time_horizon", "entry_price", "stop_loss", "take_profit", "key_reasons", "risks"],
                "additionalProperties": False
            },
            "disclaimer": {"type": "string"}
        },
        "required": ["ticker", "analysis_timestamp", "technical", "fundamental", "sentiment", "prediction", "recommendation", "disclaimer"],
        "additionalProperties": False
    }
}
