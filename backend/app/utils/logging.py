"""Structured JSON logging configuration for InvestingIQ.

Provides consistent, machine-parseable log output for observability.
"""
import json
import logging
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""
    
    def __init__(self, include_timestamp: bool = True, include_level: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        log_data = {
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        if self.include_level:
            log_data["level"] = record.levelname
        
        # Add location info for errors
        if record.levelno >= logging.ERROR:
            log_data["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[0] else None,
            }
        
        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "taskName",
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure application logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON formatting for logs
        log_file: Optional file path for log output
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("mlflow").setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response details."""
        # Generate request ID
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Get request details
        request_log = {
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        
        logger = logging.getLogger("request")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            log_data = {
                **request_log,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
            
            # Log level based on status code
            if response.status_code >= 500:
                logger.error("Request completed with error", extra=log_data)
            elif response.status_code >= 400:
                logger.warning("Request completed with client error", extra=log_data)
            else:
                logger.info("Request completed", extra=log_data)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {e}",
                extra={
                    **request_log,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise


class PerformanceLogger:
    """Context manager for logging operation performance."""
    
    def __init__(self, operation: str, logger_name: str = "performance", **extra):
        self.operation = operation
        self.logger = logging.getLogger(logger_name)
        self.extra = extra
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting: {self.operation}", extra=self.extra)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        log_data = {
            "operation": self.operation,
            "duration_ms": round(duration_ms, 2),
            **self.extra,
        }
        
        if exc_type:
            log_data["error"] = str(exc_val)
            self.logger.error(f"Failed: {self.operation}", extra=log_data)
        else:
            self.logger.info(f"Completed: {self.operation}", extra=log_data)
        
        return False  # Don't suppress exceptions


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    request_id: Optional[str] = None,
    **extra
) -> None:
    """Log a message with optional context."""
    if request_id:
        extra["request_id"] = request_id
    logger.log(level, message, extra=extra)
