"""
Resilient two-tier news fetcher: NewsAPI (Tier 1) + RSS feedparser (Tier 2).
Batches queries to conserve NewsAPI rate limits (100 req/day free tier).
"""

import datetime
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models import CollectedDataCache

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 1

# Company name mappings for RSS filtering
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "GOOG": "Google",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "AMZN": "Amazon",
    "META": "Meta",
    "NFLX": "Netflix",
    "JPM": "JPMorgan",
    "BAC": "Bank of America",
    "GS": "Goldman Sachs",
    "V": "Visa",
    "MA": "Mastercard",
}

# RSS feed URLs
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://finance.yahoo.com/rss/topstories",
    "https://www.investing.com/rss/news.rss",
]

def _get_cache(db: Session, query_key: str):
    cached = (
        db.query(CollectedDataCache)
        .filter(
            CollectedDataCache.source == "newsapi",
            CollectedDataCache.query_key == query_key,
            CollectedDataCache.expires_at > datetime.datetime.utcnow(),
        )
        .first()
    )
    return cached.data if cached else None


def _set_cache(db: Session, source: str, query_key: str, data: list):
    try:
        now = datetime.datetime.utcnow()
        entry = CollectedDataCache(
            source=source,
            query_key=query_key,
            data=data,
            fetched_at=now,
            expires_at=now + datetime.timedelta(hours=CACHE_TTL_HOURS),
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to cache news data: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        
def fetch_newsapi(
    tickers: list[str], keywords: list[str] = None, max_calls: int = 5
) -> list[dict]:
    """
    Tier 1: Fetch headlines from NewsAPI.
    Batches tickers into a single query to conserve rate limits.
    Returns standardized list of {ticker, headline, publish_date, source, url}.
    """
    if not settings.NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not configured. Skipping NewsAPI.")
        return []

    import httpx

    articles = []
    # Batch tickers into groups of 5 for efficient querying
    batch_size = 5
    calls_made = 0

    for i in range(0, len(tickers), batch_size):
        if calls_made >= max_calls:
            break

        batch = tickers[i : i + batch_size]
        query_terms = []
        for t in batch:
            query_terms.append(t)
            company = TICKER_TO_COMPANY.get(t)
            if company:
                query_terms.append(company)

        if keywords:
            query_terms.extend(keywords[:3])

        query = " OR ".join(query_terms)

        try:
            response = httpx.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 20,
                    "apiKey": settings.NEWS_API_KEY,
                },
                timeout=15,
            )
            calls_made += 1

            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    title = article.get("title", "")
                    if not title or title == "[Removed]":
                        continue

                    # Determine which ticker this article relates to
                    matched_ticker = _match_ticker(title, batch)

                    articles.append({
                        "ticker": matched_ticker or batch[0],
                        "headline": title,
                        "publish_date": article.get("publishedAt", "")[:10],
                        "source": article.get("source", {}).get("name", "NewsAPI"),
                        "url": article.get("url", ""),
                        "origin": "newsapi",
                    })
            else:
                logger.warning(
                    f"NewsAPI returned {response.status_code}: {response.text[:200]}"
                )

        except Exception as e:
            logger.warning(f"NewsAPI request failed: {e}")

    logger.info(f"NewsAPI: {len(articles)} articles from {calls_made} API calls")
    return articles


def fetch_rss(tickers: list[str]) -> list[dict]:
    """
    Tier 2: Parse RSS feeds and filter by ticker/company mentions.
    """
    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed. Skipping RSS.")
        return []

    articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", "")

                # Parse date
                pub_date = ""
                try:
                    import time
                    parsed_time = entry.get("published_parsed")
                    if parsed_time:
                        pub_date = time.strftime("%Y-%m-%d", parsed_time)
                except Exception:
                    pub_date = published[:10] if published else ""

                # Check if headline mentions any tracked ticker or company
                matched = _match_ticker(title, tickers)
                if matched:
                    articles.append({
                        "ticker": matched,
                        "headline": title,
                        "publish_date": pub_date,
                        "source": feed_url.split("/")[2],
                        "url": link,
                        "origin": "rss",
                    })

        except Exception as e:
            logger.warning(f"RSS parse error for {feed_url}: {e}")

    logger.info(f"RSS: {len(articles)} relevant articles from {len(RSS_FEEDS)} feeds")
    return articles

def _match_ticker(headline: str, tickers: list[str]) -> Optional[str]:
    headline_upper = headline.upper()
    headline_lower = headline.lower()

    for ticker in tickers:
        # Direct ticker mention
        if ticker in headline_upper:
            return ticker
        # Company name mention
        company = TICKER_TO_COMPANY.get(ticker, "")
        if company and company.lower() in headline_lower:
            return ticker

    # If no specific ticker matched, assign to first ticker
    # so general financial news still gets processed
    financial_keywords = ["stock", "market", "shares", "earnings", "revenue", 
                         "profit", "loss", "fed", "rate", "inflation", "gdp"]
    if any(kw in headline_lower for kw in financial_keywords):
        return tickers[0] if tickers else None

    return None

def fetch_all_news(
    tickers: list[str],
    keywords: list[str] = None,
    db: Session = None,
) -> dict:
    """
    Fetch news from both tiers with fallback logic.
    Returns {ticker: [articles]} — guaranteed to have a key for every ticker.
    """
    cache_key = f"news_{'_'.join(sorted(tickers))}"

    if db:
        cached = _get_cache(db, cache_key)
        if cached:
            logger.info("Cache hit for news data")
            return cached

    # Initialize result dict
    result = {ticker: [] for ticker in tickers}

    # Tier 1: NewsAPI
    newsapi_articles = fetch_newsapi(tickers, keywords)
    for article in newsapi_articles:
        ticker = article.get("ticker")
        if ticker in result:
            result[ticker].append(article)

    # Tier 2: RSS (always runs in parallel as supplement)
    rss_articles = fetch_rss(tickers)
    for article in rss_articles:
        ticker = article.get("ticker")
        if ticker in result:
            # Only add RSS if not already found by NewsAPI (avoid duplicates)
            existing_headlines = {a["headline"] for a in result[ticker]}
            if article["headline"] not in existing_headlines:
                result[ticker].append(article)

    # Fallback: If any ticker has < 3 articles from primary sources, fill from RSS
    for ticker in tickers:
        if len(result[ticker]) < 3:
            logger.warning(
                f"Low news count for {ticker}: {len(result[ticker])} articles. "
                f"This ticker will have reduced sentiment confidence."
            )

    # Log stats
    total = sum(len(v) for v in result.values())
    logger.info(f"Total news collected: {total} articles across {len(tickers)} tickers")

    # Cache
    if db:
        _set_cache(db, "newsapi", cache_key, result)

    return result
