"""
AstroOS — Unit & Verification Tests for Upgraded Multi-Tier Shastric BTR Engine
"""

import pytest
from datetime import datetime, timezone, date

from apps.api.domain.rectification import EventType, LifeEventRecord
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.rectification_engine import RectificationEngine


@pytest.fixture
def btr_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return RectificationEngine(wrapper=wrapper)


def test_shastric_btr_4tier_dasha_and_gochar(btr_engine):
    """Verify that the upgraded BTR engine evaluates 4-tier dasha (MD/AD/PD/SD) and multi-planet Gochar."""
    base_dt = datetime(2003, 5, 5, 15, 18, 15, tzinfo=timezone.utc) # 20:48:15 IST
    lat = 23.0567
    lon = 72.5539

    events = [
        LifeEventRecord(
            event_id="evt-hernia",
            event_type=EventType.HEALTH_SURGERY,
            event_date=date(2004, 10, 18),
            significance_weight=2.0,
            description="Infant hernia surgery at 1.5 years",
        ),
        LifeEventRecord(
            event_id="evt-relocation",
            event_type=EventType.RELOCATION,
            event_date=date(2007, 4, 1),
            significance_weight=1.5,
            description="First major residence change",
        ),
    ]

    result = btr_engine.search_rectification(
        base_datetime_utc=base_dt,
        latitude=lat,
        longitude=lon,
        events=events,
        window_minutes=2,
        step_seconds=30,
        ayanamsa="lahiri",
    )

    assert result.total_candidates_evaluated == 9  # -2m to +2m at 30s steps
    assert result.best_candidate is not None
    best = result.best_candidate

    # Verify that evaluations contain 4-level active dasha lords
    hernia_eval = next(e for e in best.event_evaluations if e.event_id == "evt-hernia")
    assert len(hernia_eval.active_dasha_lords) >= 3, "Expected at least 3 levels (MD, AD, PD) of dasha lords"
    assert any(p in hernia_eval.transiting_planets_activated for p in ("mars", "ketu", "saturn"))

    # Verify that explanation contains deep Shastric dimensions
    assert "MD:" in hernia_eval.explanation or "AD:" in hernia_eval.explanation
    assert "SAV" in hernia_eval.explanation or "D30" in hernia_eval.explanation

    # Verify Kunda Nakshatra score is non-zero
    assert best.tattva_shodhana_score > 0.0
    assert "Kunda:" in best.audit_trail


def test_shastric_btr_kunda_nakshatra_sensitivity(btr_engine):
    """Verify that Kunda Nakshatra varies with temporal offset and provides high resolution."""
    base_dt = datetime(2003, 5, 5, 15, 18, 15, tzinfo=timezone.utc)
    lat = 23.0567
    lon = 72.5539

    events = [
        LifeEventRecord(
            event_id="evt-1",
            event_type=EventType.CAREER_RISE,
            event_date=date(2025, 6, 1),
            significance_weight=1.0,
            description="Career test anchor",
        )
    ]

    result = btr_engine.search_rectification(
        base_datetime_utc=base_dt,
        latitude=lat,
        longitude=lon,
        events=events,
        window_minutes=3,
        step_seconds=45,
        ayanamsa="lahiri",
    )

    kunda_scores = [c.tattva_shodhana_score for c in result.top_candidates]
    # Verify that Kunda score varies across different candidate moments
    assert len(set(kunda_scores)) >= 2, "Kunda scores should discriminate between candidate moments"
