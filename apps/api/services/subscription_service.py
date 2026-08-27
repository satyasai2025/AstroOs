"""
AstroOS — Subscription Service (Phase 5)

Owns the subscription **lifecycle state machine** and its append-only history.
Everything payment/billing-related is explicitly out of scope (later phases;
see architecture/PHASE5_IMPLEMENTATION_REPORT.md).

State machine (4 statuses; architecture decision recorded in the Phase 5 report):

    TRIALING ──→ ACTIVE ──→ PAST_DUE_CANCELLED ──→ EXPIRED (terminal)
        │            │               │
        └────────────┴───────────────┴───→ EXPIRED

* EXPIRED is absorbing in Phase 5 (one-way door); reactivation means creating
  a NEW subscription row once payment exists (later phase).
* Every accepted transition appends one ``subscription_events`` row and bumps
  ``event_version`` (optimistic-concurrency counter).

Grace semantics consumed by EntitlementService.resolve_user_plan:
  ACTIVE / TRIALING / PAST_DUE_CANCELLED keep paid-plan grants (past-due is
  the grace window); EXPIRED drops them back to FREE.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Mapping, Optional
from uuid import UUID

from apps.api.domain.user import User
from apps.api.models.subscription import (
    SubscriptionEventModel,
    SubscriptionEventType,
    SubscriptionModel,
    SubscriptionStatus,
)
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.repositories.subscription_repository import SubscriptionRepository
from apps.api.schemas.subscription import SubscriptionResponse, TransitionResult


class InvalidTransitionError(ValueError):
    """Raised when a lifecycle transition violates the state machine."""


class SubscriptionService:
    """Application service over SubscriptionRepository."""

    #: Allowed lifecycle edges; keys/values are ``SubscriptionStatus.value``.
    ALLOWED_TRANSITIONS: Mapping[str, frozenset[str]] = {
        SubscriptionStatus.TRIALING.value: frozenset({
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.PAST_DUE_CANCELLED.value,
            SubscriptionStatus.EXPIRED.value,
        }),
        SubscriptionStatus.ACTIVE.value: frozenset({
            SubscriptionStatus.PAST_DUE_CANCELLED.value,
            SubscriptionStatus.EXPIRED.value,
        }),
        SubscriptionStatus.PAST_DUE_CANCELLED.value: frozenset({
            SubscriptionStatus.ACTIVE.value,   # cure within the grace window
            SubscriptionStatus.EXPIRED.value,
        }),
        # Terminal — expiration is final for Phase 5.
        SubscriptionStatus.EXPIRED.value: frozenset({}),
    }

    #: Event recorded for each legal (from_value, to_value) edge.
    TRANSITION_EVENTS: Mapping[tuple[str, str], str] = {
        (SubscriptionStatus.TRIALING.value, SubscriptionStatus.ACTIVE.value):
            SubscriptionEventType.ACTIVATED,
        (SubscriptionStatus.TRIALING.value, SubscriptionStatus.PAST_DUE_CANCELLED.value):
            SubscriptionEventType.CANCELLED,
        (SubscriptionStatus.TRIALING.value, SubscriptionStatus.EXPIRED.value):
            SubscriptionEventType.EXPIRED,
        (SubscriptionStatus.ACTIVE.value, SubscriptionStatus.PAST_DUE_CANCELLED.value):
            SubscriptionEventType.CANCELLED,
        (SubscriptionStatus.ACTIVE.value, SubscriptionStatus.EXPIRED.value):
            SubscriptionEventType.EXPIRED,
        (SubscriptionStatus.PAST_DUE_CANCELLED.value, SubscriptionStatus.ACTIVE.value):
            SubscriptionEventType.ACTIVATED,
        (SubscriptionStatus.PAST_DUE_CANCELLED.value, SubscriptionStatus.EXPIRED.value):
            SubscriptionEventType.EXPIRED,
    }

    def __init__(self, db) -> None:
        self._db = db

    # ── Queries ───────────────────────────────────────────────────────────────

    async def get_by_id(self, subscription_id: UUID) -> Optional[SubscriptionModel]:
        return await SubscriptionRepository.get_by_id(self._db, subscription_id)

    async def get_for_user(self, user: User) -> Optional[SubscriptionModel]:
        return await SubscriptionRepository.get_by_user(self._db, user.id.value)

    async def get_history(self, subscription_id: UUID):
        return await SubscriptionRepository.get_history(self._db, subscription_id)

    # ── Commands ──────────────────────────────────────────────────────────────

    async def create(
        self,
        user: User,
        plan_code: str,
        *,
        trial_end: datetime | None = None,
        current_period_end: datetime | None = None,
    ) -> SubscriptionModel:
        """Create the initial subscription row for a user (≤1 per user)."""
        existing = await SubscriptionRepository.get_by_user(self._db, user.id.value)
        if existing is not None:
            raise ValueError(
                f"User already has a subscription (status={existing.status}). "
                "Use lifecycle transitions instead of creating another row."
            )
        plan = await PlanRepository.get_by_code(self._db, plan_code.upper())
        if plan is None:
            raise LookupError(f"Unknown plan code '{plan_code}'.")

        initial_status = (
            SubscriptionStatus.TRIALING.value
            if trial_end is not None
            else SubscriptionStatus.ACTIVE.value
        )
        return await SubscriptionRepository.create_subscription(
            self._db,
            user_id=user.id.value,
            plan_id=plan.id,
            status_value=initial_status,
            current_period_end=current_period_end,
            trial_end=trial_end,
        )

    async def transition(
        self,
        subscription_id: UUID,
        target_status: str,
        *,
        reason: str | None = None,
        occurred_at: datetime | None = None,
    ) -> TransitionResult:
        """
        Apply one state-machine transition with an appended history event and
        an ``event_version`` bump. Raises InvalidTransitionError for unknown
        targets, duplicates, or illegal edges; LookupError if unknown id.
        """
        sub, previous, target, event_type = await self._apply_transition(
            subscription_id, target_status, reason=reason, occurred_at=occurred_at
        )
        return TransitionResult(
            subscription=SubscriptionResponse.model_validate(sub),
            previous_status=previous,
            new_status=target,
            event_type=event_type,
        )

    async def _apply_transition(
        self,
        subscription_id: UUID,
        target_status: str,
        *,
        reason: str | None = None,
        occurred_at: datetime | None = None,
    ) -> tuple[SubscriptionModel, str, str, str]:
        """Validate + persist one edge. Returns the ORM row and the edge taken."""
        sub = await SubscriptionRepository.get_by_id(self._db, subscription_id)
        if sub is None:
            raise LookupError(f"Subscription {subscription_id} not found.")

        normalized = (target_status or "").strip().lower()
        try:
            target = SubscriptionStatus(normalized)
        except ValueError:
            raise InvalidTransitionError(
                f"Unknown subscription status '{target_status}'. Valid: "
                f"{[s.value for s in SubscriptionStatus]}"
            ) from None

        previous = SubscriptionStatus(sub.status)
        if previous == target:
            raise InvalidTransitionError(
                f"Subscription already in status '{target.value}'."
            )
        if target.value not in self.ALLOWED_TRANSITIONS[sub.status]:
            raise InvalidTransitionError(
                f"Illegal transition {previous.value} -> {target.value}. "
                f"Allowed from '{sub.status}': "
                f"{sorted(self.ALLOWED_TRANSITIONS[sub.status])}"
            )

        event_type = self.TRANSITION_EVENTS[(previous.value, target.value)]
        now = occurred_at or datetime.now(timezone.utc)

        updates: dict = {
            "status": target.value,
            "event_version": (sub.event_version or 0) + 1,
        }
        if target is SubscriptionStatus.PAST_DUE_CANCELLED:
            updates["cancel_at_period_end"] = True
            updates["cancelled_at"] = now
        if target is SubscriptionStatus.EXPIRED:
            updates["ended_at"] = now

        await SubscriptionRepository.update_fields(sub, **updates)
        await SubscriptionRepository.append_event(
            self._db,
            subscription=sub,
            event_type=event_type,
            from_status=previous.value,
            to_status=target.value,
            payload_json=reason,
            commit=False,
        )
        await SubscriptionRepository.save(self._db, sub)

        return sub, previous.value, target.value, event_type.value

    # ── Grace / expiry policy (pure, testable) ────────────────────────────────

    @staticmethod
    def _clamp_to_utc(dt: datetime) -> datetime:
        """Naive datetimes are treated as UTC and made timezone-aware."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @classmethod
    def compute_effective_status(
        cls,
        status_value: str,
        *,
        current_period_end: datetime | None,
        now: datetime | None = None,
        grace_days: int = 3,
    ) -> str:
        """
        Pure function: fold period-expiry + grace window onto the stored status.

          * ACTIVE/TRIALING/PAST_DUE_CANCELLED whose ``current_period_end`` has
            lapsed beyond ``grace_days`` ⇒ EXPIRED.
          * Within the grace window PAST_DUE_CANCELLED still keeps paid-plan
            grants; once the window lapses the fold becomes EXPIRED.
          * EXPIRED is terminal; ``current_period_end is None`` means no clock.
        """
        now = now or datetime.now(timezone.utc)
        if current_period_end is None:
            return status_value
        if status_value == SubscriptionStatus.EXPIRED.value:
            return status_value

        period_end = cls._clamp_to_utc(current_period_end)
        if now < period_end:
            return status_value
        grace_end = period_end + timedelta(days=grace_days)
        if now >= grace_end:
            return SubscriptionStatus.EXPIRED.value
        if status_value == SubscriptionStatus.PAST_DUE_CANCELLED.value:
            return SubscriptionStatus.EXPIRED.value
        return status_value

    @classmethod
    def effective_status(
        cls,
        sub: Optional[SubscriptionModel],
        now: datetime | None = None,
        grace_days: int = 3,
    ) -> Optional[str]:
        """Convenience wrapper over :meth:`compute_effective_status` for a row."""
        if sub is None:
            return None
        return cls.compute_effective_status(
            sub.status,
            current_period_end=sub.current_period_end,
            now=now,
            grace_days=grace_days,
        )

    # ── Conveniences ──────────────────────────────────────────────────────────

    # These return the ORM row (not the response schema) — callers inside the
    # application layer keep working against SubscriptionModel.

    async def activate(
        self, subscription_id: UUID, *, reason: str | None = None
    ) -> SubscriptionModel:
        """TRIALING → ACTIVE or PAST_DUE_CANCELLED → ACTIVE (cure)."""
        sub, *_ = await self._apply_transition(
            subscription_id, SubscriptionStatus.ACTIVE.value, reason=reason
        )
        return sub

    async def cancel(
        self, subscription_id: UUID, *, reason: str | None = None
    ) -> SubscriptionModel:
        """ACTIVE/TRIALING → PAST_DUE_CANCELLED (grace window starts)."""
        sub, *_ = await self._apply_transition(
            subscription_id,
            SubscriptionStatus.PAST_DUE_CANCELLED.value,
            reason=reason,
        )
        return sub

    async def expire(
        self, subscription_id: UUID, *, reason: str | None = None
    ) -> SubscriptionModel:
        """Any non-terminal status → EXPIRED (terminal for Phase 5)."""
        sub, *_ = await self._apply_transition(
            subscription_id, SubscriptionStatus.EXPIRED.value, reason=reason
        )
        return sub

