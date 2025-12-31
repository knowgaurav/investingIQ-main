"""Utility modules for InvestingIQ backend."""
from app.utils.cache import CacheService, get_cache_service, cached, cached_async
from app.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    get_circuit,
    circuit_protected,
    get_all_circuit_stats,
)
from app.utils.errors import (
    AppError,
    ErrorCode,
    ErrorResponse,
    ValidationError,
    NotFoundError,
    TickerNotFoundError,
    ExternalServiceError,
    LLMError,
    DatabaseError,
)
from app.utils.logging import (
    setup_logging,
    RequestLoggingMiddleware,
    PerformanceLogger,
    JSONFormatter,
)

__all__ = [
    # Cache
    "CacheService",
    "get_cache_service",
    "cached",
    "cached_async",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitOpenError",
    "get_circuit",
    "circuit_protected",
    "get_all_circuit_stats",
    # Errors
    "AppError",
    "ErrorCode",
    "ErrorResponse",
    "ValidationError",
    "NotFoundError",
    "TickerNotFoundError",
    "ExternalServiceError",
    "LLMError",
    "DatabaseError",
    # Logging
    "setup_logging",
    "RequestLoggingMiddleware",
    "PerformanceLogger",
    "JSONFormatter",
]
