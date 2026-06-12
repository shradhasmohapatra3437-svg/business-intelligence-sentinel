from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200

def test_health_returns_status():
    response = client.get("/api/health")
    assert response.json()["status"] == "healthy"

def test_health_returns_models():
    response = client.get("/api/health")
    assert "models" in response.json()
    assert "finbert" in response.json()["models"]
    assert "absa" in response.json()["models"]

def test_get_reports():
    response = client.get("/api/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_reports_limit():
    response = client.get("/api/reports?limit=5")
    assert response.status_code == 200
    assert len(response.json()) <= 5

def test_get_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    assert "tickers" in response.json()

def test_get_config_has_tickers():
    response = client.get("/api/config")
    assert len(response.json()["tickers"]) > 0

def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert "total_runs" in response.json()
    assert "success_rate" in response.json()

def test_get_runs():
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_sentiment_history():
    response = client.get("/api/sentiment-history")
    assert response.status_code == 200
    assert "tickers" in response.json()
    assert "history" in response.json()

def test_invalid_report_id():
    response = client.get("/api/reports/invalid-id-that-doesnt-exist")
    assert response.status_code == 404

def test_invalid_job_id():
    response = client.get("/api/jobs/invalid-job-id")
    assert response.status_code == 404
    