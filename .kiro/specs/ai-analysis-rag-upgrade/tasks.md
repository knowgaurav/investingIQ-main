# Implementation Plan

## Overview

This plan implements the AI analysis + RAG upgrade in dependency order: data model first, then the financials ingest pipeline (Alpha Vantage fetchers → text → persistence/embedding → Durable activity), then orchestration rewiring (financials fan-out, dual-analysis normalization, HTTP starter replacing Service Bus), then frontend surfacing, then removal of legacy Service Bus/Celery code, and finally tests and docs. Most tasks extend existing files rather than introducing new abstractions.

## Tasks

- [x] 1. Add quarterly_financials data model and migration
  - Add `QuarterlyFinancials` SQLAlchemy model to `backend/app/models/database.py` with columns `id`, `ticker`, `fiscal_quarter`, `income_statement` (JSON), `balance_sheet` (JSON), `cash_flow` (JSON), `earnings` (JSON), `fetched_at`, and a `UniqueConstraint("ticker", "fiscal_quarter")`
  - Create an Alembic migration in `backend/alembic/versions/` that creates the `quarterly_financials` table with the unique constraint
  - _Requirements: 1.2, 1.4, 1.5_

- [x] 2. Extend Alpha Vantage client with quarterly statement fetchers and stateless key rotation
- [x] 2.1 Replace Redis-based key rotation with stateless selection
  - In `functions/shared/alpha_vantage.py`, change `get_api_key()` to use `random.choice(keys)` over the configured pool and remove the `redis` import, `_get_redis()`, `REDIS_URL`, and `REDIS_KEY_INDEX`
  - _Requirements: 1.3, 8.2_
- [x] 2.2 Add quarterly statement fetch functions
  - Add `fetch_income_statement`, `fetch_balance_sheet`, and `fetch_cash_flow` to `functions/shared/alpha_vantage.py`, each calling the matching Alpha Vantage function, using `get_api_key()`, detecting the `Note`/`Information` rate-limit responses (return a `_rate_limited` flag), and returning the latest quarterly report dict plus its `fiscalDateEnding`
  - _Requirements: 1.2, 1.3, 1.6_

- [x] 3. Add financials-to-text conversion module
  - Create `functions/shared/financials_text.py` with `income_statement_to_text`, `balance_sheet_to_text`, `cash_flow_to_text`, and `earnings_to_text` functions that turn a statement dict into a compact labeled passage including ticker, fiscal quarter, statement type, and the key line items
  - _Requirements: 2.1, 2.2_

- [x] 4. Add financials persistence and embedding helpers
- [x] 4.1 Add quarterly financials DB helpers to functions shared layer
  - In `functions/shared/db_utils.py`, add `get_quarterly_financials(ticker, fiscal_quarter)` (returns existing row or None) and `save_quarterly_financials(ticker, fiscal_quarter, statements)` writing to the `quarterly_financials` table
  - _Requirements: 1.4, 1.5_
- [x] 4.2 Add dedup-aware financials embedding helper
  - In `functions/shared/embedding_utils.py`, add `embed_financials_passage(ticker, fiscal_quarter, statement_type, content, chunk_index)` that checks for an existing `financial_documents` row with matching `(ticker, doc_type="quarterly_financials", fiscal_quarter, statement_type, chunk_index)` metadata before inserting, and stores `doc_type="quarterly_financials"` with metadata `{fiscal_quarter, statement_type, chunk_index}`
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 5. Create activity_financials_ingest Durable activity
  - Create `functions/activity_financials_ingest/__init__.py` and `function.json` (activityTrigger) that: fetches the four quarterly statements, resolves the latest `fiscal_quarter`, returns `status="reused"` if the financials already exist for `(ticker, fiscal_quarter)`, otherwise persists them, converts each statement to text, chunks, and embeds via the helpers; returns `{"type": "financials_ingest", "status": "ok|reused|unavailable", "fiscal_quarter": ...}` and never raises
  - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4_

- [x] 6. Wire financials ingest into the orchestrator fan-out
  - In `functions/orchestrator_func/__init__.py`, add `activity_financials_ingest` to the parallel `parallel_tasks` list so it fans out alongside ML/LLM analysis and joins at `task_all`
  - _Requirements: 7.2, 7.3_

- [x] 7. Normalize LLM analysis output and make fanned-out activities failure-safe
- [x] 7.1 Normalize the LLM activity result shape
  - In `functions/activity_llm_analysis/__init__.py`, map the analyzer output to `{outlook, sentiment: {label, score}, insight, sources}` under `data`, and wrap the body so failures return `{"type": "llm_analysis", "status": "failed", "error": ...}` instead of raising
  - _Requirements: 5.1, 5.2, 5.4_
- [x] 7.2 Make ML activity failure-safe and tagged with status
  - In `functions/activity_ml_analysis/__init__.py`, add a `status` field (`"ok"`/`"failed"`) to the returned dict and wrap the body so failures return a typed result instead of raising
  - _Requirements: 4.4, 7.5_

- [x] 8. Add dual-analysis comparison in aggregation
  - In `functions/activity_aggregate/__init__.py`, derive the ML signal from the prediction trend and the LLM signal from `outlook`, and when both are present add `dual_comparison: {ml_signal, llm_signal, agreement}` to the result; omit it when LLM did not run or failed, and record `llm_analysis.status` and `financials_ingest` status in the saved report
  - _Requirements: 5.3, 6.3, 6.4, 7.5_

- [x] 9. Replace Service Bus orchestration with HTTP Durable starter in the backend
- [x] 9.1 Add OrchestrationClient and config
  - Create `backend/app/services/orchestration_client.py` with `OrchestrationClient.start_analysis(ticker, task_id, llm_config)` that POSTs to the Durable starter URL with the function key; add `functions_orchestrator_url` and `functions_key` to `backend/app/config.py` and remove `azure_servicebus_connection_string`
  - _Requirements: 7.1, 8.1_
- [x] 9.2 Switch the analysis route to the orchestration client
  - Update `backend/app/api/routes/analysis.py` to use `OrchestrationClient` instead of `get_orchestrator()`, keeping the `task_id` generation and `AnalysisTaskResponse` contract
  - _Requirements: 7.1, 8.1_

- [x] 10. Make RAG chat financials-aware with quarter/statement citations
  - In `backend/app/services/rag_service.py`, update `build_context_string` to format `quarterly_financials` sources with their `fiscal_quarter` and `statement_type` from metadata, and return a note when no `quarterly_financials` rows exist for the ticker so `chat.py` can prompt the user to run an analysis first
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 11. Add DualAnalysisView frontend component
  - Create `frontend/src/components/DualAnalysisView.tsx` rendering ML results (forecast, RSI/MACD/Bollinger, VADER sentiment) and LLM results (outlook, LLM sentiment, narrative insight) in two columns, with an agreement chip driven by `dual_comparison` and an "LLM analysis not run" state when the LLM section is absent or failed
  - Wire it into `frontend/src/app/analyze/[ticker]/page.tsx` using the report `data` from the SSE `done` event
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 12. Show financials citations in chat UI
  - In `frontend/src/app/chat/page.tsx`, render `quarterly_financials` citations using `statement_type` + `fiscal_quarter` labels
  - _Requirements: 3.3, 3.4_

- [x] 13. Remove Service Bus, Celery, and emulator dependencies
- [x] 13.1 Delete Service Bus and Celery analysis code
  - Delete `backend/app/services/service_bus.py`, the Celery app/tasks under `backend/app/tasks/` and `backend/app/workers/` that drive the analysis pipeline, and remove their imports/usages
  - _Requirements: 8.1, 8.2, 8.4_
- [x] 13.2 Prune docker-compose and Functions Service Bus references
  - Remove the Service Bus emulator, MSSQL, Azurite, and Redis broker services from `docker-compose.yml`, and remove `servicebus_connection` from `functions/shared/config.py`
  - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [x] 14. Add tests for new behavior
- [x] 14.1 Functions unit tests
  - Add tests under `functions/tests/unit/` for `activity_financials_ingest` reuse-vs-fetch, financials-to-text formatting, dedup-aware embedding, and stateless `get_api_key()` rotation (mock Alpha Vantage HTTP and DB)
  - _Requirements: 1.4, 1.5, 2.3, 2.4_
- [x] 14.2 Backend tests
  - Add tests for `OrchestrationClient.start_analysis` payload (mock `requests`), `/analysis/request` returning 202 with a task_id, and `build_context_string` including financials citations with quarter + statement type
  - _Requirements: 3.3, 7.1, 8.1_
- [x] 14.3 Frontend tests
  - Add tests for `DualAnalysisView` rendering both columns, showing the agreement chip when both signals are present, and showing the "LLM not run" state when LLM is absent
  - _Requirements: 6.1, 6.3, 6.4_

- [x] 15. Update documentation and environment configuration
  - Update `README.md` and `DEPLOYMENT.md` to describe the Durable-only orchestration (no Service Bus/Celery/Azurite), the free hosting targets (Vercel, Render free, Supabase/Neon free Postgres+pgvector), the Azure Functions + Storage account as the only metered piece, the new backend env vars (`FUNCTIONS_ORCHESTRATOR_URL`, `FUNCTIONS_KEY`), and that quarterly financials come from Alpha Vantage with rotating keys plus how caching keeps usage within the free limit
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4_

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2.1", "2.2", "7.1", "7.2", "9.1"] },
    { "wave": 2, "tasks": ["3", "4.1", "9.2"] },
    { "wave": 3, "tasks": ["4.2", "10", "13.1"] },
    { "wave": 4, "tasks": ["5", "13.2"] },
    { "wave": 5, "tasks": ["6"] },
    { "wave": 6, "tasks": ["8"] },
    { "wave": 7, "tasks": ["11"] },
    { "wave": 8, "tasks": ["12", "14.1", "14.2", "14.3", "15"] }
  ],
  "dependencies": {
    "1": [],
    "2.1": [],
    "2.2": [],
    "7.1": [],
    "7.2": [],
    "9.1": [],
    "3": ["2.2"],
    "4.1": ["1"],
    "9.2": ["9.1"],
    "4.2": ["3"],
    "10": ["1", "4.1"],
    "13.1": ["9.2"],
    "5": ["2.2", "3", "4.1", "4.2"],
    "13.2": ["9.2"],
    "6": ["5"],
    "8": ["6", "7.1", "7.2"],
    "11": ["8"],
    "12": ["11"],
    "14.1": ["5"],
    "14.2": ["9.2", "10"],
    "14.3": ["11"],
    "15": ["13.2"]
  }
}
```

Reading of the graph:

- **Task 1** (data model) → unblocks **4.1** (financials DB helpers).
- **Tasks 2.1, 2.2, 3** → unblock **4.2** and **5** (the ingest activity needs fetchers, text conversion, and embedding helpers).
- **Task 5** → **6** (wire into orchestrator).
- **Tasks 6, 7.1, 7.2** → **8** (aggregation needs normalized ML/LLM outputs and the financials result).
- **Task 8** → **11** (frontend dual view consumes the aggregated report) → **12** (chat citations).
- **Task 9.1** → **9.2** (backend starter), independent of the financials chain.
- **Task 10** (RAG financials-aware chat) depends on **1**/**4.2** existing financials data shape.
- **Task 13.x** (removal) after **9.2** so nothing still imports Service Bus/Celery.
- **Task 14.x** tests after their respective features; **15** docs last.

## Notes

- Embedding model and vector dimension stay `text-embedding-3-small` / `Vector(1536)`; no vector migration.
- All fanned-out activities must return a typed `status` and never raise, to preserve fan-in completeness.
- Redis is removed from the deployed analysis path; key rotation becomes stateless random selection.
- Per project principles: extend existing files, avoid new abstractions, and do not add fallback behaviors beyond the specified graceful-degradation paths.

