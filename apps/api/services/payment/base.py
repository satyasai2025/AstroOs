"""
AstroOS — Payment Provider Interface (Phase 6)

Abstract base definitions and standardized dataclasses for payment gateway integrations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CheckoutSessionResult:
    """Standardized result from creating a checkout session."""
    session_id: str
    checkout_url: str
    provider: str
    amount: int
    currency: str
    customer_id: Optional[str] = None


@dataclass
class CustomerPortalResult:
    """Standardized result from creating a customer billing portal session."""
    portal_url: str
    provider: str


@dataclass
class StandardWebhookEvent:
    """Normalized webhook event representation across all gateways."""
    event_id: str
    event_type: str
    provider: str
    user_id: Optional[str] = None
    plan_code: Optional[str] = None
    customer_id: Optional[str] = None
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    receipt_url: Optional[str] = None
    error_message: Optional[str] = None
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    raw_payload: Optional[dict[str, Any]] = None


class PaymentProviderBase(ABC):
    """Abstract payment gateway provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider, e.g. 'mock', 'stripe', 'razorpay'."""
        pass

    @abstractmethod
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
        """Create a hosted checkout session."""
        pass

    @abstractmethod
    async def create_portal_session(
        self,
        *,
        customer_id: str,
        return_url: Optional[str] = None,
    ) -> CustomerPortalResult:
        """Create a customer billing management portal link."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Verify the cryptographic signature of an incoming webhook payload."""
        pass

    @abstractmethod
    def parse_webhook_event(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> StandardWebhookEvent:
        """Parse raw webhook payload and headers into a standardized event."""
        pass
