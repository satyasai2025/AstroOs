"""
AstroOS — Mock Email Delivery Provider (Phase 7)

Deterministic in-memory email provider for development, testing, and offline environments.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from apps.api.services.notification.providers.base import (
    EmailDeliveryProviderBase,
    EmailDeliveryResult,
)

logger = logging.getLogger(__name__)


@dataclass
class SentMockEmail:
    id: str
    to_email: str
    subject: str
    html_body: str
    text_body: str
    from_email: str
    sent_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class MockEmailProvider(EmailDeliveryProviderBase):
    """Captures and stores all outbound emails in memory without sending network traffic."""

    _sent_emails: list[SentMockEmail] = []

    def __init__(self, should_fail: bool = False, failure_error: str = "Simulated delivery failure"):
        self.should_fail = should_fail
        self.failure_error = failure_error

    @property
    def provider_name(self) -> str:
        return "mock"

    @classmethod
    def get_sent_emails(cls) -> list[SentMockEmail]:
        return list(cls._sent_emails)

    @classmethod
    def clear_sent_emails(cls) -> None:
        cls._sent_emails.clear()

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
        if self.should_fail:
            logger.warning("[MockEmailProvider] Simulated email failure to %s: %s", to_email, self.failure_error)
            return EmailDeliveryResult(
                success=False,
                provider=self.provider_name,
                error_message=self.failure_error,
                status="failed",
            )

        msg_id = f"mock_msg_{uuid.uuid4().hex[:16]}"
        record = SentMockEmail(
            id=msg_id,
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=from_email or "noreply@astroos.local",
            sent_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        self._sent_emails.append(record)
        logger.info("[MockEmailProvider] Email delivered to %s (subject='%s', msg_id=%s)", to_email, subject, msg_id)

        return EmailDeliveryResult(
            success=True,
            provider=self.provider_name,
            message_id=msg_id,
            status="sent",
        )
