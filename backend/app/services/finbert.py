"""
Stage 1 — FinBERT Document-Level Sentiment.
Loads ProsusAI/finbert once at startup via HuggingFace Transformers.
Provides both single and batch inference.
"""

import logging

logger = logging.getLogger(__name__)

# Global pipeline holder — loaded once at app startup
_finbert_pipeline = None
_is_fallback = False


def load_model(model_name: str = "ProsusAI/finbert"):
    """Load FinBERT model into memory. Called from FastAPI lifespan."""
    global _finbert_pipeline, _is_fallback

    try:
        from transformers import pipeline as hf_pipeline

        logger.info(f"Loading FinBERT model: {model_name}...")
        _finbert_pipeline = hf_pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            top_k=None,  # Return all class probabilities
        )
        _is_fallback = False
        logger.info("✅ FinBERT loaded successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Could not load FinBERT: {e}. Using rule-based fallback.")
        _finbert_pipeline = None
        _is_fallback = True


def is_loaded() -> bool:
    """Check if FinBERT is loaded (not in fallback mode)."""
    return _finbert_pipeline is not None and not _is_fallback


def analyze_document_sentiment(headline: str) -> dict:
    """
    Analyze a single headline. Returns:
    {"positive": float, "negative": float, "neutral": float}
    All three probabilities sum to ~1.0.
    """
    if not headline or not headline.strip():
        return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

    if _is_fallback or _finbert_pipeline is None:
        return _fallback_sentiment(headline)

    try:
        result = _finbert_pipeline(headline[:512])  # Truncate to model max

        # result is a list of list of dicts: [[{label, score}, ...]]
        scores = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
        if result and len(result) > 0:
            for item in result[0]:
                label = item["label"].lower()
                if label in scores:
                    scores[label] = round(float(item["score"]), 4)

        return scores

    except Exception as e:
        logger.error(f"FinBERT inference error: {e}")
        return _fallback_sentiment(headline)


def batch_analyze(headlines: list[str]) -> list[dict]:
    """
    Batch-analyze multiple headlines. More efficient than one call per headline.
    Returns list of score dicts in the same order.
    """
    if not headlines:
        return []

    if _is_fallback or _finbert_pipeline is None:
        return [_fallback_sentiment(h) for h in headlines]

    try:
        # Truncate each headline
        truncated = [h[:512] if h else "" for h in headlines]
        results = _finbert_pipeline(truncated)

        scored = []
        for result in results:
            scores = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
            for item in result:
                label = item["label"].lower()
                if label in scores:
                    scores[label] = round(float(item["score"]), 4)
            scored.append(scores)

        return scored

    except Exception as e:
        logger.error(f"FinBERT batch inference error: {e}")
        return [_fallback_sentiment(h) for h in headlines]


def get_dominant_label(scores: dict) -> tuple[str, float]:
    """Get the dominant sentiment label and its confidence."""
    if not scores:
        return "neutral", 0.0
    label = max(scores, key=scores.get)
    return label, scores[label]


def _fallback_sentiment(text: str) -> dict:
    """Rule-based fallback when FinBERT is unavailable."""
    text_lower = text.lower()

    positive_words = {
        "rise", "rose", "growth", "profit", "gain", "higher", "positive",
        "increase", "up", "bullish", "record", "beat", "strong", "outperform",
        "surge", "rally", "boost", "upgrade", "optimistic", "exceed",
    }
    negative_words = {
        "fall", "fell", "loss", "drop", "lower", "negative", "decrease",
        "down", "bearish", "plunge", "miss", "weak", "warn", "slump",
        "underperform", "cut", "crash", "decline", "risk", "concern",
    }

    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)

    if pos_count > neg_count:
        score = min(0.55 + 0.1 * pos_count, 0.95)
        return {"positive": round(score, 4), "negative": round(0.05, 4), "neutral": round(1 - score - 0.05, 4)}
    elif neg_count > pos_count:
        score = min(0.55 + 0.1 * neg_count, 0.95)
        return {"positive": round(0.05, 4), "negative": round(score, 4), "neutral": round(1 - score - 0.05, 4)}
    else:
        return {"positive": 0.15, "negative": 0.15, "neutral": 0.70}
