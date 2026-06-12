"""
Centralized configuration — all environment variables loaded via Pydantic BaseSettings.
Defaults are tuned for local development (SQLite, Ollama, no API keys required).
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file if it exists
load_dotenv()


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./sentinel.db"

    # ── LLM — Local (Ollama) vs Production (Groq) ────────────────────────
    USE_LOCAL_LLM: bool = True
    OLLAMA_MODEL: str = "gemma3:1b"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── Deep Learning Models ──────────────────────────────────────────────
    FINBERT_MODEL: str = "ProsusAI/finbert"
    ABSA_MODEL: str = "yangheng/deberta-v3-base-absa-v1.1"

    # ── Data Source API Keys ──────────────────────────────────────────────
    FRED_API_KEY: str = ""
    NEWS_API_KEY: str = ""

    # ── Email Delivery ────────────────────────────────────────────────────
    RESEND_API_KEY: str = ""
    DELIVERY_EMAIL: str = "recipient@example.com"

    # ── Watchlist Defaults ────────────────────────────────────────────────
    DEFAULT_TICKERS: str = "AAPL,MSFT,GOOGL,NVDA,TSLA"
    DEFAULT_KEYWORDS: str = "earnings,merger,acquisition,bankruptcy,FDA"
    DEFAULT_INDICATORS: str = "GDP,CPIAUCSL,UNRATE,FEDFUNDS,DGS10,UMCSENT"

    # ── Scheduling ────────────────────────────────────────────────────────
    SCHEDULE_CRON: str = "0 7 * * *"  # 7 AM daily — display only
    REPORT_TIMEZONE: str = "Asia/Kolkata"

    # ── Server ────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
