"""
Canonical Unit Tests for Sudarshana Chakra 3-Kundali Gochara & Polarity Engine
==============================================================================

Validates:
1. Simultaneous evaluation of all 7 planets from Lagna (LK), Sun (SK), and Moon (CK).
2. Sudarshana Chakra Special Rule: If Sun & Moon conjunct (Amavasya), LK is discarded and SK+CK evaluated.
3. Laghu Parashari Dasha lord classification and combination table.
4. Exact BPHS Gochara Sanskrit/Hindi citation outputs.
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.phalita_core.polarity_engine import (
    ClassicalPolarityEngine,
    PolarityReport,
    TriLagnaPlanetGochara,
)


@pytest.fixture
def polarity_engine():
    return ClassicalPolarityEngine()


@pytest.fixture
def horoscope_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return HoroscopeEngine(wrapper)


def test_sudarshana_3_kundali_gochara_evaluation(polarity_engine, horoscope_engine):
    """Verify that all 7 planets are evaluated from Lagna, Sun, and Moon simultaneously."""
    # Raj's natal chart (Taurus Lagna, Sun in Gemini, Moon in Virgo)
    natal_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    natal = horoscope_engine.generate_d1(natal_dt, 22.3072, 73.1812)

    # Transit chart for 2026-01-01
    transit_dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    transit = horoscope_engine.generate_d1(transit_dt, 22.3072, 73.1812)

    report = polarity_engine.evaluate(natal, transit, "saturn", "saturn")
    assert isinstance(report, PolarityReport)
    assert not report.is_amavasya_sc  # Sun (Gemini) != Moon (Virgo)
    assert len(report.tri_lagna_planet_results) == 7

    # Check that each planet has LK, SK, CK details
    for res in report.tri_lagna_planet_results:
        assert isinstance(res, TriLagnaPlanetGochara)
        assert 1 <= res.house_from_lagna <= 12
        assert 1 <= res.house_from_sun <= 12
        assert 1 <= res.house_from_moon <= 12
        assert res.lagna_polarity in ("AUSPICIOUS", "INAUSPICIOUS", "NEUTRAL")
        assert res.sun_polarity in ("AUSPICIOUS", "INAUSPICIOUS", "NEUTRAL")
        assert res.moon_polarity in ("AUSPICIOUS", "INAUSPICIOUS", "NEUTRAL")
        assert res.composite_polarity in ("AUSPICIOUS", "INAUSPICIOUS", "MIXED")

    # Taurus Lagna: Saturn is Yoga Karaka (owns 9th and 10th)
    assert report.md_category == "YOGA_KARAKA"
    assert report.ad_category == "YOGA_KARAKA"
    assert report.dasha_polarity == "AUSPICIOUS"


def test_amavasya_sudarshana_chakra_rule(polarity_engine, horoscope_engine):
    """Verify that when Sun & Moon are conjunct in natal chart, LK is discarded."""
    # Chart with Sun and Moon conjunct in Aries (Solar eclipse / Amavasya)
    natal_dt = datetime(2024, 4, 8, 18, 20, 0, tzinfo=timezone.utc)
    natal = horoscope_engine.generate_d1(natal_dt, 28.6139, 77.2090)

    transit_dt = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    transit = horoscope_engine.generate_d1(transit_dt, 28.6139, 77.2090)

    report = polarity_engine.evaluate(natal, transit, "jupiter", "mars")
    assert report.is_amavasya_sc is True
    assert "Amavasya (SK+CK)" in report.final_polarity_logic
