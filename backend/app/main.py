"""FastAPI application entry point with structured logging and error handling."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import health, stocks, analysis, chat, websocket, llm
from app.api.websocket import analysis_websocket_handler
from app.api.middleware import RateLimitMiddleware, parse_rate_limit
from app.utils.logging import setup_logging, RequestLoggingMiddleware
from app.utils.errors import setup_error_handlers

settings = get_settings()

# Configure structured logging
setup_logging(
    level="DEBUG" if settings.debug else "INFO",
    json_format=not settings.debug,  # Use human-readable format in debug mode
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v2.1.0")
    
    # Set health check start time
    from app.api.routes.health import set_start_time
    set_start_time()
    
    # Initialize cache service
    from app.utils.cache import get_cache_service
    cache = get_cache_service()
    if cache.is_connected:
        logger.info("Cache service initialized (Redis connected)")
    else:
        logger.warning("Cache service running without Redis (caching disabled)")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    description="LLM-powered financial analysis platform with AI-driven insights",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Register error handlers
setup_error_handlers(app)

# Request logging middleware (adds request_id and logs requests)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # Expose request ID to frontend
)

# Rate limiting middleware
calls, period = parse_rate_limit(settings.rate_limit)
app.add_middleware(RateLimitMiddleware, calls=calls, period=period)

# Include routers with versioned API prefix
API_V1_PREFIX = "/api/v1"

# Health routes without version prefix for k8s probes
app.include_router(health.router, prefix="/api", tags=["health"])

# Versioned API routes
app.include_router(stocks.router, prefix=API_V1_PREFIX, tags=["stocks"])
app.include_router(analysis.router, prefix=API_V1_PREFIX, tags=["analysis"])
app.include_router(chat.router, prefix=API_V1_PREFIX, tags=["chat"])
app.include_router(websocket.router, prefix=API_V1_PREFIX, tags=["websocket"])
app.include_router(llm.router, prefix=API_V1_PREFIX, tags=["llm"])

# Also keep /api routes for backward compatibility
app.include_router(stocks.router, prefix="/api", tags=["stocks"], include_in_schema=False)
app.include_router(analysis.router, prefix="/api", tags=["analysis"], include_in_schema=False)
app.include_router(chat.router, prefix="/api", tags=["chat"], include_in_schema=False)


# WebSocket endpoint for real-time analysis updates
@app.websocket("/ws/analysis/{task_id}")
async def websocket_analysis(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time analysis task progress updates.
    
    Connect to this endpoint with a task_id to receive live updates
    about the analysis progress.
    
    Messages sent to client:
    - status_update: Contains task status, progress, and current_step
    - error: Contains error information
    - connection_closing: Sent before closing the connection
    
    Messages accepted from client:
    - {"type": "ping"}: Responds with {"type": "pong"}
    - {"type": "request_status"}: Sends current status immediately
    """
    await analysis_websocket_handler(websocket, task_id)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "2.1.0",
        "status": "running",
        "docs": "/api/docs",
        "health": "/api/health",
    }
