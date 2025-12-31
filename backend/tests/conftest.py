"""Test configuration and fixtures."""
import pytest
import asyncio
from typing import Generator
from unittest.mock import MagicMock, patch

import redis


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("redis.Redis.from_url") as mock:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return {
        "ticker": "AAPL",
        "company_info": {
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 3000000000000,
        },
        "price_history": [
            {
                "date": "2024-01-01T00:00:00",
                "open": 180.0,
                "high": 185.0,
                "low": 179.0,
                "close": 184.0,
                "volume": 50000000,
            }
        ],
        "current_price": 184.0,
        "status": "success",
        "error": None,
    }


@pytest.fixture
def sample_news_articles():
    """Sample news articles for testing."""
    return [
        {
            "title": "Apple Reports Record Q4 Earnings",
            "description": "Apple Inc. reported record fourth quarter earnings...",
            "url": "https://example.com/news/1",
            "source": "Financial Times",
        },
        {
            "title": "New iPhone Launch Expected",
            "description": "Apple is expected to launch new iPhone models...",
            "url": "https://example.com/news/2",
            "source": "TechCrunch",
        },
    ]


@pytest.fixture
def sample_sentiment_result():
    """Sample sentiment analysis result."""
    return {
        "sentiment_breakdown": {
            "bullish": 3,
            "bearish": 1,
            "neutral": 1,
        },
        "details": [
            {
                "headline": "Apple Reports Record Q4 Earnings",
                "sentiment": "BULLISH",
                "confidence": 0.85,
                "reasoning": "Positive earnings report indicates strong performance",
            }
        ],
    }
