"""
Unit tests for MediniEngine (Sapta-Nadi Weather & Sensex/Gold Financial Astrology).
"""

from datetime import date
import pytest

from apps.api.services.medini_engine import (
    MarketForecast,
    MediniEngine,
    MediniForecastReport,
    WeatherForecast,
)


def test_medini_weather_and_market_forecast():
    engine = MediniEngine(ephemeris_path="data/ephemeris")

    # Forecast for 2024-07-15 (Monsoon season)
    target = date(2024, 7, 15)
    rep: MediniForecastReport = engine.generate_full_report(target)

    assert isinstance(rep, MediniForecastReport)
    assert rep.target_date == target

    # Weather checks
    assert isinstance(rep.weather, WeatherForecast)
    assert 0.0 <= rep.weather.rainfall_probability_pct <= 100.0
    assert rep.weather.rainfall_intensity in ["TORRENTIAL", "HEAVY_DOWNPOUR", "MODERATE_SHOWERS", "SCANTY", "DRY_CLEAR"]
    assert rep.weather.temperature_trend in ["INTENSE_HEAT", "WARM", "MODERATE", "COOL", "CHILLY"]

    # Market checks
    assert isinstance(rep.market, MarketForecast)
    assert -1.0 <= rep.market.sensex_sentiment_score <= 1.0
    assert -1.0 <= rep.market.gold_sentiment_score <= 1.0
    assert rep.market.sensex_trend in ["STRONGLY_BULLISH", "BULLISH_BIAS", "NEUTRAL_RANGEBOUND", "BEARISH_PRESSURE", "HIGH_VOLATILITY_CORRECTION"]
    assert rep.market.gold_trend in ["RISING_BULLISH", "STEADY_ACCUMULATION", "CONSOLIDATION", "BEARISH_CORRECTION"]
