"""
AstroOS — pytest Configuration & Fixtures

Provides fixtures shared across all test modules.
Database fixtures use an in-memory SQLite engine so tests
run without a real PostgreSQL server in CI.

For integration tests that need PostgreSQL, set TEST_DATABASE_URL.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.models.base import AstroBase
from apps.api.repositories.user_repository import UserRepository
from apps.api.services.auth_service import AuthService

# ── Test database ─────────────────────────────────────────────────────────────

TEST_DB_URL: str = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        # SQLite in-memory needs connect_args for asyncio
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DB_URL else {},
    )
    async with engine.begin() as conn:
        await conn.run_sync(AstroBase.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(AstroBase.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with factory() as session:
        yield session
        await session.rollback()  # each test gets a clean slate


@pytest_asyncio.fixture
async def user_repo(db_session: AsyncSession) -> UserRepository:
    return UserRepository(db_session)


@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis


@pytest_asyncio.fixture
async def auth_service(user_repo: UserRepository, mock_redis: AsyncMock) -> AuthService:
    return AuthService(user_repo=user_repo, redis_client=mock_redis)


# ── Domain object factories ───────────────────────────────────────────────────

def make_user(
    email: str = "test@example.com",
    display_name: str = "Test User",
    role: UserRole = UserRole.RESEARCHER,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
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
