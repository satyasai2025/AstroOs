"""
AstroOS — Email Delivery Providers Package (Phase 7)
"""

from apps.api.services.notification.providers.base import (
    EmailDeliveryProviderBase,
    EmailDeliveryResult,
)
from apps.api.services.notification.providers.factory import get_email_provider
from apps.api.services.notification.providers.mock_provider import MockEmailProvider
from apps.api.services.notification.providers.resend_provider import ResendEmailProvider
from apps.api.services.notification.providers.smtp_provider import SmtpEmailProvider

__all__ = [
    "EmailDeliveryProviderBase",
    "EmailDeliveryResult",
    "get_email_provider",
    "MockEmailProvider",
    "SmtpEmailProvider",
    "ResendEmailProvider",
]
