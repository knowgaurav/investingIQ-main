# Implementation Plan: LLM Financial Assistant

## Overview

This plan transforms InvestingIQ from a Streamlit app into a modern LLM-powered platform with Next.js frontend, FastAPI backend, and Celery task queues. Implementation follows a phased approach with git commits at each checkpoint.

## Tasks

- [x] 1. Project Setup and Git Workflow
  - [x] 1.1 Create feature branch and initialize project structure
    - Create branch `feature/llm-financial-assistant`
    - Set up monorepo structure with `backend/` and `frontend/` directories
    - Create `.gitignore` for Python and Node.js
    - _Requirements: 7.1, 8.1_

  - [x] 1.2 Set up FastAPI backend skeleton
    - Initialize Python project with `pyproject.toml` or `requirements.txt`
    - Create FastAPI app structure (`app/main.py`, `app/config.py`)
    - Add health check endpoint
    - _Requirements: 7.1, 7.7_

  - [ ]* 1.3 Write property test for health check endpoint
    - **Property 16: Health Check Availability**
    - **Validates: Requirements 7.7**

  - [x] 1.4 Set up Next.js frontend skeleton
    - Initialize Next.js 14 with TypeScript and Tailwind CSS
    - Create basic page structure (`/`, `/analyze/[ticker]`, `/chat`)
    - _Requirements: 8.1_

  - [x] 1.5 Checkpoint - Commit project skeleton
    - Ensure backend and frontend run independently
    - Git commit: "feat: initialize project structure with FastAPI and Next.js"

- [x] 2. Database and Infrastructure Setup
  - [x] 2.1 Set up PostgreSQL with pgvector
    - Create Docker Compose for local development (PostgreSQL, Redis)
    - Write SQLAlchemy models for AnalysisReport, ChatConversation, ChatMessage, AnalysisTask
    - Create Alembic migrations
    - _Requirements: 9.2_

  - [x] 2.2 Set up Redis and Celery infrastructure
    - Configure Celery with multiple queues (data, llm, embed, aggregate, dead_letter)
    - Create worker startup scripts
    - Add Celery Flower for monitoring
    - _Requirements: 11.1, 11.5_

  - [x] 2.3 Checkpoint - Commit infrastructure setup
    - Ensure Docker Compose starts all services
    - Git commit: "feat: add database models and Celery queue infrastructure"

- [x] 3. Stock Data Service
  - [x] 3.1 Implement stock search with autocomplete
    - Create `stock_service.py` with yfinance integration
    - Implement ticker validation and autocomplete
    - Add API endpoint `GET /api/stocks/search`
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 3.2 Write property test for autocomplete relevance
    - **Property 1: Stock Search Autocomplete Relevance**
    - **Validates: Requirements 1.1**

  - [ ]* 3.3 Write property test for ticker validation
    - **Property 2: Ticker Validation Correctness**
    - **Validates: Requirements 1.2**

  - [x] 3.4 Implement stock data fetching task
    - Create `fetch_stock_data_task` in data_queue
    - Fetch price history, company info from yfinance
    - _Requirements: 2.3_

  - [x] 3.5 Checkpoint - Commit stock service
    - Git commit: "feat: implement stock search and data fetching service"

- [x] 4. News Service
  - [x] 4.1 Implement news fetching service
    - Create `news_service.py` with News API integration
    - Implement `fetch_news_task` in data_queue
    - Handle rate limiting and errors gracefully
    - _Requirements: 4.1_

  - [x] 4.2 Checkpoint - Commit news service
    - Git commit: "feat: implement news fetching service"

- [x] 5. LLM Service with OhMyGPT
  - [x] 5.1 Implement LLM service core
    - Create `llm_service.py` with OhMyGPT integration
    - Configure LangChain with `gemini-3-flash-preview` model
    - Implement base chat completion method
    - _Requirements: 3.3_

  - [x] 5.2 Implement sentiment analysis
    - Create `sentiment_service.py` using LLM
    - Implement `analyze_sentiment_task` in llm_queue
    - Return sentiment (BULLISH/BEARISH/NEUTRAL) with confidence
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 5.3 Write property test for sentiment classification validity
    - **Property 11: Sentiment Classification Validity**
    - **Validates: Requirements 5.2**

  - [x] 5.4 Implement news summarization
    - Create `summarizer_service.py`
    - Implement `generate_summary_task` in llm_queue
    - Include sentiment indicator in summary
    - _Requirements: 4.2, 4.3, 4.4_

  - [ ]* 5.5 Write property test for summary sentiment indicator
    - **Property 12: News Summary Sentiment Indicator**
    - **Validates: Requirements 4.4**

  - [x] 5.6 Implement AI insights generation
    - Create `generate_insights_task` in llm_queue
    - Combine stock data, sentiment, and summary for insights
    - _Requirements: 6.2_

  - [x] 5.7 Checkpoint - Commit LLM services
    - Git commit: "feat: implement LLM services (sentiment, summary, insights)"

- [x] 6. RAG Pipeline
  - [x] 6.1 Implement document embedding service
    - Create `rag_service.py` with OpenAI embeddings via OhMyGPT
    - Implement document chunking with 512 token limit
    - Store embeddings in pgvector
    - _Requirements: 9.1, 9.5_

  - [ ]* 6.2 Write property test for document chunking
    - **Property 17: Document Chunking Size Bounds**
    - **Validates: Requirements 9.5**

  - [x] 6.3 Implement embedding task
    - Create `embed_documents_task` in embed_queue
    - Embed stock data, news, company info
    - _Requirements: 9.1, 9.2_

  - [x] 6.4 Implement RAG retrieval
    - Add semantic search with ticker filtering
    - Implement top-k retrieval
    - _Requirements: 9.3, 9.4_

  - [ ]* 6.5 Write property test for RAG retrieval relevance
    - **Property 8: RAG Retrieval Relevance**
    - **Validates: Requirements 9.3, 9.4**

  - [x] 6.6 Checkpoint - Commit RAG pipeline
    - Git commit: "feat: implement RAG pipeline with pgvector"

- [x] 7. Celery Task Orchestration
  - [x] 7.1 Implement parallel task workflow
    - Create orchestrator using Celery Canvas (group, chord, chain)
    - Implement `run_stock_analysis` workflow
    - Add progress tracking across parallel tasks
    - _Requirements: 2.1, 2.2, 2.3, 2.8_

  - [ ]* 7.2 Write property test for async task creation
    - **Property 4: Analysis Task Creation is Asynchronous**
    - **Validates: Requirements 2.1, 2.2**

  - [x] 7.3 Implement aggregation and report saving
    - Create `finalize_analysis` task in aggregate_queue
    - Save complete AnalysisReport to database
    - _Requirements: 2.5, 6.2_

  - [ ]* 7.4 Write property test for report completeness
    - **Property 5: Completed Analysis Report Completeness**
    - **Validates: Requirements 2.3, 2.5, 6.2**

  - [x] 7.5 Implement retry and dead letter queue
    - Add exponential backoff retry logic
    - Route failed tasks to dead_letter queue
    - _Requirements: 2.6, 2.7, 11.7_

  - [ ]* 7.6 Write property test for dead letter queue
    - **Property 19: Dead Letter Queue for Failed Tasks**
    - **Validates: Requirements 11.7**

  - [x] 7.7 Checkpoint - Commit task orchestration
    - Git commit: "feat: implement Celery task orchestration with parallel queues"

- [x] 8. Analysis API Endpoints
  - [x] 8.1 Implement analysis request endpoint
    - Create `POST /api/analysis/request` endpoint
    - Return task ID immediately
    - _Requirements: 2.1, 2.2_

  - [x] 8.2 Implement task status endpoint
    - Create `GET /api/analysis/status/{task_id}` endpoint
    - Return progress from parallel tasks
    - _Requirements: 2.4_

  - [x] 8.3 Implement WebSocket for real-time updates
    - Add WebSocket handler for task progress
    - Push updates as tasks complete
    - _Requirements: 7.8_

  - [x] 8.4 Implement report retrieval endpoint
    - Create `GET /api/analysis/report/{ticker}` endpoint
    - Return complete AnalysisReport
    - _Requirements: 6.1_

  - [ ]* 8.5 Write property test for API error status codes
    - **Property 14: API Error Status Codes**
    - **Validates: Requirements 7.2**

  - [ ] 8.6 Implement rate limiting
    - Add rate limiting middleware
    - Return 429 when limit exceeded
    - _Requirements: 7.4_

  - [ ]* 8.7 Write property test for rate limiting
    - **Property 15: Rate Limiting Enforcement**
    - **Validates: Requirements 7.4**

  - [x] 8.8 Checkpoint - Commit analysis API
    - Git commit: "feat: implement analysis API endpoints with WebSocket"

- [x] 9. Chat API and RAG Integration
  - [x] 9.1 Implement chat endpoint
    - Create `POST /api/chat` endpoint
    - Integrate RAG retrieval with LLM response
    - Include source citations in response
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 9.2 Write property test for chat source citations
    - **Property 9: Chat Response Source Citations**
    - **Validates: Requirements 3.4**

  - [x] 9.3 Implement conversation history
    - Store messages in ChatConversation/ChatMessage tables
    - Maintain context across messages
    - _Requirements: 3.5_

  - [ ]* 9.4 Write property test for conversation history
    - **Property 10: Conversation History Preservation**
    - **Validates: Requirements 3.5**

  - [x] 9.5 Checkpoint - Commit chat API
    - Git commit: "feat: implement chat API with RAG integration"

- [x] 10. MLflow Integration
  - [x] 10.1 Set up MLflow tracking
    - Configure MLflow server
    - Create MLflowTracker utility class
    - _Requirements: 10.1_

  - [x] 10.2 Implement experiment logging
    - Log LLM calls with tokens, latency, cost
    - Version prompt templates
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ]* 10.3 Write property test for MLflow tracking
    - **Property 18: MLflow Experiment Tracking Completeness**
    - **Validates: Requirements 10.1, 10.2, 10.3**

  - [x] 10.4 Checkpoint - Commit MLflow integration
    - Git commit: "feat: integrate MLflow for experiment tracking"

- [x] 11. Next.js Frontend - Stock Search
  - [x] 11.1 Implement stock search component
    - Create autocomplete search with debouncing
    - Display suggestions from API
    - _Requirements: 1.1, 8.1_

  - [x] 11.2 Implement recent searches
    - Store recent searches in localStorage
    - Display for quick access
    - _Requirements: 1.5_

  - [ ]* 11.3 Write property test for recent searches
    - **Property 3: Recent Searches Persistence**
    - **Validates: Requirements 1.5**

  - [x] 11.4 Checkpoint - Commit stock search UI
    - Git commit: "feat: implement stock search UI with autocomplete"

- [x] 12. Next.js Frontend - Analysis Flow
  - [x] 12.1 Implement analysis request flow
    - Create analysis request on stock selection
    - Show progress indicator with WebSocket updates
    - _Requirements: 2.4, 8.6_

  - [x] 12.2 Implement analysis report page
    - Create `/analyze/[ticker]` page
    - Display price chart, news summary, sentiment, insights
    - _Requirements: 6.1, 6.2, 6.3, 8.4_

  - [x] 12.3 Implement stock price chart
    - Use Recharts for interactive price visualization
    - _Requirements: 8.3_

  - [x] 12.4 Implement sentiment visualization
    - Display sentiment breakdown chart
    - Show contributing headlines
    - _Requirements: 5.4, 5.5_

  - [x] 12.5 Checkpoint - Commit analysis UI
    - Git commit: "feat: implement analysis report UI"

- [x] 13. Next.js Frontend - Chat Interface
  - [x] 13.1 Implement chat interface
    - Create chat component with message history
    - Connect to chat API
    - _Requirements: 3.1, 8.2_

  - [x] 13.2 Display source citations
    - Show sources for each AI response
    - Link to original documents
    - _Requirements: 3.4_

  - [x] 13.3 Integrate chat with analysis page
    - Allow follow-up questions on analysis report
    - _Requirements: 6.6_

  - [x] 13.4 Checkpoint - Commit chat UI
    - Git commit: "feat: implement chat interface with source citations"

- [ ] 14. Error Handling and Polish
  - [ ] 14.1 Implement error handling UI
    - Display user-friendly error messages
    - Handle API errors gracefully
    - _Requirements: 3.6, 8.7_

  - [ ] 14.2 Add loading states
    - Implement skeleton loaders
    - Show progress indicators
    - _Requirements: 8.6_

  - [ ] 14.3 Make responsive for mobile
    - Test and fix mobile layouts
    - _Requirements: 8.5_

  - [ ] 14.4 Checkpoint - Commit error handling and polish
    - Git commit: "feat: add error handling and responsive design"

- [ ] 15. Docker and Deployment
  - [ ] 15.1 Create Dockerfiles
    - Create Dockerfile for FastAPI backend
    - Create Dockerfile for Next.js frontend
    - Create Dockerfile for Celery workers
    - _Requirements: 11.2_

  - [ ] 15.2 Create production Docker Compose
    - Configure all services for production
    - Add environment variable management
    - _Requirements: 11.2_

  - [ ] 15.3 Final checkpoint - Merge to main
    - Run all tests
    - Git commit: "feat: add Docker deployment configuration"
    - Create PR and merge to main
    - Push to GitHub

## Notes

- Tasks marked with `*` are optional property-based tests
- Each checkpoint includes a git commit with conventional commit message
- All commits should be pushed to the feature branch
- Final merge to main after all tests pass
- Property tests use Hypothesis library with minimum 100 iterations
