"""AstroOS — Subscription Schemas (Phase 5)"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SubscriptionStatusLiteral = Literal["active", "trialing", "past_due_cancelled", "expired"]
SubscriptionEventTypeLiteral = Literal[
    "created",
    "trial_started",
    "activated",
    "past_due_marked",
    "cancelled",
    "expired",
    "renewed",
    "period_extended",
]


# ── Requests ──────────────────────────────────────────────────────────────────


class SubscriptionCreate(BaseModel):
    """Admin request body for creating a subscription for a user."""
    user_id: uuid.UUID
    plan_code: str = Field(min_length=2, max_length=50)
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None


class SubscriptionTransition(BaseModel):
    """Request body for manual status transition (admin tooling only)."""
    target_status: SubscriptionStatusLiteral
    reason: Optional[str] = Field(default=None, max_length=500)


# ── Responses ────────────────────────────────────────────────────────────────


class SubscriptionResponse(BaseModel):
    """Single subscription record with its current state."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    plan_id: uuid.UUID
    status: SubscriptionStatusLiteral
    event_version: int
    current_period_start: datetime
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SubscriptionEventResponse(BaseModel):
    """One entry in the append-only subscription history log."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID
    event_type: SubscriptionEventTypeLiteral
    from_status: Optional[SubscriptionStatusLiteral] = None
    to_status: Optional[SubscriptionStatusLiteral] = None
    payload_json: Optional[str] = None
    created_at: datetime


class SubscriptionHistoryResponse(BaseModel):
    """Full ordered event history for one subscription."""
    subscription_id: uuid.UUID
    events: list[SubscriptionEventResponse]


class RenewRequest(BaseModel):
    """Request body for extending a subscription's current period."""
    current_period_end: Optional[datetime] = None


class TransitionResult(BaseModel):
    """Result of a successful lifecycle transition applied by the service."""
    subscription: SubscriptionResponse
    previous_status: SubscriptionStatusLiteral
    new_status: SubscriptionStatusLiteral
    event_type: SubscriptionEventTypeLiteral