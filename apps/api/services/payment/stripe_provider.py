"""
AstroOS — Stripe Payment Provider (Phase 6)

Production-grade Stripe integration supporting:
  - Stripe Checkout Sessions
  - Stripe Customer Portal
  - Webhook signature verification (HMAC-SHA256 / stripe-signature)
  - Normalized event mapping
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Optional

from apps.api.config import get_settings
from apps.api.services.payment.base import (
    CheckoutSessionResult,
    CustomerPortalResult,
    PaymentProviderBase,
    StandardWebhookEvent,
)


class StripePaymentProvider(PaymentProviderBase):
    """Stripe gateway adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.STRIPE_SECRET_KEY
        self.webhook_secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET

    @property
    def provider_name(self) -> str:
        return "stripe"

    async def create_checkout_session(
        self,
        *,
        user_id: str,
        user_email: str,
        plan_code: str,
        amount: int,
        currency: str,
        billing_cycle: str = "monthly",
        customer_id: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> CheckoutSessionResult:
        """Create a Stripe Checkout Session."""
        try:
            import stripe
            stripe.api_key = self.api_key
        except ImportError:
            stripe = None

        meta = {"user_id": user_id, "plan_code": plan_code, **(metadata or {})}

        if stripe and self.api_key:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                customer_email=user_email if not customer_id else None,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": currency.lower(),
                            "product_data": {
                                "name": f"AstroOS {plan_code.upper()} Plan",
                                "description": f"{billing_cycle.capitalize()} subscription to AstroOS {plan_code.upper()}",
                            },
                            "unit_amount": amount,
                            "recurring": {
                                "interval": "month" if billing_cycle == "monthly" else "year"
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url or "http://localhost:3000/settings/billing?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url or "http://localhost:3000/settings/billing?status=cancelled",
                metadata=meta,
            )
            return CheckoutSessionResult(
                session_id=session.id,
                checkout_url=session.url,
                provider=self.provider_name,
                amount=amount,
                currency=currency,
                customer_id=getattr(session, "customer", None),
            )
        else:
            # Fallback simulated response when SDK is not present or in sandbox test
            simulated_id = f"cs_test_{hashlib.md5(f'{user_id}:{plan_code}:{time.time()}'.encode()).hexdigest()[:16]}"
            return CheckoutSessionResult(
                session_id=simulated_id,
                checkout_url=f"https://checkout.stripe.com/c/pay/{simulated_id}",
                provider=self.provider_name,
                amount=amount,
                currency=currency,
                customer_id=customer_id or f"cus_{user_id[:8]}",
            )

    async def create_portal_session(
        self,
        *,
        customer_id: str,
        return_url: Optional[str] = None,
    ) -> CustomerPortalResult:
        """Create a Stripe Customer Portal session."""
        try:
            import stripe
            stripe.api_key = self.api_key
        except ImportError:
            stripe = None

        target_return_url = return_url or "http://localhost:3000/settings/billing"

        if stripe and self.api_key:
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=target_return_url,
            )
            return CustomerPortalResult(
                portal_url=portal_session.url,
                provider=self.provider_name,
            )
        else:
            return CustomerPortalResult(
                portal_url=f"https://billing.stripe.com/p/session/test_{customer_id}",
                provider=self.provider_name,
            )

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Verify the Stripe-Signature header."""
        sig_header = headers.get("stripe-signature") or headers.get("Stripe-Signature")
        if not sig_header or not self.webhook_secret:
            return False

        try:
            import stripe
            try:
                stripe.Webhook.construct_event(
                    payload_bytes, sig_header, self.webhook_secret
                )
                return True
            except Exception:
                pass
        except ImportError:
            pass

        # Standalone HMAC-SHA256 verification (standard Stripe format: t=timestamp,v1=signature)
        try:
            pairs = dict(item.split("=", 1) for item in sig_header.split(","))
            timestamp = pairs.get("t")
            v1_sig = pairs.get("v1")
            if not timestamp or not v1_sig:
                return False

            signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
            expected_sig = hmac.new(
                self.webhook_secret.encode("utf-8"),
                signed_payload,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(v1_sig, expected_sig)
        except Exception:
            return False

    def parse_webhook_event(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> StandardWebhookEvent:
        """Normalize Stripe webhook event to StandardWebhookEvent."""
        data = json.loads(payload_bytes.decode("utf-8"))
        event_id = data.get("id", "")
        event_type = data.get("type", "")

        obj = data.get("data", {}).get("object", {})
        metadata = obj.get("metadata", {})

        user_id = metadata.get("user_id")
        plan_code = metadata.get("plan_code")
        customer_id = obj.get("customer")
        payment_id = obj.get("payment_intent") or obj.get("id")
        order_id = obj.get("id") if event_type.startswith("checkout.session") else None
        amount = obj.get("amount_total") or obj.get("amount_paid") or obj.get("amount") or 0
        currency = (obj.get("currency") or "USD").upper()
        receipt_url = obj.get("hosted_invoice_url") or obj.get("receipt_url")

        # Period calculation for subscriptions / invoices
        period_start = None
        period_end = None
        lines = obj.get("lines", {}).get("data", [])
        if lines and isinstance(lines, list):
            period = lines[0].get("period", {})
            period_start = period.get("start")
            period_end = period.get("end")

        return StandardWebhookEvent(
            event_id=event_id,
            event_type=event_type,
            provider=self.provider_name,
            user_id=user_id,
            plan_code=plan_code,
            customer_id=customer_id,
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            receipt_url=receipt_url,
            period_start=period_start,
            period_end=period_end,
            raw_payload=data,
        )
