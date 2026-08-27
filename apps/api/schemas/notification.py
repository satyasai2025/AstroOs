"""AstroOS — Notification & Email Schemas (Phase 7)"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

EmailDeliveryStatusLiteral = Literal["queued", "sent", "failed", "delivered", "bounced"]
EmailProviderLiteral = Literal["mock", "smtp", "resend"]


# ── Preferences ───────────────────────────────────────────────────────────────


class NotificationPreferenceResponse(BaseModel):
    """User notification settings."""
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    billing_notifications: bool = True  # Mandatory transactional
    security_alerts: bool = True        # Mandatory transactional
    quota_warnings: bool = True         # Configurable
    product_updates: bool = False       # Configurable


class NotificationPreferenceUpdate(BaseModel):
    """Updatable notification preferences (mandatory ones cannot be disabled)."""
    quota_warnings: Optional[bool] = None
    product_updates: Optional[bool] = None


# ── Email Logs & History ──────────────────────────────────────────────────────


class EmailLogResponse(BaseModel):
    """Single outbound email log entry."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    recipient_email: str
    template_name: str
    subject: str
    provider: EmailProviderLiteral
    provider_message_id: Optional[str] = None
    status: EmailDeliveryStatusLiteral
    attempts: int
    idempotency_key: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime


class EmailHistoryResponse(BaseModel):
    """List of email log records for user or admin auditing."""
    items: list[EmailLogResponse]
    total: int


# ── Test Email & Admin ───────────────────────────────────────────────────────


class TestEmailRequest(BaseModel):
    """Admin request to send a test transactional email."""
    to_email: str = Field(min_length=5, max_length=320)
    template_name: str = Field(min_length=2, max_length=64)
    context: Optional[dict[str, Any]] = None


class TestEmailResponse(BaseModel):
    """Outcome of test email dispatch."""
    success: bool
    template_name: str
    recipient: str
    provider: str
    message: str
    log_id: Optional[uuid.UUID] = None
