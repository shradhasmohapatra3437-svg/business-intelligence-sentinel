from app.services.finbert import analyze_document_sentiment, batch_analyze
from app.services.absa import should_run_absa

def test_positive_headline():
    result = analyze_document_sentiment("Apple stock surges on record earnings beat")
    assert result["positive"] > result["negative"]

def test_negative_headline():
    result = analyze_document_sentiment("Tesla stock crashes amid massive losses and layoffs")
    assert result["negative"] > result["positive"]

def test_neutral_headline():
    result = analyze_document_sentiment("Company files quarterly report with SEC")
    assert isinstance(result["neutral"], float)

def test_batch_analyze_length():
    headlines = ["Apple earnings beat expectations", "Market crash today", "Fed holds rates steady"]
    results = batch_analyze(headlines)
    assert len(results) == 3

def test_batch_analyze_structure():
    headlines = ["NVIDIA revenue hits record high"]
    results = batch_analyze(headlines)
    assert "positive" in results[0]
    assert "negative" in results[0]
    assert "neutral" in results[0]

def test_scores_sum_to_one():
    result = analyze_document_sentiment("Microsoft acquires new AI startup")
    total = result["positive"] + result["negative"] + result["neutral"]
    assert abs(total - 1.0) < 0.01

def test_absa_triggers_on_ambiguous():
    scores = {"positive": 0.55, "negative": 0.45, "neutral": 0.0}
    assert should_run_absa(scores) == True

def test_absa_skips_on_confident():
    scores = {"positive": 0.92, "negative": 0.05, "neutral": 0.03}
    assert should_run_absa(scores) == False

def test_absa_triggers_on_high_priority():
    scores = {"positive": 0.92, "negative": 0.05, "neutral": 0.03}
    assert should_run_absa(scores, is_high_priority=True) == True
    