"""
AstroOS — Nathonnata Bala Unit Tests (Module 9)

Uses a stub EphemerisWrapper (controllable next-sunrise) to test the
noon/midnight proximity logic precisely and deterministically. See
tests/integration/test_nathonnata_bala_integration.py for coverage
against real computed charts.
"""

import pytest

from apps.api.domain.ephemeris import (
    Ascendant, DignityType, EphemerisResult, PanchangaResult,
    SiderealPosition, TithiInfo, NakshatraInfo, YogaInfo, KaranaInfo, VaraInfo,
)
from apps.api.services.shadbala.nathonnata_bala import NathonnataBalaCalculator


def _make_planet(planet):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def _make_panchanga():
    return PanchangaResult(
        tithi=TithiInfo(number=1, name="Pratipada", paksha="shukla", completion_percent=50.0),
        nakshatra=NakshatraInfo(
            nakshatra="ashwini", nakshatra_number=1, pada=1, lord="ketu",
            degree_in_nakshatra=5.0, degree_in_pada=1.0,
        ),
        yoga=YogaInfo(number=1, name="Vishkambha", completion_percent=50.0),
        karana=KaranaInfo(number=1, name="Bava", is_fixed=False),
        vara=VaraInfo(number=0, name="Sunday", lord="sun"),
        julian_day=0.0, ayanamsa_deg=24.0,
    )


def _make_ephemeris_result(birth_jd, sunrise_jd, sunset_jd):
    return EphemerisResult(
        julian_day=birth_jd, ayanamsa_value=24.0, ayanamsa_system="lahiri",
        ascendant=Ascendant(
            longitude=0.0, sidereal_longitude=0.0, rashi="aries", rashi_degree=0.0,
            nakshatra="ashwini", pada=1,
        ),
        house_cusps=[], planet_positions=[], panchanga=_make_panchanga(),
        sunrise_jd=sunrise_jd, sunset_jd=sunset_jd, is_daytime_birth=None,
    )


class _StubWrapper:
    """Returns a FIXED next-sunrise, letting tests control noon/midnight boundaries precisely."""

    def __init__(self, next_sunrise):
        self._next_sunrise = next_sunrise

    def get_sunrise_sunset(self, jd, latitude, longitude):
        return self._next_sunrise, None


def test_diurnal_planet_max_bala_exactly_at_noon():
    result = _make_ephemeris_result(birth_jd=3.0, sunrise_jd=0.0, sunset_jd=6.0)
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    r = calc.calculate(_make_planet("sun"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(60.0, abs=1e-6)


def test_diurnal_planet_min_bala_exactly_at_midnight():
    result = _make_ephemeris_result(birth_jd=9.0, sunrise_jd=0.0, sunset_jd=6.0)
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    r = calc.calculate(_make_planet("jupiter"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(0.0, abs=1e-6)


def test_nocturnal_planet_max_bala_exactly_at_midnight():
    result = _make_ephemeris_result(birth_jd=9.0, sunrise_jd=0.0, sunset_jd=6.0)
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    r = calc.calculate(_make_planet("moon"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(60.0, abs=1e-6)


def test_nocturnal_planet_min_bala_exactly_at_noon():
    result = _make_ephemeris_result(birth_jd=3.0, sunrise_jd=0.0, sunset_jd=6.0)
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    r = calc.calculate(_make_planet("mars"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(0.0, abs=1e-6)


def test_diurnal_and_nocturnal_complementary_at_same_birth_time():
    """A diurnal and a nocturnal planet's values must sum to exactly 60 at the same birth time."""
    result = _make_ephemeris_result(birth_jd=4.0, sunrise_jd=0.0, sunset_jd=6.0)
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    diurnal = calc.calculate(_make_planet("venus"), result, latitude=0.0, longitude=0.0)
    nocturnal = calc.calculate(_make_planet("saturn"), result, latitude=0.0, longitude=0.0)
    assert diurnal.value_shashtiamsas + nocturnal.value_shashtiamsas == pytest.approx(60.0, abs=1e-6)


def test_mercury_always_full_marks_regardless_of_time():
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    for birth_jd in [0.5, 3.0, 6.0, 9.0, 11.5]:
        result = _make_ephemeris_result(birth_jd=birth_jd, sunrise_jd=0.0, sunset_jd=6.0)
        r = calc.calculate(_make_planet("mercury"), result, latitude=0.0, longitude=0.0)
        assert r.value_shashtiamsas == pytest.approx(60.0)


def test_missing_sunrise_sunset_degrades_gracefully():
    result = _make_ephemeris_result(birth_jd=1.0, sunrise_jd=None, sunset_jd=None)
    calc = NathonnataBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("sun"), result, latitude=89.0, longitude=0.0)
    assert r.value_shashtiamsas == 0.0


def test_missing_next_sunrise_degrades_gracefully():
    result = _make_ephemeris_result(birth_jd=3.0, sunrise_jd=0.0, sunset_jd=6.0)
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=None))
    r = calc.calculate(_make_planet("sun"), result, latitude=89.0, longitude=0.0)
    assert r.value_shashtiamsas == 0.0


def test_rejects_rahu_ketu():
    result = _make_ephemeris_result(birth_jd=3.0, sunrise_jd=0.0, sunset_jd=6.0)
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu"), result, latitude=0.0, longitude=0.0)


def test_calculate_all_returns_7_classical_grahas():
    result = _make_ephemeris_result(birth_jd=3.0, sunrise_jd=0.0, sunset_jd=6.0)
    planets = [_make_planet(p) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    results = calc.calculate_all(planets, result, latitude=0.0, longitude=0.0)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}


def test_values_always_between_0_and_60():
    calc = NathonnataBalaCalculator(_StubWrapper(next_sunrise=12.0))
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        for birth_jd in [0.5, 2.0, 4.0, 6.5, 9.0, 11.5]:
            result = _make_ephemeris_result(birth_jd=birth_jd, sunrise_jd=0.0, sunset_jd=6.0)
            r = calc.calculate(_make_planet(planet), result, latitude=0.0, longitude=0.0)
            assert 0.0 <= r.value_shashtiamsas <= 60.0
