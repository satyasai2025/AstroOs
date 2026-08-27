"""
AstroOS — Subscription Repository

Data access for the ``subscriptions`` and ``subscription_events`` tables.
Static-method style, mirroring PlanRepository (Phase 2 convention).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.models.subscription import (
    ACTIVE_STATUSES,
    SubscriptionEventModel,
    SubscriptionEventType,
    SubscriptionModel,
    SubscriptionStatus,
)


class SubscriptionRepository:
    """CRUD + history access for Subscription aggregates."""

    # ── Queries ───────────────────────────────────────────────────────────────

    @staticmethod
    async def get_by_id(db: AsyncSession, subscription_id: UUID) -> Optional[SubscriptionModel]:
        result = await db.execute(
            select(SubscriptionModel).where(SubscriptionModel.id == subscription_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: UUID) -> Optional[SubscriptionModel]:
        result = await db.execute(
            select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_by_user(
        db: AsyncSession, user_id: UUID,
    ) -> Optional[SubscriptionModel]:
        result = await db.execute(
            select(SubscriptionModel)
            .where(
                SubscriptionModel.user_id == user_id,
                SubscriptionModel.status.in_([s.value for s in ACTIVE_STATUSES]),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_status(
        db: AsyncSession, status_value: str,
    ) -> list[SubscriptionModel]:
        result = await db.execute(
            select(SubscriptionModel).where(SubscriptionModel.status == status_value)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_expiring_before(
        db: AsyncSession,
        cutoff: datetime,
        statuses: tuple[str, ...] = (
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
            SubscriptionStatus.PAST_DUE_CANCELLED.value,
        ),
    ) -> list[SubscriptionModel]:
        """Non-terminal subscriptions whose period already ended before ``cutoff``."""
        result = await db.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.current_period_end.is_not(None),
                SubscriptionModel.current_period_end < cutoff,
                SubscriptionModel.status.in_(list(statuses)),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_for_user(
        db: AsyncSession, user_id: UUID,
    ) -> Optional[SubscriptionModel]:
        """
        Most recently created subscription for a user.

        ``ux_subscriptions_user_id`` means there is at most one row today, but
        EntitlementService asks for "the latest" so that a future phase can
        relax the unique index (re-subscribe creates a new row) without
        changing its caller.
        """
        result = await db.execute(
            select(SubscriptionModel)
            .where(SubscriptionModel.user_id == user_id)
            .order_by(SubscriptionModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def is_lapsed(sub: Optional[SubscriptionModel]) -> bool:
        """
        True when ``sub`` no longer grants paid-plan entitlements.

        Folds the stored status through the grace window, so a row still
        stamped ``active`` whose period ended long ago counts as lapsed
        without needing a cron job. Deferred import keeps
        repository → service out of the import cycle (the service imports
        this repository at module scope).
        """
        if sub is None:
            return False
        from apps.api.services.subscription_service import SubscriptionService

        effective = SubscriptionService.effective_status(sub)
        return effective == SubscriptionStatus.EXPIRED.value

    @staticmethod
    async def get_history(
        db: AsyncSession, subscription_id: UUID,
    ) -> list[SubscriptionEventModel]:
        result = await db.execute(
            select(SubscriptionEventModel)
            .where(SubscriptionEventModel.subscription_id == subscription_id)
            .order_by(SubscriptionEventModel.created_at.asc())
        )
        return list(result.scalars().all())

    # ── Writes ────────────────────────────────────────────────────────────────

    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        *,
        user_id: UUID,
        plan_id: UUID,
        status_value: str = SubscriptionStatus.ACTIVE.value,
        current_period_start: datetime | None = None,
        current_period_end: datetime | None = None,
        trial_end: datetime | None = None,
        created_event: bool = True,
    ) -> SubscriptionModel:
        now = datetime.now(timezone.utc)
        sub = SubscriptionModel(
            user_id=user_id,
            plan_id=plan_id,
            status=status_value,
            current_period_start=current_period_start or now,
            current_period_end=current_period_end,
            trial_end=trial_end,
        )
        db.add(sub)
        await db.flush()
        if created_event:
            await SubscriptionRepository.append_event(
                db, subscription=sub, event_type=SubscriptionEventType.CREATED,
                to_status=status_value, commit=False,
            )
            if trial_end is not None and status_value == SubscriptionStatus.TRIALING.value:
                await SubscriptionRepository.append_event(
                    db, subscription=sub,
                    event_type=SubscriptionEventType.TRIAL_STARTED,
                    to_status=status_value, commit=False,
                )
        await db.commit()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def update_fields(sub: SubscriptionModel, **fields) -> SubscriptionModel:
        """Apply field updates to a loaded instance (caller commits or we do below)."""
        for key, value in fields.items():
            setattr(sub, key, value)
        return sub

    @staticmethod
    async def save(db: AsyncSession, sub: SubscriptionModel) -> SubscriptionModel:
        """Commit changes to a tracked instance."""
        await db.commit()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def append_event(
        db: AsyncSession,
        *,
        subscription: SubscriptionModel,
        event_type: SubscriptionEventType,
        to_status: str | None = None,
        from_status: str | None = None,
        payload_json: str | None = None,
        commit: bool = True,
    ) -> SubscriptionEventModel:
        event = SubscriptionEventModel(
            subscription=subscription,
            event_type=event_type.value,
            from_status=from_status,
            to_status=to_status,
            payload_json=payload_json,
        )
        db.add(event)
        await db.flush()
        if commit:
            await db.commit()
        return event
