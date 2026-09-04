"""
Unit tests for Classical Predictive Confluence Engine (Continuous & Legacy).
"""

from datetime import datetime, timezone, date
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.phalita_core.classical_filter_engine import (
    ClassicalFilterEngine,
    ContinuousConfluenceReport,
    ClassicalConfluenceReport,
)


def test_classical_filter_engine_computation():
    """Verify deterministic calculation of SAV, BAV, Double Transit, and Continuous Confluence."""
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horoscope = HoroscopeEngine(wrapper)
    filter_engine = ClassicalFilterEngine(ephemeris_path="data/ephemeris")

    birth_dt = datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc)
    chart = horoscope.generate_d1(birth_dt, 28.6139, 77.2090)

    target_d = date(2020, 6, 1)

    # 1. Test Continuous Confluence
    cont_rep = filter_engine.compute_continuous_confluence(
        chart=chart,
        target_date=target_d,
        mahadasha_lord="jupiter",
        antardasha_lord="saturn",
        domain="career",
    )

    assert isinstance(cont_rep, ContinuousConfluenceReport)
    assert 0.0 <= cont_rep.confluence_score <= 1.0
    assert 0.0 <= cont_rep.sav_score <= 1.0
    assert 0.0 <= cont_rep.bav_score <= 1.0
    assert 0.0 <= cont_rep.gochara_score <= 1.0
    assert cont_rep.amatyakaraka != ""

    # Test Candidate Synthesis Rule
    p_moe = 0.25
    p_final = filter_engine.synthesize_candidate_probability(p_moe, cont_rep.confluence_score)
    assert 0.0 <= p_final <= 1.0
    assert p_final == pytest.approx(p_moe * (0.50 + 0.50 * cont_rep.confluence_score), rel=1e-4)

    # 2. Test Legacy Confluence
    legacy_rep = filter_engine.evaluate_confluence(
        chart=chart,
        target_date=target_d,
        mahadasha_lord="jupiter",
        antardasha_lord="saturn",
        domain="career",
    )
    assert isinstance(legacy_rep, ClassicalConfluenceReport)
    assert legacy_rep.confluence_score == cont_rep.confluence_score
