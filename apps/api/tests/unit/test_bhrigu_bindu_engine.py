"""
Unit tests for BhriguBinduEngine.
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.services.bhrigu_bindu_engine import BhriguBinduEngine, BhriguBinduReport
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine


def test_bhrigu_bindu_calculation_and_transit():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horoscope = HoroscopeEngine(wrapper)
    bb_engine = BhriguBinduEngine(ephemeris_path="data/ephemeris")

    # Birth Chart: 1980-05-15 14:30 UTC
    birth_dt = datetime(1980, 5, 15, 14, 30, tzinfo=timezone.utc)
    chart = horoscope.generate_d1(birth_dt, 28.6139, 77.2090)

    bb_deg, rashi, r_deg, nak, pada, h_num = bb_engine.calculate_bhrigu_bindu(chart)

    assert 0.0 <= bb_deg <= 360.0
    assert rashi in ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    assert 0.0 <= r_deg <= 30.0
    assert 1 <= pada <= 4
    assert 1 <= h_num <= 12

    # Transit Evaluation
    rep = bb_engine.evaluate_transit(chart, target_date=date(2024, 5, 1))
    assert isinstance(rep, BhriguBinduReport)
    assert -1.0 <= rep.destiny_impact_score <= 1.0
    assert rep.activation_status in ["BENEFIC_TRIGGER", "MALEFIC_TRIGGER", "MIXED_TRIGGER", "INACTIVE"]
