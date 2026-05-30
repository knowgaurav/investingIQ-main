<!-- Improved compatibility of back to top link -->
<a name="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<br />
<div align="center">
  <a href="https://github.com/knowgaurav/investingIQ-main">
    <img src="images/logo.png" alt="Logo" height="40">
  </a>

<h3 align="center">InvestingIQ</h3>

  <p align="center">
    AI-powered financial analysis platform with real-time stock insights, ML predictions, and LLM-driven analysis
    <br />
    <a href="https://github.com/knowgaurav/investingIQ-main">View Demo</a>
    ·
    <a href="https://github.com/knowgaurav/investingIQ-main/issues">Report Bug</a>
    ·
    <a href="https://github.com/knowgaurav/investingIQ-main/issues">Request Feature</a>
  </p>
</div>

## About The Project

InvestingIQ is a modern financial analysis platform that combines machine learning predictions with LLM-powered insights to help investors make data-driven decisions. The platform provides real-time stock data, technical analysis, sentiment analysis, and AI-generated investment recommendations.

### Key Features

- **Stock Search & Validation** - Autocomplete search and ticker validation via Alpha Vantage
- **Market Data + Earnings** - Price history, company overview, and earnings data
- **ML Forecasting** - ARIMA + Prophet + ETS forecasts with Random Forest signals
- **Technical Indicators** - RSI, MACD, Bollinger Bands, support/resistance, and volume signals
- **Sentiment Analysis** - VADER/TextBlob plus optional LLM sentiment breakdowns
- **LLM Analysis with Tools** - Structured JSON insights using tool calling over cached market data
- **Multi-Provider LLMs** - OpenAI, Anthropic, Google, OHMYGPT, OpenRouter with key verification
- **RAG Chat** - pgvector embeddings and conversation history for context-aware chat
- **Live Progress Streaming** - SSE updates with WebSocket fallback
- **Performance + Ops** - Redis caching, rate limiting, health checks, MLflow tracking
- **Polished UI** - Dark mode, recent searches, floating LLM settings

### Built With

[![Next.js][Next.js]][Next-url]
[![React][React.js]][React-url]
[![TypeScript][TypeScript]][TypeScript-url]
[![TailwindCSS][TailwindCSS]][TailwindCSS-url]
[![FastAPI][FastAPI]][FastAPI-url]
[![Python][Python]][Python-url]
[![PostgreSQL][PostgreSQL]][PostgreSQL-url]
[![Redis][Redis]][Redis-url]
[![Azure Functions][AzureFunctions]][AzureFunctions-url]

Plus: Azure Service Bus, pgvector, LangChain, MLflow, Azure Storage (Azurite for local dev).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Architecture

```
┌─────────────────┐   SSE/WS   ┌─────────────────────┐   ┌──────────────────┐
│    Frontend     │◀──────────▶│  Backend (FastAPI)  │──▶│ Azure Service Bus │
│   (Next.js)     │            └─────────────────────┘   └────────┬─────────┘
└─────────────────┘                    │                          │
                                       ▼                          ▼
                               ┌─────────────────┐      ┌─────────────────┐
                               │ PostgreSQL      │      │ Azure Functions │
                               │ + pgvector      │      │   (analysis)    │
                               └─────────────────┘      └─────────────────┘
                                       │
                                       ▼
                                   ┌─────────┐
                                   │ Redis   │
                                   └─────────┘
```

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Next.js 15, React 19, TailwindCSS | UI, SSE progress, charts, LLM settings |
| Backend API | FastAPI, SQLAlchemy, LangChain | REST + SSE, RAG chat, LLM verification, health/rate limiting |
| Orchestration | Azure Service Bus | Queue-driven fan-out/fan-in analysis pipeline |
| Functions | Azure Functions | Data fetch, ML + LLM analysis, aggregation |
| Database | PostgreSQL + pgvector | Reports, chat history, vector embeddings |
| Cache | Redis | Cached stock/news/earnings for LLM tools |
| Observability | MLflow | LLM prompt and latency tracking |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose (Redis, Postgres + pgvector, Service Bus emulator + MSSQL, Azurite, MLflow)
- Azure Functions Core Tools (for running functions locally)

### Installation

1. Clone the repository
   ```sh
   git clone https://github.com/knowgaurav/investingIQ-main.git
   cd investingIQ-main
   ```

2. Start infrastructure services
   ```sh
   docker-compose up -d
   ```
   This starts Redis, Postgres + pgvector, the Service Bus emulator (with MSSQL), Azurite, and MLflow.

3. Set up the backend
   ```sh
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Create `backend/.env` with the required variables (see Environment Variables).

4. Set up Azure Functions
   ```sh
   cd functions
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Update `functions/local.settings.json` or set the same variables via environment (see Environment Variables).

5. Set up the frontend
   ```sh
   cd frontend
   npm install
   ```

6. Run database migrations
   ```sh
   cd backend
   alembic upgrade head
   ```

### Environment Variables

Backend (`backend/.env`):
```env
# Core
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/investingiq
REDIS_HOST=localhost
REDIS_PORT=6379
AZURE_SERVICEBUS_CONNECTION_STRING=Endpoint=sb://...

# LLM (OpenAI-compatible)
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://ai.megallm.io/v1
LLM_MODEL=deepseek-ai/deepseek-v3.1

# Data APIs
ALPHA_VANTAGE_API_KEY=your_key
NEWS_API_KEY=your_key

# Observability / Ops
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=investingiq-llm
RATE_LIMIT=100/minute
```

Functions (`functions/.env` or `functions/local.settings.json`):
```env
BACKEND_CALLBACK_URL=http://localhost:8000
AZURE_SERVICEBUS_CONNECTION_STRING=Endpoint=sb://...
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
AzureWebJobsStorage=UseDevelopmentStorage=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/investingiq
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://ai.megallm.io/v1
LLM_MODEL=deepseek-ai/deepseek-v3.1
ALPHA_VANTAGE_API_KEY=your_key
ALPHA_VANTAGE_API_KEYS=key1,key2,key3
```

Frontend (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running the Application

1. Start the backend
   ```sh
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. Start the frontend
   ```sh
   cd frontend
   npm run dev
   ```

3. Start Azure Functions locally (required for analysis pipeline + progress updates)
   ```sh
   cd functions
   func start
   ```

Access the application at `http://localhost:3000`

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check with dependency status |
| `/api/health/live` | GET | Liveness probe |
| `/api/health/ready` | GET | Readiness probe |
| `/api/health/cache` | GET | Cache stats |
| `/api/health/circuits` | GET | Circuit breaker status |
| `/api/v1/stocks/search` | GET | Stock search autocomplete |
| `/api/v1/stocks/{ticker}/validate` | GET | Validate ticker |
| `/api/v1/analysis/request` | POST | Queue analysis (ML-only or ML+LLM) |
| `/api/v1/analysis/status/{task_id}` | GET | Status fallback |
| `/api/v1/events/{task_id}` | GET | SSE progress stream |
| `/api/v1/callback/progress` | POST | Progress callback for Functions |
| `/api/v1/chat` | POST | Send message to RAG chat |
| `/api/v1/chat/conversations/{conversation_id}` | GET | Conversation history |
| `/api/v1/llm/verify` | POST | Verify LLM key |
| `/api/v1/llm/providers` | GET | List LLM providers/models |
| `/ws/analysis/{task_id}` | WS | WebSocket progress updates |

Full API documentation available at `/api/docs` when running the backend.
Versioned `/api/v1` endpoints are preferred; `/api` aliases are kept for backward compatibility.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Testing

```sh
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
pytest

# Functions tests
cd functions
pytest
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Deployment

The project supports deployment to:
- **Frontend**: Vercel (auto-deploy on push)
- **Backend**: Render (Docker-based)
- **Functions**: Azure Functions (GitHub Actions)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

Gaurav Singh - [@knowgaurav01](https://twitter.com/knowgaurav01) - hello@sgaurav.me

Project Link: [https://github.com/knowgaurav/investingIQ-main](https://github.com/knowgaurav/investingIQ-main)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/knowgaurav/investingIQ-main.svg?style=for-the-badge
[contributors-url]: https://github.com/knowgaurav/investingIQ-main/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/knowgaurav/investingIQ-main.svg?style=for-the-badge
[forks-url]: https://github.com/knowgaurav/investingIQ-main/network/members
[stars-shield]: https://img.shields.io/github/stars/knowgaurav/investingIQ-main.svg?style=for-the-badge
[stars-url]: https://github.com/knowgaurav/investingIQ-main/stargazers
[issues-shield]: https://img.shields.io/github/issues/knowgaurav/investingIQ-main.svg?style=for-the-badge
[issues-url]: https://github.com/knowgaurav/investingIQ-main/issues
[license-shield]: https://img.shields.io/github/license/knowgaurav/investingIQ-main.svg?style=for-the-badge
[license-url]: https://github.com/knowgaurav/investingIQ-main/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://in.linkedin.com/in/knowgaurav

[Next.js]: https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[TypeScript]: https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white
[TypeScript-url]: https://www.typescriptlang.org/
[TailwindCSS]: https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white
[TailwindCSS-url]: https://tailwindcss.com/
[FastAPI]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[PostgreSQL]: https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white
[PostgreSQL-url]: https://www.postgresql.org/
[Redis]: https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white
[Redis-url]: https://redis.io/
[AzureFunctions]: https://img.shields.io/badge/Azure_Functions-0062AD?style=for-the-badge&logo=azure-functions&logoColor=white
[AzureFunctions-url]: https://azure.microsoft.com/en-us/products/functions
