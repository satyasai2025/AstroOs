"""
AstroOS — SMTP Email Delivery Provider (Phase 7)

Standard SMTP delivery with TLS/STARTTLS executed off the event loop via asyncio.to_thread.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
import uuid
from email.message import EmailMessage
from typing import Any, Optional

from apps.api.config import get_settings
from apps.api.services.notification.providers.base import (
    EmailDeliveryProviderBase,
    EmailDeliveryResult,
)

logger = logging.getLogger(__name__)


class SmtpEmailProvider(EmailDeliveryProviderBase):
    """Outbound email provider using standard SMTP."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        from_email: Optional[str] = None,
    ):
        settings = get_settings()
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.username = username or settings.SMTP_USERNAME
        self.password = password or settings.SMTP_PASSWORD
        self.use_tls = use_tls if use_tls is not None else settings.SMTP_USE_TLS
        self.default_from = from_email or settings.EMAIL_DEFAULT_FROM

    @property
    def provider_name(self) -> str:
        return "smtp"

    def _send_sync(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: str,
        reply_to: Optional[str] = None,
    ) -> str:
        if not self.host:
            raise ValueError("SMTP_HOST is not configured.")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        if reply_to:
            msg["Reply-To"] = reply_to

        msg.set_content(text_body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username and self.password:
                smtp.login(self.username, self.password)
            smtp.send_message(msg)

        return f"smtp_{uuid.uuid4().hex[:16]}"

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
        sender = from_email or self.default_from
        if not self.host:
            logger.warning("[SMTP] Host unset — logging instead of emailing: to=%s subj=%s", to_email, subject)
            return EmailDeliveryResult(
                success=True,
                provider=self.provider_name,
                message_id=f"logged_smtp_{uuid.uuid4().hex[:12]}",
                status="sent",
            )

        try:
            msg_id = await asyncio.to_thread(
                self._send_sync,
                to_email,
                subject,
                html_body,
                text_body,
                sender,
                reply_to,
            )
            return EmailDeliveryResult(
                success=True,
                provider=self.provider_name,
                message_id=msg_id,
                status="sent",
            )
        except Exception as e:
            logger.error("[SMTP] Delivery failed to %s: %s", to_email, str(e))
            return EmailDeliveryResult(
                success=False,
                provider=self.provider_name,
                error_message=str(e),
                status="failed",
            )
