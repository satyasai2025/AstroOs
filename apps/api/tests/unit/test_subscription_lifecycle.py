"""
AstroOS — Phase 5 subscription lifecycle tests.

Covers the state machine, its history log, and the grace-window fold that
EntitlementService relies on to demote a lapsed user back to FREE.

No live database: the repository is replaced with an in-memory stub, mirroring
the _RepoStub convention already used by test_plan_entitlement.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from apps.api.models.subscription import (
    SubscriptionEventType,
    SubscriptionStatus,
)
from apps.api.services.subscription_service import (
    InvalidTransitionError,
    SubscriptionService,
)

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


# ── Fixtures / stubs ─────────────────────────────────────────────────────────


def _sub(status=SubscriptionStatus.ACTIVE.value, *, period_end=None, version=1):
    """A stand-in for SubscriptionModel carrying only the fields the service touches."""
    return SimpleNamespace(
        id=uuid4(),
        # AstroBase audit columns — SubscriptionResponse requires them.
        created_at=NOW - timedelta(days=30),
        updated_at=NOW,
        deleted_at=None,
        user_id=uuid4(),
        plan_id=uuid4(),
        status=status,
        event_version=version,
        current_period_start=NOW - timedelta(days=30),
        current_period_end=period_end,
        trial_end=None,
        cancel_at_period_end=False,
        cancelled_at=None,
        ended_at=None,
    )


class _SubRepoStub:
    """In-memory stand-in for SubscriptionRepository."""

    def __init__(self, sub=None):
        self.sub = sub
        self.events: list[SimpleNamespace] = []
        self.saved = 0

    async def get_by_id(self, db, subscription_id):
        if self.sub is not None and self.sub.id == subscription_id:
            return self.sub
        return None

    async def get_by_user(self, db, user_id):
        return self.sub

    async def get_latest_for_user(self, db, user_id):
        return self.sub

    async def get_history(self, db, subscription_id):
        return list(self.events)

    async def create_subscription(self, db, **kwargs):
        self.sub = _sub(status=kwargs.get("status_value", "active"))
        return self.sub

    async def update_fields(self, sub, **fields):
        for key, value in fields.items():
            setattr(sub, key, value)
        return sub

    async def save(self, db, sub):
        self.saved += 1
        return sub

    async def append_event(self, db, *, subscription, event_type,
                           to_status=None, from_status=None,
                           payload_json=None, commit=True):
        event = SimpleNamespace(
            subscription_id=subscription.id,
            event_type=event_type.value,
            from_status=from_status,
            to_status=to_status,
            payload_json=payload_json,
        )
        self.events.append(event)
        return event


@pytest.fixture
def repo(monkeypatch):
    stub = _SubRepoStub()
    monkeypatch.setattr(
        "apps.api.services.subscription_service.SubscriptionRepository", stub
    )
    return stub


# ── State-machine shape ──────────────────────────────────────────────────────


def test_all_statuses_have_a_transition_entry():
    assert set(SubscriptionService.ALLOWED_TRANSITIONS) == {
        s.value for s in SubscriptionStatus
    }


def test_expired_is_terminal():
    assert (
        SubscriptionService.ALLOWED_TRANSITIONS[SubscriptionStatus.EXPIRED.value]
        == frozenset()
    )


def test_every_legal_edge_has_an_event_type():
    """A legal edge with no TRANSITION_EVENTS entry would KeyError at runtime."""
    for source, targets in SubscriptionService.ALLOWED_TRANSITIONS.items():
        for target in targets:
            assert (source, target) in SubscriptionService.TRANSITION_EVENTS, (
                f"missing event mapping for {source} -> {target}"
            )


def test_no_event_mapping_for_an_illegal_edge():
    for (source, target) in SubscriptionService.TRANSITION_EVENTS:
        assert target in SubscriptionService.ALLOWED_TRANSITIONS[source]


def test_every_status_is_reachable_from_trialing():
    """Guards against a status that can be stored but never legally entered."""
    seen = {SubscriptionStatus.TRIALING.value}
    frontier = [SubscriptionStatus.TRIALING.value]
    while frontier:
        current = frontier.pop()
        for target in SubscriptionService.ALLOWED_TRANSITIONS[current]:
            if target not in seen:
                seen.add(target)
                frontier.append(target)
    assert seen == {s.value for s in SubscriptionStatus}


# ── Transitions ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_starts_the_grace_window(repo):
    repo.sub = _sub(SubscriptionStatus.ACTIVE.value)
    svc = SubscriptionService(None)

    result = await svc.transition(
        repo.sub.id, SubscriptionStatus.PAST_DUE_CANCELLED.value, reason="user asked"
    )

    assert result.previous_status == SubscriptionStatus.ACTIVE.value
    assert result.new_status == SubscriptionStatus.PAST_DUE_CANCELLED.value
    assert result.event_type == SubscriptionEventType.CANCELLED.value
    assert repo.sub.cancel_at_period_end is True
    assert repo.sub.cancelled_at is not None
    assert repo.sub.ended_at is None


@pytest.mark.asyncio
async def test_expire_stamps_ended_at(repo):
    repo.sub = _sub(SubscriptionStatus.ACTIVE.value)
    svc = SubscriptionService(None)

    await svc.expire(repo.sub.id, reason="period over")

    assert repo.sub.status == SubscriptionStatus.EXPIRED.value
    assert repo.sub.ended_at is not None


@pytest.mark.asyncio
async def test_transition_bumps_event_version_and_appends_history(repo):
    repo.sub = _sub(SubscriptionStatus.TRIALING.value, version=4)
    svc = SubscriptionService(None)

    await svc.activate(repo.sub.id)

    assert repo.sub.event_version == 5
    assert [e.event_type for e in repo.events] == [
        SubscriptionEventType.ACTIVATED.value
    ]
    assert repo.events[0].from_status == SubscriptionStatus.TRIALING.value
    assert repo.events[0].to_status == SubscriptionStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_past_due_can_be_cured_back_to_active(repo):
    repo.sub = _sub(SubscriptionStatus.PAST_DUE_CANCELLED.value)
    svc = SubscriptionService(None)

    await svc.activate(repo.sub.id, reason="payment recovered")

    assert repo.sub.status == SubscriptionStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_expired_cannot_be_reactivated(repo):
    repo.sub = _sub(SubscriptionStatus.EXPIRED.value)
    svc = SubscriptionService(None)

    with pytest.raises(InvalidTransitionError):
        await svc.activate(repo.sub.id)


@pytest.mark.asyncio
async def test_transition_to_same_status_is_rejected(repo):
    repo.sub = _sub(SubscriptionStatus.ACTIVE.value)
    svc = SubscriptionService(None)

    with pytest.raises(InvalidTransitionError):
        await svc.activate(repo.sub.id)


@pytest.mark.asyncio
async def test_unknown_target_status_is_rejected(repo):
    repo.sub = _sub(SubscriptionStatus.ACTIVE.value)
    svc = SubscriptionService(None)

    with pytest.raises(InvalidTransitionError):
        await svc.transition(repo.sub.id, "cancelled_maybe")


@pytest.mark.asyncio
async def test_unknown_subscription_id_raises_lookup_error(repo):
    repo.sub = _sub()
    svc = SubscriptionService(None)

    with pytest.raises(LookupError):
        await svc.transition(uuid4(), SubscriptionStatus.EXPIRED.value)


@pytest.mark.asyncio
async def test_a_rejected_transition_writes_no_history(repo):
    repo.sub = _sub(SubscriptionStatus.EXPIRED.value)
    svc = SubscriptionService(None)

    with pytest.raises(InvalidTransitionError):
        await svc.activate(repo.sub.id)

    assert repo.events == []
    assert repo.saved == 0
    assert repo.sub.event_version == 1


# ── Grace / expiry fold (pure) ───────────────────────────────────────────────


def test_no_period_end_means_no_clock():
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.ACTIVE.value, current_period_end=None, now=NOW
        )
        == SubscriptionStatus.ACTIVE.value
    )


def test_active_inside_its_period_is_unchanged():
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.ACTIVE.value,
            current_period_end=NOW + timedelta(days=1),
            now=NOW,
        )
        == SubscriptionStatus.ACTIVE.value
    )


def test_active_inside_the_grace_window_still_grants():
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.ACTIVE.value,
            current_period_end=NOW - timedelta(days=1),
            now=NOW,
            grace_days=3,
        )
        == SubscriptionStatus.ACTIVE.value
    )


def test_active_past_the_grace_window_folds_to_expired():
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.ACTIVE.value,
            current_period_end=NOW - timedelta(days=4),
            now=NOW,
            grace_days=3,
        )
        == SubscriptionStatus.EXPIRED.value
    )


def test_grace_boundary_is_exclusive_at_exactly_the_window_end():
    period_end = NOW - timedelta(days=3)
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.ACTIVE.value,
            current_period_end=period_end,
            now=NOW,
            grace_days=3,
        )
        == SubscriptionStatus.EXPIRED.value
    )


def test_past_due_folds_to_expired_once_the_period_ends():
    """past_due keeps grants only while the period itself is still running."""
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.PAST_DUE_CANCELLED.value,
            current_period_end=NOW - timedelta(hours=1),
            now=NOW,
            grace_days=3,
        )
        == SubscriptionStatus.EXPIRED.value
    )


def test_past_due_before_period_end_still_grants():
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.PAST_DUE_CANCELLED.value,
            current_period_end=NOW + timedelta(days=2),
            now=NOW,
            grace_days=3,
        )
        == SubscriptionStatus.PAST_DUE_CANCELLED.value
    )


def test_expired_stays_expired_even_with_a_future_period_end():
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.EXPIRED.value,
            current_period_end=NOW + timedelta(days=30),
            now=NOW,
        )
        == SubscriptionStatus.EXPIRED.value
    )


def test_naive_period_end_is_treated_as_utc():
    """A naive datetime must not raise when compared against an aware `now`."""
    assert (
        SubscriptionService.compute_effective_status(
            SubscriptionStatus.ACTIVE.value,
            current_period_end=datetime(2026, 8, 20, 12, 0),
            now=NOW,
            grace_days=3,
        )
        == SubscriptionStatus.EXPIRED.value
    )


def test_effective_status_of_none_is_none():
    assert SubscriptionService.effective_status(None) is None


def test_effective_status_reads_the_row():
    row = _sub(SubscriptionStatus.ACTIVE.value, period_end=NOW - timedelta(days=10))
    assert (
        SubscriptionService.effective_status(row, now=NOW)
        == SubscriptionStatus.EXPIRED.value
    )
