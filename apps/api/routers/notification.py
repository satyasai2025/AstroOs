"""
AstroOS — Notification & Email API Router (Phase 7)

Endpoints:
  - GET /api/v1/notifications/preferences — Get current user's preferences
  - PUT /api/v1/notifications/preferences — Update user preferences (quota, product updates)
  - GET /api/v1/notifications/history     — View user's email notification history
  - GET /api/v1/admin/notifications/logs  — Admin audit log of all system emails
  - POST /api/v1/admin/notifications/test — Admin test email trigger
"""

from __future__ import annotations

import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    require_admin,
)
from apps.api.domain.user import User
from apps.api.repositories.notification_repository import NotificationRepository
from apps.api.schemas.notification import (
    EmailHistoryResponse,
    EmailLogResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    TestEmailRequest,
    TestEmailResponse,
)
from apps.api.services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1", tags=["Notifications"])


def _svc(db: AsyncSession) -> NotificationService:
    return NotificationService(db)


# ── User Preferences & History ───────────────────────────────────────────────


@router.get("/notifications/preferences", response_model=NotificationPreferenceResponse)
async def get_my_preferences(
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve the authenticated user's notification preferences."""
    user_id_val = user.id.value if hasattr(user.id, "value") else user.id
    pref = await NotificationRepository.get_or_create_preferences(db, UUID(str(user_id_val)))
    return pref


@router.put("/notifications/preferences", response_model=NotificationPreferenceResponse)
async def update_my_preferences(
    body: NotificationPreferenceUpdate,
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Update notification preferences for configurable categories."""
    user_id_val = user.id.value if hasattr(user.id, "value") else user.id
    pref = await NotificationRepository.get_or_create_preferences(db, UUID(str(user_id_val)))
    updated = await NotificationRepository.update_preferences(
        db,
        pref,
        quota_warnings=body.quota_warnings,
        product_updates=body.product_updates,
    )
    return updated


@router.get("/notifications/history", response_model=EmailHistoryResponse)
async def get_my_notification_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """View past email delivery log for the current user."""
    user_id_val = user.id.value if hasattr(user.id, "value") else user.id
    user_uuid = UUID(str(user_id_val))
    items = await NotificationRepository.list_by_user(db, user_uuid, limit=limit, offset=offset)
    total = await NotificationRepository.count_by_user(db, user_uuid)
    return EmailHistoryResponse(
        items=[EmailLogResponse.model_validate(item) for item in items],
        total=total,
    )


# ── Admin Operations ─────────────────────────────────────────────────────────


@router.get("/admin/notifications/logs", response_model=list[EmailLogResponse])
async def admin_list_email_logs(
    status_filter: Optional[str] = Query(None, alias="status"),
    template_filter: Optional[str] = Query(None, alias="template"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Admin-only listing of all system email delivery logs."""
    logs = await NotificationRepository.list_all(
        db, status=status_filter, template_name=template_filter, limit=limit, offset=offset
    )
    return [EmailLogResponse.model_validate(item) for item in logs]


@router.post("/admin/notifications/test", response_model=TestEmailResponse)
async def admin_send_test_email(
    body: TestEmailRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Admin trigger to test render and send any transactional email template."""
    svc = _svc(db)
    test_key = f"test_{uuid.uuid4().hex[:12]}"
    context = body.context or {
        "plan_name": "PRO",
        "amount": 1900,
        "amount_formatted": "19.00",
        "currency": "USD",
        "transaction_id": "tx_test_123",
        "reset_link": "http://localhost:3000/reset-password?token=test",
        "error_message": "Test payment failure",
        "metric_name": "saved horoscopes",
        "used": 4,
        "limit": 5,
        "percentage": 80,
    }

    try:
        log = await svc.send_transactional_email(
            to_email=body.to_email,
            template_name=body.template_name,
            context=context,
            idempotency_key=test_key,
        )
        return TestEmailResponse(
            success=(log.status == "sent"),
            template_name=body.template_name,
            recipient=body.to_email,
            provider=log.provider,
            message=f"Test email dispatched with status '{log.status}'.",
            log_id=log.id,
        )
    except Exception as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to render/send test email: {str(e)}",
        )
