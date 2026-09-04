"""
AstroOS — Unified Multi-System Event Timing Engine Unit Tests
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from apps.api.config import get_settings
from apps.api.domain.unified_event_timing import (
    ConfluenceTier,
    WindowConfluenceStatus,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.unified_event_timing_engine import UnifiedEventTimingEngine


@pytest.fixture
def ephemeris_wrapper() -> EphemerisWrapper:
    settings = get_settings()
    return EphemerisWrapper(ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri")


@pytest.fixture
def timing_engine(ephemeris_wrapper: EphemerisWrapper) -> UnifiedEventTimingEngine:
    return UnifiedEventTimingEngine(ephemeris_wrapper)


@pytest.fixture
def sample_chart(ephemeris_wrapper: EphemerisWrapper):
    horoscope_eng = HoroscopeEngine(ephemeris_wrapper)
    birth_dt = datetime(1990, 5, 15, 8, 30, 0, tzinfo=timezone.utc)
    return horoscope_eng.generate_d1(
        birth_datetime_utc=birth_dt,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="P",
    )


@pytest.fixture
def sample_dasha_tree(ephemeris_wrapper: EphemerisWrapper):
    dasha_eng = DashaEngine(ephemeris_wrapper)
    birth_dt = datetime(1990, 5, 15, 8, 30, 0, tzinfo=timezone.utc)
    return dasha_eng.compute_vimshottari(
        birth_datetime_utc=birth_dt,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="P",
        max_depth=3,
    )


def test_evaluate_moment_snapshot_marriage(timing_engine, sample_chart, sample_dasha_tree):
    target_dt = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    snapshot = timing_engine.evaluate_moment(
        chart=sample_chart,
        dasha_tree=sample_dasha_tree,
        event_type="marriage",
        target_datetime_utc=target_dt,
    )

    assert snapshot.event_type == "marriage"
    assert snapshot.evaluated_datetime_utc == target_dt
    assert 0.0 <= snapshot.confluence_score <= 100.0
    assert snapshot.confidence_tier in (
        ConfluenceTier.VERY_HIGH,
        ConfluenceTier.HIGH,
        ConfluenceTier.MODERATE,
        ConfluenceTier.LOW,
        ConfluenceTier.UNFAVORABLE,
    )

    # Check 4 pillars
    assert snapshot.dasha.score >= 0.0
    assert len(snapshot.dasha.active_chain) >= 1

    assert snapshot.gochara.score >= 0.0
    assert len(snapshot.gochara.key_transits) > 0

    assert snapshot.sbc.score >= 0.0
    assert isinstance(snapshot.sbc.benefic_count, int)
    assert isinstance(snapshot.sbc.malefic_count, int)

    assert snapshot.kp.score >= 0.0
    assert snapshot.kp.primary_cusp == 7
    assert snapshot.kp.csl is not None
    assert snapshot.kp.fructification in ("OPEN", "PARTIAL", "CLOSED")

    assert len(snapshot.summary_narrative) > 20


def test_evaluate_moment_career_and_wealth(timing_engine, sample_chart, sample_dasha_tree):
    target_dt = datetime(2027, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Career
    career_snap = timing_engine.evaluate_moment(
        chart=sample_chart,
        dasha_tree=sample_dasha_tree,
        event_type="career",
        target_datetime_utc=target_dt,
    )
    assert career_snap.event_type == "career"
    assert career_snap.kp.primary_cusp == 10

    # Wealth
    wealth_snap = timing_engine.evaluate_moment(
        chart=sample_chart,
        dasha_tree=sample_dasha_tree,
        event_type="wealth",
        target_datetime_utc=target_dt,
    )
    assert wealth_snap.event_type == "wealth"
    assert wealth_snap.kp.primary_cusp == 2


def test_scan_event_windows_clustering_and_timeline(timing_engine, sample_chart, sample_dasha_tree):
    start_d = date(2026, 1, 1)
    end_d = date(2028, 1, 1)

    result = timing_engine.scan_event_windows(
        chart=sample_chart,
        dasha_tree=sample_dasha_tree,
        event_type="marriage",
        start_date=start_d,
        end_date=end_d,
        step_days=30,
        chart_id="test-chart-123",
    )

    assert result.chart_id == "test-chart-123"
    assert result.event_type == "marriage"
    assert result.start_date == start_d
    assert result.end_date == end_d

    # Time-series sampling
    assert len(result.time_series) >= 20
    for pt in result.time_series:
        assert 0.0 <= pt.confluence_score <= 100.0
        assert 0.0 <= pt.dasha_score <= 100.0
        assert 0.0 <= pt.gochara_score <= 100.0
        assert 0.0 <= pt.sbc_score <= 100.0
        assert 0.0 <= pt.kp_score <= 100.0

    # Candidate windows
    for w in result.candidate_windows:
        assert w.start_date <= w.peak_date <= w.end_date
        assert w.peak_score >= 50.0
        assert w.confluence_status in (
            WindowConfluenceStatus.HIGH_CONFLUENCE,
            WindowConfluenceStatus.MODERATE_CONFLUENCE,
            WindowConfluenceStatus.PARTIAL_WINDOW,
            WindowConfluenceStatus.INHIBITED,
        )
        assert "dasha" in w.system_scores
        assert "gochara" in w.system_scores
        assert "sbc" in w.system_scores
        assert "kp" in w.system_scores
        assert len(w.narrative) > 10
