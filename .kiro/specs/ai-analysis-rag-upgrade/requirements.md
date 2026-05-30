# Requirements Document

## Introduction

This feature upgrades InvestingIQ along three axes that together demonstrate hands-on AI/ML and full-stack range:

1. **Quarterly Financials RAG** — Ingest and embed each company's quarterly financial records (income statement, balance sheet, cash flow, earnings) so users can ask natural-language questions and receive grounded, cited explanations from an LLM.
2. **Dual Analysis (ML + LLM)** — Produce two independent analyses for the same stock: a classical statistical/ML pipeline (forecasting, technical indicators, lexicon sentiment) and an LLM-based pipeline (reasoning over the same data), then present both side by side with a combined verdict.
3. **Azure Durable Functions Migration + Free Hosting** — Remove the Azure Service Bus, Celery, and storage-emulator orchestration. Replace it with an Azure Durable Functions fan-out/fan-in orchestration that runs the analysis sub-tasks in parallel. Host the frontend and backend on free tiers; keep only the Functions app on Azure.

The goal is a portfolio-quality application: modern AI/ML techniques (RAG, embeddings, ensemble/dual reasoning) on a clean, mostly-free, serverless-orchestrated full-stack architecture.

## Glossary

- **Durable_Orchestrator**: The Azure Durable Functions orchestrator that coordinates the analysis workflow using fan-out/fan-in.
- **Activity_Function**: An Azure Durable activity function that performs one unit of work (data fetch, ML analysis, LLM analysis, financials ingest, aggregation).
- **ML_Pipeline**: The classical analysis path using statistical/ML methods (ARIMA/Prophet/ETS forecasting, RSI/MACD/Bollinger technical indicators, VADER/TextBlob sentiment).
- **LLM_Pipeline**: The LLM-based analysis path that reasons over the same market/news data to produce forecasts, sentiment, and insights.
- **Dual_Analysis_Report**: The consolidated output presenting ML_Pipeline and LLM_Pipeline results side by side plus a combined verdict.
- **Quarterly_Financials**: A company's reported financial statements for a fiscal quarter (income statement, balance sheet, cash flow, earnings figures), sourced from Alpha Vantage.
- **Financials_RAG**: The retrieval-augmented pipeline that embeds Quarterly_Financials and retrieves relevant passages to answer user questions.
- **Vector_Store**: PostgreSQL with the pgvector extension storing document embeddings (the single vector store; no separate vector database).
- **AlphaVantage_Client**: The existing Alpha Vantage client that fetches market and fundamental data using a rotating pool of API keys (`ALPHA_VANTAGE_API_KEYS`) to stay within free-tier limits.
- **FastAPI_Backend**: The Python API server that starts orchestrations, serves reports, and handles RAG chat.
- **Next.js_Frontend**: The React web application.
- **Free_Tier_Host**: A hosting platform with a no-cost tier used for the frontend, backend, or database.
- **Stock_Ticker**: A unique identifier for a publicly traded stock (e.g., AAPL, TSLA, NVDA).

## Requirements

### Requirement 1: On-Demand Quarterly Financials Ingestion

**User Story:** As an investor, I want the system to capture a company's quarterly financial records only when I query that company, so that the knowledge base stays lean and costs nothing to maintain.

#### Acceptance Criteria

1. THE system SHALL ingest quarterly financial records only for a Stock_Ticker that a user has queried; it SHALL NOT pre-ingest records for the broader universe of listed companies.
2. WHEN a user queries a Stock_Ticker for the first time, an Activity_Function SHALL fetch the company's most recent quarterly financial records (income statement, balance sheet, cash flow, and earnings figures) from the AlphaVantage_Client.
3. THE AlphaVantage_Client SHALL use its rotating pool of API keys when fetching financial records to stay within the free-tier request limit.
4. WHEN quarterly financial records are fetched, THE system SHALL persist them associated with the Stock_Ticker and the fiscal quarter.
5. WHEN quarterly financial records already exist for the Stock_Ticker and fiscal quarter, THE system SHALL reuse the stored records instead of re-fetching from Alpha Vantage.
6. IF quarterly financial records are unavailable for a Stock_Ticker, THEN THE system SHALL record that financials are unavailable and continue the rest of the analysis.

### Requirement 2: Quarterly Financials RAG Embedding

**User Story:** As an investor, I want the quarterly financials embedded into the knowledge base, so that the assistant can retrieve and explain the relevant figures.

#### Acceptance Criteria

1. WHEN quarterly financial records are persisted, THE Financials_RAG SHALL convert them into text passages and embed each passage into the Vector_Store.
2. THE Financials_RAG SHALL tag each embedded passage with the Stock_Ticker, fiscal quarter, and statement type (income, balance sheet, cash flow, earnings).
3. WHEN embedding financial passages, THE Financials_RAG SHALL chunk large statements so that each chunk fits within the embedding model's input limit.
4. WHEN the same quarterly financials are ingested again, THE Financials_RAG SHALL avoid creating duplicate embeddings for the same Stock_Ticker, fiscal quarter, and statement type.

### Requirement 3: Financials-Aware RAG Chat

**User Story:** As an investor, I want to ask questions about a company's quarterly results, so that I can understand the financials without reading the full filings.

#### Acceptance Criteria

1. WHEN a user asks a question about a Stock_Ticker, THE Financials_RAG SHALL retrieve the top-k most relevant passages for that ticker from the Vector_Store, including quarterly financial passages.
2. WHEN relevant passages are retrieved, THE LLM SHALL generate an answer grounded in those passages.
3. WHEN an answer is generated, THE Chat interface SHALL display the answer with source citations identifying the fiscal quarter and statement type used.
4. WHEN a user asks about a metric present in the financials (e.g., revenue, net income, EPS, free cash flow), THE assistant SHALL report the figure and the quarter it came from.
5. IF no quarterly financials have been ingested for the Stock_Ticker, THEN THE assistant SHALL inform the user and offer to run an analysis first.

### Requirement 4: Dual Analysis — ML Pipeline

**User Story:** As an investor, I want a classical ML/statistical analysis, so that I can see data-driven signals independent of any LLM.

#### Acceptance Criteria

1. WHEN an analysis runs, THE ML_Pipeline SHALL compute price forecasts using statistical/ML forecasting methods.
2. WHEN an analysis runs, THE ML_Pipeline SHALL compute technical indicators (at minimum RSI, MACD, and Bollinger Bands) with directional signals.
3. WHEN an analysis runs, THE ML_Pipeline SHALL compute news sentiment using a lexicon/ML method (VADER/TextBlob) with an overall score and breakdown.
4. WHEN the ML_Pipeline completes, THE system SHALL produce a structured ML result containing forecast, technical, and sentiment sections.

### Requirement 5: Dual Analysis — LLM Pipeline

**User Story:** As an investor, I want an LLM-based analysis of the same stock, so that I can compare AI reasoning against the statistical model.

#### Acceptance Criteria

1. WHEN an analysis runs AND a valid LLM configuration is provided, THE LLM_Pipeline SHALL generate a directional outlook, an LLM sentiment assessment, and a narrative insight using the same underlying market and news data.
2. THE LLM_Pipeline SHALL return its result in a structured format that mirrors the ML result's sections (outlook, sentiment, insight) to allow side-by-side comparison.
3. WHEN no LLM configuration is provided, THE system SHALL produce the ML-only analysis and mark the LLM analysis as not run.
4. IF the LLM_Pipeline fails, THEN THE system SHALL still return the ML result and mark the LLM section as failed with a reason.

### Requirement 6: Dual Analysis Presentation

**User Story:** As an investor, I want to see the ML and LLM results next to each other, so that I can judge where they agree or disagree.

#### Acceptance Criteria

1. WHEN a Dual_Analysis_Report is displayed, THE Next.js_Frontend SHALL present the ML_Pipeline results and LLM_Pipeline results in a side-by-side layout.
2. THE Next.js_Frontend SHALL display, for each pipeline, its directional signal (e.g., bullish/bearish/neutral) and key supporting values.
3. WHEN both pipelines produced a directional signal, THE Dual_Analysis_Report SHALL display whether the two pipelines agree or disagree.
4. WHEN the LLM analysis was not run or failed, THE Next.js_Frontend SHALL clearly indicate that only the ML analysis is available.

### Requirement 7: Durable Functions Parallel Orchestration

**User Story:** As a developer, I want the analysis sub-tasks to run in parallel via Durable Functions, so that the system demonstrates serverless fan-out/fan-in and returns results faster.

#### Acceptance Criteria

1. WHEN an analysis is requested, THE FastAPI_Backend SHALL start a Durable_Orchestrator instance and return a task identifier immediately.
2. WHEN the Durable_Orchestrator runs, THE orchestrator SHALL fan out the independent analysis units (ML analysis, LLM analysis, financials ingest/embed) as parallel Activity_Functions.
3. WHEN all fanned-out Activity_Functions complete, THE Durable_Orchestrator SHALL fan in their outputs into a single Dual_Analysis_Report.
4. WHILE the orchestration is running, THE Next.js_Frontend SHALL display progress updates.
5. IF an Activity_Function fails, THEN THE Durable_Orchestrator SHALL still aggregate the successful results and mark the failed unit in the report.
6. WHEN the orchestration completes, THE system SHALL persist the Dual_Analysis_Report.

### Requirement 8: Removal of Azure Service Bus and Celery Orchestration

**User Story:** As a developer, I want the legacy queue-based orchestration removed, so that the architecture is simpler and centered on Durable Functions.

#### Acceptance Criteria

1. THE system SHALL NOT depend on Azure Service Bus for analysis orchestration.
2. THE system SHALL NOT depend on Celery or a Redis broker for analysis orchestration.
3. THE system SHALL NOT require the Azure Storage emulator (Azurite) or the Service Bus emulator for local development of the analysis flow.
4. WHEN the orchestration is migrated, THE system SHALL remove or replace code paths that reference Service Bus queues and Celery tasks for the analysis pipeline.
5. THE Azure Functions app SHALL retain the Azure Storage account required by the Durable Functions runtime.

### Requirement 9: Free-Tier Hosting

**User Story:** As the project owner, I want the frontend, backend, and database hosted on free tiers, so that the live demo costs nothing beyond the Azure Functions usage.

#### Acceptance Criteria

1. THE Next.js_Frontend SHALL be deployable to a Free_Tier_Host.
2. THE FastAPI_Backend SHALL be deployable to a Free_Tier_Host.
3. THE Vector_Store SHALL be a managed PostgreSQL instance with pgvector available on a free tier.
4. THE deployment configuration SHALL document the required environment variables for each hosted component.
5. THE only component that requires a paid/metered cloud account SHALL be the Azure Functions app and its required Azure Storage account.

### Requirement 10: Configuration and Documentation

**User Story:** As a developer, I want updated configuration and docs, so that the new architecture can be run locally and deployed.

#### Acceptance Criteria

1. THE system SHALL provide environment variable definitions for the FastAPI_Backend, the Functions app, and the Next.js_Frontend covering the new architecture.
2. THE documentation SHALL describe how to run the analysis flow locally using Durable Functions without Service Bus, Celery, or Azurite-backed queues.
3. THE documentation SHALL describe the deployment targets for frontend, backend, database, and Functions.
4. THE documentation SHALL state that quarterly financials are sourced from Alpha Vantage using rotating API keys, and SHALL describe the per-key free-tier limit and how caching keeps usage within it.
