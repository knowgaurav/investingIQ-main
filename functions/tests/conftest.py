"""Shared fixtures for functions tests."""
import pytest
from unittest.mock import MagicMock, patch
import json


class MockRedis:
    """In-memory mock Redis client for testing."""
    
    def __init__(self):
        self._data = {}
    
    def get(self, key: str):
        return self._data.get(key)
    
    def setex(self, key: str, ttl: int, value: str):
        self._data[key] = value
        return True
    
    def delete(self, key: str):
        self._data.pop(key, None)
        return True
    
    def incr(self, key: str):
        val = int(self._data.get(key, 0)) + 1
        self._data[key] = str(val)
        return val


@pytest.fixture
def mock_redis():
    """Provide a fresh MockRedis instance."""
    return MockRedis()


@pytest.fixture
def mock_redis_client(mock_redis):
    """Patch Redis connections to use MockRedis."""
    with patch('shared.cache.redis.Redis') as mock_cls:
        mock_cls.return_value = mock_redis
        with patch('shared.cache.redis.ConnectionPool.from_url'):
            yield mock_redis


@pytest.fixture
def mock_stock_data():
    """Sample stock data for testing."""
    return {
        "ticker": "AAPL",
        "price_history": [
            {"date": "2024-01-01", "open": 150.0, "high": 155.0, "low": 148.0, "close": 152.0, "volume": 1000000},
            {"date": "2024-01-02", "open": 152.0, "high": 158.0, "low": 151.0, "close": 156.0, "volume": 1200000},
        ],
        "current_price": 156.0,
        "company_info": {
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 3000000000000,
            "pe_ratio": 28.5,
        }
    }


@pytest.fixture
def mock_llm_response():
    """Sample LLM analysis response for testing."""
    return {
        "success": True,
        "analysis": {
            "ticker": "AAPL",
            "technical": {"trend": "bullish", "support": 145.0, "resistance": 165.0},
            "fundamental": {"rating": "buy", "fair_value": 180.0},
            "sentiment": {"score": 0.7, "label": "positive"},
            "prediction": {"target": 160.0, "confidence": 0.75},
            "recommendation": "Buy"
        }
    }
