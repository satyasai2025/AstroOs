"""
AstroOS — Unit Tests for Mundane Analysis Engine
"""

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.mundane_analysis_engine import MundaneAnalysisEngine


@pytest.fixture
def analysis_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return MundaneAnalysisEngine(wrapper)


def test_national_forecast_generation(analysis_engine):
    """Generates complete national forecast for India in 2026."""
    forecast = analysis_engine.generate_forecast(
        country_name="India",
        capital_city="New Delhi",
        latitude=28.6139,
        longitude=77.2090,
        year=2026,
        ayanamsa="lahiri",
    )

    assert forecast.country_name == "India"
    assert forecast.capital_city == "New Delhi"
    assert forecast.year == 2026

    # 12 Mundane Bhavas
    assert len(forecast.bhava_evaluations) == 12
    h1 = next(b for b in forecast.bhava_evaluations if b.house_number == 1)
    assert "Public Health" in h1.signification

    # 4 Key Indices
    assert 0.0 <= forecast.economic_index <= 100.0
    assert 0.0 <= forecast.defense_security_index <= 100.0
    assert 0.0 <= forecast.political_stability_index <= 100.0
    assert 0.0 <= forecast.public_health_index <= 100.0

    assert len(forecast.executive_summary) > 0
