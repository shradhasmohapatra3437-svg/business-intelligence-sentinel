import logging
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize pipeline lazily to prevent slowing down application start
_sentiment_pipeline = None

def get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            logger.info("Initializing FinBERT sentiment analysis pipeline...")
            _sentiment_pipeline = pipeline(
                "text-classification",
                model="ProsusDE/finbert",
                tokenizer="ProsusDE/finbert"
            )
            logger.info("FinBERT pipeline loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load FinBERT: {e}. Falling back to rule-based mock sentiment classifier.")
            _sentiment_pipeline = "fallback"
    return _sentiment_pipeline

def analyze_text_sentiment(text: str):
    """
    Analyzes sentiment of text using FinBERT, falling back to rule-based heuristic if model is unavailable.
    Returns: dict with 'label' (positive/negative/neutral) and 'score' (float).
    """
    if not text or not text.strip():
        return {"label": "neutral", "score": 1.0}
        
    nlp = get_sentiment_pipeline()
    if nlp == "fallback":
        # Rule-based fallback
        text_lower = text.lower()
        positive_words = {"rise", "rose", "growth", "profit", "gain", "higher", "positive", "increase", "up", "bullish", "record", "beat", "strong", "outperform"}
        negative_words = {"fall", "fell", "loss", "drop", "lower", "negative", "decrease", "down", "bearish", "plunge", "miss", "weak", "warn", "slump", "underperform"}
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            return {"label": "positive", "score": min(0.6 + 0.1 * pos_count, 0.99)}
        elif neg_count > pos_count:
            return {"label": "negative", "score": min(0.6 + 0.1 * neg_count, 0.99)}
        else:
            return {"label": "neutral", "score": 0.8}
            
    try:
        result = nlp(text)
        if result and len(result) > 0:
            return {
                "label": result[0]["label"].lower(),
                "score": float(result[0]["score"])
            }
    except Exception as e:
        logger.error(f"Error during sentiment inference: {e}")
    
    return {"label": "neutral", "score": 0.8}
