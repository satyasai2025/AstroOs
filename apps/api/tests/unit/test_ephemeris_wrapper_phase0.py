"""
AstroOS — EphemerisWrapper Phase 0 Extension Tests (Module 9 Phase 0)

Covers the Foundation Extension work: sunrise/sunset computation,
declination, and threading previously-discarded tropical data (speed,
latitude, distance) through to SiderealPosition/EphemerisResult.

Uses Moshier fallback (no live .se1 files required), same pattern as
the existing ephemeris wrapper tests.
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper

_EPHE_PATH = "data/ephemeris"


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


# ── Sunrise / sunset ───────────────────────────────────────────────────────────

def test_sunrise_before_sunset(wrapper):
    jd = 2448057.9375  # 1990-06-15 10:30 UTC
    sunrise, sunset = wrapper.get_sunrise_sunset(jd, 28.6139, 77.2090)
    assert sunrise is not None
    assert sunset is not None
    assert sunrise < sunset


def test_sunset_follows_the_returned_sunrise_not_a_prior_day(wrapper):
    """
    Regression test for the specific sequencing bug found during
    development: searching sunset from the same start point as sunrise
    can return a sunset from BEFORE that sunrise. The gap between
    sunrise and sunset must be under 24 hours (same solar day), not
    negative or implausibly large.
    """
    jd = 2448057.9375
    sunrise, sunset = wrapper.get_sunrise_sunset(jd, 28.6139, 77.2090)
    assert 0 < (sunset - sunrise) < 1.0  # less than 24 hours apart


def test_daytime_birth_detected(wrapper):
    """1990-06-15 10:30 UTC at New Delhi (UTC+5:30) is ~16:00 local — daytime."""
    dt = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=28.6139, longitude=77.2090)
    assert result.is_daytime_birth is True


def test_nighttime_birth_detected(wrapper):
    """1990-06-15 20:00 UTC at New Delhi is ~01:30 local the next day — nighttime."""
    dt = datetime(1990, 6, 15, 20, 0, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=28.6139, longitude=77.2090)
    assert result.is_daytime_birth is False


def test_circumpolar_returns_none_not_error(wrapper):
    """Extreme latitude during polar day/night must degrade gracefully, not crash."""
    jd = 2448057.9375
    sunrise, sunset = wrapper.get_sunrise_sunset(jd, 89.0, 0.0)
    assert sunrise is None
    assert sunset is None


def test_ephemeris_result_is_daytime_birth_none_when_circumpolar(wrapper):
    dt = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=89.0, longitude=0.0)
    assert result.is_daytime_birth is None


# ── Declination ────────────────────────────────────────────────────────────────

def test_sun_declination_within_obliquity_bounds(wrapper):
    """Sun's declination must always be within Earth's axial tilt (~±23.44°)."""
    jd = 2448057.9375
    decl = wrapper.get_declination("sun", jd)
    assert -23.5 <= decl <= 23.5


def test_ketu_declination_is_negative_of_rahu(wrapper):
    """Ketu is derived from Rahu + 180°, and its declination mirrors Rahu's (sign-flipped)."""
    jd = 2448057.9375
    decl_rahu = wrapper.get_declination("rahu", jd)
    decl_ketu = wrapper.get_declination("ketu", jd)
    assert decl_ketu == pytest.approx(-decl_rahu, abs=1e-6)


def test_all_planets_declination_within_bounds(wrapper):
    jd = 2448057.9375
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
        decl = wrapper.get_declination(planet, jd)
        assert -90.0 <= decl <= 90.0  # sanity bound, not obliquity-specific for nodes/outer planets


# ── Threaded-through tropical data (speed, latitude, distance) ───────────────

def test_sidereal_position_carries_speed_latitude_distance(wrapper):
    dt = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=28.6139, longitude=77.2090)
    for p in result.planet_positions:
        # None of these should still be at the dataclass default (0.0) for
        # any real planet — a real ephemeris calculation always produces
        # nonzero distance and (for all but rare exact-zero-latitude
        # moments) nonzero values.
        assert p.distance_au > 0.0
        assert isinstance(p.speed_deg_per_day, float)
        assert isinstance(p.latitude_deg, float)
        assert isinstance(p.declination_deg, float)


def test_moon_speed_matches_expected_mean_motion(wrapper):
    """Moon's mean daily motion is ~13.2 degrees/day — a basic sanity check."""
    dt = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=28.6139, longitude=77.2090)
    moon = next(p for p in result.planet_positions if p.planet == "moon")
    assert 10.0 <= moon.speed_deg_per_day <= 16.0


def test_retrograde_planet_has_negative_speed(wrapper):
    """A planet flagged is_retrograde must have negative speed_deg_per_day (except Ketu, always flagged retrograde by convention)."""
    dt = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=28.6139, longitude=77.2090)
    for p in result.planet_positions:
        if p.is_retrograde and p.planet != "ketu":
            assert p.speed_deg_per_day < 0


def test_sidereal_position_defaults_preserved_for_manual_construction():
    """
    Existing test files across the codebase construct SiderealPosition
    directly without the new fields — confirm those defaults are exactly
    0.0, so none of those ~15 files silently got different behavior.
    """
    from apps.api.domain.ephemeris import DignityType, SiderealPosition

    p = SiderealPosition(
        planet="sun", sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )
    assert p.latitude_deg == 0.0
    assert p.distance_au == 0.0
    assert p.speed_deg_per_day == 0.0
    assert p.declination_deg == 0.0
