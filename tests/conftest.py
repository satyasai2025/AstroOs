"""
Shared synthetic fixtures for Module 14 (Event Engine) tests — usable
from both tests/unit and tests/integration.

Also provides shared database fixtures (test_engine, db_session, user_repo)
and domain object factories (make_user) used by auth/repository tests.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult, SarvashtakavargaResult
from apps.api.domain.ephemeris import Ascendant, HouseCusp, SiderealPosition
from apps.api.domain.events import NatalSnapshot
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.domain.yoga import YogaResult
from apps.api.models.base import AstroBase
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.dasha_repository import DashaRepository
from apps.api.repositories.divisional_chart_repository import DivisionalChartRepository
from apps.api.repositories.divisional_planet_repository import DivisionalPlanetRepository
from apps.api.repositories.house_repository import HouseRepository
from apps.api.repositories.planet_position_repository import PlanetPositionRepository
from apps.api.repositories.user_repository import UserRepository
from apps.api.services.auth_service import AuthService

# ── Test database ─────────────────────────────────────────────────────────────

TEST_DB_URL: str = os.environ.get("TEST_DATABASE_URL")
if not TEST_DB_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL environment variable is required. "
        "PostgreSQL 16 is the only supported database. "
        "Set TEST_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname"
    )

# ── PostgreSQL ENUM types ─────────────────────────────────────────────────────
# The model column factories (astrology.py) use create_type=False because
# ENUM DDL is managed by Alembic migrations. create_all() needs these types
# to exist in the database before it can create tables that reference them.

ENUM_DEFINITIONS = {
    "rashi": (
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ),
    "graha": (
        "sun", "moon", "mars", "mercury", "jupiter",
        "venus", "saturn", "rahu", "ketu",
    ),
    "nakshatra_name": (
        "ashwini", "bharani", "krittika", "rohini", "mrigashira",
        "ardra", "punarvasu", "pushya", "ashlesha", "magha",
        "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati",
        "vishakha", "anuradha", "jyeshtha", "mula", "purva_ashadha",
        "uttara_ashadha", "shravana", "dhanishtha", "shatabhisha",
        "purva_bhadrapada", "uttara_bhadrapada", "revati",
    ),
    "chart_type": (
        "D1", "D2", "D3", "D4", "D7", "D9", "D10",
        "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
    ),
    "ayanamsa_system": (
        "lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra",
    ),
    "dignity_type": (
        "exalted", "own", "moolatrikona", "friendly", "neutral", "enemy", "debilitated",
    ),
    "dasha_type": (
        "vimshottari", "ashtottari", "yogini", "kalachakra", "chara", "narayana",
    ),
}


async def _ensure_enums(conn):
    """Create PostgreSQL ENUM types if they don't already exist."""
    for enum_name, values in ENUM_DEFINITIONS.items():
        values_sql = ", ".join(f"'{v}'" for v in values)
        await conn.execute(text(f"""
            DO $$ BEGIN
                CREATE TYPE {enum_name} AS ENUM ({values_sql});
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """))


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_engine():
    """SQLAlchemy engine bound to the configured PostgreSQL test database."""
    engine = create_async_engine(TEST_DB_URL, echo=False)

    async with engine.begin() as conn:
        await _ensure_enums(conn)
        await conn.run_sync(AstroBase.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(AstroBase.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test transactional DB session; rolled back after each test."""
    factory = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user_repo(db_session: AsyncSession) -> UserRepository:
    """UserRepository wired to the test DB session."""
    return UserRepository(db_session)


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mocked Redis client — all operations return None/True."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis


@pytest_asyncio.fixture
async def auth_service(
    user_repo: UserRepository,
    mock_redis: AsyncMock,
) -> AuthService:
    """AuthService wired to the test UserRepository and mock Redis."""
    return AuthService(user_repo=user_repo, redis_client=mock_redis)


# ── Domain object factories ───────────────────────────────────────────────────


def make_user(
    email: str = "test@example.com",
    display_name: str = "Test User",
    role: UserRole = UserRole.RESEARCHER,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    """Build a User instance with sensible defaults (hashed_password is a fake)."""
    now = datetime.now(timezone.utc)
    return User(
        id=UserId(uuid.uuid4()),
        email=email,
        display_name=display_name,
        hashed_password="$2b$12$fakehash",
        role=role,
        status=status,
        created_at=now,
        updated_at=now,
    )


@pytest_asyncio.fixture
async def birth_chart_repo(db_session: AsyncSession) -> BirthChartRepository:
    """BirthChartRepository wired to the test DB session."""
    return BirthChartRepository(db_session)


@pytest_asyncio.fixture
async def dasha_repo(db_session: AsyncSession) -> DashaRepository:
    """DashaRepository wired to the test DB session."""
    return DashaRepository(db_session)


@pytest_asyncio.fixture
async def divisional_chart_repo(db_session: AsyncSession) -> DivisionalChartRepository:
    """DivisionalChartRepository wired to the test DB session."""
    return DivisionalChartRepository(db_session)


@pytest_asyncio.fixture
async def divisional_planet_repo(db_session: AsyncSession) -> DivisionalPlanetRepository:
    """DivisionalPlanetRepository wired to the test DB session."""
    return DivisionalPlanetRepository(db_session)


@pytest_asyncio.fixture
async def house_repo(db_session: AsyncSession) -> HouseRepository:
    """HouseRepository wired to the test DB session."""
    return HouseRepository(db_session)


@pytest_asyncio.fixture
async def planet_position_repo(db_session: AsyncSession) -> PlanetPositionRepository:
    """PlanetPositionRepository wired to the test DB session."""
    return PlanetPositionRepository(db_session)


@pytest.fixture
def minimal_chart() -> D1Chart:
    ascendant = Ascendant(
        longitude=10.0, sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        nakshatra="ashwini", pada=3,
    )
    moon = SiderealPosition(
        planet="moon", sidereal_longitude=40.0, rashi="taurus", rashi_degree=10.0,
        house_number=2, nakshatra="rohini", pada=1, is_retrograde=False, is_combust=False,
        combustion_orb=None, dignity=None,
    )
    houses = [
        HouseCusp(house_number=n, longitude=float(n * 10), sidereal_longitude=float(n * 10), rashi="aries")
        for n in range(1, 13)
    ]

    return D1Chart(
        ephemeris=None,
        ascendant=ascendant,
        houses=houses,
        planets=[moon],
        aspects=[],
        planet_strengths=[],
        panchanga=None,
        ayanamsa_system="lahiri",
        house_system="W",
    )


@pytest.fixture
def natal_snapshot(minimal_chart) -> NatalSnapshot:
    chart_id = uuid.uuid4()

    yoga = YogaResult(
        yoga_id="BPHS-PM-001", name="Ruchaka Yoga", category="Panch Mahapurusha",
        source_text="BPHS 46", rule_version="1.0", is_present=True, strength="full",
    )
    bala = BalaComponentResult(
        component_id="SHADBALA-NAISARGIKA", component_name="Naisargika Bala",
        rule_version="1.0", planet="jupiter", value_shashtiamsas=34.28,
    )
    bhinna = BhinnashtakavargaResult(
        target_planet="jupiter", bindus_by_rashi=tuple([4] * 12), total_bindus=48,
    )
    sarva = SarvashtakavargaResult(bindus_by_rashi=tuple([28] * 12), total_bindus=337)

    return NatalSnapshot(
        chart_id=chart_id,
        chart=minimal_chart,
        yogas=(yoga,),
        shadbala_components={"naisargika_bala": [bala]},
        bhinnashtakavarga=(bhinna,),
        sarvashtakavarga=sarva,
    )
