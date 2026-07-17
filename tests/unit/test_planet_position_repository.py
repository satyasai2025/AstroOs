"""
AstroOS — PlanetPositionRepository Unit Tests
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.models.astrology import PlanetPositionModel
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.planet_position_repository import (
    PlanetPositionRepository,
    _tropical_longitude,
)

pytestmark = pytest.mark.asyncio

_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)


def _make_planet(planet: str, sidereal_longitude: float) -> SiderealPosition:
    return SiderealPosition(
        planet=planet,
        sidereal_longitude=sidereal_longitude,
        rashi="leo",
        rashi_degree=12.5,
        house_number=5,
        nakshatra="pushya",
        pada=2,
        is_retrograde=False,
        is_combust=False,
        combustion_orb=None,
        dignity=DignityType.OWN,
    )


async def _make_chart_id(birth_chart_repo: BirthChartRepository) -> "uuid.UUID":
    return await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )


def test_tropical_longitude_recovers_correctly():
    """sidereal = tropical - ayanamsa, so tropical = sidereal + ayanamsa."""
    assert _tropical_longitude(sidereal_longitude=100.0, ayanamsa_value=24.0) == pytest.approx(124.0)
    # Wraps past 360
    assert _tropical_longitude(sidereal_longitude=350.0, ayanamsa_value=20.0) == pytest.approx(10.0)


async def test_replace_for_chart_inserts_all_planets(
    birth_chart_repo, planet_position_repo, db_session
):
    chart_id = await _make_chart_id(birth_chart_repo)
    planets = [_make_planet(p, 100.0 + i) for i, p in enumerate(
        ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    )]

    await planet_position_repo.replace_for_chart(chart_id, planets, ayanamsa_value_deg=24.0)

    rows = (
        await db_session.execute(
            select(PlanetPositionModel).where(PlanetPositionModel.chart_id == chart_id)
        )
    ).scalars().all()
    assert len(rows) == 9
    assert {r.graha for r in rows} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"
    }


async def test_replace_for_chart_is_idempotent(
    birth_chart_repo, planet_position_repo, db_session
):
    """Re-persisting the same chart must not accumulate duplicate rows."""
    chart_id = await _make_chart_id(birth_chart_repo)
    planets = [_make_planet("sun", 100.0)]

    await planet_position_repo.replace_for_chart(chart_id, planets, ayanamsa_value_deg=24.0)
    await planet_position_repo.replace_for_chart(chart_id, planets, ayanamsa_value_deg=24.0)

    rows = (
        await db_session.execute(
            select(PlanetPositionModel).where(PlanetPositionModel.chart_id == chart_id)
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_replace_for_chart_derives_tropical_longitude(
    birth_chart_repo, planet_position_repo, db_session
):
    chart_id = await _make_chart_id(birth_chart_repo)
    planets = [_make_planet("sun", 100.0)]

    await planet_position_repo.replace_for_chart(chart_id, planets, ayanamsa_value_deg=24.0)

    row = (
        await db_session.execute(
            select(PlanetPositionModel).where(PlanetPositionModel.chart_id == chart_id)
        )
    ).scalar_one()
    assert float(row.longitude_deg) == pytest.approx(124.0)
    assert float(row.sidereal_longitude_deg) == pytest.approx(100.0)
    assert row.dignity == "own"
    # As of Module 9 Phase 0, these ARE populated from SiderealPosition
    # (previously left NULL when SiderealPosition didn't carry them).
    # This test's synthetic planet doesn't set them, so they take the
    # dataclass defaults (0.0), not None.
    assert float(row.latitude_deg) == pytest.approx(0.0)
    assert float(row.speed_deg_per_day) == pytest.approx(0.0)
    assert float(row.distance_au) == pytest.approx(0.0)
    assert row.nakshatra_id is None  # still deferred — see repository docstring


async def test_replace_for_chart_persists_real_phase0_data(
    birth_chart_repo, planet_position_repo, db_session
):
    """
    Confirms actual non-zero latitude/speed/distance survive the
    round trip, not just that the zero-default case doesn't crash.
    """
    chart_id = await _make_chart_id(birth_chart_repo)
    planet = SiderealPosition(
        planet="mars", sidereal_longitude=100.0, rashi="leo", rashi_degree=12.5,
        house_number=5, nakshatra="pushya", pada=2, is_retrograde=True,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
        latitude_deg=-1.9849, distance_au=1.279408, speed_deg_per_day=-0.15,
        declination_deg=2.525,
    )

    await planet_position_repo.replace_for_chart(chart_id, [planet], ayanamsa_value_deg=24.0)

    row = (
        await db_session.execute(
            select(PlanetPositionModel).where(PlanetPositionModel.chart_id == chart_id)
        )
    ).scalar_one()
    assert float(row.latitude_deg) == pytest.approx(-1.9849)
    assert float(row.distance_au) == pytest.approx(1.279408)
    assert float(row.speed_deg_per_day) == pytest.approx(-0.15)
