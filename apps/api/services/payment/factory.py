"""
AstroOS — Payment Provider Factory (Phase 6)
"""

from __future__ import annotations

from typing import Optional

from apps.api.config import get_settings
from apps.api.services.payment.base import PaymentProviderBase
from apps.api.services.payment.mock_provider import MockPaymentProvider
from apps.api.services.payment.razorpay_provider import RazorpayPaymentProvider
from apps.api.services.payment.stripe_provider import StripePaymentProvider


def get_payment_provider(provider_name: Optional[str] = None) -> PaymentProviderBase:
    """
    Resolve and return a payment provider instance.
    Defaults to the configured application setting `PAYMENT_PROVIDER`.
    """
    name = (provider_name or get_settings().PAYMENT_PROVIDER or "mock").lower()

    if name == "stripe":
        return StripePaymentProvider()
    elif name == "razorpay":
        return RazorpayPaymentProvider()
    elif name == "mock":
        return MockPaymentProvider()
    else:
        raise ValueError(f"Unsupported payment provider: {name}. Supported: 'mock', 'stripe', 'razorpay'")
