"""
AstroOS — Admin Router (Module 23 — HTTP surface)

HTTP adapter layer over AdminEngine. No business logic lives here — only
request parsing, DTO<->schema conversion, and HTTP error mapping, same
convention as routers/events.py.

Every route on this router IS gated: app.include_router() in main.py
wires `dependencies=[Depends(require_admin)]` at inclusion time (not
per-route here), which is easy to miss reading this file in isolation —
an earlier version of this docstring incorrectly said "no auth/role-
gating is applied here," which was never true and was corrected as part
of the Phase 10 retroactive review (2026-07-23) specifically because a
stale claim like that risks someone trusting it and removing the real
gate, or duplicating this router's inclusion elsewhere without the
`dependencies=` kwarg. If you're verifying this yourself: see
apps/api/main.py's `app.include_router(admin_router.router, ...)` call.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from apps.api.dependencies import get_ephemeris_service, get_user_repo
from apps.api.repositories.user_repository import UserRepository
from apps.api.schemas.admin import (
    AdminUserListResponse,
    AdminUserSummaryResponse,
    ModuleHealthResponse,
    ModuleRegistryResponse,
    SystemStatusResponse,
    UpdateUserRoleRequest,
)
from apps.api.services.admin_engine import AdminEngine
from apps.api.services.ephemeris_service import EphemerisService

router = APIRouter(prefix="/admin", tags=["Admin"])


async def _get_admin_engine(
    user_repo: UserRepository = Depends(get_user_repo),
    ephemeris_service: EphemerisService = Depends(get_ephemeris_service),
) -> AdminEngine:
    return AdminEngine(user_repo=user_repo, ephemeris_service=ephemeris_service)


def _summary_to_response(u) -> AdminUserSummaryResponse:
    return AdminUserSummaryResponse(
        id=u.id, email=u.email, display_name=u.display_name, role=u.role,
        status=u.status, created_at=u.created_at, last_login_at=u.last_login_at,
    )


# ── System health ─────────────────────────────────────────────────────────────


@router.get("/status", response_model=SystemStatusResponse, summary="Aggregated system health")
async def get_system_status(
    engine: AdminEngine = Depends(_get_admin_engine),
) -> SystemStatusResponse:
    status_dto = await engine.get_system_status()
    return SystemStatusResponse(
        status=status_dto.status,
        modules={
            name: ModuleHealthResponse(
                module_name=m.module_name, status=m.status, version=m.version, message=m.message
            )
            for name, m in status_dto.modules.items()
        },
        ephemeris_mode=status_dto.ephemeris_mode,
        version=status_dto.version,
    )


@router.get(
    "/module-registry", response_model=ModuleRegistryResponse, summary="Registered module list"
)
async def get_module_registry() -> ModuleRegistryResponse:
    return ModuleRegistryResponse(modules=AdminEngine.get_module_registry())


# ── User management ───────────────────────────────────────────────────────────


@router.get("/users", response_model=AdminUserListResponse, summary="List users")
async def list_users(
    status_filter: str | None = None,
    role: str | None = None,
    limit: int = 100,
    offset: int = 0,
    engine: AdminEngine = Depends(_get_admin_engine),
) -> AdminUserListResponse:
    users = await engine.list_users(status=status_filter, role=role, limit=limit, offset=offset)
    total = await engine.count_users(status=status_filter, role=role)
    return AdminUserListResponse(
        users=[_summary_to_response(u) for u in users], total=total
    )


@router.get("/users/{user_id}", response_model=AdminUserSummaryResponse, summary="Get a user")
async def get_user(
    user_id: uuid.UUID, engine: AdminEngine = Depends(_get_admin_engine)
) -> AdminUserSummaryResponse:
    user = await engine.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return _summary_to_response(user)


@router.patch(
    "/users/{user_id}/role", response_model=AdminUserSummaryResponse, summary="Change a user's role"
)
async def update_user_role(
    user_id: uuid.UUID,
    body: UpdateUserRoleRequest,
    engine: AdminEngine = Depends(_get_admin_engine),
) -> AdminUserSummaryResponse:
    user = await engine.update_user_role(user_id, body.role)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User not found or invalid role.",
        )
    return _summary_to_response(user)


@router.post("/users/{user_id}/suspend", status_code=status.HTTP_204_NO_CONTENT, summary="Suspend a user")
async def suspend_user(
    user_id: uuid.UUID, engine: AdminEngine = Depends(_get_admin_engine)
) -> None:
    suspended = await engine.suspend_user(user_id)
    if not suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")


@router.post("/users/{user_id}/activate", status_code=status.HTTP_204_NO_CONTENT, summary="Activate a user")
async def activate_user(
    user_id: uuid.UUID, engine: AdminEngine = Depends(_get_admin_engine)
) -> None:
    activated = await engine.activate_user(user_id)
    if not activated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")


# ── Phase 13 Billing & Ops Console ───────────────────────────────────────────

from apps.api.dependencies import get_db_session
from apps.api.models.notification import EmailLogModel
from apps.api.models.payment import PaymentModel, PaymentStatus
from apps.api.models.subscription import SubscriptionModel
from apps.api.schemas.payment import PaymentResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession


@router.get("/billing/payments", summary="Global payment transactions with GST tax audit")
async def admin_list_payments(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """List all global payment transactions with itemized base amount and GST tax fields."""
    stmt = select(PaymentModel).order_by(desc(PaymentModel.created_at)).limit(limit).offset(offset)
    res = await db.execute(stmt)
    payments = list(res.scalars().all())

    count_res = await db.execute(select(func.count(PaymentModel.id)))
    total = count_res.scalar_one() or 0

    return {
        "items": [PaymentResponse.model_validate(p) for p in payments],
        "total": total,
    }


@router.get("/billing/subscriptions", summary="Global subscription lifecycle overview")
async def admin_list_subscriptions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """List all user subscriptions with active status, plan code, and grace periods."""
    stmt = select(SubscriptionModel).order_by(desc(SubscriptionModel.created_at)).limit(limit).offset(offset)
    res = await db.execute(stmt)
    subs = list(res.scalars().all())

    count_res = await db.execute(select(func.count(SubscriptionModel.id)))
    total = count_res.scalar_one() or 0

    return {
        "items": [
            {
                "id": str(s.id),
                "user_id": str(s.user_id),
                "plan_id": str(s.plan_id),
                "status": s.status,
                "billing_cycle": s.billing_cycle,
                "current_period_start": s.current_period_start.isoformat() if s.current_period_start else None,
                "current_period_end": s.current_period_end.isoformat() if s.current_period_end else None,
                "created_at": s.created_at.isoformat(),
            }
            for s in subs
        ],
        "total": total,
    }


@router.post("/billing/refunds/{payment_id}", summary="Process an admin refund")
async def admin_refund_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Issue an administrative refund on a transaction."""
    stmt = select(PaymentModel).where(PaymentModel.id == payment_id)
    res = await db.execute(stmt)
    payment = res.scalar_one_or_none()
    if not payment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Payment record not found.")

    payment.status = PaymentStatus.REFUNDED.value
    await db.commit()
    await db.refresh(payment)
    return PaymentResponse.model_validate(payment)
