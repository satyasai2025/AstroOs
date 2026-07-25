"""
AstroOS — Saptavargaja Bala Integration Tests (Module 9)

Exercises SaptavargajaBalaCalculator against real chart data computed
by EphemerisWrapper + DivisionalEngine (Moshier fallback, same pattern
as every other integration test in this codebase — no live .se1 files
required).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala.saptavargaja_bala import SaptavargajaBalaCalculator

_EPHE_PATH = "data/ephemeris"
_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


@pytest.fixture(scope="module")
def d1_chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    return horoscope_engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )


def test_all_7_classical_grahas_computed(wrapper, d1_chart):
    div_engine = DivisionalEngine(wrapper)
    calc = SaptavargajaBalaCalculator(div_engine)
    results = calc.calculate_all(
        d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    assert len(results) == 7
    assert {r.planet for r in results} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
    }


def test_values_within_theoretical_bounds(wrapper, d1_chart):
    """Theoretical range: 7 * 1.875 (all debilitated) to 7 * 60 (all exalted)."""
    div_engine = DivisionalEngine(wrapper)
    calc = SaptavargajaBalaCalculator(div_engine)
    results = calc.calculate_all(
        d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    for r in results:
        assert 7 * 1.875 <= r.value_shashtiamsas <= 7 * 60.0


def test_deterministic_across_repeated_calls(wrapper, d1_chart):
    div_engine = DivisionalEngine(wrapper)
    calc = SaptavargajaBalaCalculator(div_engine)
    first = calc.calculate_all(d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON)
    second = calc.calculate_all(d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON)
    assert first == second


def test_trace_covers_all_7_vargas(wrapper, d1_chart):
    div_engine = DivisionalEngine(wrapper)
    calc = SaptavargajaBalaCalculator(div_engine)
    result = calc.calculate(
        "sun", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    for varga in ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]:
        assert any(varga in t for t in result.trace)


def test_different_charts_produce_different_totals():
    """Sanity check: two unrelated birth charts should generally differ, not always coincidentally match."""
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    horoscope_engine = HoroscopeEngine(wrapper)
    div_engine = DivisionalEngine(wrapper)
    calc = SaptavargajaBalaCalculator(div_engine)

    chart_a = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    chart_b = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1975, 12, 25, 3, 0, 0, tzinfo=timezone.utc),
        latitude=40.7128, longitude=-74.0060,
    )

    results_a = {
        r.planet: r.value_shashtiamsas for r in calc.calculate_all(
            chart_a, birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
            latitude=28.6139, longitude=77.2090,
        )
    }
    results_b = {
        r.planet: r.value_shashtiamsas for r in calc.calculate_all(
            chart_b, birth_datetime_utc=datetime(1975, 12, 25, 3, 0, 0, tzinfo=timezone.utc),
            latitude=40.7128, longitude=-74.0060,
        )
    }
    assert results_a != results_b
