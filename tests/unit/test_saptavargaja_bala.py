"""
AstroOS — Saptavargaja Bala Unit Tests (Module 9)

Uses a stub DivisionalEngine (not real ephemeris computation) to test
the point-scoring arithmetic precisely and deterministically. See
tests/integration/test_saptavargaja_bala_integration.py for coverage
against real computed charts.
"""

from datetime import datetime, timezone

import pytest

from apps.api.domain.divisional import VargaAscendant, VargaChart, VargaPosition
from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.shadbala.saptavargaja_bala import SaptavargajaBalaCalculator

_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)


def _make_d1_position(planet, rashi, rashi_degree=15.0):
    return SiderealPosition(
        planet=planet, sidereal_longitude=15.0, rashi=rashi, rashi_degree=rashi_degree,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def _make_d1_chart(planets):
    class _FakeChart:
        pass

    chart = _FakeChart()
    chart.planets = planets
    return chart


def _make_varga_position(planet, varga_rashi, varga_rashi_degree=15.0):
    return VargaPosition(
        planet=planet, d1_sidereal_longitude=15.0, d1_rashi="aries", d1_rashi_degree=15.0,
        varga_rashi=varga_rashi, varga_rashi_degree=varga_rashi_degree,
        varga_house_number=1, is_retrograde=False, is_combust=False,
        nakshatra="ashwini", pada=1,
    )


class _StubDivisionalEngine:
    """Returns a FIXED rashi for every varga/planet — lets tests control dignity precisely."""

    def __init__(self, rashi_by_varga: dict[str, str]):
        self._rashi_by_varga = rashi_by_varga

    def compute(self, *, birth_datetime_utc, latitude, longitude, varga, ayanamsa="lahiri", house_system="W"):
        rashi = self._rashi_by_varga[varga]
        return VargaChart(
            varga=varga, divisor=1,
            ascendant=VargaAscendant(
                d1_sidereal_longitude=0.0, d1_rashi="aries", d1_rashi_degree=0.0,
                varga_rashi=rashi, varga_rashi_degree=0.0,
            ),
            planet_positions=(_make_varga_position("saturn", rashi),),
            ayanamsa_system=ayanamsa, julian_day=0.0,
        )


def test_all_own_sign_gives_maximum_expected_sum():
    """If dignity is 'own' in D1 and all 6 vargas, sum = 7 * 30 = 210."""
    d1_chart = _make_d1_chart([_make_d1_position("saturn", "capricorn")])  # saturn's own sign
    stub = _StubDivisionalEngine({v: "capricorn" for v in ["D2", "D3", "D7", "D9", "D12", "D30"]})
    calc = SaptavargajaBalaCalculator(stub)
    result = calc.calculate(
        "saturn", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0,
    )
    assert result.value_shashtiamsas == pytest.approx(7 * 30.0)


def test_all_exalted_gives_maximum_possible_sum():
    """Saturn exalts in Libra — if exalted in all 7, sum = 7 * 60 = 420."""
    d1_chart = _make_d1_chart([_make_d1_position("saturn", "libra")])
    stub = _StubDivisionalEngine({v: "libra" for v in ["D2", "D3", "D7", "D9", "D12", "D30"]})
    calc = SaptavargajaBalaCalculator(stub)
    result = calc.calculate(
        "saturn", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0,
    )
    assert result.value_shashtiamsas == pytest.approx(7 * 60.0)


def test_all_debilitated_gives_minimum_sum():
    """Saturn debilitates in Aries — if debilitated in all 7, sum = 7 * 1.875."""
    d1_chart = _make_d1_chart([_make_d1_position("saturn", "aries")])
    stub = _StubDivisionalEngine({v: "aries" for v in ["D2", "D3", "D7", "D9", "D12", "D30"]})
    calc = SaptavargajaBalaCalculator(stub)
    result = calc.calculate(
        "saturn", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0,
    )
    assert result.value_shashtiamsas == pytest.approx(7 * 1.875)


def test_mixed_dignities_sum_correctly():
    """D1 own (30) + 6 vargas neutral (7.5 each = 45) = 75."""
    d1_chart = _make_d1_chart([_make_d1_position("saturn", "capricorn")])  # own
    # sagittarius is ruled by jupiter — neither friend nor enemy of saturn
    # (saturn's friends: mercury, venus; enemies: sun, moon, mars) → neutral
    stub = _StubDivisionalEngine({v: "sagittarius" for v in ["D2", "D3", "D7", "D9", "D12", "D30"]})
    calc = SaptavargajaBalaCalculator(stub)
    result = calc.calculate(
        "saturn", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0,
    )
    assert result.value_shashtiamsas == pytest.approx(30.0 + 6 * 7.5)


def test_missing_d1_position_skips_d1_gracefully():
    d1_chart = _make_d1_chart([])  # saturn not present
    stub = _StubDivisionalEngine({v: "capricorn" for v in ["D2", "D3", "D7", "D9", "D12", "D30"]})
    calc = SaptavargajaBalaCalculator(stub)
    result = calc.calculate(
        "saturn", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0,
    )
    assert result.value_shashtiamsas == pytest.approx(6 * 30.0)  # only the 6 vargas count
    assert any("D1: planet not found" in t for t in result.trace)


def test_rejects_rahu_ketu():
    d1_chart = _make_d1_chart([])
    stub = _StubDivisionalEngine({v: "capricorn" for v in ["D2", "D3", "D7", "D9", "D12", "D30"]})
    calc = SaptavargajaBalaCalculator(stub)
    with pytest.raises(ValueError):
        calc.calculate("rahu", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0)


def test_trace_documents_every_varga():
    d1_chart = _make_d1_chart([_make_d1_position("saturn", "capricorn")])
    stub = _StubDivisionalEngine({v: "capricorn" for v in ["D2", "D3", "D7", "D9", "D12", "D30"]})
    calc = SaptavargajaBalaCalculator(stub)
    result = calc.calculate(
        "saturn", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0,
    )
    for varga in ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]:
        assert any(varga in t for t in result.trace)


def test_calculate_all_returns_7_classical_grahas():
    d1_chart = _make_d1_chart([_make_d1_position("saturn", "capricorn")])
    stub = _StubDivisionalEngine({v: "capricorn" for v in ["D2", "D3", "D7", "D9", "D12", "D30"]})
    calc = SaptavargajaBalaCalculator(stub)
    results = calc.calculate_all(
        d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=0.0, longitude=0.0,
    )
    assert len(results) == 7
    assert {r.planet for r in results} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
    }
