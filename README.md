<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/knowgaurav/investingIQ-main">
    <img src="images/logo.png" alt="Logo"  height="40">
  </a>

<h3 align="center">InvestingIQ – Algorithmic Trading Dashboard Powered By AI & ML Built Using ReactJS & Python</h3>

  <p align="center">
InvestingIQ is a user-friendly online platform built with ReactJS, Python, and Streamlit, designed to assist retail investors in making informed decisions in the stock market. It offers comprehensive stock information, including current and historical stock prices, company news, and management insights. The platform also features two machine learning models, Facebook's Prophet and Random Forest, for predicting future stock prices. Additionally, it provides sentiment analysis to gauge public confidence in the company. With these powerful tools and data-driven insights, InvestingIQ simplifies the investment process, allowing investors to make hassle-free decisions with confidence.
    <br />
    <a href="https://github.com/knowgaurav/investingIQ-main">View Demo</a>
    ·
    <a href="https://github.com/knowgaurav/investingIQ-main/issues">Report Bug</a>
    ·
    <a href="https://github.com/knowgaurav/investingIQ-main/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li><a href="#usage">About</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project
<p align="center">
  <a href="https://github.com/knowgaurav/investingIQ-main">
    <img src="images/project-1.jpg" alt="Logo" >
  </a>
</p>
<p align="center">
  <a href="https://github.com/knowgaurav/investingIQ-main">
    <img src="images/project-2.jpg" alt="Logo" >
  </a>
<p align="center">
  <a href="https://github.com/knowgaurav/investingIQ-main">
    <img src="images/project-3.jpg" alt="Logo" >
  </a>
</p>
<p align="center">
  <a href="https://github.com/knowgaurav/investingIQ-main">
    <img src="images/project-4.jpg" alt="Logo" >
  </a>
</p>
<p align="center">
  <a href="https://github.com/knowgaurav/investingIQ-main">
    <img src="images/project-5.jpg" alt="Logo" >
  </a>
</p>


<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
* ![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
* ![Keras](https://img.shields.io/badge/Keras-%23D00000.svg?style=for-the-badge&logo=Keras&logoColor=white)
* ![TensorFlow](https://img.shields.io/badge/TensorFlow-%23FF6F00.svg?style=for-the-badge&logo=TensorFlow&logoColor=white)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Details

**InvestingIQ: Stock Market Analysis and Prediction Platform**

Welcome to the InvestingIQ GitHub repository! This project is a cutting-edge online platform designed to empower retail investors with comprehensive information and powerful tools for stock market analysis. Built using ReactJS, Python, and Streamlit, InvestingIQ serves as a one-stop destination for investors to make informed decisions with ease.

**Key Features:**

1. **Comprehensive Stock Information:** Investors can access a wealth of information about various stocks in a user-friendly format. The platform provides current and historical stock price data, latest news updates about the company, and other relevant details to keep investors well-informed.

2. **Quantitative Analysis Made Easy:** With InvestingIQ, investors can perform quantitative analysis effortlessly. The platform offers various metrics, including Profitability, Liquidity, and Asset Turnover, formulated from the latest quarter balance sheet of each company. These metrics provide valuable insights into the company's financial performance.

3. **Machine Learning Models:** InvestingIQ incorporates two powerful machine learning models – Facebook's Prophet and Random Forest. These models independently predict the future stock prices of companies, aiding investors in understanding potential stock performance.

4. **Company Management Insights:** Each stock profile includes a dedicated section that sheds light on how the company is managed by the current leadership. This feature helps investors evaluate the overall competence and strategy of the company's management.

5. **Sentiment Analysis:** The platform utilizes a sentiment analysis model to assess the company's perception on various social network sites and news outlets. This analysis provides an understanding of the general public's confidence in the company.

**Benefits:**

- **Data-Driven Decision Making:** InvestingIQ empowers investors to make data-driven decisions by providing a wealth of financial and sentiment data for each company. This enables investors to evaluate investment opportunities with greater confidence.

- **Predictive Insights:** The inclusion of machine learning models enhances the platform's value by providing future stock price predictions. Investors can factor in these predictions while formulating their investment strategies.

- **User-Friendly Interface:** The user interface of InvestingIQ is designed to be intuitive and easy to navigate. Investors, regardless of their expertise level, can seamlessly access and comprehend the information provided.

- **Hassle-Free Investing:** By consolidating comprehensive information and analysis tools, InvestingIQ simplifies the investment process for retail investors. This one-stop platform streamlines the research and decision-making process.

Whether you are a seasoned investor or a newcomer to the stock market, InvestingIQ offers valuable insights and predictions to support your investment journey. The combination of ReactJS, Python, and Streamlit ensures a seamless and interactive experience, making InvestingIQ the go-to platform for retail investors seeking to navigate the stock market with confidence.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ARCHITECTURE -->
## Architecture & Deployment (v2)

InvestingIQ runs as a Next.js frontend, a FastAPI backend, PostgreSQL + pgvector, and an Azure Durable Functions app that performs the heavy analysis in parallel. Everything except the Functions app runs on free tiers.

```
Frontend (Vercel) ──SSE──> Backend (FastAPI, Render free) ──HTTP start──> Durable Orchestrator (Azure Functions)
        ▲                            │ progress callback (HTTP)                    │ fan-out / fan-in
        └────────────────────────────┘                                            ▼
                                   Postgres + pgvector (Supabase/Neon free) <── activity functions:
                                                                                  • fetch_data
                                                                                  • ml_analysis (ARIMA/Prophet/ETS, RSI/MACD/Bollinger, VADER)
                                                                                  • llm_analysis (LLM reasoning)
                                                                                  • financials_ingest (quarterly financials → pgvector)
                                                                                  • aggregate (combined dual-analysis report)
                                                                                  Azure Storage (Durable state)
```

### Orchestration

- The backend starts the analysis by POSTing to the Durable Functions HTTP starter (`/api/orchestrator/start`); it returns a `task_id` immediately.
- The orchestrator fans out ML analysis, LLM analysis, and quarterly-financials ingest as parallel activity functions, then fans in to a single report.
- Each fanned-out activity returns a typed `status` and never raises, so a failure in one (e.g. LLM not configured, financials unavailable) still produces a complete report.
- Progress is streamed to the frontend over SSE via an HTTP callback from the Functions app.
- There is no Azure Service Bus, Celery, or Azurite-backed queue in the analysis path — orchestration is Durable Functions only. (`docker-compose` runs just Postgres, Redis cache, and MLflow for local dev.)

### Quarterly Financials RAG

- Financials are ingested **on demand**: only for tickers a user actually queries, never the whole market.
- The `financials_ingest` activity fetches the income statement, balance sheet, cash flow, and earnings from **Alpha Vantage** using rotating API keys (`ALPHA_VANTAGE_API_KEYS`), caches them per `(ticker, fiscal_quarter)`, and embeds them into pgvector (the single vector store).
- Alpha Vantage's free tier allows ~25 requests/day per key; because each `(ticker, fiscal_quarter)` is fetched at most once and cached, plus key rotation, usage stays within the free limit for a demo.
- The RAG chat retrieves these passages and answers with citations naming the statement type and fiscal quarter (e.g. `Income Statement · 2024-12-31`).

### Dual Analysis (ML + LLM)

- The ML pipeline (statistical forecasts + technical indicators + lexicon sentiment) and the LLM pipeline run in parallel and are presented side by side under the **ML vs LLM** tab, with an agreement indicator when both produce a directional signal.

### Hosting

| Component | Host | Cost |
|-----------|------|------|
| Frontend (Next.js) | Vercel | Free |
| Backend (FastAPI) | Render | Free |
| Postgres + pgvector | Supabase or Neon | Free |
| Functions (Durable orchestrator + activities) | Azure Consumption | Free grant + metered |
| Storage (Durable runtime state) | Azure Storage | Metered (cents) |

The Azure Functions app and its required Storage account are the only metered components.

### Environment Variables

Backend (`backend/.env`):
```env
DATABASE_URL=postgresql://...
FUNCTIONS_ORCHESTRATOR_URL=https://<your-function-app>.azurewebsites.net/api/orchestrator/start
FUNCTIONS_KEY=<function key, empty for local anonymous>
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://ai.megallm.io/v1
LLM_MODEL=deepseek-ai/deepseek-v3.1
MLFLOW_TRACKING_URI=http://localhost:5000
RATE_LIMIT=100/minute
```

Functions (`functions/.env` or app settings):
```env
DATABASE_URL=postgresql://...
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://ai.megallm.io/v1
LLM_MODEL=deepseek-ai/deepseek-v3.1
BACKEND_CALLBACK_URL=https://<your-backend>
ALPHA_VANTAGE_API_KEYS=key1,key2,key3
AzureWebJobsStorage=<azure storage connection>
```

Frontend (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=https://<your-backend>
```

### Running locally

```sh
docker-compose up -d              # Postgres + pgvector, Redis cache, MLflow
cd backend && alembic upgrade head && uvicorn app.main:app --reload --port 8000
cd functions && func start        # Durable orchestrator + activities (needs Azure Functions Core Tools)
cd frontend && npm run dev
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Gaurav Singh - [@knowgaurav01](https://twitter.com/knowgaurav01) - hello@sgaurav.me

Project Link: [https://github.com/knowgaurav/investingIQ-main](https://github.com/github_username/interview-prep)

<p align="right">(<a href="#readme-top">back to top</a>)</p>





<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
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
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
[C++]: https://img.shields.io/badge/c++-%2300599C.svg?style=for-the-badge&logo=c%2B%2B&logoColor=white
[C++-url]: https://isocpp.org/
[Codeforces]: https://img.shields.io/badge/Codeforces-445f9d?style=for-the-badge&logo=Codeforces&logoColor=white
[Codeforces-url]: https://codeforces.com/
[LeetCode]: https://img.shields.io/badge/LeetCode-000000?style=for-the-badge&logo=LeetCode&logoColor=#d16c06
[LeetCode-url]: https://leetcode.com
