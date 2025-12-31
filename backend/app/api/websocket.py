"""WebSocket handlers for real-time updates."""
import asyncio
import json
import logging
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db, AnalysisTask

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for analysis task updates."""
    
    def __init__(self):
        # Map of task_id -> set of connected WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """Accept a new WebSocket connection for a task."""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task {task_id}")
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        """Remove a WebSocket connection."""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")
    
    async def send_update(self, task_id: str, data: dict):
        """Send an update to all connections for a task."""
        if task_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                self.active_connections[task_id].discard(ws)
    
    async def broadcast(self, data: dict):
        """Broadcast a message to all connected clients."""
        for task_id in self.active_connections:
            await self.send_update(task_id, data)


# Global connection manager instance
manager = ConnectionManager()


async def get_task_status(task_id: str, db: Session) -> dict:
    """
    Get the current status of an analysis task from the database.
    
    Args:
        task_id: UUID string of the task
        db: Database session
        
    Returns:
        Dict with task status information
    """
    try:
        task_uuid = UUID(task_id)
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_uuid).first()
        
        if not task:
            return {
                "type": "error",
                "error": "Task not found",
                "task_id": task_id,
            }
        
        return {
            "type": "status_update",
            "task_id": task_id,
            "ticker": task.ticker,
            "status": task.status,
            "progress": task.progress or 0,
            "current_step": task.current_step,
            "error_message": task.error_message,
            "report_id": str(task.report_id) if task.report_id else None,
        }
    except ValueError:
        return {
            "type": "error",
            "error": "Invalid task ID format",
            "task_id": task_id,
        }


async def analysis_websocket_handler(
    websocket: WebSocket,
    task_id: str,
):
    """
    WebSocket endpoint for real-time analysis task progress updates.
    
    This handler:
    1. Accepts the WebSocket connection
    2. Sends initial task status
    3. Polls for updates and sends them to the client
    4. Handles disconnection gracefully
    
    Args:
        websocket: The WebSocket connection
        task_id: UUID of the analysis task to monitor
    """
    await manager.connect(websocket, task_id)
    
    # Create a new database session for this connection
    from app.models.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Send initial status
        initial_status = await get_task_status(task_id, db)
        await websocket.send_json(initial_status)
        
        # If task is already completed or failed, close connection
        if initial_status.get("status") in ["completed", "failed"]:
            await websocket.send_json({
                "type": "connection_closing",
                "reason": f"Task already {initial_status.get('status')}",
            })
            return
        
        # Poll for updates
        poll_interval = 1.0  # seconds
        last_status = initial_status
        
        while True:
            try:
                # Check for incoming messages (allows client to send commands)
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=poll_interval
                    )
                    
                    # Handle client messages
                    try:
                        data = json.loads(message)
                        if data.get("type") == "ping":
                            await websocket.send_json({"type": "pong"})
                        elif data.get("type") == "request_status":
                            current_status = await get_task_status(task_id, db)
                            await websocket.send_json(current_status)
                    except json.JSONDecodeError:
                        pass
                        
                except asyncio.TimeoutError:
                    # No message received, check for status updates
                    pass
                
                # Refresh database session to get latest data
                db.expire_all()
                
                # Get current status
                current_status = await get_task_status(task_id, db)
                
                # Send update if status changed
                if (
                    current_status.get("status") != last_status.get("status") or
                    current_status.get("progress") != last_status.get("progress") or
                    current_status.get("current_step") != last_status.get("current_step")
                ):
                    await websocket.send_json(current_status)
                    last_status = current_status
                
                # Close connection if task is done
                if current_status.get("status") in ["completed", "failed"]:
                    await websocket.send_json({
                        "type": "connection_closing",
                        "reason": f"Task {current_status.get('status')}",
                    })
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"Client disconnected from task {task_id}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e),
            })
        except:
            pass
    finally:
        manager.disconnect(websocket, task_id)
        db.close()


async def notify_task_update(task_id: str, status: dict):
    """
    Notify all connected clients about a task status update.
    
    This function can be called from Celery task callbacks or other
    parts of the application to push updates to connected clients.
    
    Args:
        task_id: UUID string of the task
        status: Dict with status information
    """
    await manager.send_update(task_id, {
        "type": "status_update",
        **status,
    })
