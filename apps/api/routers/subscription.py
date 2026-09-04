"""
AstroOS — Subscription API Router (Phase 5)

User-visible endpoints (any authenticated user):
  GET  /api/v1/subscriptions/me           — current user's subscription
  GET  /api/v1/subscriptions/me/history   — its append-only event log

Admin-only operational endpoints (admin token required):
  POST /api/v1/admin/subscriptions                       — provision manually
  GET  /api/v1/admin/subscriptions/{id}/history          — inspect history
  POST /api/v1/admin/subscriptions/{id}/transition       — manual lifecycle op

Phase 5 explicitly does NOT include: checkout/payment gateways, webhooks,
billing cycles/renewal jobs, emails, UI.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    require_admin,
)
from apps.api.domain.user import User
from apps.api.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionHistoryResponse,
    SubscriptionResponse,
    SubscriptionTransition,
    TransitionResult,
)
from apps.api.services.subscription_service import (
    InvalidTransitionError,
    SubscriptionService,
)

router = APIRouter(prefix="/api/v1", tags=["Subscriptions"])


def _svc(db: AsyncSession) -> SubscriptionService:
    return SubscriptionService(db)


# ── Authenticated user ───────────────────────────────────────────────────────


@router.get("/subscriptions/me", response_model=SubscriptionResponse)
async def my_subscription(
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Current user's subscription row (404 when none exists yet)."""
    sub = await _svc(db).get_for_user(user)
    if sub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No subscription found.")
    return sub


@router.get("/subscriptions/me/history", response_model=SubscriptionHistoryResponse)
async def my_subscription_history(
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Full ordered event history of the current user's subscription."""
    svc = _svc(db)
    sub = await svc.get_for_user(user)
    if sub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No subscription found.")
    events = await svc.get_history(sub.id)
    return SubscriptionHistoryResponse(subscription_id=sub.id, events=events)


# ── Admin ────────────────────────────────────────────────────────────────────


@router.post("/admin/subscriptions", response_model=SubscriptionResponse)
async def admin_create_subscription(
    payload: SubscriptionCreate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Provision a subscription row without a payment gateway (Phase 5 stopgap)."""
    svc = _svc(db)
    class _Ref:  # tiny adapter: admin supplies the user_id directly
        id = type("Uid", (), {"value": payload.user_id})()
    try:
        sub = await svc.create(
            _Ref(),
            payload.plan_code,
            current_period_end=payload.current_period_end,
            trial_end=payload.trial_end,
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    return sub


@router.post("/admin/subscriptions/{subscription_id}/transition",
             response_model=TransitionResult)
async def admin_transition_subscription(
    subscription_id: UUID,
    payload: SubscriptionTransition,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Apply one manual lifecycle transition (operational tooling only)."""
    try:
        result = await _svc(db).transition(
            subscription_id, payload.target_status, reason=payload.reason
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    return result


@router.get("/admin/subscriptions/{subscription_id}/history",
            response_model=SubscriptionHistoryResponse)
async def admin_subscription_history(
    subscription_id: UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Inspect the full event history of any subscription."""
    svc = _svc(db)
    sub = await svc.get_by_id(subscription_id)
    if sub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subscription not found.")
    events = await svc.get_history(subscription_id)
    return SubscriptionHistoryResponse(subscription_id=sub.id, events=events)
