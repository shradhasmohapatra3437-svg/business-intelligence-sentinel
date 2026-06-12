"""
All SQLAlchemy table definitions — 5 tables.
UUID primary keys, JSON columns for structured data, proper relationships.
"""

import uuid
import datetime
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean,
    DateTime, Date, JSON, Enum, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


# ── Reports ───────────────────────────────────────────────────────────────

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False)
    content_markdown = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    risk_level = Column(
        String(20), nullable=False, default="low"
    )  # low / medium / high / critical
    key_findings = Column(JSON, nullable=True)
    sources_used = Column(JSON, nullable=True)
    token_usage = Column(JSON, nullable=True)  # {prompt_tokens, completion_tokens}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    run_id = Column(String(36), ForeignKey("pipeline_jobs.id"), nullable=True)

    # Relationship
    pipeline_job = relationship("PipelineJob", back_populates="report")


# ── Pipeline Jobs ─────────────────────────────────────────────────────────

class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    trigger_type = Column(
        String(20), nullable=False, default="manual"
    )  # scheduled / manual
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending / running / complete / failed
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    total_tokens = Column(Integer, nullable=True, default=0)
    model_used = Column(String(100), nullable=True)

    # Relationships
    report = relationship("Report", back_populates="pipeline_job", uselist=False)
    sentiment_logs = relationship("SentimentLog", back_populates="pipeline_job")


# ── Sentiment Logs ────────────────────────────────────────────────────────

class SentimentLog(Base):
    __tablename__ = "sentiment_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    ticker = Column(String(20), index=True, nullable=False)
    headline = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=True)

    # FinBERT document-level scores
    positive_score = Column(Float, nullable=True)
    negative_score = Column(Float, nullable=True)
    neutral_score = Column(Float, nullable=True)

    # DeBERTa ABSA output
    aspects_json = Column(JSON, nullable=True)  # {"iPhone sales": 0.91, "supply chain": -0.88}
    absa_ran = Column(Boolean, default=False)

    news_count = Column(Integer, nullable=True)
    trading_date = Column(Date, nullable=True)
    close_price = Column(Float, nullable=True)

    run_at = Column(DateTime, default=datetime.datetime.utcnow)
    run_id = Column(String(36), ForeignKey("pipeline_jobs.id"), nullable=True)

    # Relationship
    pipeline_job = relationship("PipelineJob", back_populates="sentiment_logs")


# ── Watchlist Configuration ───────────────────────────────────────────────

class WatchlistConfig(Base):
    __tablename__ = "watchlist_config"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tickers = Column(JSON, nullable=False, default=list)
    news_keywords = Column(JSON, nullable=True, default=list)
    economic_indicators = Column(JSON, nullable=True, default=list)
    delivery_email = Column(String(255), nullable=True)
    schedule_cron = Column(String(50), nullable=True, default="0 7 * * *")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


# ── Collected Data Cache ──────────────────────────────────────────────────

class CollectedDataCache(Base):
    __tablename__ = "collected_data_cache"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source = Column(String(100), nullable=False)  # yfinance / fred / newsapi / rss / sec_edgar
    query_key = Column(String(500), nullable=False)
    data = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
