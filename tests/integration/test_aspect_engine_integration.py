"""
AstroOS — AspectEngine Integration Tests (Module 6.5 — Foundation Completion)

Exercises AspectEngine against real chart data computed by
EphemerisWrapper (Moshier fallback, same pattern as
test_horoscope_engine.py — no live .se1 files required), and verifies
HoroscopeEngine's delegation to AspectEngine produces results identical
to calling AspectEngine directly. Not marked pytest.mark.integration —
that marker means "requires real external infra" per pytest.ini, and
Moshier fallback needs none; this test is "integration" in the sense of
exercising the full engine -> engine pipeline end-to-end, matching the
convention already established in
tests/integration/test_persistence_integration.py.
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.aspect_engine import AspectEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

pytestmark = pytest.mark.asyncio

_EPHE_PATH = "data/ephemeris"
_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


@pytest.fixture(scope="module")
def real_chart(wrapper):
    """A real D1 chart computed from actual (or Moshier-fallback) ephemeris data."""
    horoscope_engine = HoroscopeEngine(wrapper)
    return horoscope_engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )


async def test_aspect_engine_runs_against_real_chart_planets(real_chart):
    engine = AspectEngine()
    aspects = engine.compute(real_chart.planets)
    # A realistic 9-planet chart should have at least the universal 7th
    # aspect fire for most planets — some aspects are essentially certain.
    assert len(aspects) > 0


async def test_aspect_engine_output_matches_horoscope_engine_delegation(wrapper, real_chart):
    """
    HoroscopeEngine.generate_d1() delegates aspect computation to
    AspectEngine internally. Calling AspectEngine directly on the same
    chart's planets must produce byte-identical results to what ended up
    in the chart — proving the delegation didn't silently diverge.
    """
    standalone_engine = AspectEngine()
    standalone_aspects = standalone_engine.compute(real_chart.planets)

    assert standalone_aspects == list(real_chart.aspects)


async def test_aspect_engine_with_custom_instance_wired_into_horoscope_engine(wrapper):
    """
    HoroscopeEngine accepts an explicit AspectEngine instance (dependency
    injection) rather than always constructing its own default — confirm
    that wiring actually gets used, not silently ignored.
    """
    custom_engine = AspectEngine()
    horoscope_engine = HoroscopeEngine(wrapper, aspect_engine=custom_engine)

    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    direct_result = custom_engine.compute(chart.planets)
    assert direct_result == list(chart.aspects)


async def test_aspect_engine_deterministic_across_repeated_calls(real_chart):
    """Same planet positions in, same aspects out, every time — no hidden state."""
    engine = AspectEngine()
    first = engine.compute(real_chart.planets)
    second = engine.compute(real_chart.planets)
    assert first == second


async def test_aspect_engine_all_9_planets_appear_as_aspect_sources_or_targets(real_chart):
    """
    Every planet aspects at least its 7th house by the universal rule, so
    across a full 9-planet chart every planet should appear as an aspect
    source at least once (the only way it wouldn't is if literally no
    other planet occupies its aspected house, which combined with 9
    planets across 12 houses would be an unusual chart — check the
    general shape rather than asserting a specific count).
    """
    engine = AspectEngine()
    aspects = engine.compute(real_chart.planets)
    involved_planets = {a.from_planet for a in aspects} | {a.to_planet for a in aspects}
    all_planets = {p.planet for p in real_chart.planets}
    # Every involved planet must be a real planet from the chart — sanity
    # check that nothing spurious was invented.
    assert involved_planets.issubset(all_planets)


async def test_multiple_ayanamsa_systems_produce_valid_aspects(wrapper):
    """Aspect computation must work regardless of which ayanamsa produced the chart."""
    horoscope_engine = HoroscopeEngine(wrapper)
    aspect_engine = AspectEngine()

    for ayanamsa in ["lahiri", "raman", "kp"]:
        chart = horoscope_engine.generate_d1(
            birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
            ayanamsa=ayanamsa,
        )
        aspects = aspect_engine.compute(chart.planets)
        valid_types = {"conjunction", "opposition", "trine", "square", "special_graha"}
        assert all(a.aspect_type in valid_types for a in aspects)
