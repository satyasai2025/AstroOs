"""
AstroOS — Ojayugmarasyamsa Bala Unit Tests (Module 9)

Uses a stub DivisionalEngine (not real ephemeris computation) to test
the odd/even scoring logic precisely and deterministically. See
tests/integration/test_ojayugmarasyamsa_bala_integration.py for coverage
against real computed charts.
"""

from datetime import datetime, timezone

import pytest

from apps.api.domain.divisional import VargaAscendant, VargaChart, VargaPosition
from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.ojayugmarasyamsa_bala import OjayugmarasyamsaBalaCalculator

_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)


def _make_d1_position(planet, rashi):
    return SiderealPosition(
        planet=planet, sidereal_longitude=15.0, rashi=rashi, rashi_degree=15.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def _make_d1_chart(planets):
    class _FakeChart:
        pass

    chart = _FakeChart()
    chart.planets = planets
    return chart


def _make_varga_position(planet, varga_rashi):
    return VargaPosition(
        planet=planet, d1_sidereal_longitude=15.0, d1_rashi="aries", d1_rashi_degree=15.0,
        varga_rashi=varga_rashi, varga_rashi_degree=15.0, varga_house_number=1,
        is_retrograde=False, is_combust=False, nakshatra="ashwini", pada=1,
    )


class _StubDivisionalEngine:
    """Returns a FIXED D9 rashi for the planet under test."""

    def __init__(self, planet: str, d9_rashi: str):
        self._planet = planet
        self._d9_rashi = d9_rashi

    def compute(self, *, birth_datetime_utc, latitude, longitude, varga, ayanamsa="lahiri", house_system="W"):
        return VargaChart(
            varga=varga, divisor=9,
            ascendant=VargaAscendant(
                d1_sidereal_longitude=0.0, d1_rashi="aries", d1_rashi_degree=0.0,
                varga_rashi=self._d9_rashi, varga_rashi_degree=0.0,
            ),
            planet_positions=(_make_varga_position(self._planet, self._d9_rashi),),
            ayanamsa_system=ayanamsa, julian_day=0.0,
        )


@pytest.mark.parametrize("planet", ["sun", "mars", "jupiter", "saturn"])
def test_male_planet_full_marks_both_odd(planet):
    d1_chart = _make_d1_chart([_make_d1_position(planet, "aries")])  # odd
    stub = _StubDivisionalEngine(planet, "leo")  # odd
    calc = OjayugmarasyamsaBalaCalculator(stub)
    result = calc.calculate(planet, d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)
    assert result.value_shashtiamsas == pytest.approx(30.0)


@pytest.mark.parametrize("planet", ["sun", "mars", "jupiter", "saturn"])
def test_male_planet_zero_marks_both_even(planet):
    d1_chart = _make_d1_chart([_make_d1_position(planet, "taurus")])  # even
    stub = _StubDivisionalEngine(planet, "cancer")  # even
    calc = OjayugmarasyamsaBalaCalculator(stub)
    result = calc.calculate(planet, d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)
    assert result.value_shashtiamsas == pytest.approx(0.0)


@pytest.mark.parametrize("planet", ["moon", "venus"])
def test_female_planet_full_marks_both_even(planet):
    d1_chart = _make_d1_chart([_make_d1_position(planet, "taurus")])  # even
    stub = _StubDivisionalEngine(planet, "cancer")  # even
    calc = OjayugmarasyamsaBalaCalculator(stub)
    result = calc.calculate(planet, d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)
    assert result.value_shashtiamsas == pytest.approx(30.0)


@pytest.mark.parametrize("planet", ["moon", "venus"])
def test_female_planet_zero_marks_both_odd(planet):
    d1_chart = _make_d1_chart([_make_d1_position(planet, "aries")])  # odd
    stub = _StubDivisionalEngine(planet, "leo")  # odd
    calc = OjayugmarasyamsaBalaCalculator(stub)
    result = calc.calculate(planet, d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)
    assert result.value_shashtiamsas == pytest.approx(0.0)


def test_mercury_full_marks_regardless_of_parity():
    d1_chart = _make_d1_chart([_make_d1_position("mercury", "taurus")])  # even
    stub = _StubDivisionalEngine("mercury", "leo")  # odd
    calc = OjayugmarasyamsaBalaCalculator(stub)
    result = calc.calculate("mercury", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)
    assert result.value_shashtiamsas == pytest.approx(30.0)


def test_mixed_d1_match_d9_no_match_gives_half():
    d1_chart = _make_d1_chart([_make_d1_position("sun", "aries")])  # odd — match
    stub = _StubDivisionalEngine("sun", "taurus")  # even — no match
    calc = OjayugmarasyamsaBalaCalculator(stub)
    result = calc.calculate("sun", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)
    assert result.value_shashtiamsas == pytest.approx(15.0)


def test_missing_d1_position_only_counts_d9():
    d1_chart = _make_d1_chart([])  # sun not present
    stub = _StubDivisionalEngine("sun", "leo")  # odd — match
    calc = OjayugmarasyamsaBalaCalculator(stub)
    result = calc.calculate("sun", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)
    assert result.value_shashtiamsas == pytest.approx(15.0)
    assert any("D1: planet not found" in t for t in result.trace)


def test_rejects_rahu_ketu():
    d1_chart = _make_d1_chart([])
    stub = _StubDivisionalEngine("rahu", "aries")
    calc = OjayugmarasyamsaBalaCalculator(stub)
    with pytest.raises(ValueError):
        calc.calculate("rahu", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)


def test_calculate_all_returns_7_classical_grahas():
    d1_chart = _make_d1_chart([_make_d1_position("sun", "aries")])
    stub = _StubDivisionalEngine("sun", "leo")
    calc = OjayugmarasyamsaBalaCalculator(stub)
    results = calc.calculate_all(d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)
    assert len(results) == 7
    assert {r.planet for r in results} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
    }


def test_values_always_between_0_and_30():
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        for rashi in ["aries", "taurus", "gemini", "cancer"]:
            d1_chart = _make_d1_chart([_make_d1_position(planet, rashi)])
            stub = _StubDivisionalEngine(planet, rashi)
            calc = OjayugmarasyamsaBalaCalculator(stub)
            result = calc.calculate(
                planet, d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0,
            )
            assert 0.0 <= result.value_shashtiamsas <= 30.0
