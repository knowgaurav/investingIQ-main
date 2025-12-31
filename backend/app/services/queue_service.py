"""Queue service for InvestingIQ - uses Redis for local dev."""
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import redis

from app.config import get_settings

logger = logging.getLogger(__name__)


class QueueService:
    """Simple Redis-based queue for local development."""
    
    QUEUE_DATA = "data-queue"
    QUEUE_LLM = "llm-queue"
    QUEUE_EMBED = "embed-queue"
    QUEUE_AGGREGATE = "aggregate-queue"
    
    def __init__(self):
        settings = get_settings()
        self._redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
    
    def send_message(
        self,
        queue_name: str,
        message_body: Dict[str, Any],
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Send message to queue."""
        message = {
            "body": message_body,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._redis.rpush(queue_name, json.dumps(message))
        logger.info(f"Sent message to {queue_name}: {correlation_id}")
        return correlation_id or "unknown"
    
    def receive_message(self, queue_name: str, timeout: int = 0) -> Optional[Dict]:
        """Receive message from queue."""
        result = self._redis.blpop(queue_name, timeout=timeout)
        if result:
            return json.loads(result[1])
        return None
    
    def close(self):
        self._redis.close()


class AnalysisOrchestrator:
    """Orchestrate stock analysis workflow."""
    
    def __init__(self, queue_service: QueueService):
        self._queue = queue_service
    
    def start_analysis(self, ticker: str, task_id: str) -> Dict[str, str]:
        """Start analysis workflow."""
        stock_message = {
            "task_type": "fetch_stock_data",
            "task_id": task_id,
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        news_message = {
            "task_type": "fetch_news",
            "task_id": task_id,
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self._queue.send_message(QueueService.QUEUE_DATA, stock_message, task_id)
        self._queue.send_message(QueueService.QUEUE_DATA, news_message, task_id)
        
        logger.info(f"Started analysis for {ticker}, task_id: {task_id}")
        return {"task_id": task_id, "ticker": ticker, "status": "started"}
    
    def send_to_llm_queue(self, task_id: str, ticker: str, task_type: str, data: Dict):
        message = {
            "task_type": task_type,
            "task_id": task_id,
            "ticker": ticker,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._queue.send_message(QueueService.QUEUE_LLM, message, task_id)
    
    def send_to_embed_queue(self, task_id: str, ticker: str, stock_data: Dict, news_articles: list):
        message = {
            "task_type": "embed_documents",
            "task_id": task_id,
            "ticker": ticker,
            "stock_data": stock_data,
            "news_articles": news_articles,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._queue.send_message(QueueService.QUEUE_EMBED, message, task_id)
    
    def send_to_aggregate_queue(self, task_id: str, ticker: str, result_type: str, result_data: Any):
        message = {
            "task_type": "aggregate_result",
            "result_type": result_type,
            "task_id": task_id,
            "ticker": ticker,
            "data": result_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._queue.send_message(QueueService.QUEUE_AGGREGATE, message, task_id)


_queue_service: Optional[QueueService] = None
_orchestrator: Optional[AnalysisOrchestrator] = None


def get_queue_service() -> QueueService:
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService()
    return _queue_service


def get_orchestrator() -> AnalysisOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AnalysisOrchestrator(get_queue_service())
    return _orchestrator
