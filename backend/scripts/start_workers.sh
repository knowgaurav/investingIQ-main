#!/bin/bash
# Start all Celery workers for InvestingIQ

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting InvestingIQ Celery Workers...${NC}"

# Change to backend directory
cd "$(dirname "$0")/.."

# Start data workers (high concurrency for I/O bound tasks)
echo -e "${YELLOW}Starting data workers...${NC}"
celery -A app.tasks.celery_app worker -Q data_queue -c 4 -n data_worker_1@%h --detach --pidfile=/tmp/data_worker_1.pid
celery -A app.tasks.celery_app worker -Q data_queue -c 4 -n data_worker_2@%h --detach --pidfile=/tmp/data_worker_2.pid

# Start LLM workers (lower concurrency due to rate limits)
echo -e "${YELLOW}Starting LLM workers...${NC}"
celery -A app.tasks.celery_app worker -Q llm_queue -c 2 -n llm_worker_1@%h --detach --pidfile=/tmp/llm_worker_1.pid
celery -A app.tasks.celery_app worker -Q llm_queue -c 2 -n llm_worker_2@%h --detach --pidfile=/tmp/llm_worker_2.pid
celery -A app.tasks.celery_app worker -Q llm_queue -c 2 -n llm_worker_3@%h --detach --pidfile=/tmp/llm_worker_3.pid

# Start embedding workers
echo -e "${YELLOW}Starting embedding workers...${NC}"
celery -A app.tasks.celery_app worker -Q embed_queue -c 2 -n embed_worker_1@%h --detach --pidfile=/tmp/embed_worker_1.pid
celery -A app.tasks.celery_app worker -Q embed_queue -c 2 -n embed_worker_2@%h --detach --pidfile=/tmp/embed_worker_2.pid

# Start aggregator worker
echo -e "${YELLOW}Starting aggregator worker...${NC}"
celery -A app.tasks.celery_app worker -Q aggregate_queue -c 4 -n aggregator@%h --detach --pidfile=/tmp/aggregator.pid

# Start dead letter queue processor
echo -e "${YELLOW}Starting DLQ processor...${NC}"
celery -A app.tasks.celery_app worker -Q dead_letter -c 1 -n dlq_processor@%h --detach --pidfile=/tmp/dlq_processor.pid

echo -e "${GREEN}All workers started!${NC}"
echo -e "Use 'celery -A app.tasks.celery_app flower' to monitor at http://localhost:5555"
