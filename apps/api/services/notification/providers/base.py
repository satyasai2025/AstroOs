"""
AstroOS — Email Delivery Provider Interface (Phase 7)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class EmailDeliveryResult:
    """Standardized result of attempting to send an email."""
    success: bool
    provider: str
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    status: str = "sent"


class EmailDeliveryProviderBase(ABC):
    """Abstract interface for transactional email delivery backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the delivery provider: 'mock', 'smtp', 'resend'."""
        pass

    @abstractmethod
    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EmailDeliveryResult:
        """Deliver a transactional email."""
        pass
