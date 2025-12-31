"""Structured error handling for InvestingIQ API.

Provides consistent error responses with error codes and request tracking.
"""
import logging
import traceback
import uuid
from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Application error codes."""
    # General errors (1xxx)
    INTERNAL_ERROR = "E1000"
    VALIDATION_ERROR = "E1001"
    NOT_FOUND = "E1002"
    RATE_LIMITED = "E1003"
    
    # Stock errors (2xxx)
    INVALID_TICKER = "E2000"
    TICKER_NOT_FOUND = "E2001"
    STOCK_DATA_UNAVAILABLE = "E2002"
    
    # Analysis errors (3xxx)
    ANALYSIS_FAILED = "E3000"
    TASK_NOT_FOUND = "E3001"
    ANALYSIS_IN_PROGRESS = "E3002"
    
    # LLM errors (4xxx)
    LLM_UNAVAILABLE = "E4000"
    LLM_RATE_LIMITED = "E4001"
    LLM_RESPONSE_ERROR = "E4002"
    EMBEDDING_FAILED = "E4003"
    
    # External service errors (5xxx)
    EXTERNAL_SERVICE_ERROR = "E5000"
    NEWS_API_ERROR = "E5001"
    YFINANCE_ERROR = "E5002"
    CIRCUIT_OPEN = "E5003"
    
    # Chat errors (6xxx)
    CONVERSATION_NOT_FOUND = "E6000"
    CHAT_ERROR = "E6001"
    
    # Database errors (7xxx)
    DATABASE_ERROR = "E7000"
    DATABASE_CONNECTION_ERROR = "E7001"


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None
    request_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "E2001",
                "message": "Stock ticker 'INVALID' not found",
                "details": {"ticker": "INVALID"},
                "request_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class AppError(Exception):
    """Base application error with error code support."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None,
        original_error: Optional[Exception] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.original_error = original_error
        super().__init__(message)
    
    def to_response(self, request_id: str) -> ErrorResponse:
        """Convert to error response."""
        return ErrorResponse(
            error_code=self.error_code.value,
            message=self.message,
            details=self.details,
            request_id=request_id,
        )


# Specific error classes for common scenarios
class ValidationError(AppError):
    """Validation error."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=400,
            details=details,
        )


class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=f"{resource} '{identifier}' not found",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class TickerNotFoundError(AppError):
    """Stock ticker not found."""
    def __init__(self, ticker: str):
        super().__init__(
            error_code=ErrorCode.TICKER_NOT_FOUND,
            message=f"Stock ticker '{ticker}' not found or invalid",
            status_code=404,
            details={"ticker": ticker},
        )


class ExternalServiceError(AppError):
    """External service failure."""
    def __init__(self, service: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"External service '{service}' error: {message}",
            status_code=502,
            details={"service": service},
            original_error=original_error,
        )


class LLMError(AppError):
    """LLM service error."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.LLM_UNAVAILABLE,
            message=f"LLM service error: {message}",
            status_code=503,
            original_error=original_error,
        )


class CircuitOpenError(AppError):
    """Circuit breaker is open."""
    def __init__(self, circuit_name: str):
        super().__init__(
            error_code=ErrorCode.CIRCUIT_OPEN,
            message=f"Service '{circuit_name}' is temporarily unavailable",
            status_code=503,
            details={"circuit": circuit_name},
        )


class DatabaseError(AppError):
    """Database error."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=f"Database error: {message}",
            status_code=500,
            original_error=original_error,
        )


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions."""
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Log the error
    logger.error(
        f"[{request_id}] {exc.error_code.value}: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code.value,
            "details": exc.details,
            "path": str(request.url),
        }
    )
    
    if exc.original_error:
        logger.debug(f"[{request_id}] Original error: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response(request_id).model_dump(),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Log full traceback for unexpected errors
    logger.error(
        f"[{request_id}] Unexpected error: {exc}",
        extra={"request_id": request_id, "path": str(request.url)},
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR.value,
            message="An unexpected error occurred",
            request_id=request_id,
        ).model_dump(),
    )


def setup_error_handlers(app):
    """Register error handlers with FastAPI app."""
    app.add_exception_handler(AppError, app_error_handler)
    # Don't override HTTPException handler to keep FastAPI's default behavior
