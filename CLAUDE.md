# CLAUDE.md - Project Context for AI Assistants

## Project Overview
InvestingIQ is a stock market analysis platform with LLM-powered financial assistant, RAG pipeline, and sentiment analysis.

## Tech Stack
- **Backend**: FastAPI (Python 3.9+), SQLAlchemy, PostgreSQL with pgvector
- **Frontend**: Next.js 15, React 19, TypeScript, TailwindCSS
- **Queue**: Azure Service Bus (local emulator for dev)
- **Serverless**: Azure Functions
- **ML Tracking**: MLflow
- **LLM**: OpenAI-compatible API (MegaLLM/DeepSeek)

## Directory Structure
```
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/routes/   # API endpoints
│   │   ├── services/     # Business logic (llm, rag, stock, scraper)
│   │   ├── models/       # SQLAlchemy models
│   │   └── utils/        # Helpers (cache, circuit_breaker, errors)
│   ├── tests/            # pytest tests
│   └── alembic/          # DB migrations
├── frontend/             # Next.js frontend
├── functions/            # Azure Functions
│   ├── data_functions/
│   ├── llm_functions/
│   └── orchestrator/
└── config/               # Config files
```

## Architecture

**Cloud-Only Processing** with real-time updates via Server-Sent Events (SSE):
- `POST /analysis/request` - Creates task, sends message to Service Bus
- `GET /events/{task_id}` - SSE endpoint for real-time progress updates
- `POST /callback/progress` - Azure Functions POST progress here
- Frontend receives real-time updates via SSE (no polling, no external service)

```
Frontend (SSE) ←─────────────── FastAPI ←─── Azure Functions (HTTP callback)
    ↓                             ↓
    └── GET /events/{task_id}     └── POST /callback/progress
    
FastAPI → Service Bus → Azure Functions → PostgreSQL
              ↓
   [data-queue] → data_functions (10%)
              ↓
   [llm-queue] → llm_functions (50%)
              ↓
   [aggregate-queue] → save_report (100%)
```

## Commands

### 1. Start Local Services (Docker)
```bash
docker-compose up -d      # PostgreSQL, Redis, Service Bus Emulator, Azurite, MLflow
```

### 2. Configure Environment
```bash
# Backend
cp backend/.env.example backend/.env

# Functions
# Edit functions/.env with your OPENAI_API_KEY
```

### 3. Start Azure Functions (Required)
```bash
cd functions
pip install -r requirements.txt
func start                # Runs on http://localhost:7071
```

### 4. Start Backend API
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev               # Development server (port 3000)
```

### Testing
```bash
cd backend && pytest      # Backend tests
cd frontend && npm test   # Frontend tests
```

### Database Migrations
```bash
cd backend && alembic upgrade head
```

## Environment Variables

**Backend** (`backend/.env`):
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - LLM API key
- `OPENAI_BASE_URL` - LLM API base URL
- `AZURE_SERVICEBUS_CONNECTION_STRING` - Service Bus connection string

**Functions** (`functions/.env`):
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - LLM API key
- `OPENAI_BASE_URL` - LLM API base URL
- `LLM_MODEL` - LLM model name
- `BACKEND_CALLBACK_URL` - Backend API URL for SSE callbacks
- `AZURE_SERVICEBUS_CONNECTION_STRING` - Service Bus emulator connection
- `AZURE_STORAGE_CONNECTION_STRING` - Azurite emulator connection

**Note:** `local.settings.json` contains Azure Functions runtime settings (Storage, Service Bus bindings). App config uses `.env` file.

## Key Conventions
- Use async/await for all I/O operations
- Services are in `backend/app/services/`
- API routes follow REST conventions
- Use Pydantic for request/response validation
- Frontend uses TanStack Query for data fetching
- All API calls go through `/api/` prefix

## Testing
- Backend: pytest with pytest-asyncio
- Frontend: Jest with React Testing Library
- Test files: `backend/tests/`, `frontend/__tests__/`
