"""
Shared fixtures for Module 14 Phase 3 (EventRepository) persistence
tests — a REAL PostgreSQL 16 database.

Depends on the root tests/conftest.py for the authoritative test engine,
schema lifecycle (create_all / drop_all), and db_session. This file only
adds integration-specific convenience fixtures.

birth_chart_id opens a dedicated session (not db_session) so that
the router test can inject db_session via dependency_overrides without
transaction conflicts from the setup fixture.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.models.astrology import BirthChartModel
from apps.api.models import user as _user_models  # noqa: F401 — registers UserModel's table in AstroBase.metadata


@pytest_asyncio.fixture(autouse=True)
async def _truncate_committed_data(test_engine):
    """Remove committed rows that leak across tests via birth_chart_id or persist_d1."""
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE dashas, planet_positions, houses, divisional_planet_positions, divisional_charts, events, birth_charts RESTART IDENTITY CASCADE"))
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE dashas, planet_positions, houses, divisional_planet_positions, divisional_charts, events, birth_charts RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def birth_chart_id(test_engine) -> uuid.UUID:
    """Creates one real birth_charts row and commits it.

    Uses its own session so that the shared test db_session (used both
    by the test assertion and the router's dependency override) is never
    touched by setup DML.
    """
    factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with factory() as session:
        model = BirthChartModel(
            subject_name="Test Subject",
            birth_datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc),
            birth_latitude=28.6139,
            birth_longitude=77.2090,
            timezone_offset_minutes=330,
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        id_ = model.id
    return id_
