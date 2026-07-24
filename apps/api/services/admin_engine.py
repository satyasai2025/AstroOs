"""
AstroOS — Admin Engine (Module 23, Phase 1)

User management and system health aggregation for the admin portal.
"""

from __future__ import annotations

import uuid
from typing import Optional

from apps.api.config import get_settings
from apps.api.domain.admin import AdminUserSummary, ModuleHealth, SystemStatus
from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.repositories.user_repository import UserRepository
from apps.api.services.ephemeris_service import EphemerisService

_MODULE_REGISTRY: dict[str, str] = {
    "foundation": "1.0",
    "chart_engine": "1.0",
    "graha_module": "1.0",
    "nakshatra_module": "1.0",
    "dasha_module": "1.0",
    "divisional_charts": "1.0",
    "ashtakavarga": "1.0",
    "yoga_module": "1.0",
    "shadbala": "1.0",
    "transit": "1.0",
    "ontology": "1.0",
    "rule_engine": "1.0",
    "event_engine": "1.0",
    "timeline_engine": "1.0",
    "verification_engine": "1.0",
    "research_engine": "1.0",
    "statistics_engine": "1.0",
    "knowledge_engine": "1.0",
    "report_engine": "1.0",
    "export_engine": "1.0",
    "visualization_engine": "1.0",
    "admin_portal": "1.0",
}


def _user_to_summary(user: User) -> AdminUserSummary:
    return AdminUserSummary(
        id=user.id.value,
        email=user.email,
        display_name=user.display_name or user.email,
        role=user.role.value,
        status=user.status.value,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


class AdminEngine:
    """
    Admin operations for user management and system health.

    All User-aggregate DB access goes through UserRepository (see its
    "Admin listing/moderation" section) — this engine used to hold a raw
    AsyncSession and query UserModel directly, the one place in the
    codebase that bypassed the repository layer every other engine uses.
    Fixed as part of Phase 10's cleanup pass (2026-07-23); behavior is
    unchanged, this is purely a layering fix.
    """

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        ephemeris_service: Optional[EphemerisService] = None,
    ) -> None:
        self._user_repo = user_repo
        self._ephemeris_service = ephemeris_service

    # ── User management ───────────────────────────────────────────────────

    async def list_users(
        self,
        status: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[AdminUserSummary, ...]:
        if self._user_repo is None:
            return ()
        users = await self._user_repo.list_all(
            status=status, role=role, limit=limit, offset=offset,
        )
        return tuple(_user_to_summary(u) for u in users)

    async def count_users(
        self,
        status: Optional[str] = None,
        role: Optional[str] = None,
    ) -> int:
        """True count of users matching the filter, independent of
        limit/offset — used by callers that need pagination totals
        rather than the current page's size."""
        if self._user_repo is None:
            return 0
        return await self._user_repo.count_all(status=status, role=role)

    async def get_user(self, user_id: uuid.UUID) -> Optional[AdminUserSummary]:
        if self._user_repo is None:
            return None
        domain_user = await self._user_repo.get_by_id(UserId(user_id))
        if domain_user is None:
            return None
        return _user_to_summary(domain_user)

    async def update_user_role(
        self, user_id: uuid.UUID, new_role: str,
    ) -> Optional[AdminUserSummary]:
        if self._user_repo is None:
            return None
        try:
            role_enum = UserRole(new_role)
        except ValueError:
            return None
        updated = await self._user_repo.set_role(UserId(user_id), role_enum)
        return _user_to_summary(updated) if updated else None

    async def suspend_user(self, user_id: uuid.UUID) -> bool:
        if self._user_repo is None:
            return False
        return await self._user_repo.set_status(UserId(user_id), UserStatus.SUSPENDED)

    async def activate_user(self, user_id: uuid.UUID) -> bool:
        if self._user_repo is None:
            return False
        return await self._user_repo.set_status(UserId(user_id), UserStatus.ACTIVE)

    # ── System health ─────────────────────────────────────────────────────

    async def get_system_status(self) -> SystemStatus:
        modules: dict[str, ModuleHealth] = {}
        overall = "healthy"

        for name, ver in _MODULE_REGISTRY.items():
            modules[name] = ModuleHealth(
                module_name=name, status="ok", version=ver,
            )

        # Ephemeris health.
        ephe_mode = "unknown"
        if self._ephemeris_service:
            try:
                status_dto = self._ephemeris_service.get_status()
                ephe_mode = status_dto.mode.value if hasattr(status_dto.mode, "value") else str(status_dto.mode)
                if not status_dto.official_data:
                    modules["ephemeris"] = ModuleHealth(
                        module_name="ephemeris", status="warning",
                        version="1.0", message="Moshier fallback mode (no .se1 files)",
                    )
                    overall = "degraded"
            except Exception:
                modules["ephemeris"] = ModuleHealth(
                    module_name="ephemeris", status="error",
                    version="1.0", message="Ephemeris probe failed",
                )
                overall = "degraded"

        return SystemStatus(
            status=overall,
            modules=modules,
            ephemeris_mode=ephe_mode,
            version=get_settings().APP_VERSION,
        )

    @staticmethod
    def get_module_registry() -> dict[str, str]:
        return dict(_MODULE_REGISTRY)
