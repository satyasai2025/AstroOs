"""
AstroOS — HouseRepository Unit Tests
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from apps.api.domain.ephemeris import HouseCusp
from apps.api.models.astrology import HouseModel

_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)


def _make_houses() -> list[HouseCusp]:
    return [
        HouseCusp(house_number=n, longitude=float(n * 30), sidereal_longitude=float(n * 30 - 24), rashi="aries")
        for n in range(1, 13)
    ]


async def _make_chart_id(birth_chart_repo) -> "uuid.UUID":
    return await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )


async def test_replace_for_chart_inserts_all_12_houses(
    birth_chart_repo, house_repo, db_session
):
    chart_id = await _make_chart_id(birth_chart_repo)
    await house_repo.replace_for_chart(chart_id, _make_houses())

    rows = (
        await db_session.execute(
            select(HouseModel).where(HouseModel.chart_id == chart_id)
        )
    ).scalars().all()
    assert len(rows) == 12
    assert {r.house_number for r in rows} == set(range(1, 13))


async def test_replace_for_chart_stores_tropical_cusp_degree(
    birth_chart_repo, house_repo, db_session
):
    chart_id = await _make_chart_id(birth_chart_repo)
    await house_repo.replace_for_chart(chart_id, _make_houses())

    row = (
        await db_session.execute(
            select(HouseModel)
            .where(HouseModel.chart_id == chart_id)
            .where(HouseModel.house_number == 5)
        )
    ).scalar_one()
    assert float(row.cusp_degree) == pytest.approx(150.0)  # house 5 -> longitude = 5*30
    assert row.mid_degree is None  # no domain equivalent computed


async def test_replace_for_chart_is_idempotent(
    birth_chart_repo, house_repo, db_session
):
    chart_id = await _make_chart_id(birth_chart_repo)
    await house_repo.replace_for_chart(chart_id, _make_houses())
    await house_repo.replace_for_chart(chart_id, _make_houses())

    rows = (
        await db_session.execute(
            select(HouseModel).where(HouseModel.chart_id == chart_id)
        )
    ).scalars().all()
    assert len(rows) == 12
