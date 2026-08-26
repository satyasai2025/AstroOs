"""
AstroOS — Usage Tracking Repository (Phase 4)

CRUD operations for usage records with automatic monthly reset support.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.usage import UsageRecordModel


class UsageRepository:
    """Repository for usage tracking data access."""

    @staticmethod
    async def get_by_user_feature_period(
        db: AsyncSession,
        user_id: UUID,
        feature_key: str,
        period: str,
    ) -> UsageRecordModel | None:
        """Get usage record for a user-feature-period combination."""
        result = await db.execute(
            select(UsageRecordModel).where(
                UsageRecordModel.user_id == user_id,
                UsageRecordModel.feature_key == feature_key,
                UsageRecordModel.period == period,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_reset(
        db: AsyncSession,
        user_id: UUID,
        feature_key: str,
        period: str,
        reset_if_full: bool = False,
    ) -> UsageRecordModel:
        """Create or get existing usage record, optionally resetting if at limit."""
        record = await UsageRepository.get_by_user_feature_period(
            db, user_id, feature_key, period
        )
        
        if record is None:
            record = UsageRecordModel(
                user_id=user_id,
                feature_key=feature_key,
                period=period,
                count=0,
            )
            db.add(record)
        elif reset_if_full and record.count >= 0:
            # Reset monthly quota when period changes
            record.count = 0
            record.last_incremented_at = datetime.now(timezone.utc)
        
        await db.flush()
        await db.refresh(record)
        return record

    @staticmethod
    async def increment(
        db: AsyncSession,
        user_id: UUID,
        feature_key: str,
        period: str,
        amount: int = 1,
    ) -> UsageRecordModel:
        """Increment usage count by amount (default 1)."""
        record = await UsageRepository.get_by_user_feature_period(
            db, user_id, feature_key, period
        )
        
        if record is None:
            record = UsageRecordModel(
                user_id=user_id,
                feature_key=feature_key,
                period=period,
                count=amount,
            )
            db.add(record)
        else:
            record.count += amount
            record.last_incremented_at = datetime.now(timezone.utc)
        
        await db.flush()
        await db.refresh(record)
        return record

    @staticmethod
    async def reset_period(db: AsyncSession, user_id: UUID, feature_key: str) -> None:
        """Reset usage count for a user-feature combination (monthly rollover)."""
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        record = await UsageRepository.get_by_user_feature_period(
            db, user_id, feature_key, period
        )
        if record:
            record.count = 0
            record.last_incremented_at = datetime.now(timezone.utc)
        await db.flush()

    @staticmethod
    async def get_usage(
        db: AsyncSession,
        user_id: UUID,
        feature_key: str,
        period: str | None = None,
    ) -> int:
        """Get current usage count for a user-feature combination."""
        if period is None:
            period = datetime.now(timezone.utc).strftime("%Y-%m")
        record = await UsageRepository.get_by_user_feature_period(
            db, user_id, feature_key, period
        )
        return record.count if record else 0