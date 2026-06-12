"""
FRED API wrapper — macroeconomic indicators.
Fetches GDP, CPI, unemployment, interest rates, Treasury yields, consumer sentiment.
VIX fetched via yfinance. Caches with 24-hour TTL.
"""

import datetime
import logging
import yfinance as yf
from sqlalchemy.orm import Session
from app.config import settings
from app.models import CollectedDataCache

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 24

# Default FRED series to track
DEFAULT_SERIES = {
    "GDP": "Real GDP Growth Rate",
    "CPIAUCSL": "Consumer Price Index (Inflation)",
    "UNRATE": "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Rate",
    "DGS10": "10-Year Treasury Yield",
    "UMCSENT": "Consumer Sentiment Index",
}


def _get_cache(db: Session, query_key: str):
    cached = (
        db.query(CollectedDataCache)
        .filter(
            CollectedDataCache.source == "fred",
            CollectedDataCache.query_key == query_key,
            CollectedDataCache.expires_at > datetime.datetime.utcnow(),
        )
        .first()
    )
    return cached.data if cached else None


def _set_cache(db: Session, query_key: str, data: dict):
    now = datetime.datetime.utcnow()
    entry = CollectedDataCache(
        source="fred",
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


def fetch_fred_series(series_id: str) -> dict:
    """
    Fetch a single FRED series. Returns current value and prior-period change.
    """
    result = {
        "series_id": series_id,
        "name": DEFAULT_SERIES.get(series_id, series_id),
        "current_value": None,
        "previous_value": None,
        "change_pct": None,
        "last_updated": None,
        "error": None,
    }

    if not settings.FRED_API_KEY:
        result["error"] = "FRED_API_KEY not configured"
        logger.warning(f"FRED API key not set. Skipping {series_id}.")
        return result

    try:
        from fredapi import Fred
        fred = Fred(api_key=settings.FRED_API_KEY)

        data = fred.get_series(series_id)
        if data is not None and len(data) >= 2:
            # Drop NaN values and get last two valid points
            clean = data.dropna()
            if len(clean) >= 2:
                current = float(clean.iloc[-1])
                previous = float(clean.iloc[-2])
                result["current_value"] = round(current, 4)
                result["previous_value"] = round(previous, 4)
                result["change_pct"] = (
                    round(((current - previous) / abs(previous)) * 100, 2)
                    if previous != 0 else 0.0
                )
                result["last_updated"] = str(clean.index[-1].date())
                logger.info(f"FRED {series_id}: {current} (Δ {result['change_pct']}%)")
            elif len(clean) == 1:
                result["current_value"] = round(float(clean.iloc[-1]), 4)
                result["last_updated"] = str(clean.index[-1].date())
        else:
            result["error"] = "No data returned"

    except ImportError:
        result["error"] = "fredapi package not installed"
        logger.error("fredapi not installed. Run: pip install fredapi")
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Error fetching FRED series {series_id}: {e}")

    return result


def fetch_vix() -> dict:
    """Fetch VIX volatility index via yfinance."""
    result = {
        "series_id": "VIX",
        "name": "CBOE Volatility Index (VIX)",
        "current_value": None,
        "previous_value": None,
        "change_pct": None,
        "last_updated": None,
        "error": None,
    }

    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if not hist.empty:
            current = round(float(hist["Close"].iloc[-1]), 2)
            result["current_value"] = current
            result["last_updated"] = hist.index[-1].strftime("%Y-%m-%d")

            if len(hist) >= 2:
                previous = round(float(hist["Close"].iloc[-2]), 2)
                result["previous_value"] = previous
                result["change_pct"] = (
                    round(((current - previous) / abs(previous)) * 100, 2)
                    if previous != 0 else 0.0
                )
            logger.info(f"VIX: {current}")
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Error fetching VIX: {e}")

    return result


def fetch_all_indicators(
    indicator_ids: list[str] = None, db: Session = None
) -> list[dict]:
    """
    Fetch all macro indicators. Returns list of indicator dicts.
    """
    cache_key = "all_indicators"

    # Check cache
    if db:
        cached = _get_cache(db, cache_key)
        if cached:
            logger.info("Cache hit for macro indicators")
            return cached

    if indicator_ids is None:
        indicator_ids = list(DEFAULT_SERIES.keys())

    results = []
    for series_id in indicator_ids:
        results.append(fetch_fred_series(series_id))

    # Always include VIX
    results.append(fetch_vix())

    # Cache
    if db:
        _set_cache(db, cache_key, results)

    return results
