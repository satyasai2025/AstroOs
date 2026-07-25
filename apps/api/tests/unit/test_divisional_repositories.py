"""
AstroOS — DivisionalChartRepository & DivisionalPlanetRepository Unit Tests
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from apps.api.domain.divisional import VargaPosition
from apps.api.models.astrology import DivisionalChartModel, DivisionalPlanetPositionModel

_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)


def _make_varga_position(planet: str) -> VargaPosition:
    return VargaPosition(
        planet=planet,
        d1_sidereal_longitude=100.0,
        d1_rashi="leo",
        d1_rashi_degree=10.0,
        varga_rashi="cancer",
        varga_rashi_degree=5.0,
        varga_house_number=3,
        is_retrograde=False,
        is_combust=False,
        nakshatra="pushya",
        pada=2,
    )


async def _make_chart_id(birth_chart_repo) -> "uuid.UUID":
    return await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )


async def test_replace_for_birth_chart_creates_row(
    birth_chart_repo, divisional_chart_repo, db_session
):
    birth_chart_id = await _make_chart_id(birth_chart_repo)
    divisional_chart_id = await divisional_chart_repo.replace_for_birth_chart(
        birth_chart_id, "D9", lagna_rashi="cancer", lagna_degree=5.0
    )
    row = (
        await db_session.execute(
            select(DivisionalChartModel).where(DivisionalChartModel.id == divisional_chart_id)
        )
    ).scalar_one()
    assert row.chart_type == "D9"
    assert row.birth_chart_id == birth_chart_id
    assert row.lagna_rashi == "cancer"


async def test_replace_for_birth_chart_replaces_existing(
    birth_chart_repo, divisional_chart_repo, db_session
):
    """Calling twice for the same (birth_chart, varga) must not leave two rows."""
    birth_chart_id = await _make_chart_id(birth_chart_repo)
    first_id = await divisional_chart_repo.replace_for_birth_chart(
        birth_chart_id, "D9", lagna_rashi="cancer", lagna_degree=5.0
    )
    second_id = await divisional_chart_repo.replace_for_birth_chart(
        birth_chart_id, "D9", lagna_rashi="leo", lagna_degree=10.0
    )
    assert first_id != second_id  # old row deleted, new row created

    rows = (
        await db_session.execute(
            select(DivisionalChartModel)
            .where(DivisionalChartModel.birth_chart_id == birth_chart_id)
            .where(DivisionalChartModel.chart_type == "D9")
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].lagna_rashi == "leo"


async def test_replace_for_birth_chart_allows_multiple_vargas(
    birth_chart_repo, divisional_chart_repo, db_session
):
    birth_chart_id = await _make_chart_id(birth_chart_repo)
    await divisional_chart_repo.replace_for_birth_chart(
        birth_chart_id, "D9", lagna_rashi="cancer", lagna_degree=5.0
    )
    await divisional_chart_repo.replace_for_birth_chart(
        birth_chart_id, "D10", lagna_rashi="leo", lagna_degree=10.0
    )
    rows = (
        await db_session.execute(
            select(DivisionalChartModel).where(
                DivisionalChartModel.birth_chart_id == birth_chart_id
            )
        )
    ).scalars().all()
    assert {r.chart_type for r in rows} == {"D9", "D10"}


async def test_bulk_insert_persists_all_planets(
    birth_chart_repo, divisional_chart_repo, divisional_planet_repo, db_session
):
    birth_chart_id = await _make_chart_id(birth_chart_repo)
    divisional_chart_id = await divisional_chart_repo.replace_for_birth_chart(
        birth_chart_id, "D9", lagna_rashi="cancer", lagna_degree=5.0
    )
    planets = [
        _make_varga_position(p)
        for p in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    ]
    await divisional_planet_repo.bulk_insert(divisional_chart_id, planets)

    rows = (
        await db_session.execute(
            select(DivisionalPlanetPositionModel).where(
                DivisionalPlanetPositionModel.divisional_chart_id == divisional_chart_id
            )
        )
    ).scalars().all()
    assert len(rows) == 9
    assert {r.graha for r in rows} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"
    }
    assert all(r.rashi == "cancer" for r in rows)
    assert all(r.house_number == 3 for r in rows)


async def test_cascade_delete_removes_planet_positions(
    birth_chart_repo, divisional_chart_repo, divisional_planet_repo, db_session
):
    """
    Replacing a divisional chart deletes the old divisional_charts row,
    which must cascade-delete its divisional_planet_positions at the DB
    level (ON DELETE CASCADE from migration 0002) — no orphaned rows.
    """
    birth_chart_id = await _make_chart_id(birth_chart_repo)
    old_divisional_id = await divisional_chart_repo.replace_for_birth_chart(
        birth_chart_id, "D9", lagna_rashi="cancer", lagna_degree=5.0
    )
    await divisional_planet_repo.bulk_insert(old_divisional_id, [_make_varga_position("sun")])

    await divisional_chart_repo.replace_for_birth_chart(
        birth_chart_id, "D9", lagna_rashi="leo", lagna_degree=1.0
    )

    orphaned = (
        await db_session.execute(
            select(DivisionalPlanetPositionModel).where(
                DivisionalPlanetPositionModel.divisional_chart_id == old_divisional_id
            )
        )
    ).scalars().all()
    assert orphaned == []
