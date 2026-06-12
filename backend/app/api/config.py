from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models import WatchlistConfig
from app.tools.finance import validate_ticker
from app.config import settings

router = APIRouter()

class ConfigUpdate(BaseModel):
    tickers: List[str]
    news_keywords: Optional[List[str]] = None
    economic_indicators: Optional[List[str]] = None
    delivery_email: Optional[str] = None

@router.get("/api/config")
def get_config(db: Session = Depends(get_db)):
    config = db.query(WatchlistConfig).first()
    if not config:
        return {
            "tickers": [t.strip() for t in settings.DEFAULT_TICKERS.split(",") if t.strip()],
            "news_keywords": [k.strip() for k in settings.DEFAULT_KEYWORDS.split(",") if k.strip()],
            "economic_indicators": [i.strip() for i in settings.DEFAULT_INDICATORS.split(",") if i.strip()],
            "delivery_email": settings.DELIVERY_EMAIL
        }
        
    return {
        "tickers": config.tickers,
        "news_keywords": config.news_keywords,
        "economic_indicators": config.economic_indicators,
        "delivery_email": config.delivery_email
    }

@router.put("/api/config")
def update_config(data: ConfigUpdate, db: Session = Depends(get_db)):
    valid_tickers = []
    rejected_tickers = []
    
    # Validate tickers
    for t in data.tickers:
        t_clean = t.strip().upper()
        if t_clean:
            if validate_ticker(t_clean):
                valid_tickers.append(t_clean)
            else:
                rejected_tickers.append(t_clean)
                
    if not valid_tickers:
        raise HTTPException(status_code=400, detail="No valid tickers provided")
        
    config = db.query(WatchlistConfig).first()
    if not config:
        config = WatchlistConfig()
        db.add(config)
        
    config.tickers = valid_tickers
    
    if data.news_keywords is not None:
        config.news_keywords = [k.strip() for k in data.news_keywords if k.strip()]
        
    if data.economic_indicators is not None:
        config.economic_indicators = [i.strip() for i in data.economic_indicators if i.strip()]
        
    if data.delivery_email is not None:
        config.delivery_email = data.delivery_email
        
    db.commit()
    
    return {
        "saved": valid_tickers,
        "rejected": rejected_tickers
    }
