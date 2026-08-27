"""
AstroOS — Email Delivery Provider Factory (Phase 7)
"""

from __future__ import annotations

from typing import Optional

from apps.api.config import get_settings
from apps.api.services.notification.providers.base import EmailDeliveryProviderBase
from apps.api.services.notification.providers.mock_provider import MockEmailProvider
from apps.api.services.notification.providers.resend_provider import ResendEmailProvider
from apps.api.services.notification.providers.smtp_provider import SmtpEmailProvider


def get_email_provider(provider_name: Optional[str] = None) -> EmailDeliveryProviderBase:
    """
    Resolve and return an email delivery provider instance.
    Defaults to the configured application setting `EMAIL_PROVIDER`.
    """
    name = (provider_name or get_settings().EMAIL_PROVIDER or "mock").lower()

    if name == "smtp":
        return SmtpEmailProvider()
    elif name == "resend":
        return ResendEmailProvider()
    elif name == "mock":
        return MockEmailProvider()
    else:
        raise ValueError(f"Unsupported email provider: '{name}'. Supported: 'mock', 'smtp', 'resend'")
