"""
Sequential pipeline orchestrator.
Called as a background task by POST /api/trigger.
Runs the complete data collection → sentiment → ABSA → LLM → report → email pipeline.
"""

import json
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import settings
from app.database import SessionLocal
from app.models import PipelineJob, Report, SentimentLog, WatchlistConfig

logger = logging.getLogger(__name__)


def run_pipeline(job_id: str, trigger_type: str = "manual"):
    """
    Main pipeline function. Updates PipelineJob status at each stage.
    Designed to run as a FastAPI BackgroundTask.
    """
    db = SessionLocal()

    try:
        # ── Step 1: Update job status to running ──────────────────────
        job = db.query(PipelineJob).filter(PipelineJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        job.status = "running"
        job.started_at = datetime.datetime.utcnow()
        db.commit()

        logger.info(f"🚀 Pipeline started — Job: {job_id}, Trigger: {trigger_type}")

        # Reset LLM token counters
        from app.services.llm import reset_token_usage, get_token_usage, get_model_name
        reset_token_usage()

        # ── Step 2: Load watchlist config ──────────────────────────────
        config = db.query(WatchlistConfig).first()
        if config and config.tickers:
            tickers = config.tickers
            keywords = config.news_keywords or []
            indicators = config.economic_indicators or []
        else:
            tickers = [t.strip() for t in settings.DEFAULT_TICKERS.split(",") if t.strip()]
            keywords = [k.strip() for k in settings.DEFAULT_KEYWORDS.split(",") if k.strip()]
            indicators = [i.strip() for i in settings.DEFAULT_INDICATORS.split(",") if i.strip()]

        logger.info(f"Watchlist: {tickers}")

        # ── Step 3: Data Collection (parallel) ────────────────────────
        stock_data = {}
        news_data = {}
        macro_data = []
        filings_data = {}
        errors = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}

            # Submit all data collection tasks
            from app.tools.finance import fetch_all_stocks
            from app.tools.news import fetch_all_news
            from app.tools.economics import fetch_all_indicators
            from app.tools.sec_edgar import fetch_all_filings

            futures["stocks"] = executor.submit(fetch_all_stocks, tickers, db)
            futures["news"] = executor.submit(fetch_all_news, tickers, keywords, db)
            futures["macro"] = executor.submit(fetch_all_indicators, indicators or None, db)
            futures["filings"] = executor.submit(fetch_all_filings, tickers, db)

            for name, future in futures.items():
                try:
                    result = future.result(timeout=60)
                    if name == "stocks":
                        stock_data = result
                    elif name == "news":
                        news_data = result
                    elif name == "macro":
                        macro_data = result
                    elif name == "filings":
                        filings_data = result
                    logger.info(f"✅ {name} collection complete")
                except Exception as e:
                    logger.error(f"❌ {name} collection failed: {e}")
                    errors.append(f"{name}: {str(e)}")

        # ── Step 4a: FinBERT Sentiment (Stage 1) ──────────────────────
        from app.services.finbert import batch_analyze, get_dominant_label
        from app.services.absa import should_run_absa, run_full_absa

        all_sentiment_logs = []
        sentiment_summary = {}  # {ticker: [{headline, finbert_scores, absa_data}]}
        aspect_highlights = {}  # {ticker: {aspect: score}}

        for ticker in tickers:
            articles = news_data.get(ticker, [])
            if not articles:
                logger.warning(f"No news for {ticker} — skipping sentiment analysis")
                sentiment_summary[ticker] = []
                continue

            headlines = [a.get("headline", "") for a in articles]
            news_count = len(headlines)

            # Batch FinBERT inference
            finbert_results = batch_analyze(headlines)
            ticker_entries = []

            for i, (article, scores) in enumerate(zip(articles, finbert_results)):
                headline = article.get("headline", "")
                pub_date = article.get("publish_date", "")

                entry = {
                    "headline": headline,
                    "finbert_scores": scores,
                    "absa_data": None,
                    "absa_ran": False,
                }

                # ── Step 4b: ABSA (Stage 2) — Conditional ────────────
                if should_run_absa(scores, is_high_priority=False):
                    try:
                        absa_result = run_full_absa(headline)
                        entry["absa_data"] = absa_result.get("aspects", {})
                        entry["absa_ran"] = True

                        # Accumulate aspect highlights per ticker
                        if ticker not in aspect_highlights:
                            aspect_highlights[ticker] = {}
                        for aspect, score in entry["absa_data"].items():
                            aspect_highlights[ticker][aspect] = score

                    except Exception as e:
                        logger.warning(f"ABSA failed for headline: {e}")

                ticker_entries.append(entry)

                # Parse trading date
                trading_date = None
                try:
                    if pub_date:
                        trading_date = datetime.date.fromisoformat(pub_date[:10])
                except (ValueError, TypeError):
                    pass

                # Get current price from stock data
                close_price = stock_data.get(ticker, {}).get("current_price")

                # Create SentimentLog record
                log = SentimentLog(
                    ticker=ticker,
                    headline=headline,
                    source_url=article.get("url", ""),
                    positive_score=scores.get("positive", 0),
                    negative_score=scores.get("negative", 0),
                    neutral_score=scores.get("neutral", 0),
                    aspects_json=entry.get("absa_data"),
                    absa_ran=entry.get("absa_ran", False),
                    news_count=news_count,
                    trading_date=trading_date,
                    close_price=close_price,
                    run_id=job_id,
                )
                all_sentiment_logs.append(log)

            sentiment_summary[ticker] = ticker_entries
            logger.info(
                f"Sentiment for {ticker}: {news_count} headlines, "
                f"{sum(1 for e in ticker_entries if e['absa_ran'])} with ABSA"
            )

        # ── Step 5: LLM Urgency Classification ───────────────────────
        from app.services.llm import generate_text
        from app.prompts.urgency_classification import build_prompt as build_urgency_prompt

        # Build data summary for LLM
        data_summary = _build_data_summary(
            stock_data, sentiment_summary, macro_data, filings_data
        )

        urgency_prompt = build_urgency_prompt(data_summary)
        urgency_response = generate_text(urgency_prompt, max_tokens=1024)

        # Parse urgency response
        risk_level = "medium"
        key_findings = []
        ticker_summaries = {}

        try:
            # Try to parse JSON from response
            urgency_json = _extract_json(urgency_response)
            if urgency_json:
                risk_level = urgency_json.get("risk_level", "medium")
                key_findings = urgency_json.get("key_findings", [])
                ticker_summaries = urgency_json.get("summaries", {})
        except Exception as e:
            logger.warning(f"Could not parse urgency JSON: {e}")

        # Check for 8-K material events — override to high if found
        for ticker, filings in filings_data.items():
            for f in filings:
                if isinstance(f, dict) and f.get("is_material_event"):
                    if risk_level in ("low", "medium"):
                        risk_level = "high"
                        key_findings.append({
                            "finding": f"8-K material event filing for {ticker}",
                            "significance": 0.95,
                            "source": "SEC EDGAR",
                        })

        logger.info(f"Risk level: {risk_level}, Key findings: {len(key_findings)}")

        # ── Step 6: Report Generation ─────────────────────────────────
        from app.prompts.report_generation import build_prompt as build_report_prompt

        report_prompt = build_report_prompt(
            risk_level=risk_level,
            stock_data=stock_data,
            sentiment_data=sentiment_summary,
            macro_data=macro_data,
            filings_data=filings_data,
            key_findings=key_findings,
            aspect_highlights=aspect_highlights,
        )

        system_prompt = (
            "You are an expert financial analyst. Write a comprehensive, "
            "professional market intelligence report in Markdown."
        )
        report_content = generate_text(
            report_prompt,
            system_prompt=system_prompt,
            max_tokens=2048,
        )

        # Fallback if LLM returns empty
        if not report_content:
            report_content = _build_fallback_report(
                stock_data, sentiment_summary, macro_data, 
                filings_data, risk_level, aspect_highlights
            )

        # ── Step 7: Database Storage ──────────────────────────────────
        # Build executive summary (first paragraph)
        summary_lines = report_content.split("\n")
        summary = ""
        for line in summary_lines:
         stripped = line.strip()
         if (stripped 
             and not stripped.startswith("#") 
             and not stripped.startswith("|")
             and not stripped.startswith("```")
             and not stripped.startswith("**Risk")
             and not stripped.startswith("**Date")
             and len(stripped) > 30):
            summary = stripped[:500]
            break

        # Get token usage
        token_usage = get_token_usage()

        # Build sources list
        sources_used = ["yfinance", "FinBERT (ProsusAI/finbert)"]
        if any(e.get("absa_ran") for entries in sentiment_summary.values() for e in entries):
            sources_used.append("DeBERTa ABSA (yangheng/deberta-v3-base-absa-v1.1)")
        if settings.NEWS_API_KEY:
            sources_used.append("NewsAPI")
        sources_used.append("RSS Feeds")
        if settings.FRED_API_KEY:
            sources_used.append("FRED API")
        sources_used.append("SEC EDGAR")
        sources_used.append(get_model_name())

        # Save Report
        title = f"Market Intelligence Report — {datetime.datetime.now().strftime('%b %d, %Y %H:%M')}"
        report_record = Report(
            title=title,
            content_markdown=report_content,
            summary=summary,
            risk_level=risk_level,
            key_findings=key_findings,
            sources_used=sources_used,
            token_usage=token_usage,
            run_id=job_id,
        )
        db.add(report_record)

        # Save all SentimentLogs
        for log in all_sentiment_logs:
            db.add(log)

        db.commit()
        logger.info(f"✅ Report saved: {title}")

        # ── Step 8: Email Delivery ────────────────────────────────────
        from app.services.email import send_report_email

        email_subject = f"🛡️ Sentinel Report: {risk_level.upper()} — {title}"
        delivery_email = None
        if config and config.delivery_email:
            delivery_email = config.delivery_email

        send_report_email(email_subject, report_content, delivery_email)

        # ── Step 9: Mark job complete ─────────────────────────────────
        finished_at = datetime.datetime.utcnow()
        job.status = "complete"
        job.finished_at = finished_at
        job.duration_seconds = (finished_at - job.started_at).total_seconds()
        job.total_tokens = token_usage.get("total_tokens", 0)
        job.model_used = get_model_name()
        if errors:
            job.error_message = "; ".join(errors)
        db.commit()

        logger.info(
            f"🏁 Pipeline complete — Duration: {job.duration_seconds:.1f}s, "
            f"Tokens: {job.total_tokens}"
        )

    except Exception as e:
        logger.exception(f"💥 Pipeline failed: {e}")
        try:
            job = db.query(PipelineJob).filter(PipelineJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.finished_at = datetime.datetime.utcnow()
                job.error_message = str(e)
                if job.started_at:
                    job.duration_seconds = (job.finished_at - job.started_at).total_seconds()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _build_data_summary(
    stock_data: dict,
    sentiment_summary: dict,
    macro_data: list,
    filings_data: dict,
) -> str:
    """Build a text summary of all collected data for the urgency LLM."""
    lines = []

    lines.append("=== STOCK DATA ===")
    for ticker, data in stock_data.items():
        if isinstance(data, dict):
            price = data.get("current_price", "N/A")
            change = data.get("daily_change_pct", 0)
            lines.append(f"{ticker}: ${price} ({change:+.2f}%)")

    lines.append("\n=== SENTIMENT SCORES ===")
    for ticker, entries in sentiment_summary.items():
        if entries:
            avg_pos = sum(e["finbert_scores"].get("positive", 0) for e in entries) / len(entries)
            avg_neg = sum(e["finbert_scores"].get("negative", 0) for e in entries) / len(entries)
            lines.append(f"{ticker}: avg_positive={avg_pos:.2f}, avg_negative={avg_neg:.2f}, headlines={len(entries)}")
        else:
            lines.append(f"{ticker}: no news data")

    lines.append("\n=== MACRO INDICATORS ===")
    for ind in macro_data:
        if isinstance(ind, dict) and ind.get("current_value") is not None:
            lines.append(f"{ind.get('name', '')}: {ind['current_value']} (change: {ind.get('change_pct', 'N/A')}%)")

    lines.append("\n=== SEC FILINGS ===")
    has_filings = False
    for ticker, filings in filings_data.items():
        for f in filings:
            if isinstance(f, dict) and not f.get("error"):
                has_filings = True
                lines.append(f"{ticker}: {f.get('form_type', '')} filed {f.get('filed_date', '')} {'🚨 MATERIAL EVENT' if f.get('is_material_event') else ''}")
    if not has_filings:
        lines.append("No significant filings detected.")

    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    """Try to extract JSON from LLM response text."""
    import json

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in text
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return None


def _build_fallback_report(
    stock_data, sentiment_summary, macro_data, 
    filings_data, risk_level, aspect_highlights
) -> str:
    """Generate a structural report when the LLM is unavailable."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    risk_badges = {
        "low": "🟢 LOW", "medium": "🟡 MEDIUM",
        "high": "🔴 HIGH", "critical": "🚨 CRITICAL",
    }
    badge = risk_badges.get(risk_level, "🟡 MEDIUM")

    report = f"""# 🛡️ Market Intelligence Report

**Date:** {now}
**Risk Level:** {badge}
**Mode:** Structural Fallback (LLM unavailable)

---

## Executive Summary

This automated report covers {len(stock_data)} tracked assets with sentiment analysis from {sum(len(v) for v in sentiment_summary.values())} news headlines.

## Market Overview

| Ticker | Price | Daily Chg | Sentiment | Headlines |
|:-------|------:|----------:|----------:|----------:|
"""

    for ticker in stock_data:
        data = stock_data[ticker]
        price = data.get("current_price", 0)
        change = data.get("daily_change_pct", 0)
        entries = sentiment_summary.get(ticker, [])
        count = len(entries)
        if entries:
            avg_score = sum(
                e["finbert_scores"].get("positive", 0) - e["finbert_scores"].get("negative", 0)
                for e in entries
            ) / count
        else:
            avg_score = 0
        emoji = "🟢" if avg_score > 0.2 else ("🔴" if avg_score < -0.2 else "🟡")
        report += f"| **{ticker}** | ${price:.2f} | {change:+.2f}% | {emoji} {avg_score:+.2f} | {count} |\n"

    # Aspect highlights
    if aspect_highlights:
        report += "\n## Aspect Sentiment Breakdown\n\n"
        for ticker, aspects in aspect_highlights.items():
            if aspects:
                report += f"### {ticker}\n\n| Aspect | Score | Signal |\n|:-------|------:|:-------|\n"
                for aspect, score in aspects.items():
                    emoji = "🟢" if score > 0.3 else ("🔴" if score < -0.3 else "🟡")
                    report += f"| {aspect} | {score:+.2f} | {emoji} |\n"
                report += "\n"

    # Macro indicators
    report += "\n## Economic Indicators\n\n| Indicator | Value | Change |\n|:----------|------:|-------:|\n"
    for ind in macro_data:
        if isinstance(ind, dict) and ind.get("current_value") is not None:
            name = ind.get("name", "")
            value = ind["current_value"]
            change = ind.get("change_pct", 0)
            report += f"| {name} | {value} | {change:+.2f}% |\n"

    report += f"\n---\n*Generated by Business Intelligence Sentinel automated pipeline.*\n"

    return report
