"""Server-Sent Events endpoints for real-time updates."""
import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.sse_service import get_sse_manager, TaskUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


class ProgressCallback(BaseModel):
    """Progress update from Azure Functions."""
    task_id: str
    progress: int
    current_step: str
    status: str = "processing"
    ticker: str = ""
    report_id: str = ""
    error: str = ""
    data: dict = {}  # Analysis results (stock_data, sentiment, summary, insights)


@router.get("/events/{task_id}")
async def sse_events(task_id: str, request: Request):
    """
    SSE endpoint for real-time task progress updates.
    
    Frontend connects here to receive progress updates pushed from Azure Functions.
    """
    manager = get_sse_manager()
    queue = await manager.connect(task_id)
    
    async def event_generator():
        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'task_id': task_id})}\n\n"
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for update with timeout
                    update: TaskUpdate = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    data = {
                        "task_id": update.task_id,
                        "progress": update.progress,
                        "current_step": update.current_step,
                        "status": update.status,
                        "ticker": update.ticker,
                    }
                    
                    if update.report_id:
                        data["report_id"] = update.report_id
                    if update.error:
                        data["error"] = update.error
                    if update.data:
                        data["data"] = update.data
                    
                    yield f"event: progress\ndata: {json.dumps(data)}\n\n"
                    
                    # Close connection if task completed or failed
                    if update.status in ("completed", "failed"):
                        yield f"event: done\ndata: {json.dumps({'status': update.status})}\n\n"
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"event: ping\ndata: {json.dumps({'type': 'keepalive'})}\n\n"
                    
        finally:
            await manager.disconnect(task_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/callback/progress")
async def progress_callback(payload: ProgressCallback):
    """
    Callback endpoint for Azure Functions to POST progress updates.
    
    Azure Functions call this endpoint to push updates to connected SSE clients.
    """
    manager = get_sse_manager()
    
    update = TaskUpdate(
        task_id=payload.task_id,
        progress=payload.progress,
        current_step=payload.current_step,
        status=payload.status,
        ticker=payload.ticker,
        report_id=payload.report_id,
        error=payload.error,
        data=payload.data,
    )
    
    await manager.send_update(update)
    
    return {"status": "ok", "connections": manager.get_connection_count(payload.task_id)}
