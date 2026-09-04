
"""
AstroOS — Plan Repository
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.models.plan import PlanModel, FeatureModel, PlanFeatureModel, PlanLimitModel, UserPlanModel


class PlanRepository:
    """Repository for plan, feature, plan_feature, plan_limit, user_plan operations."""
    # ── Plan CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    async def get_by_id(db: AsyncSession, plan_id: UUID) -> PlanModel | None:
        result = await db.execute(select(PlanModel).where(PlanModel.id == plan_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> PlanModel | None:
        result = await db.execute(
            select(PlanModel).where(PlanModel.plan_code == code.upper())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession, include_inactive: bool = False) -> list[PlanModel]:
        stmt = select(PlanModel).order_by(PlanModel.created_at)
        if not include_inactive:
            stmt = stmt.where(PlanModel.is_active.is_(True))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_limit(db: AsyncSession, plan_id: UUID) -> PlanLimitModel | None:
        result = await db.execute(
            select(PlanLimitModel).where(PlanLimitModel.plan_id == plan_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_limits(db: AsyncSession, plan_id: UUID) -> PlanLimitModel:
        """Return the plan's limit row, creating an empty one if absent."""
        existing = await PlanRepository.get_limit(db, plan_id)
        if existing is not None:
            return existing
        limits = PlanLimitModel(
            plan_id=plan_id,
            saved_horoscopes=None,
            research_projects_monthly=None,
        )
        db.add(limits)
        await db.flush()
        await db.refresh(limits)
        return limits

    @staticmethod
    async def create_plan(
        db: AsyncSession, plan_code: str, name: str,
        description: str = "", is_active: bool = True,
    ) -> PlanModel:
        plan = PlanModel(
            plan_code=plan_code.upper(), name=name,
            description=description, is_active=is_active,
        )
        db.add(plan)
        await db.flush()
    # ── User plan assignment ─────────────────────────────────────────────────

    @staticmethod
    async def get_user_plan(db: AsyncSession, user_id: UUID) -> UserPlanModel | None:
        result = await db.execute(
            select(UserPlanModel).where(UserPlanModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def assign_user_to_plan(
        db: AsyncSession, user_id: UUID, plan_id: UUID,
        expires_at: datetime | None = None, auto_renew: bool = False,
    ) -> UserPlanModel:
        """Create or update the user's plan assignment (idempotent upsert)."""
        existing = await PlanRepository.get_user_plan(db, user_id)
        if existing is not None:
            existing.plan_id = plan_id
            existing.expires_at = expires_at
            existing.auto_renew = auto_renew
        else:
            existing = UserPlanModel(
                user_id=user_id,
                plan_id=plan_id,
                started_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                auto_renew=auto_renew,
            )
            db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing

    # ── Feature catalog ──────────────────────────────────────────────────────

    @staticmethod
    async def get_feature_by_key(db: AsyncSession, key: str) -> FeatureModel | None:
        result = await db.execute(
            select(FeatureModel).where(FeatureModel.feature_key == key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_feature_by_id(db: AsyncSession, feature_id: UUID) -> FeatureModel | None:
        result = await db.execute(
            select(FeatureModel).where(FeatureModel.id == feature_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_features(db: AsyncSession) -> list[FeatureModel]:
        result = await db.execute(
            select(FeatureModel).order_by(FeatureModel.category, FeatureModel.feature_key)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_feature(
        db: AsyncSession, feature_key: str, name: str,
        description: str = "", category: str = "core", is_system: bool = False,
    ):
        feature = FeatureModel(
            feature_key=feature_key.lower(),
            name=name,
            description=description,
            category=category,
            is_system=is_system,
        )
        db.add(feature)
        await db.commit()
        await db.refresh(feature)
        return feature

    # ── Entitlements ─────────────────────────────────────────────────────────

    @staticmethod
    async def get_entitlement(
        db: AsyncSession, plan_id: UUID, feature_id: UUID,
    ) -> PlanFeatureModel | None:
        result = await db.execute(
            select(PlanFeatureModel).where(
                PlanFeatureModel.plan_id == plan_id,
                PlanFeatureModel.feature_id == feature_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_entitlements_for_plan(
        db: AsyncSession, plan_id: UUID,
    ) -> list[PlanFeatureModel]:
        """All entitlement rows for a plan, with feature eagerly loaded."""
        result = await db.execute(
            select(PlanFeatureModel)
            .where(PlanFeatureModel.plan_id == plan_id)
            .options(selectinload(PlanFeatureModel.feature))
        )
        return list(result.scalars().all())

    @staticmethod
    async def set_entitlement(
        db: AsyncSession, plan_id: UUID, feature_id: UUID,
        can_view: bool = False, can_create: bool = False,
        can_edit: bool = False, can_run: bool = False,
        can_export: bool = False,
        view_limit: int | None = None, create_limit: int | None = None,
        edit_limit: int | None = None, run_limit: int | None = None,
    ) -> PlanFeatureModel:
        """Create or update one entitlement row (upsert)."""
        existing = await PlanRepository.get_entitlement(db, plan_id, feature_id)
        if existing is not None:
            existing.can_view = can_view
            existing.can_create = can_create
            existing.can_edit = can_edit
            existing.can_run = can_run
            existing.can_export = can_export
            existing.view_limit = view_limit
            existing.create_limit = create_limit
            existing.edit_limit = edit_limit
            existing.run_limit = run_limit
        else:
            existing = PlanFeatureModel(
                plan_id=plan_id, feature_id=feature_id,
                can_view=can_view, can_create=can_create,
                can_edit=can_edit, can_run=can_run, can_export=can_export,
                view_limit=view_limit, create_limit=create_limit,
                edit_limit=edit_limit, run_limit=run_limit,
            )
            db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing