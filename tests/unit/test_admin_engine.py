"""
AstroOS — AdminEngine Unit Tests (Module 23, Phase 1)

Updated as part of Phase 10's R3 cleanup (2026-07-23): AdminEngine no
longer holds a raw AsyncSession — all User-aggregate DB access now goes
through UserRepository (list_all/count_all/set_role/set_status), matching
every other engine's layering. These tests mock UserRepository instead
of a raw session; the engine's own branching behavior (no-repo guards,
invalid-role handling, ephemeris status logic) is otherwise unchanged.
"""

import uuid
from unittest.mock import AsyncMock

from apps.api.services.admin_engine import AdminEngine


class TestListUsers:
    async def test_empty_result(self):
        repo = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        engine = AdminEngine(user_repo=repo)
        users = await engine.list_users()
        assert users == ()

    async def test_with_status_filter(self):
        repo = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        engine = AdminEngine(user_repo=repo)
        users = await engine.list_users(status="active")
        assert users == ()
        repo.list_all.assert_awaited_once_with(status="active", role=None, limit=100, offset=0)

    async def test_with_role_filter(self):
        repo = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        engine = AdminEngine(user_repo=repo)
        users = await engine.list_users(role="researcher")
        assert users == ()
        repo.list_all.assert_awaited_once_with(status=None, role="researcher", limit=100, offset=0)

    async def test_no_repo_returns_empty(self):
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
    async def test_no_repo_returns_none(self):
        engine = AdminEngine()
        result = await engine.update_user_role(uuid.uuid4(), "admin")
        assert result is None

    async def test_invalid_role_with_repo_returns_none_without_calling_repo(self):
        """Invalid role strings must fail UserRole(...) parsing before
        ever reaching the repository — set_role should not be called."""
        repo = AsyncMock()
        engine = AdminEngine(user_repo=repo)
        result = await engine.update_user_role(uuid.uuid4(), "not_a_real_role")
        assert result is None
        repo.set_role.assert_not_awaited()

    async def test_user_not_found_returns_none(self):
        repo = AsyncMock()
        repo.set_role = AsyncMock(return_value=None)
        engine = AdminEngine(user_repo=repo)
        result = await engine.update_user_role(uuid.uuid4(), "admin")
        assert result is None


class TestSuspendActivate:
    async def test_suspend_no_repo_returns_false(self):
        engine = AdminEngine()
        assert await engine.suspend_user(uuid.uuid4()) is False

    async def test_activate_no_repo_returns_false(self):
        engine = AdminEngine()
        assert await engine.activate_user(uuid.uuid4()) is False

    async def test_suspend_delegates_to_repo(self):
        repo = AsyncMock()
        repo.set_status = AsyncMock(return_value=True)
        engine = AdminEngine(user_repo=repo)
        assert await engine.suspend_user(uuid.uuid4()) is True
        repo.set_status.assert_awaited_once()


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
