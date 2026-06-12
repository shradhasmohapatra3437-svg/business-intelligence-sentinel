"""
SEC EDGAR filing watcher via edgartools.
Monitors 8-K, 10-K, 10-Q filings for watchlist tickers.
8-K filings are flagged as high-priority signals.
"""

import datetime
import logging
from sqlalchemy.orm import Session
from app.models import CollectedDataCache

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 6

# Filing types to watch
WATCHED_FORMS = ["8-K", "10-K", "10-Q"]


def _get_cache(db: Session, query_key: str):
    cached = (
        db.query(CollectedDataCache)
        .filter(
            CollectedDataCache.source == "sec_edgar",
            CollectedDataCache.query_key == query_key,
            CollectedDataCache.expires_at > datetime.datetime.utcnow(),
        )
        .first()
    )
    return cached.data if cached else None


def _set_cache(db: Session, query_key: str, data):
    now = datetime.datetime.utcnow()
    entry = CollectedDataCache(
        source="sec_edgar",
        query_key=query_key,
        data=data,
        fetched_at=now,
        expires_at=now + datetime.timedelta(hours=CACHE_TTL_HOURS),
    )
    db.add(entry)
    try:
        db.commit()
    except Exception:
        db.rollback()


def fetch_filings_for_ticker(ticker: str, days_back: int = 30) -> list[dict]:
    """
    Fetch recent SEC filings for a single ticker.
    Returns list of {form_type, filed_date, description, url, is_material_event}.
    """
    filings_list = []

    try:
        from edgar import Company

        company = Company(ticker)
        filings = company.get_filings()

        cutoff_date = datetime.date.today() - datetime.timedelta(days=days_back)

        for filing in filings[:50]:  # Check last 50 filings
            try:
                form_type = str(getattr(filing, "form", ""))
                filed_date_str = str(getattr(filing, "filing_date", ""))

                # Filter by form type
                if form_type not in WATCHED_FORMS:
                    continue

                # Parse date
                try:
                    filed_date = datetime.date.fromisoformat(filed_date_str)
                except (ValueError, TypeError):
                    continue

                # Filter by date
                if filed_date < cutoff_date:
                    continue

                filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={form_type}"

                filings_list.append({
                    "ticker": ticker,
                    "form_type": form_type,
                    "filed_date": filed_date_str,
                    "description": f"{form_type} filing for {ticker}",
                    "url": filing_url,
                    "is_material_event": form_type == "8-K",
                })
            except Exception:
                continue

        logger.info(f"SEC EDGAR: {len(filings_list)} filings for {ticker}")

    except ImportError:
        logger.warning("edgartools not installed. Skipping SEC EDGAR.")
        return [{
            "ticker": ticker,
            "error": "edgartools not installed",
        }]
    except Exception as e:
        logger.warning(f"Error fetching SEC filings for {ticker}: {e}")
        return [{
            "ticker": ticker,
            "error": str(e),
        }]

    return filings_list


def fetch_all_filings(tickers: list[str], db: Session = None) -> dict:
    """
    Fetch SEC filings for all watchlist tickers.
    Returns {ticker: [filing_dicts]}.
    """
    cache_key = f"sec_{'_'.join(sorted(tickers))}"

    if db:
        cached = _get_cache(db, cache_key)
        if cached:
            logger.info("Cache hit for SEC filings")
            return cached

    results = {}
    has_material_events = False

    for ticker in tickers:
        try:
            filings = fetch_filings_for_ticker(ticker)
            results[ticker] = filings

            # Check for 8-K material events
            for f in filings:
                if f.get("is_material_event"):
                    has_material_events = True
                    logger.warning(
                        f"🚨 Material event (8-K) detected for {ticker} "
                        f"filed {f.get('filed_date')}"
                    )
        except Exception as e:
            logger.error(f"SEC EDGAR failed for {ticker}: {e}")
            results[ticker] = [{"ticker": ticker, "error": str(e)}]

    if has_material_events:
        logger.warning("⚠️ One or more 8-K filings detected — high priority signal")

    # Cache
    if db:
        _set_cache(db, cache_key, results)

    return results
