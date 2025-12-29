"""FastAPI application entry point."""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import health, stocks, analysis, chat
from app.api.websocket import analysis_websocket_handler
from app.api.middleware import RateLimitMiddleware, parse_rate_limit

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="LLM-powered financial analysis platform",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
calls, period = parse_rate_limit(settings.rate_limit)
app.add_middleware(RateLimitMiddleware, calls=calls, period=period)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(stocks.router, prefix="/api", tags=["stocks"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "status": "running"
    }
