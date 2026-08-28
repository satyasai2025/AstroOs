"""
Unit tests for SarvatoBhadraEngine (28-Nakshatra SBC & Special Nadi Vedhas).
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.sarvato_bhadra_engine import SarvatoBhadraEngine, SarvatoBhadraReport


def test_sarvato_bhadra_engine_evaluation():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horoscope = HoroscopeEngine(wrapper)
    sbc_engine = SarvatoBhadraEngine(ephemeris_path="data/ephemeris")

    # Birth chart: 1980-05-15 14:30 UTC
    birth_dt = datetime(1980, 5, 15, 14, 30, tzinfo=timezone.utc)
    chart = horoscope.generate_d1(birth_dt, 28.6139, 77.2090)

    # Evaluate SBC on 2024-05-01
    rep = sbc_engine.evaluate_sbc(chart, target_date=date(2024, 5, 1))

    assert isinstance(rep, SarvatoBhadraReport)
    assert rep.janma_nakshatra_28 != ""
    assert -1.0 <= rep.sbc_composite_score <= 1.0
    assert rep.overall_transit_shield in ["EXCELLENT", "AUSPICIOUS", "MIXED", "AFFLICTED", "SEVERE_VULNERABILITY"]
    assert "JANMA" in rep.nadi_nakshatras
    assert "KARMA" in rep.nadi_nakshatras
    assert "VAINASHIKA" in rep.nadi_nakshatras
    assert len(rep.active_planet_positions_28) >= 7
