"""
AstroOS — AdminEngine Unit Tests (Module 23, Phase 1)
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.domain.admin import AdminUserSummary
from apps.api.services.admin_engine import AdminEngine


def _make_repo_mock(list_result=()) -> AsyncMock:
    """UserRepository mock. AdminEngine now delegates all User access to
    UserRepository (Phase 10 cleanup, 2026-07-23) — no raw session."""
    repo = AsyncMock()
    repo.list_all = AsyncMock(return_value=list_result)
    repo.count_all = AsyncMock(return_value=0)
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


class TestListUsers:
    async def test_empty_result(self):
        engine = AdminEngine(user_repo=_make_repo_mock())
        users = await engine.list_users()
        assert users == ()

    async def test_with_status_filter(self):
        engine = AdminEngine(user_repo=_make_repo_mock())
        users = await engine.list_users(status="active")
        assert users == ()

    async def test_with_role_filter(self):
        engine = AdminEngine(user_repo=_make_repo_mock())
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
        engine = AdminEngine(user_repo=repo)
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
