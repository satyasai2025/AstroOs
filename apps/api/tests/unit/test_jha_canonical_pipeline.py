"""
AstroOS — Unit Tests for Vinay Jha Canonical 10-Step Prediction Pipeline
"""

import pytest
from datetime import datetime, timezone, date

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.jha_canonical_pipeline import JhaCanonicalPredictionPipeline


@pytest.fixture
def jha_pipeline():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return JhaCanonicalPredictionPipeline(wrapper=wrapper)


def test_jha_pipeline_career_evaluation(jha_pipeline):
    """Verify that Jha pipeline executes all 10 steps for a career milestone."""
    # Native born: 5 May 2003, 20:48:15 IST (15:18:15 UTC) in Ahmedabad
    birth_dt = datetime(2003, 5, 5, 15, 18, 15, tzinfo=timezone.utc)
    lat = 23.0567
    lon = 72.5539
    event_date = date(2025, 6, 1)

    result = jha_pipeline.evaluate(
        birth_datetime_utc=birth_dt,
        latitude=lat,
        longitude=lon,
        event_date=event_date,
        domain="career",
        ayanamsa="lahiri",
    )

    assert result.domain == "career"
    assert result.target_varga == "D10"
    assert len(result.steps) == 10
    assert result.total_confluent_layers >= 0
    assert result.confidence_tier in ("DEFER", "REASONABLE", "HIGH_CONFIDENCE")
    assert 0.0 <= result.calibrated_probability <= 1.0

    # Verify Step 1: Bhavachalita
    s1 = result.steps[0]
    assert s1.step_number == 1
    assert "Bhavachalita" in s1.explanation

    # Verify Step 3: Main Strength Log-Base-2
    s3 = result.steps[2]
    assert s3.step_number == 3
    assert "Main Strength" in s3.explanation
    assert result.main_strength_karyesha >= 1.0


def test_jha_pipeline_marriage_evaluation(jha_pipeline):
    """Verify that Jha pipeline selects D9 for marriage and evaluates 7 Chara Karakas."""
    birth_dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    lat = 13.0827
    lon = 80.2707
    event_date = date(2018, 11, 25)

    result = jha_pipeline.evaluate(
        birth_datetime_utc=birth_dt,
        latitude=lat,
        longitude=lon,
        event_date=event_date,
        domain="marriage",
        ayanamsa="lahiri",
    )

    assert result.domain == "marriage"
    assert result.target_varga == "D9"
    assert len(result.steps) == 10
    assert result.primary_karyesha != ""
