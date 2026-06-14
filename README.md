---
title: Business Intelligence Sentinel
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Business Intelligence Sentinel 🛡️

An autonomous AI system that crawls financial data sources, runs a two-stage deep learning sentiment pipeline over collected news, reasons over signals using a local LLM, and delivers a structured intelligence report entirely without human intervention.

## Architecture

*   **Data Collection**: yfinance, FRED, NewsAPI, RSS feeds, SEC EDGAR
*   **Deep Learning (Stage 1)**: Document-level sentiment using `ProsusAI/finbert`
*   **Deep Learning (Stage 2)**: Aspect-Based Sentiment Analysis using `yangheng/deberta-v3-base-absa-v1.1`
*   **Reasoning (LLM)**: Local fallback using Ollama (Gemma 3B), production using Groq (Llama 3.3 70B)
*   **Backend**: FastAPI, SQLAlchemy, APScheduler
*   **Frontend**: React (Vite), Recharts, Lucide Icons

## Quick Start

### 1. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys (FRED, NewsAPI, Resend, Groq). You can use the system locally without keys by relying on RSS feeds, yfinance, and local Ollama inference.

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

Access the dashboard at `http://localhost:3000`.

### 3. Run Locally (Development)

**Backend:**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Dashboard Features

*   **Agent Status**: Real-time health check for deep learning models.
*   **Signal Visualization**: View timeseries sentiment scores and aspect-based distributions.
*   **Intelligence Archive**: Browse generated markdown reports with detailed market overviews and material event alerts.
*   **Cost Tracker**: Monitor token consumption across inference requests.

## Pipeline Trigger

The pipeline runs automatically based on the schedule configured in the dashboard (or via cron-job.org pointing to `/api/trigger`). You can also initiate an ad-hoc run using the "Manual Override" button in the dashboard.
