"""
AstroOS — Notification & Email ORM Models (Phase 7)

Models for:
  - ``email_logs``                : append-only audit & deduplication log for outbound emails
  - ``notification_preferences``  : user notification opt-in/opt-out settings
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


class EmailDeliveryStatus(str, Enum):
    """Lifecycle status of an outbound email."""

    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    BOUNCED = "bounced"


class EmailLogModel(AstroBase):
    """
    Audit log entry for an outbound transactional email.
    """

    __tablename__ = "email_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    recipient_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        index=True,
    )
    template_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'mock'"),
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=EmailDeliveryStatus.QUEUED.value,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    payload_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ux_email_logs_idempotency_key", "idempotency_key", unique=True),
        Index("ix_email_logs_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmailLogModel id={self.id} to={self.recipient_email} "
            f"template={self.template_name} status={self.status}>"
        )


class NotificationPreferenceModel(AstroBase):
    """
    User settings for notification channels and categories.

    Note: Mandatory transactional categories (billing, security) cannot be
    disabled to ensure system integrity and compliance.
    """

    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Mandatory transactional — opt-out not permitted
    billing_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    security_alerts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # Configurable notifications
    quota_warnings: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    product_updates: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    __table_args__ = (
        Index("ux_notification_preferences_user_id", "user_id", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationPreferenceModel id={self.id} user_id={self.user_id} "
            f"quota={self.quota_warnings} product={self.product_updates}>"
        )
