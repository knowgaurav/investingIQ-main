"""Mock LLM clients for testing."""
from unittest.mock import MagicMock
import json


MOCK_ANALYSIS_JSON = json.dumps({
    "technical": {"trend": "bullish", "support": 145.0, "resistance": 165.0},
    "fundamental": {"rating": "buy", "fair_value": 180.0},
    "sentiment": {"score": 0.7, "label": "positive"},
    "prediction": {"target": 160.0, "confidence": 0.75},
    "recommendation": "Hold"
})

MOCK_SENTIMENT_JSON = json.dumps({
    "results": [
        {"headline": "Apple reports record earnings", "sentiment": "bullish", "confidence": 0.9, "reasoning": "Strong financials"},
        {"headline": "Tech sector faces headwinds", "sentiment": "bearish", "confidence": 0.6, "reasoning": "Market concerns"}
    ]
})


def create_mock_openai_client():
    """Create a mock OpenAI-compatible client.
    
    Returns a MagicMock that simulates ChatOpenAI behavior.
    """
    mock_client = MagicMock()
    
    # Mock response object
    mock_response = MagicMock()
    mock_response.content = MOCK_ANALYSIS_JSON
    
    # Mock invoke method
    mock_client.invoke.return_value = mock_response
    
    return mock_client


def create_mock_anthropic_client():
    """Create a mock Anthropic client.
    
    Returns a MagicMock that simulates ChatAnthropic behavior.
    """
    mock_client = MagicMock()
    
    # Mock response object
    mock_response = MagicMock()
    mock_response.content = MOCK_ANALYSIS_JSON
    
    # Mock invoke method
    mock_client.invoke.return_value = mock_response
    
    return mock_client


def create_mock_llm_provider(response_content=None):
    """Create a mock LLM provider instance.
    
    Args:
        response_content: Custom response content (uses default if None)
    
    Returns a MagicMock that simulates BaseLLMProvider behavior.
    """
    mock_provider = MagicMock()
    
    content = response_content or MOCK_ANALYSIS_JSON
    
    # Mock sentiment analysis
    mock_provider.analyze_sentiment.return_value = {
        "overall_score": 0.5,
        "breakdown": {"positive": 1, "negative": 1, "neutral": 0},
        "details": json.loads(MOCK_SENTIMENT_JSON)["results"]
    }
    
    # Mock summary generation
    mock_provider.generate_summary.return_value = "Apple Inc. continues to show strong performance with record earnings."
    
    # Mock insights generation
    mock_provider.generate_insights.return_value = "Based on current data, AAPL shows bullish momentum. This is not financial advice."
    
    return mock_provider
