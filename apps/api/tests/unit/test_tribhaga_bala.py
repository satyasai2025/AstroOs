"""
AstroOS — Tribhaga Bala Unit Tests (Module 9)

Uses a stub EphemerisWrapper (controllable next-sunrise) to test the
day/night tribhaga boundary logic precisely and deterministically. See
tests/integration/test_tribhaga_bala_integration.py for coverage against
real computed charts.
"""

import pytest

from apps.api.domain.ephemeris import (
    Ascendant, DignityType, EphemerisResult, PanchangaResult,
    SiderealPosition, TithiInfo, NakshatraInfo, YogaInfo, KaranaInfo, VaraInfo,
)
from apps.api.services.shadbala.tribhaga_bala import TribhagaBalaCalculator


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


def _make_ephemeris_result(birth_jd, sunrise_jd, sunset_jd, is_daytime_birth):
    return EphemerisResult(
        julian_day=birth_jd, ayanamsa_value=24.0, ayanamsa_system="lahiri",
        ascendant=Ascendant(
            longitude=0.0, sidereal_longitude=0.0, rashi="aries", rashi_degree=0.0,
            nakshatra="ashwini", pada=1,
        ),
        house_cusps=[], planet_positions=[], panchanga=_make_panchanga(),
        sunrise_jd=sunrise_jd, sunset_jd=sunset_jd, is_daytime_birth=is_daytime_birth,
    )


class _StubWrapper:
    """Returns a FIXED next-sunrise, letting tests control night-tribhaga boundaries precisely."""

    def __init__(self, next_sunrise):
        self._next_sunrise = next_sunrise

    def get_sunrise_sunset(self, jd, latitude, longitude):
        return self._next_sunrise, None


def test_day_first_tribhaga_lord_is_mercury():
    """Sunrise=0, sunset=3 (day_length=3) -> tribhaga width=1. Birth at 0.5 -> tribhaga 1."""
    result = _make_ephemeris_result(birth_jd=0.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=True)
    calc = TribhagaBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("mercury"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(60.0)


def test_day_second_tribhaga_lord_is_sun():
    result = _make_ephemeris_result(birth_jd=1.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=True)
    calc = TribhagaBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("sun"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(60.0)


def test_day_third_tribhaga_lord_is_saturn():
    result = _make_ephemeris_result(birth_jd=2.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=True)
    calc = TribhagaBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("saturn"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(60.0)


def test_day_non_lord_planet_scores_zero():
    result = _make_ephemeris_result(birth_jd=0.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=True)
    calc = TribhagaBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("venus"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(0.0)


def test_jupiter_never_a_tribhaga_lord():
    """Jupiter should score 0 regardless of which tribhaga (day or night) it falls in."""
    calc = TribhagaBalaCalculator(_StubWrapper(10.0))
    for birth_jd in [0.5, 1.5, 2.5]:
        result = _make_ephemeris_result(birth_jd=birth_jd, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=True)
        r = calc.calculate(_make_planet("jupiter"), result, latitude=0.0, longitude=0.0)
        assert r.value_shashtiamsas == pytest.approx(0.0)


def test_night_first_tribhaga_lord_is_moon():
    """Sunset=3, next_sunrise=6 (night_length=3) -> width=1. Birth at 3.5 -> night tribhaga 1."""
    result = _make_ephemeris_result(birth_jd=3.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=False)
    calc = TribhagaBalaCalculator(_StubWrapper(next_sunrise=6.0))
    r = calc.calculate(_make_planet("moon"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(60.0)


def test_night_second_tribhaga_lord_is_venus():
    result = _make_ephemeris_result(birth_jd=4.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=False)
    calc = TribhagaBalaCalculator(_StubWrapper(next_sunrise=6.0))
    r = calc.calculate(_make_planet("venus"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(60.0)


def test_night_third_tribhaga_lord_is_mars():
    result = _make_ephemeris_result(birth_jd=5.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=False)
    calc = TribhagaBalaCalculator(_StubWrapper(next_sunrise=6.0))
    r = calc.calculate(_make_planet("mars"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(60.0)


def test_missing_sunrise_sunset_degrades_gracefully():
    result = _make_ephemeris_result(birth_jd=1.0, sunrise_jd=None, sunset_jd=None, is_daytime_birth=None)
    calc = TribhagaBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("sun"), result, latitude=89.0, longitude=0.0)
    assert r.value_shashtiamsas == 0.0


def test_missing_next_sunrise_degrades_gracefully():
    """Circumpolar edge case: current sunset known but following sunrise not computable."""
    result = _make_ephemeris_result(birth_jd=3.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=False)
    calc = TribhagaBalaCalculator(_StubWrapper(next_sunrise=None))
    r = calc.calculate(_make_planet("moon"), result, latitude=89.0, longitude=0.0)
    assert r.value_shashtiamsas == 0.0


def test_rejects_rahu_ketu():
    result = _make_ephemeris_result(birth_jd=0.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=True)
    calc = TribhagaBalaCalculator(_StubWrapper(None))
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu"), result, latitude=0.0, longitude=0.0)


def test_calculate_all_returns_7_classical_grahas():
    result = _make_ephemeris_result(birth_jd=0.5, sunrise_jd=0.0, sunset_jd=3.0, is_daytime_birth=True)
    planets = [_make_planet(p) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    calc = TribhagaBalaCalculator(_StubWrapper(None))
    results = calc.calculate_all(planets, result, latitude=0.0, longitude=0.0)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}
