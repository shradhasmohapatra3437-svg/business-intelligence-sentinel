"""
yfinance wrapper — stock prices, volume, ratios.
Caches responses to CollectedDataCache with 6-hour TTL.
"""

import datetime
import logging
import yfinance as yf
from sqlalchemy.orm import Session
from app.models import CollectedDataCache

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 6


def _get_cache(db: Session, source: str, query_key: str):
    """Check cache for a fresh entry."""
    cached = (
        db.query(CollectedDataCache)
        .filter(
            CollectedDataCache.source == source,
            CollectedDataCache.query_key == query_key,
            CollectedDataCache.expires_at > datetime.datetime.utcnow(),
        )
        .first()
    )
    return cached.data if cached else None


def _set_cache(db: Session, source: str, query_key: str, data: dict, ttl_hours: int):
    """Write a cache entry with TTL."""
    now = datetime.datetime.utcnow()
    entry = CollectedDataCache(
        source=source,
        query_key=query_key,
        data=data,
        fetched_at=now,
        expires_at=now + datetime.timedelta(hours=ttl_hours),
    )
    db.add(entry)
    try:
        db.commit()
    except Exception:
        db.rollback()


def validate_ticker(symbol: str) -> bool:
    """Validate a ticker symbol by checking if yfinance returns data."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        return info is not None and hasattr(info, "market_cap")
    except Exception:
        return False


def fetch_stock_data(ticker_symbol: str, db: Session = None) -> dict:
    """
    Fetch stock data for a single ticker.
    Returns: {
        ticker, current_price, daily_change_pct, high_52w, low_52w,
        prices_7d: [{date, price}], volume, avg_volume_30d,
        market_cap, pe_ratio
    }
    """
    cache_key = f"stock_{ticker_symbol}"

    # Check cache
    if db:
        cached = _get_cache(db, "yfinance", cache_key)
        if cached:
            logger.info(f"Cache hit for {ticker_symbol} stock data")
            return cached

    result = {
        "ticker": ticker_symbol,
        "current_price": 0.0,
        "daily_change_pct": 0.0,
        "high_52w": 0.0,
        "low_52w": 0.0,
        "prices_7d": [],
        "volume": 0,
        "avg_volume_30d": 0,
        "market_cap": 0,
        "pe_ratio": 0.0,
        "error": None,
    }

    try:
        stock = yf.Ticker(ticker_symbol)

        # 7-day price history
        hist = stock.history(period="7d")
        if not hist.empty:
            prices_7d = []
            for date_idx, row in hist.iterrows():
                prices_7d.append({
                    "date": date_idx.strftime("%Y-%m-%d"),
                    "price": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                })
            result["prices_7d"] = prices_7d
            result["current_price"] = prices_7d[-1]["price"]

            # Daily change
            if len(prices_7d) >= 2:
                prev = prices_7d[-2]["price"]
                curr = prices_7d[-1]["price"]
                result["daily_change_pct"] = round(
                    ((curr - prev) / prev) * 100, 2
                ) if prev else 0.0

        # Fast info for market cap, volume, etc.
        try:
            info = stock.fast_info
            result["market_cap"] = int(getattr(info, "market_cap", 0) or 0)
            result["high_52w"] = round(float(getattr(info, "year_high", 0) or 0), 2)
            result["low_52w"] = round(float(getattr(info, "year_low", 0) or 0), 2)
        except Exception:
            pass

        # 30-day volume average
        try:
            hist_30d = stock.history(period="1mo")
            if not hist_30d.empty:
                result["volume"] = int(hist_30d["Volume"].iloc[-1])
                result["avg_volume_30d"] = int(hist_30d["Volume"].mean())
        except Exception:
            pass

        # P/E ratio
        try:
            info_dict = stock.info
            result["pe_ratio"] = round(float(info_dict.get("trailingPE", 0) or 0), 2)
        except Exception:
            pass

        logger.info(f"Fetched stock data for {ticker_symbol}: ${result['current_price']}")

    except Exception as e:
        logger.warning(f"Error fetching stock data for {ticker_symbol}: {e}")
        result["error"] = str(e)

    # Cache the result
    if db:
        _set_cache(db, "yfinance", cache_key, result, CACHE_TTL_HOURS)

    return result


def fetch_all_stocks(tickers: list[str], db: Session = None) -> dict:
    """Fetch stock data for all watchlist tickers. Returns {ticker: data_dict}."""
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = fetch_stock_data(ticker, db)
        except Exception as e:
            logger.error(f"Failed to fetch {ticker}: {e}")
            results[ticker] = {"ticker": ticker, "error": str(e)}
    return results
