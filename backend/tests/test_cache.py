"""Tests for cache service."""
import pytest
import json
from unittest.mock import MagicMock, patch

from app.utils.cache import CacheService, cached


class TestCacheService:
    """Tests for CacheService class."""
    
    def test_make_key_generates_consistent_keys(self):
        """Test that make_key generates consistent cache keys."""
        # Create a cache service instance directly with mocked redis
        with patch("app.utils.cache.redis.Redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client
            
            cache = CacheService()
            
            key1 = cache._make_key("test", "arg1", "arg2")
            key2 = cache._make_key("test", "arg1", "arg2")
            key3 = cache._make_key("test", "arg1", "arg3")
            
            assert key1 == key2  # Same args should produce same key
            assert key1 != key3  # Different args should produce different key
            assert key1.startswith("investingiq:test:")
    
    def test_cache_service_handles_connection_failure(self):
        """Test cache service handles connection failure gracefully."""
        with patch("app.utils.cache.redis.Redis.from_url") as mock_redis:
            # Simulate connection failure
            mock_client = MagicMock()
            mock_client.ping.side_effect = Exception("Connection refused")
            mock_redis.return_value = mock_client
            
            cache = CacheService()
            
            # Should be disconnected
            assert cache._connected is False
    
    def test_get_returns_none_when_not_connected(self):
        """Test that get returns None when not connected."""
        with patch("app.utils.cache.redis.Redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.side_effect = Exception("Connection refused")
            mock_redis.return_value = mock_client
            
            cache = CacheService()
            result = cache.get("any_key")
            
            assert result is None
    
    def test_set_returns_false_when_not_connected(self):
        """Test that set returns False when not connected."""
        with patch("app.utils.cache.redis.Redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.side_effect = Exception("Connection refused")
            mock_redis.return_value = mock_client
            
            cache = CacheService()
            result = cache.set("any_key", {"data": "test"})
            
            assert result is False
    
    def test_get_returns_cached_value(self):
        """Test that get returns cached value when connected."""
        with patch("app.utils.cache.redis.Redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.get.return_value = json.dumps({"result": "cached"})
            mock_redis.return_value = mock_client
            
            cache = CacheService()
            result = cache.get("test_key")
            
            assert result == {"result": "cached"}
    
    def test_set_stores_value(self):
        """Test that set stores value when connected."""
        with patch("app.utils.cache.redis.Redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client
            
            cache = CacheService()
            result = cache.set("test_key", {"data": "value"}, ttl=300)
            
            assert result is True
            mock_client.setex.assert_called_once()


class TestCachedDecorator:
    """Tests for the cached decorator."""
    
    def test_cached_decorator_returns_function_result(self):
        """Test that cached decorator returns the function result."""
        @cached("test", ttl=60)
        def my_function(arg: str) -> dict:
            return {"result": arg}
        
        with patch("app.utils.cache.get_cache_service") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get.return_value = None  # Cache miss
            mock_cache._make_key.return_value = "test_key"
            mock_get_cache.return_value = mock_cache
            
            result = my_function("hello")
            
            assert result == {"result": "hello"}
    
    def test_cached_returns_cached_value_on_hit(self):
        """Test that cached decorator returns cached value on hit."""
        @cached("test", ttl=60)
        def my_function(arg: str) -> dict:
            return {"result": arg}
        
        with patch("app.utils.cache.get_cache_service") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get.return_value = {"result": "cached"}
            mock_cache._make_key.return_value = "test_key"
            mock_get_cache.return_value = mock_cache
            
            result = my_function("hello")
            
            # Should return cached value, not function result
            assert result == {"result": "cached"}
    
    def test_cached_skips_caching_error_results(self):
        """Test that cached decorator doesn't cache error results."""
        @cached("test", ttl=60, skip_cache_on_error=True)
        def failing_function() -> dict:
            return {"status": "error", "message": "Something went wrong"}
        
        with patch("app.utils.cache.get_cache_service") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get.return_value = None
            mock_cache._make_key.return_value = "test_key"
            mock_get_cache.return_value = mock_cache
            
            result = failing_function()
            
            assert result["status"] == "error"
            # set should not be called for error results
            mock_cache.set.assert_not_called()
