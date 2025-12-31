"""Celery application configuration with multiple queues."""
from celery import Celery
from kombu import Queue
import os

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "investingiq",
    broker=REDIS_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.data_tasks",
        "app.tasks.llm_tasks",
        "app.tasks.embed_tasks",
        "app.tasks.aggregate_tasks",
    ]
)

# Queue definitions for parallel processing
celery_app.conf.task_queues = (
    Queue("data_queue", routing_key="data.#"),
    Queue("llm_queue", routing_key="llm.#"),
    Queue("embed_queue", routing_key="embed.#"),
    Queue("aggregate_queue", routing_key="aggregate.#"),
    Queue("dead_letter", routing_key="dlq.#"),
)

# Default queue
celery_app.conf.task_default_queue = "data_queue"

# Task routing - route tasks to specific queues
celery_app.conf.task_routes = {
    "app.tasks.data_tasks.*": {"queue": "data_queue"},
    "app.tasks.llm_tasks.*": {"queue": "llm_queue"},
    "app.tasks.embed_tasks.*": {"queue": "embed_queue"},
    "app.tasks.aggregate_tasks.*": {"queue": "aggregate_queue"},
}

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task tracking
    task_track_started=True,
    
    # Timeouts
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Soft limit for graceful shutdown
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Fair task distribution
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=3,
)


def handle_task_failure(self, exc, task_id, args, kwargs, einfo):
    """Route failed tasks to dead letter queue after max retries."""
    from app.tasks.aggregate_tasks import dead_letter_task
    
    if self.request.retries >= self.max_retries:
        dead_letter_task.apply_async(
            args=[task_id, str(exc), args, kwargs],
            queue="dead_letter"
        )


# Apply failure handler to all tasks
celery_app.conf.task_annotations = {
    "*": {
        "on_failure": handle_task_failure,
    }
}
