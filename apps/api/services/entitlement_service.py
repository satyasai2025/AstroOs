"""
AstroOS — Entitlement Service (Phase 2 foundation)

Answers plan/feature/limit questions against the user's assigned plan:

    is_feature_enabled(user, feature)
    can_view / can_create / can_edit / can_run / can_export (user, feature)
    get_plan_limits(user)
    resolve_user_plan(user)

Phase 2 scope — explicitly OUT of scope here:
  * subscription lifecycle, payment verification (later phases)
  * quota consumption / usage tracking / monthly resets (later phases)

Resolution rules
----------------
1. The user's plan is their explicit `user_plans` row when present; otherwise
   the FREE plan (default tier).
2. An entitlement cell is GRANTED only via an explicit `plan_features` row.
3. A missing `plan_features` row means UNRESOLVED (never decided). For
   backward compatibility the boolean helpers fall back to
   Settings.ENTITLEMENT_UNRESOLVED_DEFAULT ("allow", default) so existing
   behaviour is unchanged until enforcement arrives in a later phase. This
   fallback is a compatibility shim, NOT a product decision — see
   services/feature_catalog.py's docstring and the Phase 2 report.
4. research_projects on FREE additionally honours its limit of 0/month: the
   limit is returned as 0 and can_create() reports denied even though the
   matrix seed also leaves that cell empty.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.user import User
from apps.api.models.subscription import SubscriptionStatus
from apps.api.repositories.plan_repository import PlanRepository

from apps.api.services.subscription_service import SubscriptionService
from apps.api.repositories.subscription_repository import SubscriptionRepository
from apps.api.services.feature_catalog import ACTION_COLUMNS

EntitlementStatus = Literal["granted", "denied", "unresolved"]

DEFAULT_PLAN_CODE = "FREE"


@dataclass(frozen=True)
class EntitlementDecision:
    """Result of one entitlement question."""
    status: EntitlementStatus
    reason: str = ""
    # Populated for "unresolved" so callers/UI can distinguish a deliberate
    # denial from an undecided cell.
    fallback_allowed: bool = False

    @property
    def allowed(self) -> bool:
        if self.status == "granted":
            return True
        if self.status == "unresolved":
            return self.fallback_allowed
        return False


@dataclass
class PlanLimits:
    """Resolved numeric limits for a plan. None = unlimited/configurable."""
    plan_code: str
    saved_horoscopes: int | None = None
    research_projects_monthly: int | None = None
    extra: dict[str, int | None] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "plan_code": self.plan_code,
            "saved_horoscopes": self.saved_horoscopes,
            "research_projects_monthly": self.research_projects_monthly,
            **dict(self.extra),
        }


class EntitlementService:
    """Stateless query surface over the plan/entitlement tables."""

    def __init__(self, db: AsyncSession, unresolved_default: str = "allow"):
        self._db = db
        self._unresolved_fallback = unresolved_default == "allow"

    # ── Plan resolution ──────────────────────────────────────────────────────

    async def resolve_user_plan(self, user: User):
        """
        Return the PlanModel for the user's current plan (default FREE).

        Phase 5 integration: subscription status gates the assignment.
          - No subscription row  → historical behaviour (user_plans honoured).
          - active / trialing / past_due_cancelled (within grace, folded by
            SubscriptionService.compute_effective_status) → subscription's plan;
            past_due_cancelled is the grace window so grants are kept.
          - expired, or a lapsed grace window (terminal) → FREE fallback,
            whatever user_plans says.
        The decision, including the reason, is observable via
        ``resolve_subscription_status``.
        """
        sub = await SubscriptionRepository.get_by_user(self._db, user.id.value)
        if sub is None:
            assignment = await PlanRepository.get_user_plan(self._db, user.id.value)
            if assignment is not None and assignment.plan_id is not None:
                plan = await PlanRepository.get_by_id(self._db, assignment.plan_id)
                if plan is not None and plan.is_active:
                    return plan
        else:
            effective = SubscriptionService.effective_status(sub)
            if (
                effective is not None
                and SubscriptionStatus(effective) is not SubscriptionStatus.EXPIRED
            ):
                plan = await PlanRepository.get_by_id(self._db, sub.plan_id)
                if plan is not None and plan.is_active:
                    return plan
            # EXPIRED (stored or folded), or inactive/expired-plan row:
            # fall through to FREE below.
        default_plan = await PlanRepository.get_by_code(self._db, DEFAULT_PLAN_CODE)
        if default_plan is None:
            raise LookupError(
                f"Default plan '{DEFAULT_PLAN_CODE}' is not seeded. Run migrations."
            )
        return default_plan

    async def resolve_subscription_status(
        self, user: User,
    ) -> tuple[str | None, str]:
        """
        Subscription-aware resolution trace for the current user.

        Returns ``(effective_subscription_status_or_None, resolved_plan_code)``
        where ``resolved_plan_code`` matches what ``resolve_user_plan`` returns
        (``None`` means no subscription row exists). Used by the router to
        explain WHY a plan was (or wasn't) applied.
        """
        plan = await self.resolve_user_plan(user)
        sub = await SubscriptionRepository.get_by_user(self._db, user.id.value)
        effective = (
            SubscriptionService.effective_status(sub) if sub is not None else None
        )
        return effective, plan.plan_code

    async def resolve_effective_entitlement_plan(self, user: User):
        """
        Return the PlanModel whose entitlements actually apply to `user` now.

        Phase 5 integration point: subscription lifecycle state overrides the
        raw user_plans row. Any subscription attached to this user that has
        already lapsed demotes the effective plan to FREE so the expired user
        loses premium entitlements immediately (no cron needed).

        Terminal-status subscriptions (expired / past_due_cancelled with no
        valid window remaining) do not change resolution: either there is no
        active paid period left, or the FREE fallback below applies naturally.
        """
        plan = await self.resolve_user_plan(user)
        from apps.api.repositories.subscription_repository import SubscriptionRepository

        latest = await SubscriptionRepository.get_latest_for_user(self._db, user.id.value)
        if latest is None:
            return plan
        if not SubscriptionRepository.is_lapsed(latest):
            return plan

        free = await PlanRepository.get_by_code(self._db, DEFAULT_PLAN_CODE)
        if free is None:
            raise LookupError(
                f"Default plan '{DEFAULT_PLAN_CODE}' is not seeded. Run migrations."
            )
        return free


    # ── Entitlement queries ──────────────────────────────────────────────────

    async def get_decision(self, user: User, feature_key: str, action: str) -> EntitlementDecision:
        """Resolve one Feature x Plan x Action cell to a tri-state decision."""
        if action not in ACTION_COLUMNS:
            raise ValueError(f"Unknown entitlement action: {action}")
        plan = await self.resolve_user_plan(user)
        feature = await PlanRepository.get_feature_by_key(self._db, feature_key)
        if feature is None:
            return EntitlementDecision(
                "unresolved", reason=f"Unknown feature '{feature_key}'.",
                fallback_allowed=self._unresolved_fallback,
            )
        row = await PlanRepository.get_entitlement(self._db, plan.id, feature.id)
        if row is None:
            return EntitlementDecision(
                "unresolved",
                reason=f"'{feature_key}' x '{plan.plan_code}' not decided.",
                fallback_allowed=self._unresolved_fallback,
            )
        allowed = bool(getattr(row, f"can_{action}"))
        if not allowed and feature_key in DECIDED_MATRIX:
            matrix_plan = DECIDED_MATRIX[feature_key].get(plan.plan_code, {})
            if matrix_plan.get(action) is True:
                allowed = True
        return EntitlementDecision(
            "granted" if allowed else "denied",
            reason=(
                f"Plan '{plan.plan_code}' "
                f"{'grants' if allowed else 'denies'} {action} on '{feature_key}'."
            ),
        )

    async def is_feature_enabled(self, user: User, feature_key: str) -> bool:
        """True when ANY action on the feature is granted for the user's plan."""
        plan = await self.resolve_user_plan(user)
        feature = await PlanRepository.get_feature_by_key(self._db, feature_key)
        if feature is None:
            return self._unresolved_fallback
        row = await PlanRepository.get_entitlement(self._db, plan.id, feature.id)
        if row is None:
            return self._unresolved_fallback
        return any(
            getattr(row, f"can_{action}") for action in ACTION_COLUMNS
        )

    # ── Action helpers ───────────────────────────────────────────────────────

    async def can_view(self, user: User, feature_key: str) -> bool:
        decision = await self.get_decision(user, feature_key, "view")
        return decision.allowed

    async def can_create(self, user: User, feature_key: str) -> bool:
        decision = await self.get_decision(user, feature_key, "create")
        if not decision.allowed:
            return False
        return not await self.creation_blocked_by_zero_limit(user, feature_key)

    async def creation_blocked_by_zero_limit(self, user: User, feature_key: str) -> bool:
        """True when the feature's numeric plan limit is exactly 0, making
        creation impossible regardless of the entitlement flag (e.g.
        research_projects on FREE: 0/month). Features without a mapped
        count-limit are never blocked here."""
        limit_key = _LIMIT_FOR_FEATURE.get(feature_key)
        if limit_key is None:
            return False
        limits = await self.get_plan_limits(user)
        return getattr(limits, limit_key, None) == 0

    # ── Plan limits ───────────────────────────────────────────────────────────

    async def get_plan_limits(self, user: User) -> PlanLimits:
        """Resolve numeric limits for the user's current plan."""
        plan = await self.resolve_user_plan(user)
        limit_row = await PlanRepository.get_limit(self._db, plan.id)
        extra: dict[str, int | None] = {}
        if limit_row is not None and limit_row.extra_limits_json:
            try:
                import json
                raw = json.loads(limit_row.extra_limits_json)
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        extra[str(k)] = int(v) if v is not None else None
            except (ValueError, TypeError):
                pass
        return PlanLimits(
            plan_code=plan.plan_code,
            saved_horoscopes=(
                limit_row.saved_horoscopes if limit_row is not None else None
            ),
            research_projects_monthly=(
                limit_row.research_projects_monthly if limit_row is not None else None
            ),
            extra=extra,
        )

    async def get_plan_limits_for_code(self, plan_code: str) -> PlanLimits:
        plan = await PlanRepository.get_by_code(self._db, plan_code.upper())
        if plan is None:
            raise LookupError(f"Plan '{plan_code}' not found.")
        limit_row = await PlanRepository.get_limit(self._db, plan.id)
        extra: dict[str, int | None] = {}
        if limit_row is not None and limit_row.extra_limits_json:
            try:
                import json
                raw = json.loads(limit_row.extra_limits_json)
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        extra[str(k)] = int(v) if v is not None else None
            except (ValueError, TypeError):
                pass
        return PlanLimits(
            plan_code=plan.plan_code,
            saved_horoscopes=(
                limit_row.saved_horoscopes if limit_row is not None else None
            ),
            research_projects_monthly=(
                limit_row.research_projects_monthly if limit_row is not None else None
            ),
            extra=extra,
        )

    async def can_edit(self, user: User, feature_key: str) -> bool:
        return (await self.get_decision(user, feature_key, "edit")).allowed

    async def can_run(self, user: User, feature_key: str) -> bool:
        return (await self.get_decision(user, feature_key, "run")).allowed

    async def can_export(self, user: User, feature_key: str) -> bool:
        return (await self.get_decision(user, feature_key, "export")).allowed


# Maps count-limited features to their PlanLimits attribute.
_LIMIT_FOR_FEATURE: dict[str, str] = {
    "saved_horoscopes": "saved_horoscopes",
    "research_projects": "research_projects_monthly",
}