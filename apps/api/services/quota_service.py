"""
AstroOS — Quota Enforcement Service (Phase 4)

Enforces monthly usage quotas for plan-limited features.
Works with EntitlementService to block creation when quota exceeded.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.user import User
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.repositories.usage_repository import UsageRepository
from apps.api.services.entitlement_service import EntitlementService
from apps.api.services.feature_catalog import PLAN_LIMITS


@dataclass(frozen=True)
class QuotaStatus:
    """Result of a quota check."""
    allowed: bool
    current_usage: int
    limit: int | None  # None = unlimited
    period: str        # YYYY-MM format
    exhausted: bool    # True if quota fully used
    reset_in: int | None  # seconds until reset (None for unlimited)


class QuotaService:
    """
    Service for checking and enforcing monthly usage quotas.
    
    Features tracked:
    - saved_horoscopes (viewed via EntitlementService.can_create)
    - research_projects (viewed via EntitlementService.can_create)
    
    Integration:
    - Called from EntitlementService.creation_blocked_by_zero_limit() for hard 0 limits
    - Called from route dependencies to enforce quotas before creation
    """
    
    # Map feature keys to their quota limit fields in PlanLimitModel
    _QUOTA_FEATURES = {
        "saved_horoscopes": "saved_horoscopes",
        "research_projects": "research_projects_monthly",
    }

    def __init__(self, db: AsyncSession):
        self._db = db
        self._entitlement = EntitlementService(db)
        self._usage_repo = UsageRepository()
        self._plan_repo = PlanRepository()

    async def check_quota(
        self,
        user: User,
        feature_key: str,
        amount: int = 1,
    ) -> QuotaStatus:
        """
        Check if user has quota available for feature.
        
        Returns QuotaStatus indicating if the usage is allowed.
        Does NOT increment usage - caller must call consume_quota() if allowed.
        """
        # Validate feature is quota-tracked
        limit_field = self._QUOTA_FEATURES.get(feature_key)
        if limit_field is None:
            # Feature not quota-tracked - allow by default
            return QuotaStatus(
                allowed=True,
                current_usage=0,
                limit=None,
                period=datetime.now(timezone.utc).strftime("%Y-%m"),
                exhausted=False,
                reset_in=None,
            )
        
        # Get user's current plan
        plan = await self._entitlement.resolve_user_plan(user)
        plan_code = plan.plan_code
        
        # Get plan limits
        limits = await self._entitlement.get_plan_limits(user)
        limit = getattr(limits, limit_field)
        
        # If limit is None (unlimited/configurable), allow
        if limit is None:
            return QuotaStatus(
                allowed=True,
                current_usage=await self._usage_repo.get_usage(user.id, feature_key),
                limit=None,
                period=datetime.now(timezone.utc).strftime("%Y-%m"),
                exhausted=False,
                reset_in=None,
            )
        
        # Get current usage for this month
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        current_usage = await self._usage_repo.get_usage(user.id, feature_key, period)
        
        # Check if quota exhausted
        allowed = (current_usage + amount) <= limit
        exhausted = current_usage >= limit
        
        # Calculate seconds until month-end reset (approximate)
        reset_in = None
        if limit is not None:
            now = datetime.now(timezone.utc)
            # Next month first day
            if now.month == 12:
                next_month = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                next_month = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
            reset_in = int((next_month - now).total_seconds())
        
        return QuotaStatus(
            allowed=allowed,
            current_usage=current_usage,
            limit=limit,
            period=period,
            exhausted=exhausted,
            reset_in=reset_in,
        )

    async def consume_quota(
        self,
        user: User,
        feature_key: str,
        amount: int = 1,
    ) -> bool:
        """
        Consume quota for a feature if available.
        
        Returns True if quota was consumed, False if insufficient quota.
        Does NOT check entitlement - caller must verify entitlement first.
        """
        quota_status = await self.check_quota(user, feature_key, amount)
        if not quota_status.allowed:
            return False
        
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        await self._usage_repo.increment(
            self._db,
            user.id,
            feature_key,
            period,
            amount,
        )
        return True

    async def reset_monthly_quota(
        self,
        user: User,
        feature_key: str | None = None,
    ) -> None:
        """
        Reset quota for a user (typically called by monthly cron job).
        If feature_key is None, resets all quota-tracked features.
        """
        if feature_key is None:
            # Reset all quota-tracked features
            for feat_key in self._QUOTA_FEATURES.keys():
                await self._usage_repo.reset_period(self._db, user.id, feat_key)
        else:
            await self._usage_repo.reset_period(self._db, user.id, feature_key)