# Design Document: LLM Financial Assistant

## Overview

This design transforms InvestingIQ into a modern, scalable financial analysis platform powered by LLMs. The system uses a microservices-inspired architecture with Next.js frontend, FastAPI backend, Celery task queue, and MLflow for MLOps. Users can analyze any publicly traded stock through an async pipeline that orchestrates data fetching, RAG embedding, sentiment analysis, and AI summarization.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Next.js Frontend                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │Stock Search │  │Chat Interface│  │Analysis View│  │Progress Tracker    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ REST API / WebSocket
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Backend                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │Stock API    │  │Chat API     │  │Analysis API │  │WebSocket Handler   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
          │                │                │                    │
          │                │                │                    │
          ▼                ▼                ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐    ┌──────────────┐
│   yfinance   │  │  OhMyGPT API │  │    Redis     │    │  PostgreSQL  │
│  (Stock Data)│  │   (LLM)      │  │   (Broker)   │    │  (Database)  │
└──────────────┘  └──────────────┘  └──────────────┘    └──────────────┘
                                           │
                                           ▼
                         ┌─────────────────────────────────────┐
                         │         Celery Workers              │
                         │  ┌───────────┐  ┌───────────────┐  │
                         │  │Analysis   │  │Embedding      │  │
                         │  │Task       │  │Task           │  │
                         │  └───────────┘  └───────────────┘  │
                         └─────────────────────────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
           ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
           │ Vector Store │       │    MLflow    │       │Celery Flower │
           │  (pgvector)  │       │  (Tracking)  │       │ (Monitoring) │
           └──────────────┘       └──────────────┘       └──────────────┘
```

## Components and Interfaces

### 1. Next.js Frontend

**Technology Stack:**
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS for styling
- TanStack Query for data fetching
- Recharts for stock charts
- Socket.io-client for WebSocket

**Key Components:**

```typescript
// Stock Search Component
interface StockSearchProps {
  onSelect: (ticker: string) => void;
}

// Analysis Request Response
interface AnalysisTaskResponse {
  taskId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
}

// Analysis Report
interface AnalysisReport {
  ticker: string;
  companyName: string;
  analyzedAt: string;
  priceData: PriceDataPoint[];
  newsSummary: NewsSummary;
  sentiment: SentimentAnalysis;
  aiInsights: string;
}

// Chat Message
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: string;
}
```

**Pages:**
- `/` - Home with stock search
- `/analyze/[ticker]` - Analysis report page
- `/chat` - AI chat interface

### 2. FastAPI Backend

**Technology Stack:**
- FastAPI with async support
- Pydantic for validation
- SQLAlchemy for ORM
- Celery for task queue
- LangChain for LLM orchestration

**API Endpoints:**

```python
# Stock Search
GET /api/stocks/search?q={query}
Response: List[StockSearchResult]

# Request Analysis
POST /api/analysis/request
Body: { "ticker": "AAPL" }
Response: { "task_id": "uuid", "status": "pending" }

# Get Task Status
GET /api/analysis/status/{task_id}
Response: { "task_id": "uuid", "status": "processing", "progress": 45 }

# Get Analysis Report
GET /api/analysis/report/{ticker}
Response: AnalysisReport

# Chat
POST /api/chat
Body: { "message": "Why did AAPL drop?", "ticker": "AAPL", "conversation_id": "uuid" }
Response: { "response": "...", "sources": [...] }

# WebSocket for real-time updates
WS /ws/analysis/{task_id}
```

**Backend Structure:**

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings and env vars
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── stocks.py    # Stock search endpoints
│   │   │   ├── analysis.py  # Analysis request/status
│   │   │   ├── chat.py      # Chat endpoints
│   │   │   └── health.py    # Health checks
│   │   └── websocket.py     # WebSocket handlers
│   ├── services/
│   │   ├── stock_service.py     # yfinance integration
│   │   ├── llm_service.py       # OpenAI/LangChain
│   │   ├── news_service.py      # News API integration
│   │   ├── sentiment_service.py # Sentiment analysis
│   │   ├── rag_service.py       # RAG pipeline
│   │   └── summarizer_service.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py    # Celery configuration
│   │   └── analysis_task.py # Main analysis task
│   ├── models/
│   │   ├── database.py      # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   └── utils/
│       ├── embeddings.py    # Vector embedding utils
│       └── mlflow_utils.py  # MLflow tracking
├── tests/
├── requirements.txt
└── Dockerfile
```

### 3. Celery Task Pipeline (Parallel Queue Architecture)

The system uses dedicated queues with specialized workers for parallel processing. This architecture enables:
- Independent scaling of each task type
- Isolation of failures (LLM failures don't block data fetching)
- Optimal resource allocation per task type

**Queue Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Redis Message Broker                               │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│  data_queue │  llm_queue  │ embed_queue │ aggregate_q │    dead_letter      │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴──────────┬──────────┘
       │             │             │             │                 │
       ▼             ▼             ▼             ▼                 ▼
┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────────┐
│ Data Worker ││ LLM Worker  ││Embed Worker ││ Aggregator  ││  DLQ Processor  │
│ (2 workers) ││ (3 workers) ││ (2 workers) ││ (1 worker)  ││   (1 worker)    │
│             ││             ││             ││             ││                 │
│ - Stock API ││ - Sentiment ││ - OpenAI    ││ - Combine   ││ - Log failures  │
│ - News API  ││ - Summary   ││   Embeddings││   results   ││ - Alert         │
│ - yfinance  ││ - Insights  ││ - pgvector  ││ - Save      ││ - Retry logic   │
└─────────────┘└─────────────┘└─────────────┘└─────────────┘└─────────────────┘
```

**Queue Definitions:**

| Queue | Purpose | Workers | Concurrency |
|-------|---------|---------|-------------|
| `data_queue` | Stock data & news fetching | 2 | 4 per worker |
| `llm_queue` | Sentiment, summary, insights | 3 | 2 per worker (rate limited) |
| `embed_queue` | Vector embeddings | 2 | 2 per worker |
| `aggregate_queue` | Combine results, save report | 1 | 4 per worker |
| `dead_letter` | Failed tasks after max retries | 1 | 1 |

**Parallel Task Flow with Celery Canvas:**

```python
from celery import chain, group, chord
from app.tasks.celery_app import celery_app

# Individual tasks routed to specific queues
@celery_app.task(bind=True, queue='data_queue', max_retries=3)
def fetch_stock_data_task(self, ticker: str) -> dict:
    """Fetch stock price history from yfinance."""
    return stock_service.fetch_stock_data(ticker)

@celery_app.task(bind=True, queue='data_queue', max_retries=3)
def fetch_news_task(self, ticker: str) -> list:
    """Fetch news articles from news APIs."""
    return news_service.fetch_news(ticker)

@celery_app.task(bind=True, queue='embed_queue', max_retries=3)
def embed_documents_task(self, ticker: str, stock_data: dict, news: list) -> str:
    """Generate embeddings and store in vector DB."""
    return rag_service.embed_documents(ticker, stock_data, news)

@celery_app.task(bind=True, queue='llm_queue', max_retries=3, rate_limit='10/m')
def analyze_sentiment_task(self, news: list) -> dict:
    """LLM-based sentiment analysis."""
    return sentiment_service.analyze(news)

@celery_app.task(bind=True, queue='llm_queue', max_retries=3, rate_limit='10/m')
def generate_summary_task(self, ticker: str, news: list) -> str:
    """Generate news summary using LLM."""
    return summarizer_service.summarize(ticker, news)

@celery_app.task(bind=True, queue='llm_queue', max_retries=3, rate_limit='10/m')
def generate_insights_task(self, ticker: str, stock_data: dict, sentiment: dict, summary: str) -> str:
    """Generate AI insights using LLM."""
    return llm_service.generate_insights(ticker, stock_data, sentiment, summary)

@celery_app.task(bind=True, queue='aggregate_queue')
def aggregate_and_save_task(self, results: list, ticker: str) -> dict:
    """Combine all results and save the analysis report."""
    stock_data, news, embedding_id, sentiment, summary, insights = results
    report = report_service.save(ticker, stock_data, news, sentiment, summary, insights)
    return {'status': 'completed', 'report_id': str(report.id)}


def run_stock_analysis(ticker: str) -> str:
    """
    Orchestrate parallel analysis using Celery Canvas.
    Returns the task group ID for tracking.
    """
    # Phase 1: Fetch data in parallel
    data_tasks = group(
        fetch_stock_data_task.s(ticker),
        fetch_news_task.s(ticker)
    )
    
    # Phase 2: After data is fetched, run embedding + LLM tasks in parallel
    def create_analysis_workflow(data_results):
        stock_data, news = data_results
        
        return group(
            embed_documents_task.s(ticker, stock_data, news),
            analyze_sentiment_task.s(news),
            generate_summary_task.s(ticker, news),
        )
    
    # Phase 3: Generate insights (needs sentiment + summary)
    # Phase 4: Aggregate and save
    
    # Full workflow using chord (group with callback)
    workflow = chain(
        # Step 1: Fetch stock data and news in parallel
        group(
            fetch_stock_data_task.s(ticker),
            fetch_news_task.s(ticker)
        ),
        # Step 2: Fan out to embedding + sentiment + summary in parallel
        # Using chord to wait for all to complete
        chord_callback.s(ticker)
    )
    
    result = workflow.apply_async()
    return result.id


@celery_app.task(bind=True, queue='aggregate_queue')
def chord_callback(self, data_results: list, ticker: str) -> dict:
    """
    Callback after data fetch completes.
    Spawns parallel LLM tasks and waits for completion.
    """
    stock_data, news = data_results
    
    # Run embedding, sentiment, and summary in parallel
    parallel_tasks = chord(
        group(
            embed_documents_task.s(ticker, stock_data, news),
            analyze_sentiment_task.s(news),
            generate_summary_task.s(ticker, news),
        ),
        finalize_analysis.s(ticker, stock_data, news)
    )
    
    return parallel_tasks.apply_async()


@celery_app.task(bind=True, queue='aggregate_queue')
def finalize_analysis(self, llm_results: list, ticker: str, stock_data: dict, news: list) -> dict:
    """
    Final step: generate insights and save report.
    """
    embedding_id, sentiment, summary = llm_results
    
    # Generate insights (needs sentiment + summary)
    insights = generate_insights_task.apply_async(
        args=[ticker, stock_data, sentiment, summary],
        queue='llm_queue'
    ).get(timeout=120)
    
    # Save the complete report
    report = report_service.save(
        ticker=ticker,
        stock_data=stock_data,
        news=news,
        sentiment=sentiment,
        summary=summary,
        insights=insights
    )
    
    return {'status': 'completed', 'report_id': str(report.id), 'ticker': ticker}
```

**Celery Configuration with Multiple Queues:**

```python
from celery import Celery
from kombu import Queue

celery_app = Celery(
    'investingiq',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
    include=[
        'app.tasks.data_tasks',
        'app.tasks.llm_tasks',
        'app.tasks.embed_tasks',
        'app.tasks.aggregate_tasks'
    ]
)

# Queue definitions
celery_app.conf.task_queues = (
    Queue('data_queue', routing_key='data.#'),
    Queue('llm_queue', routing_key='llm.#'),
    Queue('embed_queue', routing_key='embed.#'),
    Queue('aggregate_queue', routing_key='aggregate.#'),
    Queue('dead_letter', routing_key='dlq.#'),
)

# Default queue
celery_app.conf.task_default_queue = 'data_queue'

# Task routing
celery_app.conf.task_routes = {
    'app.tasks.data_tasks.*': {'queue': 'data_queue'},
    'app.tasks.llm_tasks.*': {'queue': 'llm_queue'},
    'app.tasks.embed_tasks.*': {'queue': 'embed_queue'},
    'app.tasks.aggregate_tasks.*': {'queue': 'aggregate_queue'},
}

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Soft limit for graceful shutdown
    worker_prefetch_multiplier=1,  # Fair task distribution
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    result_expires=3600,  # Results expire after 1 hour
)

# Dead letter queue configuration
celery_app.conf.task_annotations = {
    '*': {
        'on_failure': handle_task_failure,  # Custom failure handler
    }
}

def handle_task_failure(self, exc, task_id, args, kwargs, einfo):
    """Route failed tasks to dead letter queue after max retries."""
    if self.request.retries >= self.max_retries:
        dead_letter_task.apply_async(
            args=[task_id, str(exc), args, kwargs],
            queue='dead_letter'
        )
```

**Worker Startup Commands:**

```bash
# Start workers for each queue (run in separate terminals or as services)

# Data workers (high concurrency for I/O bound tasks)
celery -A app.tasks.celery_app worker -Q data_queue -c 4 -n data_worker_1@%h
celery -A app.tasks.celery_app worker -Q data_queue -c 4 -n data_worker_2@%h

# LLM workers (lower concurrency due to rate limits and cost)
celery -A app.tasks.celery_app worker -Q llm_queue -c 2 -n llm_worker_1@%h
celery -A app.tasks.celery_app worker -Q llm_queue -c 2 -n llm_worker_2@%h
celery -A app.tasks.celery_app worker -Q llm_queue -c 2 -n llm_worker_3@%h

# Embedding workers
celery -A app.tasks.celery_app worker -Q embed_queue -c 2 -n embed_worker_1@%h
celery -A app.tasks.celery_app worker -Q embed_queue -c 2 -n embed_worker_2@%h

# Aggregator worker
celery -A app.tasks.celery_app worker -Q aggregate_queue -c 4 -n aggregator@%h

# Dead letter queue processor
celery -A app.tasks.celery_app worker -Q dead_letter -c 1 -n dlq_processor@%h

# Celery Flower for monitoring (all queues)
celery -A app.tasks.celery_app flower --port=5555
```

**Docker Compose for Workers:**

```yaml
# docker-compose.workers.yml
version: '3.8'

services:
  data-worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker -Q data_queue -c 4
    deploy:
      replicas: 2
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://...
    depends_on:
      - redis
      - postgres

  llm-worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker -Q llm_queue -c 2
    deploy:
      replicas: 3
    environment:
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis

  embed-worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker -Q embed_queue -c 2
    deploy:
      replicas: 2
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://...
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
      - postgres

  aggregator:
    build: ./backend
    command: celery -A app.tasks.celery_app worker -Q aggregate_queue -c 4
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://...
    depends_on:
      - redis
      - postgres

  dlq-processor:
    build: ./backend
    command: celery -A app.tasks.celery_app worker -Q dead_letter -c 1
    environment:
      - REDIS_URL=redis://redis:6379/0
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}  # For alerting
    depends_on:
      - redis

  flower:
    build: ./backend
    command: celery -A app.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
```

**Progress Tracking with Parallel Tasks:**

```python
from celery import current_app
from celery.result import GroupResult

class AnalysisProgressTracker:
    """Track progress across parallel task queues."""
    
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.group_result = GroupResult.restore(group_id)
    
    def get_progress(self) -> dict:
        """Calculate overall progress from all sub-tasks."""
        if not self.group_result:
            return {'progress': 0, 'status': 'unknown'}
        
        completed = sum(1 for r in self.group_result.results if r.ready())
        total = len(self.group_result.results)
        
        # Get individual task statuses
        task_statuses = []
        for result in self.group_result.results:
            task_statuses.append({
                'task_id': result.id,
                'status': result.status,
                'queue': result.queue or 'unknown'
            })
        
        return {
            'progress': int((completed / total) * 100) if total > 0 else 0,
            'completed_tasks': completed,
            'total_tasks': total,
            'status': 'completed' if completed == total else 'processing',
            'tasks': task_statuses
        }
```

### 4. LLM Service (LangChain + OhMyGPT)

**OhMyGPT Integration:**

OhMyGPT (ohmygpt.com) provides an OpenAI-compatible API endpoint, allowing us to use LangChain with minimal configuration changes. This gives access to various models (GPT-4, Claude, etc.) through a single API.

**RAG Pipeline:**

```python
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import PGVector
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
import os

# OhMyGPT Configuration
OHMYGPT_API_BASE = "https://api.ohmygpt.com/v1"
OHMYGPT_API_KEY = os.getenv("OHMYGPT_API_KEY")

class LLMService:
    def __init__(self):
        # Use OhMyGPT as OpenAI-compatible endpoint with Gemini model
        self.llm = ChatOpenAI(
            model="gemini-3-flash-preview",  # Google's Gemini model via OhMyGPT
            temperature=0.1,
            openai_api_base=OHMYGPT_API_BASE,
            openai_api_key=OHMYGPT_API_KEY
        )
        
        # Embeddings can also use OhMyGPT if supported, or use local model
        self.embeddings = OpenAIEmbeddings(
            openai_api_base=OHMYGPT_API_BASE,
            openai_api_key=OHMYGPT_API_KEY
        )
        
        self.vector_store = PGVector(
            connection_string=DATABASE_URL,
            embedding_function=self.embeddings,
            collection_name="financial_docs"
        )
    
    def chat(self, query: str, ticker: str, conversation_history: list) -> dict:
        """RAG-powered chat with financial context."""
        retriever = self.vector_store.as_retriever(
            search_kwargs={"filter": {"ticker": ticker}, "k": 5}
        )
        
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            return_source_documents=True
        )
        
        result = chain({"question": query, "chat_history": conversation_history})
        return {
            "response": result["answer"],
            "sources": [doc.metadata.get("source") for doc in result["source_documents"]]
        }
    
    def analyze_sentiment(self, headlines: list[str]) -> list[dict]:
        """LLM-based sentiment analysis."""
        prompt = PromptTemplate(
            input_variables=["headline"],
            template="""Analyze the sentiment of this financial news headline.
            
Headline: {headline}

Classify as: BULLISH, BEARISH, or NEUTRAL
Provide a confidence score from 0.0 to 1.0.
Consider financial context (e.g., "beat expectations" is bullish).

Response format:
sentiment: <BULLISH|BEARISH|NEUTRAL>
confidence: <0.0-1.0>
reasoning: <brief explanation>"""
        )
        
        results = []
        for headline in headlines:
            response = self.llm.predict(prompt.format(headline=headline))
            results.append(parse_sentiment_response(response, headline))
        return results
    
    def summarize_news(self, articles: list[dict], ticker: str) -> str:
        """Generate concise news summary."""
        prompt = f"""Summarize the following news articles about {ticker} stock.

Articles:
{format_articles(articles)}

Provide a concise summary (2-3 paragraphs) highlighting:
1. Key events and announcements
2. Market-moving information
3. Overall sentiment and outlook

Summary:"""
        
        return self.llm.predict(prompt)
```

### 5. Vector Store (pgvector)

**Schema:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE financial_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10) NOT NULL,
    doc_type VARCHAR(50) NOT NULL,  -- 'news', 'price_history', 'company_info'
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_ticker (ticker),
    INDEX idx_doc_type (doc_type)
);

-- Vector similarity search index
CREATE INDEX ON financial_documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 6. MLflow Integration

**Experiment Tracking:**

```python
import mlflow
from mlflow.tracking import MlflowClient

class MLflowTracker:
    def __init__(self):
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("investingiq-llm")
    
    def log_llm_call(self, prompt_template: str, model: str, 
                     input_tokens: int, output_tokens: int, 
                     latency_ms: float, cost: float):
        """Log LLM API call metrics."""
        with mlflow.start_run(nested=True):
            mlflow.log_params({
                "model": model,
                "prompt_template_hash": hash(prompt_template)
            })
            mlflow.log_metrics({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "cost_usd": cost
            })
    
    def log_sentiment_accuracy(self, predictions: list, ground_truth: list):
        """Log sentiment model performance."""
        accuracy = sum(p == g for p, g in zip(predictions, ground_truth)) / len(predictions)
        mlflow.log_metric("sentiment_accuracy", accuracy)
    
    def register_prompt_version(self, prompt_name: str, prompt_template: str):
        """Version control for prompt templates."""
        client = MlflowClient()
        client.log_text(
            run_id=mlflow.active_run().info.run_id,
            text=prompt_template,
            artifact_file=f"prompts/{prompt_name}.txt"
        )
```

## Data Models

### Database Schema (PostgreSQL)

```python
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

class AnalysisReport(Base):
    __tablename__ = "analysis_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)
    company_name = Column(String(255))
    analyzed_at = Column(DateTime, nullable=False)
    
    # Price data stored as JSON array
    price_data = Column(JSON)
    
    # Analysis results
    news_summary = Column(String)
    sentiment_score = Column(Float)  # -1.0 to 1.0
    sentiment_breakdown = Column(JSON)  # {bullish: 5, bearish: 2, neutral: 3}
    ai_insights = Column(String)
    
    # Metadata
    news_count = Column(Integer)
    data_sources = Column(ARRAY(String))
    processing_time_seconds = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("ChatMessage", back_populates="conversation")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.id"))
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(String)
    sources = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("ChatConversation", back_populates="messages")

class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    celery_task_id = Column(String(255), unique=True)
    ticker = Column(String(10), nullable=False)
    status = Column(String(20))  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    current_step = Column(String(100))
    error_message = Column(String)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis_reports.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
```

### Pydantic Schemas

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class StockSearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str
    type: str  # 'stock', 'etf', etc.

class AnalysisRequest(BaseModel):
    ticker: str

class AnalysisTaskStatus(BaseModel):
    task_id: UUID
    status: str
    progress: int
    current_step: Optional[str]
    error_message: Optional[str]

class PriceDataPoint(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class SentimentResult(BaseModel):
    headline: str
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float
    reasoning: str

class AnalysisReportResponse(BaseModel):
    id: UUID
    ticker: str
    company_name: str
    analyzed_at: datetime
    price_data: List[PriceDataPoint]
    news_summary: str
    sentiment_score: float
    sentiment_breakdown: dict
    sentiment_details: List[SentimentResult]
    ai_insights: str

class ChatRequest(BaseModel):
    message: str
    ticker: str
    conversation_id: Optional[UUID]

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    conversation_id: UUID
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Stock Search Autocomplete Relevance

*For any* partial search query string, the autocomplete function SHALL return suggestions where each suggestion's ticker or company name contains the query substring (case-insensitive).

**Validates: Requirements 1.1**

### Property 2: Ticker Validation Correctness

*For any* ticker string, the validation function SHALL return true if and only if the ticker exists in a supported exchange's listing.

**Validates: Requirements 1.2**

### Property 3: Recent Searches Persistence

*For any* sequence of stock searches performed by a user, the recent searches list SHALL contain all searched tickers in reverse chronological order, up to the configured maximum.

**Validates: Requirements 1.5**

### Property 4: Analysis Task Creation is Asynchronous

*For any* valid analysis request, the API SHALL return a task ID within 500ms, regardless of how long the actual analysis takes to complete.

**Validates: Requirements 2.1, 2.2**

### Property 5: Completed Analysis Report Completeness

*For any* successfully completed analysis task, the resulting Analysis_Report SHALL contain non-null values for: price_data, news_summary, sentiment_score, sentiment_breakdown, and ai_insights.

**Validates: Requirements 2.3, 2.5, 6.2**

### Property 6: Task Retry with Exponential Backoff

*For any* analysis task that fails, the system SHALL retry up to 3 times with delays of approximately 60s, 120s, and 180s respectively before marking as permanently failed.

**Validates: Requirements 2.6**

### Property 7: Concurrent Task Processing

*For any* set of N analysis tasks submitted simultaneously (where N ≤ worker count), all N tasks SHALL begin processing within 5 seconds of submission.

**Validates: Requirements 2.8**

### Property 8: RAG Retrieval Relevance

*For any* chat query about a specific stock ticker, the RAG pipeline SHALL return only documents where the ticker metadata matches the queried ticker.

**Validates: Requirements 3.2, 9.3, 9.4**

### Property 9: Chat Response Source Citations

*For any* chat response generated by the LLM service, the response object SHALL include a non-empty sources array containing document references used in generation.

**Validates: Requirements 3.4**

### Property 10: Conversation History Preservation

*For any* conversation with N messages, querying the conversation SHALL return all N messages in chronological order with correct role assignments.

**Validates: Requirements 3.5**

### Property 11: Sentiment Classification Validity

*For any* news headline processed by the sentiment analyzer, the output SHALL have: sentiment ∈ {BULLISH, BEARISH, NEUTRAL} and confidence ∈ [0.0, 1.0].

**Validates: Requirements 5.2**

### Property 12: News Summary Sentiment Indicator

*For any* generated news summary, the summary object SHALL include a sentiment_indicator field with value in {bullish, bearish, neutral}.

**Validates: Requirements 4.4**

### Property 13: Analysis Report Timestamp Validity

*For any* Analysis_Report, the analyzed_at timestamp SHALL be within 1 hour of the current time when the report was generated.

**Validates: Requirements 6.3**

### Property 14: API Error Status Codes

*For any* API request that results in an error, the response status code SHALL be: 400 for validation errors, 404 for not found, 429 for rate limit, 500 for server errors.

**Validates: Requirements 7.2**

### Property 15: Rate Limiting Enforcement

*For any* client exceeding the configured rate limit (e.g., 100 requests/minute), subsequent requests SHALL receive HTTP 429 status until the rate limit window resets.

**Validates: Requirements 7.4**

### Property 16: Health Check Availability

*For any* request to the health check endpoint when all dependencies are available, the response SHALL be HTTP 200 with status "healthy".

**Validates: Requirements 7.7**

### Property 17: Document Chunking Size Bounds

*For any* document embedded by the RAG pipeline, each chunk SHALL have token count ≤ 512 tokens and overlap of approximately 50 tokens with adjacent chunks.

**Validates: Requirements 9.5**

### Property 18: MLflow Experiment Tracking Completeness

*For any* LLM API call, MLflow SHALL log: model name, prompt template hash, input tokens, output tokens, latency_ms, and cost_usd.

**Validates: Requirements 10.1, 10.2, 10.3**

### Property 19: Dead Letter Queue for Failed Tasks

*For any* task that fails after exhausting all retries, the task SHALL be moved to the dead letter queue with full error details preserved.

**Validates: Requirements 11.7**

### Property 20: Worker Crash Recovery

*For any* task that was in-progress when a worker crashes, the task SHALL be reassigned to another available worker within the visibility timeout period.

**Validates: Requirements 11.6**

## Error Handling

### API Error Responses

All API errors follow a consistent format:

```python
class ErrorResponse(BaseModel):
    error: str           # Error type (e.g., "ValidationError", "NotFound")
    message: str         # Human-readable message
    details: Optional[dict]  # Additional context
    request_id: str      # For debugging/support

# Example error responses
{
    "error": "ValidationError",
    "message": "Invalid stock ticker: INVALID",
    "details": {"ticker": "INVALID", "suggestions": ["INTL", "INVA"]},
    "request_id": "req_abc123"
}

{
    "error": "AnalysisTaskFailed",
    "message": "Analysis failed after 3 retries",
    "details": {"task_id": "uuid", "last_error": "News API rate limit exceeded"},
    "request_id": "req_def456"
}
```

### Error Categories and Handling

| Error Type | HTTP Status | Retry | User Message |
|------------|-------------|-------|--------------|
| Invalid ticker | 400 | No | "We couldn't find that stock. Did you mean...?" |
| Rate limit exceeded | 429 | Yes (after delay) | "Too many requests. Please wait a moment." |
| LLM API failure | 500 | Yes (3x) | "AI service temporarily unavailable. Retrying..." |
| News API failure | 500 | Yes (3x) | "Unable to fetch news. Analysis will continue with available data." |
| Database error | 500 | Yes (3x) | "Service error. Please try again." |
| Task timeout | 500 | Yes (1x) | "Analysis is taking longer than expected. We'll notify you when complete." |

### Celery Task Error Handling

```python
@celery_app.task(bind=True, max_retries=3, autoretry_for=(Exception,),
                 retry_backoff=60, retry_backoff_max=300)
def run_stock_analysis(self, ticker: str):
    try:
        # ... task logic
    except NewsAPIError as e:
        # Non-critical: continue without news
        logger.warning(f"News fetch failed for {ticker}: {e}")
        news_articles = []
    except OpenAIError as e:
        # Critical: retry
        raise self.retry(exc=e)
    except Exception as e:
        # Unknown error: log and retry
        logger.error(f"Analysis failed for {ticker}: {e}")
        raise self.retry(exc=e)
```

### Circuit Breaker Pattern

For external API calls (OpenAI, News APIs), implement circuit breaker:

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_openai(prompt: str) -> str:
    return openai_client.chat.completions.create(...)
```

## Testing Strategy

### Dual Testing Approach

This project uses both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and integration points
- **Property-based tests**: Verify universal properties across randomized inputs

### Testing Framework

- **Python Backend**: pytest + hypothesis (property-based testing)
- **Next.js Frontend**: Jest + React Testing Library
- **Integration**: pytest with testcontainers for Redis/PostgreSQL
- **E2E**: Playwright

### Property-Based Testing Configuration

```python
# conftest.py
from hypothesis import settings, Verbosity

settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=20, deadline=None)
settings.load_profile("ci")
```

Each property test must:
1. Run minimum 100 iterations
2. Reference the design document property
3. Use the tag format: **Feature: llm-financial-assistant, Property {number}: {property_text}**

### Test Structure

```
backend/tests/
├── unit/
│   ├── test_stock_service.py
│   ├── test_sentiment_service.py
│   ├── test_llm_service.py
│   └── test_rag_service.py
├── property/
│   ├── test_autocomplete_properties.py    # Property 1
│   ├── test_ticker_validation_properties.py  # Property 2
│   ├── test_sentiment_properties.py       # Property 11
│   ├── test_chunking_properties.py        # Property 17
│   └── test_api_properties.py             # Properties 14, 15, 16
├── integration/
│   ├── test_celery_tasks.py              # Properties 4, 5, 6, 7
│   ├── test_rag_pipeline.py              # Properties 8, 9
│   ├── test_mlflow_tracking.py           # Property 18
│   └── test_database.py                  # Property 10
└── e2e/
    └── test_analysis_flow.py

frontend/
├── __tests__/
│   ├── components/
│   │   ├── StockSearch.test.tsx
│   │   ├── ChatInterface.test.tsx
│   │   └── AnalysisReport.test.tsx
│   └── pages/
│       └── analyze.test.tsx
└── e2e/
    └── analysis.spec.ts
```

### Example Property Tests

```python
# test_sentiment_properties.py
from hypothesis import given, strategies as st
import pytest

class TestSentimentProperties:
    """
    Feature: llm-financial-assistant, Property 11: Sentiment Classification Validity
    For any news headline, output SHALL have sentiment ∈ {BULLISH, BEARISH, NEUTRAL} 
    and confidence ∈ [0.0, 1.0].
    Validates: Requirements 5.2
    """
    
    @given(headline=st.text(min_size=10, max_size=500))
    def test_sentiment_output_validity(self, headline, sentiment_analyzer):
        result = sentiment_analyzer.analyze(headline)
        
        assert result.sentiment in {"BULLISH", "BEARISH", "NEUTRAL"}
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.reasoning, str)


# test_autocomplete_properties.py
class TestAutocompleteProperties:
    """
    Feature: llm-financial-assistant, Property 1: Stock Search Autocomplete Relevance
    For any partial search query, suggestions SHALL contain the query substring.
    Validates: Requirements 1.1
    """
    
    @given(query=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    def test_autocomplete_relevance(self, query, stock_search_service):
        suggestions = stock_search_service.autocomplete(query)
        
        for suggestion in suggestions:
            assert (query.upper() in suggestion.ticker.upper() or 
                    query.upper() in suggestion.name.upper())


# test_api_properties.py
class TestRateLimitingProperty:
    """
    Feature: llm-financial-assistant, Property 15: Rate Limiting Enforcement
    For any client exceeding rate limit, subsequent requests SHALL receive HTTP 429.
    Validates: Requirements 7.4
    """
    
    @given(request_count=st.integers(min_value=101, max_value=200))
    def test_rate_limit_enforcement(self, request_count, test_client):
        # Make requests up to limit
        for i in range(100):
            response = test_client.get("/api/stocks/search?q=AAPL")
            assert response.status_code == 200
        
        # Exceed limit
        response = test_client.get("/api/stocks/search?q=AAPL")
        assert response.status_code == 429
```

### Unit Test Examples

```python
# test_stock_service.py
class TestStockService:
    def test_validate_ticker_valid(self, stock_service):
        """Test that known valid tickers pass validation."""
        assert stock_service.validate_ticker("AAPL") is True
        assert stock_service.validate_ticker("GOOGL") is True
        assert stock_service.validate_ticker("MSFT") is True
    
    def test_validate_ticker_invalid(self, stock_service):
        """Test that invalid tickers fail validation."""
        assert stock_service.validate_ticker("INVALID123") is False
        assert stock_service.validate_ticker("") is False
    
    def test_fetch_stock_data_returns_expected_fields(self, stock_service):
        """Test that stock data contains required fields."""
        data = stock_service.fetch_stock_data("AAPL")
        
        assert "price_history" in data
        assert "company_name" in data
        assert len(data["price_history"]) > 0
```

### Integration Test Examples

```python
# test_celery_tasks.py
class TestCeleryTasks:
    """
    Feature: llm-financial-assistant, Property 4: Analysis Task Creation is Asynchronous
    Validates: Requirements 2.1, 2.2
    """
    
    def test_analysis_request_returns_immediately(self, test_client, celery_app):
        import time
        
        start = time.time()
        response = test_client.post("/api/analysis/request", json={"ticker": "AAPL"})
        elapsed = time.time() - start
        
        assert response.status_code == 202
        assert "task_id" in response.json()
        assert elapsed < 0.5  # Must return within 500ms
    
    def test_completed_task_has_all_components(self, test_client, celery_app):
        """
        Feature: llm-financial-assistant, Property 5: Completed Analysis Report Completeness
        Validates: Requirements 2.3, 2.5, 6.2
        """
        # Request analysis
        response = test_client.post("/api/analysis/request", json={"ticker": "AAPL"})
        task_id = response.json()["task_id"]
        
        # Wait for completion (with timeout)
        result = celery_app.AsyncResult(task_id).get(timeout=120)
        
        # Fetch report
        report_response = test_client.get(f"/api/analysis/report/AAPL")
        report = report_response.json()
        
        assert report["price_data"] is not None
        assert report["news_summary"] is not None
        assert report["sentiment_score"] is not None
        assert report["sentiment_breakdown"] is not None
        assert report["ai_insights"] is not None
```

### CI/CD Test Pipeline

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/unit -v
      
      - name: Run property tests
        run: pytest tests/property -v --hypothesis-profile=ci
      
      - name: Run integration tests
        run: pytest tests/integration -v
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: cd frontend && npm ci
      
      - name: Run tests
        run: cd frontend && npm test
```
