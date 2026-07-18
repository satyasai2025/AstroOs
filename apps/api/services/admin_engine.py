"""
AstroOS — Admin Engine (Module 23, Phase 1)

User management and system health aggregation for the admin portal.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select, update

from apps.api.config import get_settings
from apps.api.domain.admin import AdminUserSummary, ModuleHealth, SystemStatus
from apps.api.domain.user import UserId, UserRole, UserStatus
from apps.api.models.user import UserModel
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


def _user_to_summary(model: UserModel) -> AdminUserSummary:
    return AdminUserSummary(
        id=model.id,
        email=model.email,
        display_name=model.display_name or model.email,
        role=model.role.value if hasattr(model.role, "value") else str(model.role),
        status=model.status.value if hasattr(model.status, "value") else str(model.status),
        created_at=model.created_at,
        last_login_at=model.last_login_at,
    )


class AdminEngine:
    """Admin operations for user management and system health."""

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        session: Any = None,
        ephemeris_service: Optional[EphemerisService] = None,
    ) -> None:
        self._user_repo = user_repo
        self._session = session
        self._ephemeris_service = ephemeris_service

    # ── User management ───────────────────────────────────────────────────

    @staticmethod
    def _filtered_users_stmt(status: Optional[str], role: Optional[str]):
        """Shared status/role filter, reused by list_users and count_users
        so pagination's total always reflects the exact same WHERE clause
        as the page it's counting."""
        stmt = select(UserModel).where(UserModel.deleted_at.is_(None))
        if status:
            stmt = stmt.where(UserModel.status == status)
        if role:
            stmt = stmt.where(UserModel.role == role)
        return stmt

    async def list_users(
        self,
        status: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[AdminUserSummary, ...]:
        if self._session is None:
            return ()
        stmt = self._filtered_users_stmt(status, role)
        stmt = stmt.order_by(UserModel.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return tuple(_user_to_summary(r) for r in rows)

    async def count_users(
        self,
        status: Optional[str] = None,
        role: Optional[str] = None,
    ) -> int:
        """True count of users matching the filter, independent of
        limit/offset — used by callers that need pagination totals
        rather than the current page's size."""
        if self._session is None:
            return 0
        stmt = self._filtered_users_stmt(status, role)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self._session.execute(count_stmt)
        return result.scalar_one()

    async def get_user(self, user_id: uuid.UUID) -> Optional[AdminUserSummary]:
        if self._user_repo is None:
            return None
        domain_user = await self._user_repo.get_by_id(UserId(user_id))
        if domain_user is None:
            return None
        return AdminUserSummary(
            id=domain_user.id.value,
            email=domain_user.email,
            display_name=domain_user.display_name,
            role=domain_user.role.value,
            status=domain_user.status.value,
            created_at=domain_user.created_at,
            last_login_at=domain_user.last_login_at,
        )

    async def update_user_role(
        self, user_id: uuid.UUID, new_role: str,
    ) -> Optional[AdminUserSummary]:
        if self._session is None:
            return None
        try:
            role_enum = UserRole(new_role)
        except ValueError:
            return None
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
            .values(role=role_enum)
            .returning(UserModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_user(user_id)

    async def suspend_user(self, user_id: uuid.UUID) -> bool:
        if self._session is None:
            return False
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
            .values(status=UserStatus.SUSPENDED)
            .returning(UserModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def activate_user(self, user_id: uuid.UUID) -> bool:
        if self._session is None:
            return False
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
            .values(status=UserStatus.ACTIVE)
            .returning(UserModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

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
