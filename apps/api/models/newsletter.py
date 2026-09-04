"""
AstroOS — Newsletter & Transit Digest Subscriber Model
======================================================
Stores newsletter subscriptions, double opt-in tokens, frequency preferences,
and optional linkage to registered user profiles & default birth charts.
"""

from __future__ import annotations

import secrets
import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


def _generate_unsubscribe_token() -> str:
    return secrets.token_urlsafe(32)


class NewsletterSubscriberModel(AstroBase):
    """Newsletter subscriber record for monthly ingress & personalized transit digests."""

    __tablename__ = "newsletter_subscribers"

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Frequency: "monthly" (default), "weekly", "ingress_only"
    frequency: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="monthly",
        server_default="'monthly'",
    )

    unsubscribe_token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=_generate_unsubscribe_token,
        unique=True,
        index=True,
    )
