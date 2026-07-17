"""
AstroOS — Ojayugmarasyamsa Bala Integration Tests (Module 9)

Exercises OjayugmarasyamsaBalaCalculator against real chart data
computed by EphemerisWrapper + DivisionalEngine (Moshier fallback, same
pattern as every other integration test in this codebase — no live
.se1 files required).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala.ojayugmarasyamsa_bala import OjayugmarasyamsaBalaCalculator

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
    calc = OjayugmarasyamsaBalaCalculator(div_engine)
    results = calc.calculate_all(
        d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    assert len(results) == 7
    assert {r.planet for r in results} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
    }


def test_values_within_theoretical_bounds(wrapper, d1_chart):
    div_engine = DivisionalEngine(wrapper)
    calc = OjayugmarasyamsaBalaCalculator(div_engine)
    results = calc.calculate_all(
        d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    for r in results:
        assert 0.0 <= r.value_shashtiamsas <= 30.0


def test_mercury_always_scores_full_marks(wrapper, d1_chart):
    """Mercury (neuter) should always score exactly 30, regardless of actual sign parity."""
    div_engine = DivisionalEngine(wrapper)
    calc = OjayugmarasyamsaBalaCalculator(div_engine)
    result = calc.calculate(
        "mercury", d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    assert result.value_shashtiamsas == pytest.approx(30.0)


def test_deterministic_across_repeated_calls(wrapper, d1_chart):
    div_engine = DivisionalEngine(wrapper)
    calc = OjayugmarasyamsaBalaCalculator(div_engine)
    first = calc.calculate_all(d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON)
    second = calc.calculate_all(d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON)
    assert first == second
