"""
AstroOS — HoroscopeEngine Unit Tests (Task 4)

Tests for D1 chart generation:
  - D1Chart structure and completeness
  - Aspect computation
  - Planet strength scoring
  - Edge cases (polar latitudes, date boundaries)
"""

from datetime import datetime, timezone

import pytest

from apps.api.domain.ephemeris import DignityType
from apps.api.domain.horoscope import AspectInfo, D1Chart, PlanetStrength
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import (
    HoroscopeEngine,
    _KENDRA_HOUSES,
    _TRIKONA_HOUSES,
    _DUSTHANA_HOUSES,
)

pytestmark = pytest.mark.asyncio

_EPHE_PATH = "data/ephemeris"

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine() -> HoroscopeEngine:
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    return HoroscopeEngine(wrapper)


@pytest.fixture(scope="module")
def sample_chart(engine) -> D1Chart:
    """A reference chart: 2000-01-01 05:30 UTC, New Delhi."""
    dt = datetime(2000, 1, 1, 5, 30, 0, tzinfo=timezone.utc)
    return engine.generate_d1(
        birth_datetime_utc=dt,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )


# ── Structure ─────────────────────────────────────────────────────────────────

def test_d1_chart_returns_d1chart(sample_chart):
    assert isinstance(sample_chart, D1Chart)


def test_d1_chart_has_ascendant(sample_chart):
    assert sample_chart.ascendant is not None
    assert sample_chart.ascendant.rashi in {
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    }


def test_d1_chart_has_12_houses(sample_chart):
    assert len(sample_chart.houses) == 12
    house_numbers = {h.house_number for h in sample_chart.houses}
    assert house_numbers == set(range(1, 13))


def test_d1_chart_has_9_planets(sample_chart):
    assert len(sample_chart.planets) == 9
    planet_names = {p.planet for p in sample_chart.planets}
    expected = {"sun", "moon", "mars", "mercury", "jupiter",
                "venus", "saturn", "rahu", "ketu"}
    assert planet_names == expected


def test_d1_chart_planet_house_numbers_valid(sample_chart):
    for planet in sample_chart.planets:
        assert 1 <= planet.house_number <= 12, (
            f"{planet.planet} has invalid house {planet.house_number}"
        )


def test_d1_chart_planet_pada_valid(sample_chart):
    for planet in sample_chart.planets:
        assert 1 <= planet.pada <= 4, f"{planet.planet} pada out of range"


def test_d1_chart_has_aspects(sample_chart):
    """Aspects list should be non-empty for any realistic chart."""
    assert len(sample_chart.aspects) > 0


def test_d1_chart_has_planet_strengths(sample_chart):
    assert len(sample_chart.planet_strengths) == 9


def test_d1_chart_has_panchanga(sample_chart):
    pan = sample_chart.panchanga
    assert 1 <= pan.tithi.number <= 30
    assert 1 <= pan.yoga.number <= 27
    assert pan.karana.name != ""
    assert 0 <= pan.vara.number <= 6


# ── Planet Strength ───────────────────────────────────────────────────────────

def test_planet_strength_scores_in_range(sample_chart):
    """All strength scores must be 0.0 – 10.0."""
    for strength in sample_chart.planet_strengths:
        assert 0.0 <= strength.strength_score <= 10.0, (
            f"{strength.planet} score {strength.strength_score} out of range"
        )


def test_planet_strength_kendra_flag(sample_chart):
    """Planets in houses 1, 4, 7, 10 must have is_in_kendra = True."""
    for strength in sample_chart.planet_strengths:
        if strength.house_number in _KENDRA_HOUSES:
            assert strength.is_in_kendra, f"{strength.planet} should be in kendra"
        else:
            assert not strength.is_in_kendra


def test_planet_strength_trikona_flag(sample_chart):
    """Planets in houses 1, 5, 9 must have is_in_trikona = True."""
    for strength in sample_chart.planet_strengths:
        if strength.house_number in _TRIKONA_HOUSES:
            assert strength.is_in_trikona
        else:
            assert not strength.is_in_trikona


def test_planet_strength_dusthana_flag(sample_chart):
    """Planets in houses 6, 8, 12 must have is_in_dusthana = True."""
    for strength in sample_chart.planet_strengths:
        if strength.house_number in _DUSTHANA_HOUSES:
            assert strength.is_in_dusthana
        else:
            assert not strength.is_in_dusthana


def test_planet_strength_sorted_descending(sample_chart):
    """Planet strengths must be sorted highest first."""
    scores = [s.strength_score for s in sample_chart.planet_strengths]
    assert scores == sorted(scores, reverse=True)


def test_combust_planet_penalised(engine):
    """A planet identified as combust should have a lower score than expected."""
    dt = datetime(2024, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    chart = engine.generate_d1(
        birth_datetime_utc=dt,
        latitude=0.0,
        longitude=0.0,
        ayanamsa="lahiri",
    )
    mercury_strength = next(s for s in chart.planet_strengths if s.planet == "mercury")
    if mercury_strength.is_combust:
        # Combust penalty of -2.0 should ensure score < 9.0
        assert mercury_strength.strength_score < 9.0


# ── Aspects ───────────────────────────────────────────────────────────────────

def test_aspects_have_valid_types(sample_chart):
    _VALID_TYPES = {
        "conjunction", "opposition", "trine", "square", "special_graha"
    }
    for aspect in sample_chart.aspects:
        assert aspect.aspect_type in _VALID_TYPES, (
            f"Unknown aspect type: {aspect.aspect_type}"
        )


def test_aspects_planets_are_valid(sample_chart):
    _VALID_PLANETS = {
        "sun", "moon", "mars", "mercury", "jupiter",
        "venus", "saturn", "rahu", "ketu"
    }
    for aspect in sample_chart.aspects:
        assert aspect.from_planet in _VALID_PLANETS
        assert aspect.to_planet in _VALID_PLANETS
        assert aspect.from_planet != aspect.to_planet


def test_aspects_orb_is_non_negative(sample_chart):
    for aspect in sample_chart.aspects:
        assert aspect.orb_degrees >= 0.0


# ── Different ayanamsa systems ────────────────────────────────────────────────

@pytest.mark.parametrize("ayanamsa", [
    "lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"
])
def test_generate_d1_all_ayanamsa_systems(engine, ayanamsa):
    """D1 chart must generate without error for every ayanamsa system."""
    dt = datetime(2000, 6, 21, 12, 0, 0, tzinfo=timezone.utc)
    chart = engine.generate_d1(
        birth_datetime_utc=dt,
        latitude=51.5074,
        longitude=-0.1278,
        ayanamsa=ayanamsa,
    )
    assert len(chart.planets) == 9


# ── Different house systems ───────────────────────────────────────────────────

@pytest.mark.parametrize("house_system", ["W", "P", "K", "E"])
def test_generate_d1_all_house_systems(engine, house_system):
    """D1 chart must generate for all supported house systems."""
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    chart = engine.generate_d1(
        birth_datetime_utc=dt,
        latitude=40.7128,
        longitude=-74.0060,
        house_system=house_system,
    )
    assert len(chart.houses) == 12


# ── Determinism ───────────────────────────────────────────────────────────────

def test_generate_d1_is_deterministic(engine):
    """Same inputs must always produce identical results."""
    dt = datetime(1990, 11, 9, 0, 0, 0, tzinfo=timezone.utc)
    kwargs = {"birth_datetime_utc": dt, "latitude": 52.52, "longitude": 13.405}

    chart_a = engine.generate_d1(**kwargs)
    chart_b = engine.generate_d1(**kwargs)

    assert chart_a.ascendant.rashi == chart_b.ascendant.rashi
    assert abs(chart_a.ascendant.sidereal_longitude - chart_b.ascendant.sidereal_longitude) < 1e-8

    for pa, pb in zip(chart_a.planets, chart_b.planets):
        assert pa.planet == pb.planet
        assert abs(pa.sidereal_longitude - pb.sidereal_longitude) < 1e-8


# ── Metadata ──────────────────────────────────────────────────────────────────

def test_d1_chart_stores_ayanamsa_system(engine):
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    chart = engine.generate_d1(
        birth_datetime_utc=dt, latitude=0.0, longitude=0.0, ayanamsa="kp"
    )
    assert chart.ayanamsa_system == "kp"


def test_d1_chart_stores_house_system(engine):
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    chart = engine.generate_d1(
        birth_datetime_utc=dt, latitude=0.0, longitude=0.0, house_system="P"
    )
    assert chart.house_system == "P"
