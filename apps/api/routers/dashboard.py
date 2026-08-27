"""
AstroOS — Account & User Dashboard Router (Phase 9)

Endpoints:
  - GET /api/v1/dashboard/summary — Unified aggregated user overview
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import User
from apps.api.models.astrology import BirthChartModel
from apps.api.models.subscription import SubscriptionStatus
from apps.api.repositories.payment_repository import PaymentRepository
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.repositories.subscription_repository import SubscriptionRepository
from apps.api.schemas.dashboard import DashboardSummaryResponse
from apps.api.schemas.payment import PaymentResponse
from apps.api.services.entitlement_service import EntitlementService

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> DashboardSummaryResponse:
    """Return unified dashboard metrics: profile, quotas, subscription, and payments."""
    user_id_val = user.id.value if hasattr(user.id, "value") else user.id
    user_uuid = UUID(str(user_id_val))

    # 1. Plan & Limits via Entitlement Service
    ent_svc = EntitlementService(db)
    plan = await ent_svc.resolve_user_plan(user)
    limits = plan.limits if plan else {}
    features = plan.features if plan else {}

    # 2. Subscription
    sub = await SubscriptionRepository.get_by_user(db, user_uuid)
    is_grace = sub.status == SubscriptionStatus.PAST_DUE_CANCELLED.value if sub else False

    # 3. Saved Horoscopes Count
    chart_count_res = await db.execute(
        select(func.count(BirthChartModel.id)).where(BirthChartModel.user_id == user_uuid)
    )
    saved_charts_count = chart_count_res.scalar_one() or 0

    # 4. Recent Payments
    payments = await PaymentRepository.list_by_user(db, user_uuid, limit=5)
    payments_count = await PaymentRepository.count_by_user(db, user_uuid)

    return DashboardSummaryResponse(
        user_id=user_uuid,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        status=user.status.value if hasattr(user.status, "value") else str(user.status),
        plan_code=plan.plan_code if plan else "FREE",
        plan_name=plan.name if plan else "Free Community",
        subscription_status=sub.status if sub else None,
        period_start=sub.current_period_start if sub else None,
        period_end=sub.current_period_end if sub else None,
        is_in_grace_period=is_grace,
        saved_horoscopes_count=saved_charts_count,
        saved_horoscopes_limit=limits.get("saved_horoscopes", 5),
        research_runs_used=0,
        research_runs_limit=limits.get("research_projects_monthly", 0),
        max_storage_mb=limits.get("max_storage_mb", 50),
        recent_payments=[PaymentResponse.model_validate(p) for p in payments],
        total_payments_count=payments_count,
    )
