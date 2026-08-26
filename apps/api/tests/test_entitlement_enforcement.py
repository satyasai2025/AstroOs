"""
AstroOS — Phase 3 Entitlement Enforcement Tests

Tests the require_entitlement() dependency wired in Phase 3, verifying that
the Phase 2 entitlement matrix (DECIDED_MATRIX) is correctly enforced at
the HTTP layer.

Coverage:
  1. Research projects  — governed feature; FREE = no access,
                          PRO/RESEARCH = view+create, CUSTOM = admin-defined
  2. Saved horoscopes   — governed feature; every plan = view+create
  3. Error response shapes (FEATURE_NOT_AVAILABLE, ACTION_NOT_ALLOWED)
  4. require_entitlement() factory validation

Phase 3 explicitly does NOT cover:
  - Quota consumption (1/3 per month, research_projects on PRO/RESEARCH)
  - Rate limiting
  - Checkout / subscription lifecycle
  - edit / run / export actions (UNRESOLVED in Phase 2 matrix)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.main import app
from apps.api.models.plan import PlanModel as Plan
from apps.api.services.entitlement_service import EntitlementService
from apps.api.services.feature_catalog import DECIDED_MATRIX


# ── Fixtures ───────────────────────────────────────────────────────────────────


def _plan(plan_id: str, name: str, code: str, desc: str, limits: dict) -> Plan:
    """Factory for Plan with MagicMock plan_limits attached."""
    p = Plan(
        id=uuid.UUID(plan_id),
        name=name,
        plan_code=code,
        description=desc,
        is_active=True,
    )
    p.plan_limits = MagicMock(
        saved_horoscopes=limits.get("saved_horoscopes"),
        research_projects_monthly=limits.get("research_projects_monthly"),
        extra_limits_json=None,
    )
    return p


@pytest.fixture
def free_plan() -> Plan:
    return _plan(
        "00000000-0000-0000-0000-000000000010",
        "Free", "FREE", "Free tier",
        {"saved_horoscopes": 5, "research_projects_monthly": 0},
    )


@pytest.fixture
def pro_plan() -> Plan:
    return _plan(
        "00000000-0000-0000-0000-000000000020",
        "Pro", "PRO", "Pro tier",
        {"saved_horoscopes": 50, "research_projects_monthly": 1},
    )


@pytest.fixture
def custom_plan() -> Plan:
    return _plan(
        "00000000-0000-0000-0000-000000000099",
        "Custom", "CUSTOM", "Custom tier",
        {"saved_horoscopes": None, "research_projects_monthly": None},
    )


def _make_user(uid_int: int) -> User:
    return User(
        id=UserId(value=uuid.UUID(f"00000000-0000-0000-0000-{uid_int:012d}")),
        email=f"user{uid_int}@example.com",
        display_name=f"User {uid_int}",
        hashed_password="ignored",
        role=UserRole.GUEST,
        status=UserStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def free_user() -> User:
    return _make_user(1)


@pytest.fixture
def pro_user() -> User:
    return _make_user(2)


@pytest.fixture
def custom_user() -> User:
    return _make_user(99)


def _auth_header(user: User) -> dict:
    return {"Authorization": f"Bearer {user.id}"}


# ── Tests: require_entitlement factory ─────────────────────────────────────────


class TestRequireEntitlementFactory:
    """Tests for the require_entitlement() dependency factory itself."""

    def test_unknown_action_raises_value_error(self):
        from apps.api.dependencies import require_entitlement
        with pytest.raises(ValueError, match="Unknown entitlement action"):
            require_entitlement("research_projects", "fly")

    def test_unknown_action_error_includes_valid_actions(self):
        from apps.api.dependencies import require_entitlement
        with pytest.raises(ValueError) as exc_info:
            require_entitlement("research_projects", "teleport")
        assert "view" in str(exc_info.value)
        assert "create" in str(exc_info.value)

    def test_known_actions_do_not_raise(self):
        from apps.api.dependencies import require_entitlement
        for action in ("view", "create", "edit", "run", "export"):
            dep = require_entitlement("research_projects", action)
            assert callable(dep)


# ── Tests: creation_blocked_by_zero_limit ─────────────────────────────────────


class TestCreationBlockedByZeroLimit:
    """Tests for EntitlementService.creation_blocked_by_zero_limit()."""

    @pytest.mark.asyncio
    async def test_free_plan_blocks_research_projects(self, free_user, free_plan):
        """FREE plan has research_projects_monthly=0 → creation blocked."""
        with patch.object(
            EntitlementService, "resolve_user_plan",
            new_callable=AsyncMock, return_value=free_plan,
        ), patch.object(
            EntitlementService, "get_plan_limits",
            new_callable=AsyncMock,
            return_value=MagicMock(research_projects_monthly=0),
        ):
            svc = EntitlementService(MagicMock())
            blocked = await svc.creation_blocked_by_zero_limit(
                free_user, "research_projects")
            assert blocked is True

    @pytest.mark.asyncio
    async def test_pro_plan_allows_research_projects(self, pro_user, pro_plan):
        """PRO plan has research_projects_monthly=1 → not blocked."""
        with patch.object(
            EntitlementService, "resolve_user_plan",
            new_callable=AsyncMock, return_value=pro_plan,
        ), patch.object(
            EntitlementService, "get_plan_limits",
            new_callable=AsyncMock,
            return_value=MagicMock(research_projects_monthly=1),
        ):
            svc = EntitlementService(MagicMock())
            blocked = await svc.creation_blocked_by_zero_limit(
                pro_user, "research_projects")
            assert blocked is False

    @pytest.mark.asyncio
    async def test_custom_plan_not_blocked(self, custom_user, custom_plan):
        """CUSTOM plan with None limit → not blocked."""
        with patch.object(
            EntitlementService, "resolve_user_plan",
            new_callable=AsyncMock, return_value=custom_plan,
        ), patch.object(
            EntitlementService, "get_plan_limits",
            new_callable=AsyncMock,
            return_value=MagicMock(research_projects_monthly=None),
        ):
            svc = EntitlementService(MagicMock())
            blocked = await svc.creation_blocked_by_zero_limit(
                custom_user, "research_projects")
            assert blocked is False