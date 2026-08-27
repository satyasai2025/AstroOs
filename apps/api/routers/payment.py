"""
AstroOS — Payment API Router (Phase 6)

Endpoints:
  - GET  /api/v1/payments/config           — Gateway config (active provider, publishable keys)
  - POST /api/v1/payments/checkout         — Initiate checkout session for a plan
  - POST /api/v1/payments/portal           — Customer billing management portal link
  - GET  /api/v1/payments/history          — Current user's payment receipts
  - POST /api/v1/payments/webhook/{provider} — Gateway webhook receiver (Stripe, Razorpay, Mock)
  - GET  /api/v1/admin/payments            — Admin payment transaction audit
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    require_admin,
)
from apps.api.domain.user import User
from apps.api.schemas.payment import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalRequest,
    CustomerPortalResponse,
    PaymentConfigResponse,
    PaymentHistoryResponse,
    PaymentResponse,
    PricingCatalogResponse,
    WebhookProcessingResult,
)
from apps.api.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1", tags=["Payments"])


def _svc(db: AsyncSession) -> PaymentService:
    return PaymentService(db)


# ── Configuration & Pricing ───────────────────────────────────────────────────


@router.get("/payments/config", response_model=PaymentConfigResponse)
async def payment_config(db: AsyncSession = Depends(get_db_session)):
    """Return active payment provider and client credentials."""
    return _svc(db).get_config()


@router.get("/payments/pricing", response_model=PricingCatalogResponse)
async def get_pricing_catalog(
    currency: Optional[str] = Query("INR", description="Currency code: 'INR' (India-first ₹) or 'USD'"),
    db: AsyncSession = Depends(get_db_session),
):
    """Return complete authoritative backend pricing catalog with tax breakdowns."""
    return await _svc(db).get_pricing_catalog(currency=currency or "INR")


# ── User Checkout & Portal ───────────────────────────────────────────────────


@router.post("/payments/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    body: CheckoutSessionRequest,
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Initiate a checkout session for subscribing to a plan."""
    try:
        return await _svc(db).initiate_checkout(user, body)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/payments/portal", response_model=CustomerPortalResponse)
async def create_portal_session(
    body: CustomerPortalRequest,
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Generate a customer billing portal URL."""
    return await _svc(db).initiate_portal(user, body)


@router.get("/payments/history", response_model=PaymentHistoryResponse)
async def payment_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve payment receipts for the authenticated user."""
    user_id_val = user.id.value if hasattr(user.id, "value") else user.id
    return await _svc(db).list_user_payments(UUID(str(user_id_val)), limit=limit, offset=offset)


# ── Webhooks (Public with signature check) ───────────────────────────────────


@router.post("/payments/webhook/{provider}", response_model=WebhookProcessingResult)
async def handle_payment_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Receive and process inbound webhook events from payment gateways (Stripe, Razorpay, Mock).
    """
    payload_bytes = await request.body()
    headers_dict = dict(request.headers)

    try:
        return await _svc(db).process_webhook(
            provider_name=provider.lower(),
            payload_bytes=payload_bytes,
            headers=headers_dict,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}",
        )


# ── Admin Operations ─────────────────────────────────────────────────────────


@router.get("/admin/payments", response_model=list[PaymentResponse])
async def admin_list_payments(
    status_filter: Optional[str] = Query(None, alias="status"),
    provider_filter: Optional[str] = Query(None, alias="provider"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Admin-only listing of all payment transactions."""
    return await _svc(db).list_all_payments(
        status=status_filter,
        provider=provider_filter,
        limit=limit,
        offset=offset,
    )
