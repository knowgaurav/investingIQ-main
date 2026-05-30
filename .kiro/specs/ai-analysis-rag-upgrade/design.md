# Design Document

## Overview

This design upgrades InvestingIQ with three coordinated changes:

1. **Quarterly Financials RAG** — A new Durable activity fetches a company's quarterly financial statements from Alpha Vantage (on first query only), persists them, embeds them into pgvector, and exposes them to the existing RAG chat so the LLM can explain the numbers with citations.
2. **Dual Analysis (ML + LLM)** — The orchestrator already fans out ML and LLM analysis in parallel. This design formalizes both into mirrored result shapes and adds a side-by-side frontend view with an agreement indicator.
3. **Azure Durable Functions Migration + Free Hosting** — Remove Azure Service Bus and Celery from the analysis path. The backend starts the existing Durable orchestrator over HTTP instead of enqueuing Service Bus messages. Frontend (Vercel), backend (Render free), and Postgres+pgvector (Supabase/Neon free) host the rest; only the Functions app and its required Storage account stay on Azure.

The design deliberately reuses what already exists: the Durable orchestrator (`orchestrator_func`), the activity functions, the Alpha Vantage client with key rotation, the pgvector schema, the SSE progress callback, and the RAG service. New surface area is kept minimal.

## Architecture

### Target architecture

```
┌──────────────┐   SSE    ┌──────────────────────┐   HTTP start   ┌────────────────────────┐
│  Frontend    │◀────────▶│   Backend (FastAPI)  │───────────────▶│  Durable Orchestrator  │
│  (Vercel)    │  /events │   (Render free)      │                │   (Azure Functions)    │
└──────────────┘          └──────────┬───────────┘                └───────────┬────────────┘
                                      │  progress callback (HTTP)              │ fan-out / fan-in
                                      │◀───────────────────────────────────────┤
                                      ▼                                         ▼
                            ┌──────────────────────┐            ┌──────────────────────────────┐
                            │ Postgres + pgvector  │◀───────────│ Activity functions (parallel):│
                            │ (Supabase / Neon)    │   writes   │  • fetch_data                  │
                            └──────────────────────┘            │  • ml_analysis                 │
                                                                │  • llm_analysis                │
                                                                │  • financials_ingest (NEW)     │
                                                                │  • aggregate                   │
                                                                └────────────────┬───────────────┘
                                                                                 │
                                                                        ┌────────▼─────────┐
                                                                        │ Azure Storage    │
                                                                        │ (Durable state)  │
                                                                        └──────────────────┘
```

### What is removed

- `backend/app/services/service_bus.py` (Service Bus client + `AnalysisOrchestrator`).
- Celery app and tasks under `backend/app/tasks/` and `backend/app/workers/` that drive the analysis pipeline.
- The Service Bus emulator (MSSQL), Azurite, and Redis broker services from `docker-compose.yml` for the analysis flow.
- Service Bus queue references in the Functions app (the orchestration is Durable-only).

### What stays on Azure

- The Functions app (Durable orchestrator + activities).
- One Azure Storage account (required by the Durable Functions runtime for orchestration state and the task hub).

## Components and Interfaces

### 1. Backend — start orchestration over HTTP

`backend/app/api/routes/analysis.py` currently calls `get_orchestrator().start_analysis(...)` (Service Bus). It will instead POST to the Durable HTTP starter (`orchestrator_starter`) and return the `task_id`.

New service `backend/app/services/orchestration_client.py`:

```python
class OrchestrationClient:
    """Starts the Azure Durable orchestration over HTTP."""

    def __init__(self):
        settings = get_settings()
        self._starter_url = settings.functions_orchestrator_url  # e.g. https://<app>.azurewebsites.net/api/orchestrators/start
        self._functions_key = settings.functions_key            # function-level auth key

    def start_analysis(self, ticker: str, task_id: str, llm_config: dict | None) -> None:
        requests.post(
            self._starter_url,
            params={"code": self._functions_key},
            json={"ticker": ticker, "task_id": task_id, "llm_config": llm_config},
            timeout=15,
        )
```

`request_analysis` keeps its current contract: validate ticker, generate `task_id`, call `start_analysis`, return `AnalysisTaskResponse`. The SSE endpoint (`/events/{task_id}`) and progress callback (`/callback/progress`) are unchanged — Functions already POST progress there via `webpubsub_utils.send_progress`.

The `orchestrator_starter` is updated to register the orchestration route name and accept the same payload it already accepts.

### 2. Durable orchestration — add financials fan-out

`functions/orchestrator_func/__init__.py` adds `activity_financials_ingest` to the parallel fan-out. The financials ingest is independent of ML/LLM analysis, so it runs concurrently and joins at fan-in.

```python
def orchestrator_function(context):
    input_data = context.get_input()
    ticker, task_id, llm_config = input_data["ticker"], input_data["task_id"], input_data.get("llm_config")

    fetch_result = yield context.call_activity("activity_fetch_data", {"ticker": ticker, "task_id": task_id})
    stock_data, news_data = fetch_result["stock_data"], fetch_result["news_data"]

    yield context.call_activity("activity_cache_data", {"ticker": ticker, "stock_data": stock_data, "news_data": news_data})

    parallel_tasks = [
        context.call_activity("activity_ml_analysis", {...}),
        context.call_activity("activity_financials_ingest", {"ticker": ticker, "task_id": task_id}),  # NEW
    ]
    if llm_config:
        parallel_tasks.append(context.call_activity("activity_llm_analysis", {...}))

    results = yield context.task_all(parallel_tasks)   # fan-in

    aggregated = yield context.call_activity("activity_aggregate", {
        "ticker": ticker, "task_id": task_id, "stock_data": stock_data,
        "news_data": news_data, "analysis_results": results, "llm_enabled": llm_config is not None,
    })
    return aggregated
```

Partial-failure handling (Requirement 7.5): each fanned-out activity wraps its body in try/except and returns a typed result with a `status` field rather than raising, so `task_all` always resolves and `aggregate` records which units succeeded or failed.

### 3. New activity — `activity_financials_ingest`

A new folder `functions/activity_financials_ingest/` with `__init__.py` + `function.json`. Logic:

1. Fetch the four quarterly statements via the Alpha Vantage client.
2. Determine the latest fiscal quarter present across statements.
3. Check the DB for an existing `quarterly_financials` row for `(ticker, fiscal_quarter)`; if present, skip fetch/embed and return `status="reused"`.
4. Persist the raw statements as a `quarterly_financials` row.
5. Convert each statement into a readable text passage, chunk, and embed into `financial_documents` with `doc_type="quarterly_financials"` and metadata `{fiscal_quarter, statement_type, chunk_index}` — skipping any `(ticker, fiscal_quarter, statement_type)` already embedded.

Alpha Vantage functions needed (extend `functions/shared/alpha_vantage.py`):

```python
def fetch_income_statement(ticker: str) -> dict   # function=INCOME_STATEMENT  -> quarterlyReports[]
def fetch_balance_sheet(ticker: str) -> dict       # function=BALANCE_SHEET     -> quarterlyReports[]
def fetch_cash_flow(ticker: str) -> dict           # function=CASH_FLOW         -> quarterlyReports[]
# EARNINGS already exists via fetch_earnings()
```

Each returns the latest quarterly report dict plus its `fiscalDateEnding`. All use the existing `get_api_key()` rotation.

**Key-rotation simplification:** `alpha_vantage.py` currently round-robins keys using a hardcoded `redis://localhost:6379/0`. Since Redis is removed from the deployed path, `get_api_key()` switches to a stateless `random.choice(keys)` over the configured key pool (still honoring `ALPHA_VANTAGE_API_KEYS`). This removes the Redis dependency while preserving multi-key spreading.

### 4. Financials → text passages

`functions/shared/financials_text.py` (new) turns a statement dict into a compact labeled passage so the embedding and the LLM citation are meaningful:

```python
def income_statement_to_text(ticker, fiscal_quarter, report) -> str
def balance_sheet_to_text(ticker, fiscal_quarter, report) -> str
def cash_flow_to_text(ticker, fiscal_quarter, report) -> str
def earnings_to_text(ticker, fiscal_quarter, earnings) -> str
```

Example output:

```
AAPL — Income Statement (fiscal quarter ending 2024-12-31)
Total revenue: $124.30B; Gross profit: $58.27B; Operating income: $42.83B;
Net income: $36.33B; EPS (reported): 2.41; ...
```

Passages are chunked with the existing `chunk_text` approach (≤2000 chars per embedding input, matching `embedding_utils.embed_and_store`).

### 5. RAG chat — financials-aware retrieval and citations

`RAGService.retrieve_context` already filters by ticker and orders by cosine distance, and `financial_documents` now contains `quarterly_financials` passages, so retrieval includes them automatically. Two refinements:

- `build_context_string` formats financials sources with their `fiscal_quarter` and `statement_type` so citations name the quarter and statement (Requirement 3.3).
- When no `quarterly_financials` rows exist for the ticker, chat prepends a note prompting the user to run an analysis first (Requirement 3.5).

Embedding model stays `text-embedding-3-small` (1536 dims), matching the existing `Vector(1536)` column — no migration of the vector dimension.

### 6. Dual analysis result shapes

The ML activity already returns `{prediction, technical, sentiment}`. The LLM activity returns provider output. This design defines a mirrored shape so the frontend can compare them directly.

ML result (existing, unchanged):
```json
{ "type": "ml_analysis", "status": "ok",
  "data": { "prediction": {...}, "technical": {...}, "sentiment": {...} } }
```

LLM result (normalized in `activity_llm_analysis`):
```json
{ "type": "llm_analysis", "status": "ok",
  "data": { "outlook": "bullish|bearish|neutral",
            "sentiment": { "label": "...", "score": 0.0 },
            "insight": "narrative text",
            "sources": [...] } }
```

`activity_aggregate` adds a comparison block when both pipelines produced a directional signal:
```json
{ "dual_comparison": { "ml_signal": "bullish", "llm_signal": "neutral", "agreement": false } }
```

ML signal is derived from the prediction trend; LLM signal from `outlook`. If LLM was not run or failed, `dual_comparison` is omitted and the report marks `llm_analysis.status` accordingly.

### 7. Frontend — side-by-side dual view

`frontend/src/components/MLAnalysisView.tsx` exists. Add a sibling `DualAnalysisView` (or extend the analyze page) that renders two columns:

- **Left — ML (Statistical):** forecast, RSI/MACD/Bollinger signals, VADER sentiment.
- **Right — LLM (AI):** outlook, LLM sentiment, narrative insight.
- **Header band:** agreement chip ("Models agree: Bullish" / "Models disagree") driven by `dual_comparison`. When LLM is absent, the right column shows an "LLM analysis not run" state and the chip is hidden.

The analyze page consumes the completed report `data` already delivered through the SSE `progress`/`done` events.

### 8. Chat UI — financials citations

`frontend/src/app/chat/page.tsx` renders `sources`. Citation labels use `statement_type` + `fiscal_quarter` (e.g., "Income Statement · Q ending 2024-12-31") when the source is a `quarterly_financials` doc.

## Data Models

### New table: `quarterly_financials`

```python
class QuarterlyFinancials(Base):
    __tablename__ = "quarterly_financials"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)
    fiscal_quarter = Column(String(10), nullable=False)   # fiscalDateEnding, e.g. 2024-12-31
    income_statement = Column(JSON)
    balance_sheet = Column(JSON)
    cash_flow = Column(JSON)
    earnings = Column(JSON)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("ticker", "fiscal_quarter", name="uq_ticker_quarter"),)
```

The unique constraint enforces Requirement 1.4/1.5 (reuse instead of re-fetch).

### `financial_documents` (existing) — dedup

Add a partial uniqueness guard for financials passages on `(ticker, doc_type, fiscal_quarter, statement_type, chunk_index)` via metadata-aware insert (check-then-insert in the activity). The column stays `Vector(1536)`; no schema change to the embedding type.

### Alembic migration

One new migration adds `quarterly_financials`. Both the backend (`backend/alembic/versions/`) and the Functions app read the same Postgres, so the table is created via the backend migration and consumed by both.

## Orchestration Flow (end to end)

```
User clicks Analyze (ticker, optional llm_config)
        │
        ▼
POST /api/v1/analysis/request ──▶ generate task_id ──▶ OrchestrationClient.start_analysis (HTTP)
        │                                                        │
        ▼                                                        ▼
Frontend opens SSE /events/{task_id}                  Durable orchestrator_func
        ▲                                                        │
        │ progress callbacks (HTTP)                              ├─ activity_fetch_data
        │◀───────────────────────────────────────────────────── ├─ activity_cache_data
        │                                                        ├─ FAN-OUT (parallel):
        │                                                        │    activity_ml_analysis
        │                                                        │    activity_financials_ingest (NEW)
        │                                                        │    activity_llm_analysis (if llm_config)
        │                                                        ├─ FAN-IN: task_all
        │                                                        └─ activity_aggregate ─▶ Postgres
        │◀──────────────────────── done (status=completed, data) ┘
        ▼
Frontend renders Dual Analysis view; financials now queryable via RAG chat
```

## Error Handling

- **Activity failure:** Each fanned-out activity returns `{"type": ..., "status": "failed", "error": ...}` instead of raising, so fan-in always completes and `aggregate` persists a partial report (Requirement 7.5).
- **Financials unavailable / rate-limited:** `activity_financials_ingest` returns `status="unavailable"`; the report records financials as unavailable and the rest proceeds (Requirement 1.6).
- **Alpha Vantage rate limit:** Existing client already detects `Note`/`Information` responses and flags `_rate_limited`; the financials activity treats this as `unavailable` for that run (cached/reused next time).
- **LLM pipeline failure:** Report returns ML-only with `llm_analysis.status="failed"` and a reason; frontend shows ML-only state (Requirements 5.4, 6.4).
- **Orchestration start failure:** Backend returns HTTP 503 with a clear message (mirrors current behavior).

## Hosting & Configuration

| Component | Host | Free? | Notes |
|-----------|------|-------|-------|
| Frontend (Next.js) | Vercel | Yes | `NEXT_PUBLIC_API_URL` → backend URL |
| Backend (FastAPI) | Render free | Yes | Spins down when idle; acceptable for demo |
| Postgres + pgvector | Supabase or Neon free | Yes | `DATABASE_URL`; enable `pgvector` extension |
| Functions (Durable) | Azure Consumption | Metered (~free grant) | Durable orchestrator + activities |
| Storage (Durable state) | Azure Storage | Metered (cents) | Required by Durable runtime |

### Environment variables

Backend adds:
```
FUNCTIONS_ORCHESTRATOR_URL=https://<app>.azurewebsites.net/api/orchestrators/start
FUNCTIONS_KEY=<function key>
```
and removes `AZURE_SERVICEBUS_CONNECTION_STRING` from the analysis path.

Functions keep:
```
DATABASE_URL, OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL,
BACKEND_CALLBACK_URL, ALPHA_VANTAGE_API_KEYS,
AzureWebJobsStorage=<storage connection>
```
and remove `AZURE_SERVICEBUS_CONNECTION_STRING`.

`backend/app/config.py` gains `functions_orchestrator_url` and `functions_key`; the Service Bus setting is dropped.

## Testing Strategy

- **Functions unit tests** (`functions/tests/unit/`): `activity_financials_ingest` reuse-vs-fetch logic, financials→text formatting, and `get_api_key()` stateless rotation. Mock Alpha Vantage HTTP and DB.
- **Backend tests**: `OrchestrationClient.start_analysis` posts the right payload (mock `requests`); `/analysis/request` returns 202 with a task_id; RAG `build_context_string` includes financials citations with quarter + statement type.
- **Frontend tests**: `DualAnalysisView` renders both columns, shows agreement chip when both signals present, and shows "LLM not run" state when LLM absent (extends existing `MLAnalysisView.test.tsx` patterns).
- **Migration test**: `quarterly_financials` table creates and the unique constraint rejects duplicate `(ticker, fiscal_quarter)`.

## Correctness Properties

These invariants must hold and are the basis for the testing strategy.

### Property 1: On-demand only
No `quarterly_financials` row or `quarterly_financials` embedding exists for a ticker unless a user has requested analysis for that ticker.

**Validates: Requirements 1.1, 2.1**

### Property 2: Single fetch per quarter
For any `(ticker, fiscal_quarter)`, financial statements are fetched from Alpha Vantage at most once; subsequent runs reuse the stored row (enforced by the unique constraint).

**Validates: Requirements 1.4, 1.5**

### Property 3: Embedding idempotency
Re-ingesting the same `(ticker, fiscal_quarter, statement_type)` does not create duplicate embedding rows.

**Validates: Requirements 2.4**

### Property 4: Fan-in completeness
`task_all` always resolves; every fanned-out activity returns a typed result with a `status` field and never propagates an unhandled exception to the orchestrator.

**Validates: Requirements 7.3, 7.5**

### Property 5: Graceful degradation
A failed or absent LLM pipeline still yields a persisted report containing complete ML results; a failed financials ingest still yields a complete ML (+LLM) report.

**Validates: Requirements 1.6, 5.3, 5.4, 6.4, 7.5**

### Property 6: Citation fidelity
Every financials-derived chat citation names the statement type and fiscal quarter of the passage it came from.

**Validates: Requirements 2.2, 3.3, 3.4**

### Property 7: Vector dimension stability
All embeddings written to `financial_documents` are 1536-dimensional, matching the existing column; no dimension migration occurs.

**Validates: Requirements 2.1, 2.3**

### Property 8: No Service Bus or Celery on the analysis path
The analysis request-to-report flow performs no Service Bus or Celery operations.

**Validates: Requirements 8.1, 8.2, 8.4**

## Migration / Removal Plan

1. Add `OrchestrationClient`; switch `analysis.py` off Service Bus.
2. Add `activity_financials_ingest`, financials Alpha Vantage fetchers, and `financials_text.py`.
3. Add `quarterly_financials` model + Alembic migration.
4. Update orchestrator fan-out + aggregate comparison block.
5. Normalize LLM activity output shape.
6. Add `DualAnalysisView` + chat citation labels.
7. Delete Service Bus + Celery code paths; prune `docker-compose.yml` (drop Service Bus emulator, MSSQL, Azurite, Redis broker).
8. Update `README.md` / `DEPLOYMENT.md` for the new hosting + run instructions.
