#!/bin/bash
# Stop all Celery workers

echo "Stopping all Celery workers..."

# Kill all celery workers
pkill -f "celery.*worker" || true

# Remove PID files
rm -f /tmp/data_worker_*.pid
rm -f /tmp/llm_worker_*.pid
rm -f /tmp/embed_worker_*.pid
rm -f /tmp/aggregator.pid
rm -f /tmp/dlq_processor.pid

echo "All workers stopped."
