"""Server-Sent Events service for real-time updates."""
import asyncio
import logging
from typing import Dict, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TaskUpdate:
    """Progress update for a task."""
    task_id: str
    progress: int
    current_step: str
    status: str
    ticker: str = ""
    report_id: str = ""
    error: str = ""
    data: dict = field(default_factory=dict)  # Analysis results


class SSEManager:
    """Manages SSE connections and broadcasts updates."""
    
    def __init__(self):
        # task_id -> set of asyncio.Queue for each connected client
        self._connections: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, task_id: str) -> asyncio.Queue:
        """Register a new SSE client for a task."""
        queue = asyncio.Queue()
        async with self._lock:
            if task_id not in self._connections:
                self._connections[task_id] = set()
            self._connections[task_id].add(queue)
        logger.info(f"SSE client connected for task {task_id}")
        return queue
    
    async def disconnect(self, task_id: str, queue: asyncio.Queue):
        """Remove an SSE client."""
        async with self._lock:
            if task_id in self._connections:
                self._connections[task_id].discard(queue)
                if not self._connections[task_id]:
                    del self._connections[task_id]
        logger.info(f"SSE client disconnected for task {task_id}")
    
    async def send_update(self, update: TaskUpdate):
        """Send update to all clients watching a task."""
        task_id = update.task_id
        async with self._lock:
            if task_id not in self._connections:
                return
            
            dead_queues = set()
            for queue in self._connections[task_id]:
                try:
                    await queue.put(update)
                except Exception:
                    dead_queues.add(queue)
            
            # Clean up dead connections
            for q in dead_queues:
                self._connections[task_id].discard(q)
    
    def get_connection_count(self, task_id: str) -> int:
        """Get number of connected clients for a task."""
        return len(self._connections.get(task_id, set()))


# Global singleton
_sse_manager = None


def get_sse_manager() -> SSEManager:
    global _sse_manager
    if _sse_manager is None:
        _sse_manager = SSEManager()
    return _sse_manager
