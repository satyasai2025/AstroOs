"""
AstroOS — Razorpay Payment Provider (Phase 6)

Production-grade Razorpay integration supporting:
  - Razorpay Orders and Subscription payment sessions
  - Webhook signature verification (HMAC-SHA256 / X-Razorpay-Signature)
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


class RazorpayPaymentProvider(PaymentProviderBase):
    """Razorpay gateway adapter."""

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        settings = get_settings()
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET

    @property
    def provider_name(self) -> str:
        return "razorpay"

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
        """Create a Razorpay Order / Subscription payment session."""
        try:
            import razorpay
            client = razorpay.Client(auth=(self.key_id, self.key_secret)) if (self.key_id and self.key_secret) else None
        except ImportError:
            client = None

        meta = {"user_id": user_id, "plan_code": plan_code, **(metadata or {})}

        if client:
            order_data = {
                "amount": amount,
                "currency": currency.upper(),
                "receipt": f"rcpt_{user_id[:8]}_{int(time.time())}",
                "notes": meta,
            }
            order = client.order.create(data=order_data)
            order_id = order.get("id")
            checkout_url = success_url or f"http://localhost:3000/settings/billing?order_id={order_id}"
            return CheckoutSessionResult(
                session_id=order_id,
                checkout_url=checkout_url,
                provider=self.provider_name,
                amount=amount,
                currency=currency.upper(),
                customer_id=customer_id or f"rzp_cus_{user_id[:8]}",
            )
        else:
            simulated_id = f"order_test_{hashlib.md5(f'{user_id}:{plan_code}:{time.time()}'.encode()).hexdigest()[:16]}"
            return CheckoutSessionResult(
                session_id=simulated_id,
                checkout_url=f"https://api.razorpay.com/v1/checkout/{simulated_id}",
                provider=self.provider_name,
                amount=amount,
                currency=currency.upper(),
                customer_id=customer_id or f"rzp_cus_{user_id[:8]}",
            )

    async def create_portal_session(
        self,
        *,
        customer_id: str,
        return_url: Optional[str] = None,
    ) -> CustomerPortalResult:
        """Razorpay customer portal or subscriptions management URL."""
        portal_url = return_url or f"https://dashboard.razorpay.com/app/subscriptions/{customer_id}"
        return CustomerPortalResult(
            portal_url=portal_url,
            provider=self.provider_name,
        )

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Verify the X-Razorpay-Signature header against the webhook secret."""
        signature = headers.get("x-razorpay-signature") or headers.get("X-Razorpay-Signature")
        if not signature or not self.webhook_secret:
            return False

        try:
            expected_sig = hmac.new(
                self.webhook_secret.encode("utf-8"),
                payload_bytes,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(signature, expected_sig)
        except Exception:
            return False

    def parse_webhook_event(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> StandardWebhookEvent:
        """Normalize Razorpay webhook event into StandardWebhookEvent."""
        data = json.loads(payload_bytes.decode("utf-8"))
        event_type = data.get("event", "")
        event_id = data.get("id") or f"rzp_evt_{hashlib.md5(payload_bytes).hexdigest()[:16]}"

        payload_obj = data.get("payload", {})
        payment_entity = payload_obj.get("payment", {}).get("entity", {})
        order_entity = payload_obj.get("order", {}).get("entity", {})
        subscription_entity = payload_obj.get("subscription", {}).get("entity", {})

        notes = payment_entity.get("notes", {}) or order_entity.get("notes", {}) or subscription_entity.get("notes", {})
        user_id = notes.get("user_id")
        plan_code = notes.get("plan_code")
        customer_id = payment_entity.get("customer_id") or subscription_entity.get("customer_id")
        payment_id = payment_entity.get("id")
        order_id = order_entity.get("id") or payment_entity.get("order_id")
        amount = payment_entity.get("amount") or order_entity.get("amount") or 0
        currency = (payment_entity.get("currency") or order_entity.get("currency") or "INR").upper()
        error_message = payment_entity.get("error_description")

        period_start = subscription_entity.get("current_start")
        period_end = subscription_entity.get("current_end")

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
            error_message=error_message,
            period_start=period_start,
            period_end=period_end,
            raw_payload=data,
        )
