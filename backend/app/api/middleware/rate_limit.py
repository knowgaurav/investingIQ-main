"""Rate limiting middleware for FastAPI."""
import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    
    For production, consider using Redis-based rate limiting.
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            calls: Number of allowed calls per period
            period: Time period in seconds
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/api/health", "/health", "/"]:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        is_allowed, remaining, reset_time = self._check_rate_limit(client_ip)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - time.time())),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, client_id: str) -> Tuple[bool, int, float]:
        """
        Check if client is within rate limit.
        
        Returns:
            Tuple of (is_allowed, remaining_calls, reset_time)
        """
        current_time = time.time()
        count, window_start = self.clients[client_id]
        
        # Reset window if period has passed
        if current_time - window_start >= self.period:
            self.clients[client_id] = (1, current_time)
            return True, self.calls - 1, current_time + self.period
        
        # Check if within limit
        if count >= self.calls:
            return False, 0, window_start + self.period
        
        # Increment counter
        self.clients[client_id] = (count + 1, window_start)
        return True, self.calls - count - 1, window_start + self.period


def parse_rate_limit(rate_limit_str: str) -> Tuple[int, int]:
    """
    Parse rate limit string like "100/minute" into (calls, period_seconds).
    
    Supported formats:
    - "100/minute"
    - "1000/hour"
    - "10/second"
    """
    parts = rate_limit_str.split("/")
    if len(parts) != 2:
        return 100, 60  # Default
    
    calls = int(parts[0])
    period_str = parts[1].lower()
    
    period_map = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
    }
    
    period = period_map.get(period_str, 60)
    return calls, period
