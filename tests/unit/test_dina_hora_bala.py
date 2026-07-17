"""
AstroOS — Dina-Hora Bala Unit Tests (Module 9)

Uses a stub EphemerisWrapper (controllable next-sunrise) to test the
Dina/Hora lord matching precisely and deterministically. See
tests/integration/test_dina_hora_bala_integration.py for coverage
against real computed charts.
"""

import pytest

from apps.api.domain.ephemeris import (
    Ascendant, DignityType, EphemerisResult, PanchangaResult,
    SiderealPosition, TithiInfo, NakshatraInfo, YogaInfo, KaranaInfo, VaraInfo,
)
from apps.api.services.shadbala.dina_hora_bala import DinaHoraBalaCalculator


def _make_planet(planet):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def _make_panchanga(vara_lord="sun"):
    return PanchangaResult(
        tithi=TithiInfo(number=1, name="Pratipada", paksha="shukla", completion_percent=50.0),
        nakshatra=NakshatraInfo(
            nakshatra="ashwini", nakshatra_number=1, pada=1, lord="ketu",
            degree_in_nakshatra=5.0, degree_in_pada=1.0,
        ),
        yoga=YogaInfo(number=1, name="Vishkambha", completion_percent=50.0),
        karana=KaranaInfo(number=1, name="Bava", is_fixed=False),
        vara=VaraInfo(number=0, name="Sunday", lord=vara_lord),
        julian_day=0.0, ayanamsa_deg=24.0,
    )


def _make_ephemeris_result(birth_jd, sunrise_jd, sunset_jd, is_daytime_birth, vara_lord="sun"):
    return EphemerisResult(
        julian_day=birth_jd, ayanamsa_value=24.0, ayanamsa_system="lahiri",
        ascendant=Ascendant(
            longitude=0.0, sidereal_longitude=0.0, rashi="aries", rashi_degree=0.0,
            nakshatra="ashwini", pada=1,
        ),
        house_cusps=[], planet_positions=[], panchanga=_make_panchanga(vara_lord),
        sunrise_jd=sunrise_jd, sunset_jd=sunset_jd, is_daytime_birth=is_daytime_birth,
    )


class _StubWrapper:
    def __init__(self, next_sunrise):
        self._next_sunrise = next_sunrise

    def get_sunrise_sunset(self, jd, latitude, longitude):
        return self._next_sunrise, None


def test_dina_lord_matches_scores_15():
    """Sunday's lord is Sun — birth right at sunrise, hora 1 = sun's own hora too (both match)."""
    result = _make_ephemeris_result(
        birth_jd=0.0, sunrise_jd=0.0, sunset_jd=1.0, is_daytime_birth=True, vara_lord="sun",
    )
    calc = DinaHoraBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("sun"), result, latitude=0.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(30.0)


def test_dina_lord_no_match_scores_0_for_dina_component():
    result = _make_ephemeris_result(
        birth_jd=0.0, sunrise_jd=0.0, sunset_jd=1.0, is_daytime_birth=True, vara_lord="venus",
    )
    calc = DinaHoraBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("mars"), result, latitude=0.0, longitude=0.0)
    assert any("Dina" in t and "no match" in t for t in r.trace)


def test_hora_sequence_follows_chaldean_order_from_dina_lord():
    """Day split into 12 horas from sunrise=0 to sunset=12 -> each hora is exactly 1.0 wide."""
    calc = DinaHoraBalaCalculator(_StubWrapper(None))
    expected_sequence = ["saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon",
                          "saturn", "jupiter", "mars", "sun", "venus"]
    for hora_index, expected_lord in enumerate(expected_sequence):
        birth_jd = hora_index + 0.5
        result = _make_ephemeris_result(
            birth_jd=birth_jd, sunrise_jd=0.0, sunset_jd=12.0, is_daytime_birth=True, vara_lord="saturn",
        )
        r = calc.calculate(_make_planet(expected_lord), result, latitude=0.0, longitude=0.0)
        assert any(f"hora lord -> {expected_lord}" in t for t in r.trace), (
            f"hora {hora_index}: expected {expected_lord}"
        )


def test_night_hora_continues_from_hora_13():
    """Night horas (13-24) continue the same Chaldean cycle, not restart."""
    result = _make_ephemeris_result(
        birth_jd=12.5, sunrise_jd=0.0, sunset_jd=12.0, is_daytime_birth=False, vara_lord="saturn",
    )
    calc = DinaHoraBalaCalculator(_StubWrapper(next_sunrise=24.0))
    r = calc.calculate(_make_planet("saturn"), result, latitude=0.0, longitude=0.0)
    assert any("hora lord -> mercury" in t for t in r.trace)


def test_missing_sunrise_sunset_skips_hora_but_keeps_dina():
    result = _make_ephemeris_result(
        birth_jd=1.0, sunrise_jd=None, sunset_jd=None, is_daytime_birth=None, vara_lord="mars",
    )
    calc = DinaHoraBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("mars"), result, latitude=89.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(15.0)


def test_missing_next_sunrise_skips_hora_but_keeps_dina():
    result = _make_ephemeris_result(
        birth_jd=12.5, sunrise_jd=0.0, sunset_jd=12.0, is_daytime_birth=False, vara_lord="moon",
    )
    calc = DinaHoraBalaCalculator(_StubWrapper(next_sunrise=None))
    r = calc.calculate(_make_planet("moon"), result, latitude=89.0, longitude=0.0)
    assert r.value_shashtiamsas == pytest.approx(15.0)


def test_rejects_rahu_ketu():
    result = _make_ephemeris_result(birth_jd=0.5, sunrise_jd=0.0, sunset_jd=1.0, is_daytime_birth=True)
    calc = DinaHoraBalaCalculator(_StubWrapper(None))
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu"), result, latitude=0.0, longitude=0.0)


def test_calculate_all_returns_7_classical_grahas():
    result = _make_ephemeris_result(birth_jd=0.5, sunrise_jd=0.0, sunset_jd=1.0, is_daytime_birth=True)
    planets = [_make_planet(p) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    calc = DinaHoraBalaCalculator(_StubWrapper(None))
    results = calc.calculate_all(planets, result, latitude=0.0, longitude=0.0)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}


def test_trace_notes_varsha_masa_not_computed():
    result = _make_ephemeris_result(birth_jd=0.5, sunrise_jd=0.0, sunset_jd=1.0, is_daytime_birth=True)
    calc = DinaHoraBalaCalculator(_StubWrapper(None))
    r = calc.calculate(_make_planet("sun"), result, latitude=0.0, longitude=0.0)
    assert any("Varsha/Masa not computed" in t for t in r.trace)
