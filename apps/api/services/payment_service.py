"""
AstroOS — Payment Service (Phase 6)

Core orchestration service managing:
  - Checkout initiation
  - Customer billing portal sessions
  - Webhook cryptographic verification and normalized event ingestion
  - Subscription lifecycle transitions (activation, renewal, grace, expiration)
  - Payment record auditing and idempotency
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.domain.user import User
from apps.api.models.payment import (
    PaymentModel,
    PaymentProviderType,
    PaymentStatus,
)
from apps.api.models.subscription import (
    SubscriptionEventType,
    SubscriptionModel,
    SubscriptionStatus,
)
from apps.api.repositories.payment_repository import PaymentRepository
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.repositories.subscription_repository import SubscriptionRepository
from apps.api.schemas.payment import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalRequest,
    CustomerPortalResponse,
    PaymentConfigResponse,
    PaymentHistoryResponse,
    PaymentResponse,
    PricingCatalogResponse,
    PricingPlanDetail,
    WebhookProcessingResult,
)
from apps.api.services.payment.base import PaymentProviderBase
from apps.api.services.payment.factory import get_payment_provider
from apps.api.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class PaymentService:
    """Application service for payment processing and subscription billing orchestration."""

    # Multi-currency base pricing catalog (in smallest currency units, e.g. paise / cents)
    PLAN_PRICING: Mapping[str, dict[str, dict[str, int]]] = {
        "INR": {
            "PRO": {"monthly": 199900, "yearly": 1999000},       # ₹1,999/mo, ₹19,990/yr (in paise)
            "RESEARCH": {"monthly": 499900, "yearly": 4999000},  # ₹4,999/mo, ₹49,990/yr (in paise)
            "CUSTOM": {"monthly": 999900, "yearly": 9999000},    # ₹9,999/mo, ₹99,990/yr (in paise)
            "FREE": {"monthly": 0, "yearly": 0},
        },
        "USD": {
            "PRO": {"monthly": 1900, "yearly": 19000},           # $19/mo, $190/yr (in cents)
            "RESEARCH": {"monthly": 4900, "yearly": 49000},      # $49/mo, $490/yr (in cents)
            "CUSTOM": {"monthly": 9900, "yearly": 99000},        # $99/mo, $990/yr (in cents)
            "FREE": {"monthly": 0, "yearly": 0},
        },
    }

    CURRENCY_SYMBOLS: Mapping[str, str] = {
        "INR": "₹",
        "USD": "$",
    }

    def __init__(
        self,
        db: AsyncSession,
        provider: Optional[PaymentProviderBase] = None,
    ) -> None:
        self._db = db
        self._provider = provider or get_payment_provider()

    # ── Config & Info ─────────────────────────────────────────────────────────

    def get_config(self) -> PaymentConfigResponse:
        """Return public payment gateway configuration."""
        settings = get_settings()
        active = self._provider.provider_name
        pub_key = None
        if active == "stripe":
            pub_key = settings.STRIPE_PUBLISHABLE_KEY
        elif active == "razorpay":
            pub_key = settings.RAZORPAY_KEY_ID

        return PaymentConfigResponse(
            active_provider=active,  # type: ignore[arg-type]
            publishable_key=pub_key,
            default_currency=settings.PAYMENT_DEFAULT_CURRENCY,
            supported_currencies=["INR", "USD"],
            tax_rate_inr=settings.TAX_RATE_INR_PERCENT,
            tax_rate_usd=settings.TAX_RATE_USD_PERCENT,
            supported_providers=["mock", "stripe", "razorpay"],
        )

    # ── Tax & Pricing Engine (Authoritative Backend Calculation) ──────────────

    @classmethod
    def get_tax_rate_for_currency(cls, currency: str) -> tuple[float, str]:
        """Return (tax_rate_percent, tax_name) for a given currency."""
        curr = currency.upper()
        settings = get_settings()
        if curr == "INR":
            return (settings.TAX_RATE_INR_PERCENT, "GST")
        elif curr == "USD":
            return (settings.TAX_RATE_USD_PERCENT, "Sales Tax")
        return (0.0, "Tax")

    @classmethod
    def calculate_pricing(
        cls, plan_code: str, billing_cycle: str = "monthly", currency: str = "INR"
    ) -> dict[str, Any]:
        """
        Pure, authoritative tax and total payable calculation.
        Computes: Base Amount + Tax Amount = Total Payable Amount.
        All integer amounts are in the smallest currency denomination (paise / cents).
        """
        curr = currency.upper()
        code = plan_code.upper()
        cycle = billing_cycle.lower()

        # Resolve base price
        curr_pricing = cls.PLAN_PRICING.get(curr, cls.PLAN_PRICING["INR"])
        plan_cycle_pricing = curr_pricing.get(code, {"monthly": 199900 if curr == "INR" else 1900, "yearly": 1999000 if curr == "INR" else 19000})
        base_amount = plan_cycle_pricing.get(cycle, plan_cycle_pricing["monthly"])

        tax_rate, tax_name = cls.get_tax_rate_for_currency(curr)

        # Tax calculation with precise integer rounding
        if base_amount > 0 and tax_rate > 0.0:
            tax_amount = round(base_amount * (tax_rate / 100.0))
        else:
            tax_amount = 0

        total_amount = base_amount + tax_amount
        sym = cls.CURRENCY_SYMBOLS.get(curr, curr)

        return {
            "plan_code": code,
            "billing_cycle": cycle,
            "currency": curr,
            "currency_symbol": sym,
            "base_amount": base_amount,
            "base_amount_formatted": f"{sym}{base_amount / 100:,.2f}" if base_amount > 0 else f"{sym}0",
            "tax_rate": tax_rate,
            "tax_name": tax_name,
            "tax_amount": tax_amount,
            "tax_amount_formatted": f"{sym}{tax_amount / 100:,.2f}" if tax_amount > 0 else f"{sym}0",
            "total_amount": total_amount,
            "total_amount_formatted": f"{sym}{total_amount / 100:,.2f}" if total_amount > 0 else f"{sym}0",
        }

    async def get_pricing_catalog(self, currency: str = "INR") -> PricingCatalogResponse:
        """Generate complete backend-driven pricing catalog with tax breakdowns."""
        curr = currency.upper() if currency else "INR"
        if curr not in ("INR", "USD"):
            curr = "INR"

        tax_rate, tax_name = self.get_tax_rate_for_currency(curr)
        sym = self.CURRENCY_SYMBOLS.get(curr, curr)

        plans_meta = [
            {
                "code": "FREE",
                "name": "Free Community",
                "description": "Essential Vedic chart calculation & sky transit clock for personal study.",
                "horoscopes": 5,
                "research": 0,
                "features": ["5 Saved Horoscopes", "D1 to D60 Divisional Charts", "Vimshottari Dasha Engine", "Live Sky Transit Clock"],
            },
            {
                "code": "PRO",
                "name": "Professional Astrologer",
                "description": "Advanced predictive engines, chart editing, Prashna, and PDF export reports.",
                "horoscopes": 50,
                "research": 1,
                "features": ["50 Saved Horoscopes", "1 Research Project / Month", "Chart Edit Mode", "Prashna & Horary Engine", "PDF & CSV Export Reports", "AI Chart Explanations"],
            },
            {
                "code": "RESEARCH",
                "name": "Astrological Research Scholar",
                "description": "Custom AstroDSL technique authoring, statistical correlation, and Knowledge Graph.",
                "horoscopes": 100,
                "research": 3,
                "features": ["100 Saved Horoscopes", "3 Research Projects / Month", "Custom AstroDSL Rule Engine", "Statistical Correlation & Bayes Studio", "Complete Knowledge Graph RAG", "Unlimited Batch Exports"],
            },
            {
                "code": "CUSTOM",
                "name": "Institutional / Enterprise",
                "description": "High-throughput batch computation, dedicated API SDK access, and priority support.",
                "horoscopes": None,
                "research": None,
                "features": ["Unlimited Saved Horoscopes", "Unlimited Research Runs", "Python & TypeScript SDK Access", "High-Throughput Batch Engine", "Priority Support & Custom Yogas"],
            },
        ]

        catalog_plans: list[PricingPlanDetail] = []
        for p in plans_meta:
            m_calc = self.calculate_pricing(p["code"], "monthly", curr)
            y_calc = self.calculate_pricing(p["code"], "yearly", curr)

            catalog_plans.append(
                PricingPlanDetail(
                    plan_code=p["code"],
                    name=p["name"],
                    description=p["description"],
                    currency=curr,
                    currency_symbol=sym,
                    tax_rate=tax_rate,
                    tax_name=tax_name,
                    monthly_base_amount=m_calc["base_amount"],
                    monthly_base_formatted=m_calc["base_amount_formatted"],
                    monthly_tax_amount=m_calc["tax_amount"],
                    monthly_tax_formatted=m_calc["tax_amount_formatted"],
                    monthly_total_amount=m_calc["total_amount"],
                    monthly_total_formatted=m_calc["total_amount_formatted"],
                    yearly_base_amount=y_calc["base_amount"],
                    yearly_base_formatted=y_calc["base_amount_formatted"],
                    yearly_tax_amount=y_calc["tax_amount"],
                    yearly_tax_formatted=y_calc["tax_amount_formatted"],
                    yearly_total_amount=y_calc["total_amount"],
                    yearly_total_formatted=y_calc["total_amount_formatted"],
                    saved_horoscopes_limit=p["horoscopes"],
                    research_projects_monthly_limit=p["research"],
                    features=p["features"],
                )
            )

        return PricingCatalogResponse(
            currency=curr,
            currency_symbol=sym,
            supported_currencies=["INR", "USD"],
            tax_rate=tax_rate,
            tax_name=tax_name,
            plans=catalog_plans,
        )

    # ── Checkout & Portal ─────────────────────────────────────────────────────

    async def initiate_checkout(
        self,
        user: User,
        request: CheckoutSessionRequest,
    ) -> CheckoutSessionResponse:
        """Create a checkout session for subscribing to a plan with exact tax calculation."""
        plan_code = request.plan_code.upper()
        plan = await PlanRepository.get_by_code(self._db, plan_code)
        if plan is None or not plan.is_active:
            raise LookupError(f"Plan '{plan_code}' is not available for purchase.")

        currency = (request.currency or get_settings().PAYMENT_DEFAULT_CURRENCY).upper()
        if currency not in ("INR", "USD"):
            currency = "INR"

        pricing = self.calculate_pricing(plan_code, request.billing_cycle, currency)
        base_amount = pricing["base_amount"]
        tax_amount = pricing["tax_amount"]
        tax_rate = pricing["tax_rate"]
        total_amount = pricing["total_amount"]

        user_id_val = user.id.value if hasattr(user.id, "value") else user.id
        user_uuid = UUID(str(user_id_val))

        # Check existing customer record
        customer = await PaymentRepository.get_customer(
            self._db, user_uuid, self._provider.provider_name
        )
        customer_id = customer.provider_customer_id if customer else None

        session_res = await self._provider.create_checkout_session(
            user_id=str(user_uuid),
            user_email=user.email,
            plan_code=plan_code,
            amount=total_amount,
            currency=currency,
            billing_cycle=request.billing_cycle,
            customer_id=customer_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(user_uuid),
                "plan_code": plan_code,
                "base_amount": str(base_amount),
                "tax_amount": str(tax_amount),
                "tax_rate": str(tax_rate),
            },
        )

        # Store pending payment record with tax breakdown
        await PaymentRepository.create_payment(
            self._db,
            user_id=user_uuid,
            plan_id=plan.id,
            amount=total_amount,
            base_amount=base_amount,
            tax_amount=tax_amount,
            tax_rate=tax_rate,
            currency=currency,
            provider=self._provider.provider_name,
            provider_order_id=session_res.session_id,
            status_value=PaymentStatus.PENDING.value,
        )

        # Update customer mapping if newly provided
        if session_res.customer_id and not customer:
            await PaymentRepository.upsert_customer(
                self._db,
                user_id=user_uuid,
                provider=self._provider.provider_name,
                provider_customer_id=session_res.customer_id,
            )

        return CheckoutSessionResponse(
            session_id=session_res.session_id,
            checkout_url=session_res.checkout_url,
            provider=self._provider.provider_name,  # type: ignore[arg-type]
            plan_code=plan_code,
            currency=currency,
            base_amount=base_amount,
            tax_amount=tax_amount,
            tax_rate=tax_rate,
            total_amount=total_amount,
            amount=total_amount,
        )

    async def initiate_portal(
        self,
        user: User,
        request: CustomerPortalRequest,
    ) -> CustomerPortalResponse:
        """Create a billing customer portal session."""
        user_id_val = user.id.value if hasattr(user.id, "value") else user.id
        user_uuid = UUID(str(user_id_val))

        customer = await PaymentRepository.get_customer(
            self._db, user_uuid, self._provider.provider_name
        )
        customer_id = (
            customer.provider_customer_id
            if customer
            else f"cus_{str(user_uuid)[:8]}"
        )

        portal_res = await self._provider.create_portal_session(
            customer_id=customer_id,
            return_url=request.return_url,
        )

        return CustomerPortalResponse(
            portal_url=portal_res.portal_url,
            provider=self._provider.provider_name,  # type: ignore[arg-type]
        )

    # ── History & Auditing ────────────────────────────────────────────────────

    async def list_user_payments(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> PaymentHistoryResponse:
        """List past payment receipts for a user."""
        items = await PaymentRepository.list_by_user(self._db, user_id, limit, offset)
        total = await PaymentRepository.count_by_user(self._db, user_id)
        return PaymentHistoryResponse(
            items=[PaymentResponse.model_validate(p) for p in items],
            total=total,
        )

    async def list_all_payments(
        self,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PaymentResponse]:
        """Admin listing of all payments across users."""
        items = await PaymentRepository.list_all(
            self._db, status=status, provider=provider, limit=limit, offset=offset
        )
        return [PaymentResponse.model_validate(p) for p in items]

    # ── Webhook Processing & Lifecycle Synchronization ───────────────────────

    async def process_webhook(
        self,
        provider_name: str,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> WebhookProcessingResult:
        """
        Verify signature, parse event, ensure idempotency, and synchronize subscription state.
        """
        provider = get_payment_provider(provider_name)

        # 1. Verify signature
        if not provider.verify_webhook_signature(payload_bytes, headers):
            raise ValueError(f"Invalid webhook signature for provider '{provider_name}'.")

        # 2. Parse standardized event
        event = provider.parse_webhook_event(payload_bytes, headers)

        # 3. Check replay / idempotency
        if await PaymentRepository.is_event_processed(self._db, provider_name, event.event_id):
            return WebhookProcessingResult(
                status="ignored",
                provider=provider_name,
                event_id=event.event_id,
                event_type=event.event_type,
                message="Event already processed (idempotent skip).",
            )

        # 4. Resolve user
        user_uuid: Optional[UUID] = None
        if event.user_id:
            try:
                user_uuid = UUID(event.user_id)
            except ValueError:
                pass

        if not user_uuid and event.customer_id:
            user_uuid = await PaymentRepository.get_user_id_by_customer_id(
                self._db, provider_name, event.customer_id
            )

        if not user_uuid and event.order_id:
            pending_p = await PaymentRepository.get_by_provider_order_id(
                self._db, event.order_id
            )
            if pending_p:
                user_uuid = pending_p.user_id

        # 5. Dispatch based on event type
        now = datetime.now(timezone.utc)
        sub_service = SubscriptionService(self._db)

        # ── Checkout / Initial Activation
        if event.event_type in (
            "checkout.session.completed",
            "payment.captured",
            "order.paid",
        ):
            if user_uuid:
                plan_code = (event.plan_code or "PRO").upper()
                plan = await PlanRepository.get_by_code(self._db, plan_code)
                plan_id = plan.id if plan else None

                period_end = (
                    datetime.fromtimestamp(event.period_end, tz=timezone.utc)
                    if event.period_end
                    else now + timedelta(days=30)
                )

                sub = await SubscriptionRepository.get_by_user(self._db, user_uuid)
                if sub is None and plan_id:
                    sub = await SubscriptionRepository.create_subscription(
                        self._db,
                        user_id=user_uuid,
                        plan_id=plan_id,
                        status_value=SubscriptionStatus.ACTIVE.value,
                        current_period_start=now,
                        current_period_end=period_end,
                    )
                elif sub:
                    # Update subscription attributes
                    if plan_id:
                        sub.plan_id = plan_id
                    sub.current_period_start = now
                    sub.current_period_end = period_end

                    if sub.status in (
                        SubscriptionStatus.TRIALING.value,
                        SubscriptionStatus.PAST_DUE_CANCELLED.value,
                    ):
                        await sub_service.activate(sub.id, reason="checkout_completed")
                    elif sub.status == SubscriptionStatus.EXPIRED.value:
                        # Reactivation from expired state
                        sub.status = SubscriptionStatus.ACTIVE.value
                        sub.ended_at = None
                        sub.event_version = (sub.event_version or 0) + 1
                        await SubscriptionRepository.append_event(
                            self._db,
                            subscription=sub,
                            event_type=SubscriptionEventType.ACTIVATED,
                            from_status=SubscriptionStatus.EXPIRED.value,
                            to_status=SubscriptionStatus.ACTIVE.value,
                            payload_json="reactivated_via_payment",
                            commit=False,
                        )
                        await SubscriptionRepository.save(self._db, sub)

                # Record or update payment
                pending_payment = None
                if event.order_id:
                    pending_payment = await PaymentRepository.get_by_provider_order_id(
                        self._db, event.order_id
                    )

                if pending_payment:
                    await PaymentRepository.update_payment_status(
                        self._db,
                        pending_payment,
                        status_value=PaymentStatus.SUCCEEDED.value,
                        provider_payment_id=event.payment_id,
                        receipt_url=event.receipt_url,
                        payload=event.raw_payload,
                    )
                elif plan_id:
                    await PaymentRepository.create_payment(
                        self._db,
                        user_id=user_uuid,
                        plan_id=plan_id,
                        subscription_id=sub.id if sub else None,
                        amount=event.amount or 0,
                        currency=event.currency or "USD",
                        provider=provider_name,
                        status_value=PaymentStatus.SUCCEEDED.value,
                        provider_payment_id=event.payment_id,
                        provider_order_id=event.order_id,
                        receipt_url=event.receipt_url,
                        payload=event.raw_payload,
                    )

                if event.customer_id:
                    await PaymentRepository.upsert_customer(
                        self._db,
                        user_id=user_uuid,
                        provider=provider_name,
                        provider_customer_id=event.customer_id,
                    )

        # ── Recurring Payment / Renewal
        elif event.event_type in ("invoice.payment_succeeded", "subscription.charged"):
            if user_uuid:
                sub = await SubscriptionRepository.get_by_user(self._db, user_uuid)
                if sub:
                    new_end = (
                        datetime.fromtimestamp(event.period_end, tz=timezone.utc)
                        if event.period_end
                        else (sub.current_period_end or now) + timedelta(days=30)
                    )
                    sub.current_period_end = new_end
                    if sub.status == SubscriptionStatus.PAST_DUE_CANCELLED.value:
                        sub.status = SubscriptionStatus.ACTIVE.value

                    await SubscriptionRepository.append_event(
                        self._db,
                        subscription=sub,
                        event_type=SubscriptionEventType.RENEWED,
                        to_status=sub.status,
                        payload_json="subscription_renewed",
                        commit=False,
                    )
                    await SubscriptionRepository.append_event(
                        self._db,
                        subscription=sub,
                        event_type=SubscriptionEventType.PERIOD_EXTENDED,
                        to_status=sub.status,
                        payload_json=f"period_extended_to_{new_end.isoformat()}",
                        commit=False,
                    )
                    await SubscriptionRepository.save(self._db, sub)

                    await PaymentRepository.create_payment(
                        self._db,
                        user_id=user_uuid,
                        plan_id=sub.plan_id,
                        subscription_id=sub.id,
                        amount=event.amount or 0,
                        currency=event.currency or "USD",
                        provider=provider_name,
                        status_value=PaymentStatus.SUCCEEDED.value,
                        provider_payment_id=event.payment_id,
                        receipt_url=event.receipt_url,
                        payload=event.raw_payload,
                    )

        # ── Payment Failure
        elif event.event_type in (
            "invoice.payment_failed",
            "subscription.halted",
            "payment.failed",
        ):
            if user_uuid:
                sub = await SubscriptionRepository.get_by_user(self._db, user_uuid)
                if sub and sub.status in (
                    SubscriptionStatus.ACTIVE.value,
                    SubscriptionStatus.TRIALING.value,
                ):
                    await sub_service.cancel(sub.id, reason=event.error_message or "payment_failed")

                await PaymentRepository.create_payment(
                    self._db,
                    user_id=user_uuid,
                    plan_id=sub.plan_id if sub else None,
                    subscription_id=sub.id if sub else None,
                    amount=event.amount or 0,
                    currency=event.currency or "USD",
                    provider=provider_name,
                    status_value=PaymentStatus.FAILED.value,
                    provider_payment_id=event.payment_id,
                    error_message=event.error_message,
                    payload=event.raw_payload,
                )

        # ── Subscription Deleted / Expired
        elif event.event_type in ("customer.subscription.deleted", "subscription.cancelled"):
            if user_uuid:
                sub = await SubscriptionRepository.get_by_user(self._db, user_uuid)
                if sub and sub.status != SubscriptionStatus.EXPIRED.value:
                    await sub_service.expire(sub.id, reason="cancelled_at_gateway")

        # ── Refund
        elif event.event_type in ("charge.refunded", "payment.refunded"):
            if event.payment_id:
                p = await PaymentRepository.get_by_provider_payment_id(
                    self._db, provider_name, event.payment_id
                )
                if p:
                    await PaymentRepository.update_payment_status(
                        self._db, p, status_value=PaymentStatus.REFUNDED.value
                    )

        # 6. Record processed webhook event
        await PaymentRepository.record_webhook_event(
            self._db,
            provider=provider_name,
            provider_event_id=event.event_id,
            event_type=event.event_type,
            status="processed",
            payload=event.raw_payload,
        )

        return WebhookProcessingResult(
            status="processed",
            provider=provider_name,
            event_id=event.event_id,
            event_type=event.event_type,
            message="Webhook event processed successfully.",
        )
