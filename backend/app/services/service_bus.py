"""Azure Service Bus client for InvestingIQ."""
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient as AsyncServiceBusClient

from app.config import get_settings

logger = logging.getLogger(__name__)


class ServiceBusService:
    """Service for Azure Service Bus operations."""
    
    # Queue names
    QUEUE_DATA = "data-queue"
    QUEUE_ML = "ml-queue"
    QUEUE_LLM = "llm-queue"
    QUEUE_EMBED = "embed-queue"
    QUEUE_AGGREGATE = "aggregate-queue"
    QUEUE_DEAD_LETTER = "dead-letter-queue"
    
    def __init__(self):
        """Initialize Service Bus client."""
        settings = get_settings()
        self._connection_string = settings.azure_servicebus_connection_string
        self._client: Optional[ServiceBusClient] = None
    
    def _get_client(self) -> ServiceBusClient:
        """Get or create Service Bus client."""
        if self._client is None:
            self._client = ServiceBusClient.from_connection_string(
                self._connection_string
            )
        return self._client
    
    def send_message(
        self,
        queue_name: str,
        message_body: Dict[str, Any],
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        scheduled_enqueue_time: Optional[datetime] = None
    ) -> str:
        """
        Send a message to a Service Bus queue.
        
        Args:
            queue_name: Name of the queue
            message_body: Message payload as dict
            session_id: Optional session ID for ordered processing
            correlation_id: Optional correlation ID for tracking
            scheduled_enqueue_time: Optional scheduled delivery time
            
        Returns:
            Message ID
        """
        try:
            client = self._get_client()
            
            with client.get_queue_sender(queue_name) as sender:
                message = ServiceBusMessage(
                    body=json.dumps(message_body),
                    content_type="application/json",
                    session_id=session_id,
                    correlation_id=correlation_id,
                )
                
                if scheduled_enqueue_time:
                    message.scheduled_enqueue_time_utc = scheduled_enqueue_time
                
                sender.send_messages(message)
                
                logger.info(f"Sent message to {queue_name}: {correlation_id}")
                return message.message_id or correlation_id or "unknown"
                
        except Exception as e:
            logger.error(f"Failed to send message to {queue_name}: {e}")
            raise
    
    def send_batch(
        self,
        queue_name: str,
        messages: list[Dict[str, Any]],
        correlation_id: Optional[str] = None
    ) -> int:
        """
        Send a batch of messages to a queue.
        
        Args:
            queue_name: Name of the queue
            messages: List of message payloads
            correlation_id: Optional correlation ID for all messages
            
        Returns:
            Number of messages sent
        """
        try:
            client = self._get_client()
            
            with client.get_queue_sender(queue_name) as sender:
                batch = sender.create_message_batch()
                
                for msg_body in messages:
                    message = ServiceBusMessage(
                        body=json.dumps(msg_body),
                        content_type="application/json",
                        correlation_id=correlation_id,
                    )
                    batch.add_message(message)
                
                sender.send_messages(batch)
                
                logger.info(f"Sent {len(messages)} messages to {queue_name}")
                return len(messages)
                
        except Exception as e:
            logger.error(f"Failed to send batch to {queue_name}: {e}")
            raise
    
    def close(self):
        """Close the Service Bus client."""
        if self._client:
            self._client.close()
            self._client = None


class AnalysisOrchestrator:
    """Orchestrate stock analysis workflow using Service Bus."""
    
    def __init__(self, service_bus: ServiceBusService):
        self._service_bus = service_bus
    
    def start_analysis(
        self, 
        ticker: str, 
        task_id: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Start the analysis workflow by sending messages to queues.
        
        The workflow:
        1. Send fetch_stock_data and fetch_news to data-queue (parallel)
        2. ML functions run prediction/technical/sentiment (always)
        3. If llm_config provided, LLM functions run sentiment/summary/insights
        4. Aggregate function combines results and saves report
        
        Args:
            ticker: Stock ticker symbol
            task_id: UUID for tracking the analysis task
            llm_config: Optional LLM configuration (provider, api_key, model)
            
        Returns:
            Dict with task_id and status
        """
        base_payload = {
            "task_id": task_id,
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat(),
            "llm_config": llm_config,
        }
        
        # Send parallel data fetch tasks
        stock_message = {**base_payload, "task_type": "fetch_stock_data"}
        news_message = {**base_payload, "task_type": "fetch_news"}
        
        self._service_bus.send_message(
            queue_name=ServiceBusService.QUEUE_DATA,
            message_body=stock_message,
            correlation_id=task_id,
        )
        
        self._service_bus.send_message(
            queue_name=ServiceBusService.QUEUE_DATA,
            message_body=news_message,
            correlation_id=task_id,
        )
        
        logger.info(
            f"Started analysis for {ticker}, task_id: {task_id}, "
            f"llm_enabled: {llm_config is not None}"
        )
        
        return {
            "task_id": task_id,
            "ticker": ticker,
            "status": "started",
            "llm_enabled": llm_config is not None,
        }
    
    def send_to_llm_queue(
        self,
        task_id: str,
        ticker: str,
        task_type: str,
        data: Dict[str, Any]
    ):
        """Send a task to the LLM processing queue."""
        message = {
            "task_type": task_type,
            "task_id": task_id,
            "ticker": ticker,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self._service_bus.send_message(
            queue_name=ServiceBusService.QUEUE_LLM,
            message_body=message,
            correlation_id=task_id,
        )
    
    def send_to_embed_queue(
        self,
        task_id: str,
        ticker: str,
        stock_data: Dict[str, Any],
        news_articles: list
    ):
        """Send documents to embedding queue."""
        message = {
            "task_type": "embed_documents",
            "task_id": task_id,
            "ticker": ticker,
            "stock_data": stock_data,
            "news_articles": news_articles,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self._service_bus.send_message(
            queue_name=ServiceBusService.QUEUE_EMBED,
            message_body=message,
            correlation_id=task_id,
        )
    
    def send_to_aggregate_queue(
        self,
        task_id: str,
        ticker: str,
        result_type: str,
        result_data: Any
    ):
        """Send partial results to aggregate queue."""
        message = {
            "task_type": "aggregate_result",
            "result_type": result_type,
            "task_id": task_id,
            "ticker": ticker,
            "data": result_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self._service_bus.send_message(
            queue_name=ServiceBusService.QUEUE_AGGREGATE,
            message_body=message,
            correlation_id=task_id,
        )


# Singleton instances
_service_bus: Optional[ServiceBusService] = None
_orchestrator: Optional[AnalysisOrchestrator] = None


def get_service_bus() -> ServiceBusService:
    """Get or create Service Bus service singleton."""
    global _service_bus
    if _service_bus is None:
        _service_bus = ServiceBusService()
    return _service_bus


def get_orchestrator() -> AnalysisOrchestrator:
    """Get or create orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AnalysisOrchestrator(get_service_bus())
    return _orchestrator
