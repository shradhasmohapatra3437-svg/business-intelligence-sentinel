import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SentimentLog, WatchlistConfig

router = APIRouter()

@router.get("/api/sentiment-history")
def get_sentiment_history(days: int = 14, db: Session = Depends(get_db)):
    """Retrieve historical sentiment and stock price data grouped by ticker."""
    cutoff_date = datetime.datetime.utcnow().date() - datetime.timedelta(days=days)
    
    logs = (db.query(SentimentLog)
            .filter(SentimentLog.trading_date >= cutoff_date)
            .order_by(SentimentLog.trading_date.asc())
            .all())
    
    # Structure data per ticker
    history = {}
    
    for log in logs:
        # Avoid duplicate data points for the same trading day/ticker by averaging or picking the latest run
        # For simplicity, we just group by ticker
        if log.ticker not in history:
            history[log.ticker] = []
            
        history[log.ticker].append({
            "id": log.id,
            "date": str(log.trading_date) if log.trading_date else str(log.run_at.date()),
            "headline": log.headline,
            "sentiment_score": (log.positive_score or 0) - (log.negative_score or 0),
            "price": log.close_price,
            "absa_data": log.aspects_json
        })
        
    # Get currently active watchlist tickers
    config = db.query(WatchlistConfig).first()
    tickers = config.tickers if config and config.tickers else []
    
    return {
        "tickers": tickers,
        "history": history
    }
