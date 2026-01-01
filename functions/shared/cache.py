"""Redis caching for stock data - persists across analysis requests."""
import json
import logging
from typing import Optional, Any

import redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Singleton Redis client with connection pooling."""
    
    _instance: Optional["RedisClient"] = None
    _pool: Optional[redis.ConnectionPool] = None
    
    # TTL values in seconds
    TTL_STOCK_PRICES = 300     # 5 minutes
    TTL_COMPANY_INFO = 86400   # 24 hours
    TTL_NEWS = 900             # 15 minutes
    TTL_EARNINGS = 86400       # 24 hours
    
    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._pool = redis.ConnectionPool.from_url(
                "redis://localhost:6379/0",
                decode_responses=True,
                max_connections=10,
            )
        return cls._instance
    
    @property
    def client(self) -> redis.Redis:
        return redis.Redis(connection_pool=self._pool)
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.client.get(key)
            if value:
                logger.info(f"Cache HIT: {key}")
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        try:
            self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False


def get_redis_client() -> RedisClient:
    """Get singleton Redis client."""
    return RedisClient()


class StockCache:
    """Stock-specific caching operations."""
    
    def __init__(self, redis_client: RedisClient):
        self._redis = redis_client
    
    def get_prices(self, ticker: str) -> Optional[dict]:
        return self._redis.get(f"stock:prices:{ticker.upper()}")
    
    def set_prices(self, ticker: str, data: dict) -> bool:
        return self._redis.set(f"stock:prices:{ticker.upper()}", data, RedisClient.TTL_STOCK_PRICES)
    
    def get_company_info(self, ticker: str) -> Optional[dict]:
        return self._redis.get(f"stock:company:{ticker.upper()}")
    
    def set_company_info(self, ticker: str, data: dict) -> bool:
        return self._redis.set(f"stock:company:{ticker.upper()}", data, RedisClient.TTL_COMPANY_INFO)
    
    def get_news(self, ticker: str) -> Optional[list]:
        return self._redis.get(f"stock:news:{ticker.upper()}")
    
    def set_news(self, ticker: str, data: list) -> bool:
        return self._redis.set(f"stock:news:{ticker.upper()}", data, RedisClient.TTL_NEWS)
    
    def get_earnings(self, ticker: str) -> Optional[dict]:
        return self._redis.get(f"stock:earnings:{ticker.upper()}")
    
    def set_earnings(self, ticker: str, data: dict) -> bool:
        return self._redis.set(f"stock:earnings:{ticker.upper()}", data, RedisClient.TTL_EARNINGS)


def get_stock_cache() -> StockCache:
    """Get stock cache instance."""
    return StockCache(get_redis_client())
