import datetime
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health")
def health_check():
    from app.services.finbert import is_loaded as finbert_loaded
    from app.services.absa import is_loaded as absa_loaded
    
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "models": {
            "finbert": "loaded" if finbert_loaded() else "fallback",
            "absa": "loaded" if absa_loaded() else "fallback"
        }
    }
