from app.services.finbert import get_dominant_label
from app.services.absa import should_run_absa, _fallback_extract
from app.pipeline import _extract_json, _build_data_summary

def test_dominant_label_positive():
    scores = {"positive": 0.8, "negative": 0.1, "neutral": 0.1}
    label, confidence = get_dominant_label(scores)
    assert label == "positive"
    assert confidence == 0.8

def test_dominant_label_negative():
    scores = {"positive": 0.1, "negative": 0.75, "neutral": 0.15}
    label, confidence = get_dominant_label(scores)
    assert label == "negative"

def test_dominant_label_empty():
    label, confidence = get_dominant_label({})
    assert label == "neutral"
    assert confidence == 0.0

def test_fallback_extract_finds_earnings():
    aspects = _fallback_extract("Apple reports record earnings this quarter")
    assert len(aspects) > 0

def test_fallback_extract_finds_supply_chain():
    aspects = _fallback_extract("Supply chain disruptions hit Tesla production")
    assert "supply chain" in aspects

def test_fallback_extract_max_four():
    aspects = _fallback_extract("Apple earnings revenue sales profit supply chain merger acquisition")
    assert len(aspects) <= 4

def test_extract_json_valid():
    text = '{"risk_level": "medium", "key_findings": []}'
    result = _extract_json(text)
    assert result["risk_level"] == "medium"

def test_extract_json_embedded():
    text = 'Here is the result: {"risk_level": "high", "key_findings": []} done.'
    result = _extract_json(text)
    assert result["risk_level"] == "high"

def test_extract_json_invalid():
    result = _extract_json("this is not json at all")
    assert result is None

def test_build_data_summary():
    stock_data = {"AAPL": {"current_price": 180.0, "daily_change_pct": 1.5}}
    sentiment_summary = {"AAPL": [{"finbert_scores": {"positive": 0.8, "negative": 0.1, "neutral": 0.1}}]}
    macro_data = [{"name": "GDP", "current_value": 2.5, "change_pct": 0.3}]
    filings_data = {"AAPL": []}
    result = _build_data_summary(stock_data, sentiment_summary, macro_data, filings_data)
    assert "AAPL" in result
    assert "GDP" in result
    