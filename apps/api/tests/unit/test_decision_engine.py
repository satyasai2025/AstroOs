"""
Unit tests for PhalitaDecisionEngine (Supervisory Adaptive Governor).
"""

from datetime import datetime, timezone, date
import pytest

from apps.api.services.phalita_core.decision_engine import (
    PhalitaDecisionEngine,
    PhalitaConsultationTimeline,
    PhalitaDecisionWindow,
)


def test_decision_engine_single_window():
    """Verify single window arbitration into 4 decision tiers."""
    engine = PhalitaDecisionEngine(ephemeris_path="data/ephemeris")

    birth_dt = datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc)
    chart = engine.horoscope_engine.generate_d1(birth_dt, 28.6139, 77.2090)

    # Mock 128-D vector
    mock_features = [0.1] * 128

    win = engine.evaluate_window(
        chart=chart,
        slice_start=date(2020, 1, 1),
        slice_end=date(2022, 6, 1),
        mahadasha_lord="jupiter",
        antardasha_lord="saturn",
        features=mock_features,
        domain="career",
    )

    assert isinstance(win, PhalitaDecisionWindow)
    assert win.decision_tier in ["PRATYAKSHA_PHALA", "SUSHUPTA_BEEJA", "ALPA_PHALA", "SAMANYA_KAL"]
    assert win.confidence_level in ["VERY_HIGH", "HIGH", "MODERATE", "LOW"]
    assert win.explanation_hi != ""
    assert win.explanation_en != ""


def test_decision_engine_life_timeline_scan():
    """Verify multi-year timeline scan across Antardashas."""
    engine = PhalitaDecisionEngine(ephemeris_path="data/ephemeris")

    birth_dt = datetime(1975, 5, 15, 8, 30, tzinfo=timezone.utc)
    timeline = engine.scan_life_timeline(
        birth_datetime=birth_dt,
        latitude=19.0760,
        longitude=72.8777,
        native_name="Test Native",
        scan_start_year=2010,
        scan_end_year=2025,
        domain="career",
    )

    assert isinstance(timeline, PhalitaConsultationTimeline)
    assert timeline.total_windows_scanned > 0
    assert len(timeline.windows) == timeline.total_windows_scanned
    for w in timeline.windows:
        assert w.window_start < w.window_end
