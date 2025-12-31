"""Redis caching service for InvestingIQ.

Provides request caching with TTL for expensive operations like stock data fetching.
"""
import json
import logging
import hashlib
from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from datetime import timedelta

try:
    from typing import ParamSpec
except ImportError:
    # Python < 3.10 compatibility
    ParamSpec = TypeVar  # Fallback - decorators will work but without full typing

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheService:
    """Redis-based caching service with TTL support."""
    
    # Default TTL values in seconds
    TTL_SHORT = 60  # 1 minute
    TTL_MEDIUM = 300  # 5 minutes
    TTL_LONG = 3600  # 1 hour
    TTL_DAY = 86400  # 24 hours
    
    def __init__(self):
        """Initialize Redis connection."""
        settings = get_settings()
        self._redis: Optional[redis.Redis] = None
        self._redis_url = f"redis://{settings.redis_host}:{settings.redis_port}"
        self._connected = False
        self._connect()
    
    def _connect(self) -> bool:
        """Establish Redis connection."""
        try:
            self._redis = redis.Redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Test connection
            self._redis.ping()
            self._connected = True
            logger.info("Redis cache connected successfully")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self._connected = False
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is available."""
        if not self._connected or not self._redis:
            return False
        try:
            self._redis.ping()
            return True
        except redis.ConnectionError:
            self._connected = False
            return False
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"investingiq:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_connected:
            return None
        try:
            value = self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM) -> bool:
        """Set value in cache with TTL."""
        if not self.is_connected:
            return False
        try:
            serialized = json.dumps(value, default=str)
            self._redis.setex(key, ttl, serialized)
            return True
        except (redis.RedisError, TypeError) as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self.is_connected:
            return False
        try:
            self._redis.delete(key)
            return True
        except redis.RedisError as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all keys with a given prefix."""
        if not self.is_connected:
            return 0
        try:
            pattern = f"investingiq:{prefix}:*"
            keys = self._redis.keys(pattern)
            if keys:
                return self._redis.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.warning(f"Cache invalidate error: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.is_connected:
            return {"status": "disconnected"}
        try:
            info = self._redis.info("stats")
            return {
                "status": "connected",
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "keys": self._redis.dbsize(),
            }
        except redis.RedisError:
            return {"status": "error"}


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(
    prefix: str,
    ttl: int = CacheService.TTL_MEDIUM,
    skip_cache_on_error: bool = True
):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix (e.g., "stock_data")
        ttl: Time-to-live in seconds
        skip_cache_on_error: If True, don't cache error results
    
    Usage:
        @cached("stock_data", ttl=300)
        def fetch_stock_data(ticker: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Generate cache key
            cache_key = cache._make_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result
            
            logger.debug(f"Cache MISS: {cache_key}")
            
            # Call the actual function
            result = func(*args, **kwargs)
            
            # Cache the result (unless it's an error)
            if skip_cache_on_error and isinstance(result, dict) and result.get("status") == "error":
                return result
            
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def cached_async(
    prefix: str,
    ttl: int = CacheService.TTL_MEDIUM,
    skip_cache_on_error: bool = True
):
    """
    Async version of cached decorator.
    
    Usage:
        @cached_async("stock_data", ttl=300)
        async def fetch_stock_data(ticker: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Generate cache key
            cache_key = cache._make_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result
            
            logger.debug(f"Cache MISS: {cache_key}")
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Cache the result
            if skip_cache_on_error and isinstance(result, dict) and result.get("status") == "error":
                return result
            
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
