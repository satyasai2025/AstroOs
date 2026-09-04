"""
AstroOS — Resend Email Delivery Provider (Phase 7)

Direct HTTP REST API delivery via Resend.
"""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request
import uuid
from typing import Any, Optional

from apps.api.config import get_settings
from apps.api.services.notification.providers.base import (
    EmailDeliveryProviderBase,
    EmailDeliveryResult,
)

logger = logging.getLogger(__name__)


class ResendEmailProvider(EmailDeliveryProviderBase):
    """Outbound email provider using Resend REST API."""

    API_URL = "https://api.resend.com/emails"

    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.RESEND_API_KEY
        self.default_from = from_email or settings.EMAIL_DEFAULT_FROM

    @property
    def provider_name(self) -> str:
        return "resend"

    def _send_sync(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: str,
        reply_to: Optional[str] = None,
    ) -> str:
        if not self.api_key:
            raise ValueError("RESEND_API_KEY is not configured.")

        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        }
        if reply_to:
            payload["reply_to"] = reply_to

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.API_URL,
            data=data_bytes,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AstroOS-Email/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8")
            res_json = json.loads(resp_body)
            return res_json.get("id") or f"resend_{uuid.uuid4().hex[:12]}"

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
        if not self.api_key:
            logger.warning("[Resend] API key unset — simulated send: to=%s subj=%s", to_email, subject)
            return EmailDeliveryResult(
                success=True,
                provider=self.provider_name,
                message_id=f"sim_resend_{uuid.uuid4().hex[:12]}",
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
            logger.error("[Resend] Delivery failed to %s: %s", to_email, str(e))
            return EmailDeliveryResult(
                success=False,
                provider=self.provider_name,
                error_message=str(e),
                status="failed",
            )
