"""
AstroOS — Mock Payment Provider (Phase 6)

Deterministic in-memory/simulated provider for local testing and CI without external API keys.
"""

from __future__ import annotations

import hmac
import hashlib
import json
import time
import uuid
from typing import Any, Optional

from apps.api.services.payment.base import (
    CheckoutSessionResult,
    CustomerPortalResult,
    PaymentProviderBase,
    StandardWebhookEvent,
)


class MockPaymentProvider(PaymentProviderBase):
    """Mock payment provider for development, testing, and offline environments."""

    MOCK_SECRET: str = "mock_secret_key_12345"

    @property
    def provider_name(self) -> str:
        return "mock"

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
        session_id = f"mock_cs_{uuid.uuid4().hex[:16]}"
        cust_id = customer_id or f"mock_cus_{uuid.uuid4().hex[:12]}"
        checkout_url = success_url or f"https://astroos.local/checkout/{session_id}"

        return CheckoutSessionResult(
            session_id=session_id,
            checkout_url=checkout_url,
            provider=self.provider_name,
            amount=amount,
            currency=currency,
            customer_id=cust_id,
        )

    async def create_portal_session(
        self,
        *,
        customer_id: str,
        return_url: Optional[str] = None,
    ) -> CustomerPortalResult:
        portal_url = return_url or f"https://astroos.local/portal/{customer_id}"
        return CustomerPortalResult(
            portal_url=portal_url,
            provider=self.provider_name,
        )

    def generate_mock_signature(self, payload_bytes: bytes) -> str:
        """Helper to generate a valid signature for mock webhook test payloads."""
        return hmac.new(
            self.MOCK_SECRET.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> bool:
        signature = headers.get("x-mock-signature") or headers.get("X-Mock-Signature")
        if not signature:
            # If no signature provided, allow in mock mode if header 'x-mock-skip-signature' is 'true'
            if headers.get("x-mock-skip-signature") == "true":
                return True
            return False

        expected = self.generate_mock_signature(payload_bytes)
        return hmac.compare_digest(signature, expected)

    def parse_webhook_event(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> StandardWebhookEvent:
        data = json.loads(payload_bytes.decode("utf-8"))
        event_id = data.get("id") or f"mock_evt_{uuid.uuid4().hex[:12]}"
        event_type = data.get("event_type") or "checkout.session.completed"

        event_data = data.get("data", {})
        metadata = event_data.get("metadata", {})

        return StandardWebhookEvent(
            event_id=event_id,
            event_type=event_type,
            provider=self.provider_name,
            user_id=metadata.get("user_id") or event_data.get("user_id"),
            plan_code=metadata.get("plan_code") or event_data.get("plan_code"),
            customer_id=event_data.get("customer_id"),
            payment_id=event_data.get("payment_id") or f"mock_pi_{uuid.uuid4().hex[:12]}",
            order_id=event_data.get("order_id"),
            amount=event_data.get("amount", 0),
            currency=event_data.get("currency", "USD"),
            receipt_url=event_data.get("receipt_url"),
            error_message=event_data.get("error_message"),
            period_start=event_data.get("period_start", int(time.time())),
            period_end=event_data.get("period_end", int(time.time()) + 30 * 86400),
            raw_payload=data,
        )
