"""
Unit tests for Sapta-Nadi Weather & Market Forecasting router endpoints.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from apps.api.routers.mundane import router as mundane_router

app = FastAPI()
app.include_router(mundane_router)
client = TestClient(app)


def test_weather_forecast_endpoint():
    res = client.get("/research/mundane/weather-forecast?target_date=2024-07-15")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "rainfall_probability_pct" in data
    assert "rainfall_intensity" in data
    assert "temperature_trend" in data


def test_market_forecast_endpoint():
    res = client.get("/research/mundane/market-forecast?target_date=2024-07-15")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "sensex_trend" in data
    assert "sensex_sentiment_score" in data
    assert "gold_trend" in data
    assert "gold_sentiment_score" in data
