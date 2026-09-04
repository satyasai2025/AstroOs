"""
AstroOS — Payment Gateway ORM Models (Phase 6)

Multi-provider payment data models supporting:
  - ``payments``               : transaction/receipt records (Stripe, Razorpay, Mock)
  - ``payment_customers``      : mapping of internal user ID to gateway customer ID
  - ``payment_webhook_events`` : append-only audit & deduplication log for webhooks
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
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


class PaymentStatus(str, Enum):
    """Status of a payment transaction."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentProviderType(str, Enum):
    """Supported payment gateway providers."""

    MOCK = "mock"
    STRIPE = "stripe"
    RAZORPAY = "razorpay"


class PaymentModel(AstroBase):
    """
    Individual payment or checkout transaction record.
    """

    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=PaymentProviderType.MOCK.value,
        index=True,
    )
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        # NOTE: no index=True here — a composite index ix_payments_provider_payment_id
        # on (provider, provider_payment_id) is declared in __table_args__ below.
        # index=True here would auto-generate the SAME index name and collide with
        # __table_args__ (DuplicateTableError during create_all).
    )
    provider_order_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Stored in smallest currency unit (e.g. cents, paise)
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    base_amount: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    tax_amount: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    tax_rate: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'INR'"),
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=PaymentStatus.PENDING.value,
        index=True,
    )
    payment_method: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    receipt_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    payload_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_payments_user_status", "user_id", "status"),
        Index("ix_payments_provider_payment_id", "provider", "provider_payment_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentModel id={self.id} user_id={self.user_id} "
            f"provider={self.provider} amount={self.amount} {self.currency} status={self.status}>"
        )


class PaymentCustomerModel(AstroBase):
    """
    Mapping between AstroOS internal user and payment gateway customer.
    """

    __tablename__ = "payment_customers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    provider_customer_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index("ux_payment_customers_user_provider", "user_id", "provider", unique=True),
        Index("ix_payment_customers_provider_id", "provider", "provider_customer_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentCustomerModel id={self.id} user_id={self.user_id} "
            f"provider={self.provider} customer_id={self.provider_customer_id}>"
        )


class PaymentWebhookEventModel(AstroBase):
    """
    Immutable audit & idempotency log for incoming webhook events.
    """

    __tablename__ = "payment_webhook_events"

    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    provider_event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'processed'"),
    )
    payload_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ux_payment_webhooks_provider_event", "provider", "provider_event_id", unique=True),
        Index("ix_payment_webhooks_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentWebhookEventModel id={self.id} provider={self.provider} "
            f"event_id={self.provider_event_id} type={self.event_type} status={self.status}>"
        )
