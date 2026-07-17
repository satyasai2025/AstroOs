"""
AstroOS — BirthChartRepository Unit Tests

All DB I/O runs against the shared in-memory SQLite fixture from
tests/conftest.py — no real PostgreSQL required.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from apps.api.models.astrology import BirthChartModel
from apps.api.repositories.birth_chart_repository import BirthChartRepository

pytestmark = pytest.mark.asyncio

_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)


async def test_get_or_create_creates_new_row(birth_chart_repo: BirthChartRepository):
    chart_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )
    assert chart_id is not None


async def test_get_or_create_deduplicates_identical_input(
    birth_chart_repo: BirthChartRepository,
):
    """A second call with the exact same birth input must reuse the row."""
    first_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )
    second_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )
    assert first_id == second_id


async def test_get_or_create_distinguishes_different_ayanamsa(
    birth_chart_repo: BirthChartRepository,
):
    """Same birth moment/location but different ayanamsa must NOT dedupe."""
    lahiri_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )
    raman_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="raman",
        house_system="W",
    )
    assert lahiri_id != raman_id


async def test_get_or_create_stores_subject_name_and_defaults(
    birth_chart_repo: BirthChartRepository, db_session
):
    chart_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )
    row = (
        await db_session.execute(
            select(BirthChartModel).where(BirthChartModel.id == chart_id)
        )
    ).scalar_one()
    assert row.subject_name == "Unnamed"
    assert row.timezone_offset_minutes == 0  # _BIRTH_DT is true UTC


async def test_get_or_create_custom_subject_name(birth_chart_repo, db_session):
    chart_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=10.0,
        longitude=20.0,
        ayanamsa="lahiri",
        house_system="W",
        subject_name="Test Subject",
    )
    row = (
        await db_session.execute(
            select(BirthChartModel).where(BirthChartModel.id == chart_id)
        )
    ).scalar_one()
    assert row.subject_name == "Test Subject"


async def test_update_d1_summary_fills_expected_fields(birth_chart_repo, db_session):
    chart_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )
    await birth_chart_repo.update_d1_summary(
        chart_id,
        ayanamsa_value_deg=24.123456,
        lagna_rashi="leo",
        lagna_degree=15.5,
        moon_nakshatra="pushya",
    )
    row = (
        await db_session.execute(
            select(BirthChartModel).where(BirthChartModel.id == chart_id)
        )
    ).scalar_one()
    assert row.lagna_rashi == "leo"
    assert row.moon_nakshatra == "pushya"
    assert float(row.lagna_degree) == pytest.approx(15.5)
    assert float(row.ayanamsa_value_deg) == pytest.approx(24.123456, abs=1e-5)


async def test_update_d1_summary_unknown_chart_raises(birth_chart_repo):
    import uuid

    with pytest.raises(ValueError):
        await birth_chart_repo.update_d1_summary(
            uuid.uuid4(),
            ayanamsa_value_deg=1.0,
            lagna_rashi="aries",
            lagna_degree=1.0,
            moon_nakshatra="ashwini",
        )
