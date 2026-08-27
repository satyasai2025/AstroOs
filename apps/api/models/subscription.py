"""
AstroOS — Subscription ORM Models (Phase 5)

Separate table pair for subscription lifecycle management:
  - ``subscriptions``       : one row per user (lifecycle state machine)
  - ``subscription_events`` : append-only lifecycle/history log

``user_plans`` (Phase 2) remains the plan-assignment table that
EntitlementService reads; ``subscriptions`` tracks lifecycle status and an
optional expiry used by grace enforcement.

Phase 5 explicitly does NOT include: payment gateways, invoicing, billing
cycles, emails, or UI.
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


class SubscriptionStatus(str, Enum):
    """Lifecycle states of a subscription."""

    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE_CANCELLED = "past_due_cancelled"
    EXPIRED = "expired"


#: Statuses treated as "active" by repository-level queries (e.g. one active
#: row per user). NOTE: PAST_DUE_CANCELLED still grants paid-plan entitlements
#: within its grace window — that granting decision is made by
#: EntitlementService via SubscriptionService.effective_status, not here.
ACTIVE_STATUSES = (SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE)


class SubscriptionEventType(str, Enum):
    """Types recorded in the append-only subscription history."""

    CREATED = "created"
    TRIAL_STARTED = "trial_started"
    ACTIVATED = "activated"
    PAST_DUE_MARKED = "past_due_marked"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    RENEWED = "renewed"
    PERIOD_EXTENDED = "period_extended"


class SubscriptionModel(AstroBase):
    """
    One row per user's subscription lifecycle record.

    The repository treats this as ≤1 row per user (unique index); a cancelled
    or expired row is reused/re-activated instead of duplicated so that
    ``get_by_user`` can rely on scalar semantics.
    """

    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        # Covered by the unique index ux_subscriptions_user_id below.
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id"),
        nullable=False,
        index=True,
    )
    # Stored as plain VARCHAR values ("active", ...) — see SubscriptionStatus.
    status: Mapped[str] = mapped_column(
        String(32), nullable=False,
        server_default=SubscriptionStatus.ACTIVE.value,
    )
    # Optimistic-concurrency counter bumped on every lifecycle transition.
    event_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"),
    )

    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(),
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    trial_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"),
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ux_subscriptions_user_id", "user_id", unique=True),
        Index("ix_subscriptions_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<SubscriptionModel id={self.id} user_id={self.user_id} "
            f"plan_id={self.plan_id} status={self.status}>"
        )


class SubscriptionEventModel(AstroBase):
    """Immutable audit trail entry: one lifecycle transition."""

    __tablename__ = "subscription_events"

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Many-to-one; declared here only so ``SubscriptionEventModel(subscription=s)``
    # works. No back_populates → frozen User/Plan models stay untouched.
    subscription: Mapped[SubscriptionModel] = relationship("SubscriptionModel")

    __table_args__ = (
        Index(
            "ix_subscription_events_sub_created",
            "subscription_id",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SubscriptionEventModel id={self.id} sub={self.subscription_id} "
            f"type={self.event_type} {self.from_status}->{self.to_status}>"
        )
