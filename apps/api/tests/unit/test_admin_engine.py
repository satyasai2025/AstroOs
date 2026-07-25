"""
AstroOS — AdminEngine Unit Tests (Module 23, Phase 1)
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.admin import AdminUserSummary
from apps.api.services.admin_engine import AdminEngine


def _make_session_mock() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    # AsyncSession.execute() is the only async boundary — it returns an
    # already-materialized, synchronous sqlalchemy.engine.Result. Every
    # method on that Result (.scalars(), .all(), .scalar_one_or_none(), ...)
    # is synchronous, matching admin_engine.py's real (non-awaited) usage.
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=[])
    scalars_mock.scalar_one_or_none = MagicMock(return_value=None)
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=scalars_mock)
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=result_mock)
    return session


class TestListUsers:
    async def test_empty_result(self):
        session = _make_session_mock()
        engine = AdminEngine(session=session)
        users = await engine.list_users()
        assert users == ()

    async def test_with_status_filter(self):
        session = _make_session_mock()
        engine = AdminEngine(session=session)
        users = await engine.list_users(status="active")
        assert users == ()

    async def test_with_role_filter(self):
        session = _make_session_mock()
        engine = AdminEngine(session=session)
        users = await engine.list_users(role="researcher")
        assert users == ()

    async def test_no_session_returns_empty(self):
        engine = AdminEngine()
        users = await engine.list_users()
        assert users == ()


class TestGetUser:
    async def test_no_repo_returns_none(self):
        engine = AdminEngine()
        result = await engine.get_user(uuid.uuid4())
        assert result is None

    async def test_user_not_found(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        engine = AdminEngine(user_repo=repo, session=_make_session_mock())
        result = await engine.get_user(uuid.uuid4())
        assert result is None


class TestUpdateUserRole:
    async def test_invalid_role_returns_none(self):
        engine = AdminEngine()
        result = await engine.update_user_role(uuid.uuid4(), "invalid_role")
        assert result is None

    async def test_no_session_returns_none(self):
        engine = AdminEngine()
        result = await engine.update_user_role(uuid.uuid4(), "admin")
        assert result is None


class TestSuspendActivate:
    async def test_suspend_no_session_returns_false(self):
        engine = AdminEngine()
        assert await engine.suspend_user(uuid.uuid4()) is False

    async def test_activate_no_session_returns_false(self):
        engine = AdminEngine()
        assert await engine.activate_user(uuid.uuid4()) is False


class TestSystemHealth:
    async def test_no_ephemeris_still_returns_status(self):
        engine = AdminEngine()
        status = await engine.get_system_status()
        assert status.status == "healthy"
        assert "chart_engine" in status.modules

    async def test_module_registry_has_all_modules(self):
        registry = AdminEngine.get_module_registry()
        assert "foundation" in registry
        assert "admin_portal" in registry
        assert registry["admin_portal"] == "1.0"

    async def test_ephemeris_warning_degrades_status(self):
        ephe = AsyncMock()
        mode = AsyncMock()
        mode.value = "moshier"
        status_dto = AsyncMock()
        status_dto.mode = mode
        status_dto.official_data = False
        ephe.get_status = AsyncMock(return_value=status_dto)
        engine = AdminEngine(ephemeris_service=ephe)
        status = await engine.get_system_status()
        assert status.status == "degraded"
