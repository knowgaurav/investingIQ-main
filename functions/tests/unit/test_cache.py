"""Tests for Redis cache module."""
import pytest
import json
from unittest.mock import patch, MagicMock

from shared.cache import RedisClient, StockCache


class TestRedisClient:
    """Tests for RedisClient operations."""

    def test_get_returns_parsed_json(self):
        """Test get returns parsed JSON data."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"key": "value"}'
        
        with patch.object(RedisClient, '_pool', None):
            with patch.object(RedisClient, '_instance', None):
                with patch('shared.cache.redis.ConnectionPool.from_url'):
                    with patch('shared.cache.redis.Redis', return_value=mock_redis):
                        client = RedisClient()
                        result = client.get("test_key")
        
        assert result == {"key": "value"}

    def test_get_returns_none_for_missing_key(self):
        """Test get returns None when key doesn't exist."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        with patch.object(RedisClient, '_pool', None):
            with patch.object(RedisClient, '_instance', None):
                with patch('shared.cache.redis.ConnectionPool.from_url'):
                    with patch('shared.cache.redis.Redis', return_value=mock_redis):
                        client = RedisClient()
                        result = client.get("missing_key")
        
        assert result is None

    def test_set_stores_json(self):
        """Test set stores JSON-serialized data."""
        mock_redis = MagicMock()
        
        with patch.object(RedisClient, '_pool', None):
            with patch.object(RedisClient, '_instance', None):
                with patch('shared.cache.redis.ConnectionPool.from_url'):
                    with patch('shared.cache.redis.Redis', return_value=mock_redis):
                        client = RedisClient()
                        result = client.set("test_key", {"data": 123}, 300)
        
        assert result is True
        mock_redis.setex.assert_called_once()

    def test_delete_removes_key(self):
        """Test delete removes key from cache."""
        mock_redis = MagicMock()
        
        with patch.object(RedisClient, '_pool', None):
            with patch.object(RedisClient, '_instance', None):
                with patch('shared.cache.redis.ConnectionPool.from_url'):
                    with patch('shared.cache.redis.Redis', return_value=mock_redis):
                        client = RedisClient()
                        result = client.delete("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")


class TestStockCache:
    """Tests for StockCache operations."""

    def test_get_set_prices(self):
        """Test get/set prices operations."""
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = {"price": 150.0}
        mock_redis_client.set.return_value = True
        
        cache = StockCache(mock_redis_client)
        
        # Test set
        result = cache.set_prices("AAPL", {"price": 150.0})
        assert result is True
        mock_redis_client.set.assert_called_with("stock:prices:AAPL", {"price": 150.0}, RedisClient.TTL_STOCK_PRICES)
        
        # Test get
        result = cache.get_prices("aapl")  # lowercase should be uppercased
        assert result == {"price": 150.0}
        mock_redis_client.get.assert_called_with("stock:prices:AAPL")

    def test_get_set_company_info(self):
        """Test get/set company_info operations."""
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = {"name": "Apple Inc."}
        mock_redis_client.set.return_value = True
        
        cache = StockCache(mock_redis_client)
        
        result = cache.set_company_info("AAPL", {"name": "Apple Inc."})
        assert result is True
        
        result = cache.get_company_info("AAPL")
        assert result == {"name": "Apple Inc."}

    def test_get_set_news(self):
        """Test get/set news operations."""
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = [{"title": "News 1"}]
        mock_redis_client.set.return_value = True
        
        cache = StockCache(mock_redis_client)
        
        result = cache.set_news("AAPL", [{"title": "News 1"}])
        assert result is True
        
        result = cache.get_news("AAPL")
        assert result == [{"title": "News 1"}]

    def test_get_set_earnings(self):
        """Test get/set earnings operations."""
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = {"annual": []}
        mock_redis_client.set.return_value = True
        
        cache = StockCache(mock_redis_client)
        
        result = cache.set_earnings("AAPL", {"annual": []})
        assert result is True
        
        result = cache.get_earnings("AAPL")
        assert result == {"annual": []}


# Property-Based Tests
from hypothesis import given, strategies as st, settings


class TestStockCacheRoundTripProperty:
    """Property-based tests for StockCache round-trip.
    
    **Feature: functions-testing-setup, Property 3: StockCache Round-Trip**
    **Validates: Requirements 6.2**
    """

    @settings(max_examples=100)
    @given(
        ticker=st.text(min_size=1, max_size=5, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        price_data=st.fixed_dictionaries({
            "price": st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
            "volume": st.integers(min_value=0, max_value=10**9)
        })
    )
    def test_prices_round_trip(self, ticker, price_data):
        """For any ticker and valid price data, set_prices then get_prices SHALL return equivalent data."""
        stored_data = {}
        
        mock_redis_client = MagicMock()
        mock_redis_client.set.side_effect = lambda k, v, ttl: stored_data.update({k: v}) or True
        mock_redis_client.get.side_effect = lambda k: stored_data.get(k)
        
        cache = StockCache(mock_redis_client)
        cache.set_prices(ticker, price_data)
        result = cache.get_prices(ticker)
        
        assert result == price_data
