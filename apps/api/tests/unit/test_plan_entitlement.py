"""
AstroOS — Plan / Entitlement Phase 2 Tests

Layers (matching existing conventions):

1. PURE / DATA tests (no DB) — validate the canonical catalog
   (apps/api/services/feature_catalog.py): the four plans, their numeric
   limits, feature catalog validity and the decided Feature x Plan x Action
   matrix. FREE=5/PRO=50/RESEARCH=100 and research limits are asserted here
   against the single source of truth.

2. SERVICE tests — EntitlementService with a mocked PlanRepository
   (AsyncMock), following the test_auth_service.py convention. Validates
   resolution, action helpers (incl. FREE research 0/month deny) and
   PlanLimits assembly — no live DB.

3. DB-backed tests — use the shared `db_session` fixture + make_user,
   auto-skipped when TEST_DATABASE_URL is unset.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.services.entitlement_service import (
    DEFAULT_PLAN_CODE,
    EntitlementDecision,
    EntitlementService,
    PlanLimits,
)
from apps.api.services import feature_catalog as fc
from apps.api.tests.conftest import make_user
from apps.api.repositories.plan_repository import PlanRepository as RealPlanRepo


# ════════════════════════════════════════════════════════════════════════════
# 1. Catalog / data tests (no DB)
# ════════════════════════════════════════════════════════════════════════════


def test_four_plans_defined():
    codes = [p.code for p in fc.PLANS]
    assert codes == ["FREE", "PRO", "RESEARCH", "CUSTOM"]


def test_plan_codes_unique():
    codes = [p.code for p in fc.PLANS]
    assert len(codes) == len(set(codes))


def test_feature_keys_unique_and_lowercase():
    keys = [f.key for f in fc.FEATURES]
    assert len(keys) == len(set(keys))
    assert "saved_horoscopes" in keys
    assert "research_projects" in keys
    for f in fc.FEATURES:
        assert f.key == f.key.lower()


def test_feature_categories_valid():
    valid = {"core", "premium", "research", "enterprise"}
    for f in fc.FEATURES:
        assert f.category in valid


def test_action_columns_are_valid():
    assert set(fc.ACTION_COLUMNS) == {"view", "create", "edit", "run", "export"}


def test_plan_limits_match_spec():
    lu = {l.plan_code: l for l in fc.PLAN_LIMITS}
    assert lu["FREE"].saved_horoscopes == 5
    assert lu["FREE"].research_projects_monthly == 0
    assert lu["PRO"].saved_horoscopes == 50
    assert lu["PRO"].research_projects_monthly == 1
    assert lu["RESEARCH"].saved_horoscopes == 100
    assert lu["RESEARCH"].research_projects_monthly == 3
    assert lu["CUSTOM"].saved_horoscopes is None
    assert lu["CUSTOM"].research_projects_monthly is None


def test_plan_limits_cover_all_plans():
    codes = {p.code for p in fc.PLANS}
    limit_codes = {l.plan_code for l in fc.PLAN_LIMITS}
    assert codes == limit_codes


def test_decided_matrix_uses_valid_keys_actions_and_plans():
    action_cols = set(fc.ACTION_COLUMNS)
    plan_codes = {p.code for p in fc.PLANS}
    feature_keys = {f.key for f in fc.FEATURES}
    for fkey, by_plan in fc.DECIDED_MATRIX.items():
        assert fkey in feature_keys
        for plan_code, actions in by_plan.items():
            assert plan_code in plan_codes
            for a in actions:
                assert a in action_cols
                assert isinstance(actions[a], bool)


def test_saved_horoscopes_creatable_all_plans():
    m = fc.DECIDED_MATRIX["saved_horoscopes"]
    for plan in fc.PLANS:
        assert m[plan.code].get("create") is True


def test_free_has_no_research_project_entitlement():
    # FREE has 0/month -> deliberately NO decided create/view cell.
    m = fc.DECIDED_MATRIX["research_projects"]
    assert m.get("FREE") == {}
# ════════════════════════════════════════════════════════════════════════════
# 2. EntitlementService unit tests (mocked PlanRepository, no DB)
# ════════════════════════════════════════════════════════════════════════════


def _plan(code="FREE", is_active=True):
    p = MagicMock()
    p.id = uuid.uuid4()
    p.plan_code = code
    p.name = code.title()
    p.is_active = is_active
    return p


def _feature(key="saved_horoscopes"):
    f = MagicMock()
    f.id = uuid.uuid4()
    f.feature_key = key
    return f


def _limit_row(saved=None, research=None, extra_json=None):
    r = MagicMock()
    r.saved_horoscopes = saved
    r.research_projects_monthly = research
    r.extra_limits_json = extra_json
    return r


def _entitlement(can_view=False, can_create=False, can_edit=False,
                 can_run=False, can_export=False):
    row = MagicMock()
    row.can_view = can_view
    row.can_create = can_create
    row.can_edit = can_edit
    row.can_run = can_run
    row.can_export = can_export
    return row


class _RepoStub:
    """Async stand-in for PlanRepository static methods used by the service."""

    def __init__(self, plan=None, feature=None, entitlement=None,
                 limit=None, assignment=None):
        self._plan = plan
        self._feature = feature
        self._entitlement = entitlement
        self._limit = limit
        self._assignment = assignment

    async def get_user_plan(self, db, user_id):
        return self._assignment

    async def get_by_id(self, db, plan_id):
        return self._plan

    async def get_by_code(self, db, code):
        return self._plan

    async def get_feature_by_key(self, db, key):
        return self._feature

    async def get_entitlement(self, db, plan_id, feature_id):
        return self._entitlement

    async def get_limit(self, db, plan_id):
        return self._limit


@pytest.mark.asyncio
async def test_resolve_default_plan_is_free(monkeypatch):
    free = _plan("FREE")
    stub = _RepoStub(plan=free)
    monkeypatch.setattr(
        "apps.api.services.entitlement_service.PlanRepository", stub
    )
    svc = EntitlementService(None)
    plan = await svc.resolve_user_plan(make_user())
    assert plan.plan_code == "FREE"


@pytest.mark.asyncio
async def test_resolve_assigned_plan(monkeypatch):
    pro = _plan("PRO")
    assignment = MagicMock()
    assignment.plan_id = pro.id
    stub = _RepoStub(plan=pro, assignment=assignment)
    monkeypatch.setattr(
        "apps.api.services.entitlement_service.PlanRepository", stub
    )
    svc = EntitlementService(None)
    plan = await svc.resolve_user_plan(make_user())
    assert plan.plan_code == "PRO"


@pytest.mark.asyncio
async def test_can_create_saved_horoscopes_granted(monkeypatch):
    free = _plan("free")
    limit = _limit_row(saved=5, research=0)
    ent = _entitlement(can_view=True, can_create=True)
    stub = _RepoStub(plan=free, feature=_feature("saved_horoscopes"),
                     entitlement=ent, limit=limit)
    monkeypatch.setattr(
        "apps.api.services.entitlement_service.PlanRepository", stub
    )
    svc = EntitlementService(None)
    assert await svc.can_create(make_user(), "saved_horoscopes") is True


@pytest.mark.asyncio
async def test_free_cannot_create_research(monkeypatch):
    free = _plan("free")
    limit = _limit_row(saved=5, research=0)
    # Entitlement would GRANT create, but the 0/month limit overrides.
    ent = _entitlement(can_view=True, can_create=True)
    stub = _RepoStub(plan=free, feature=_feature("research_projects"),
                     entitlement=ent, limit=limit)
    monkeypatch.setattr(
        "apps.api.services.entitlement_service.PlanRepository", stub
    )
    svc = EntitlementService(None)
    assert await svc.can_create(make_user(), "research_projects") is False


@pytest.mark.asyncio
async def test_get_plan_limits_resolves(monkeypatch):
    pro = _plan("PRO")
    limit = _limit_row(saved=50, research=1)
    stub = _RepoStub(plan=pro, limit=limit)
    monkeypatch.setattr(
        "apps.api.services.entitlement_service.PlanRepository", stub
    )
    svc = EntitlementService(None)
    limits = await svc.get_plan_limits_for_code("PRO")
    assert limits.plan_code == "PRO"
    assert limits.saved_horoscopes == 50
    assert limits.research_projects_monthly == 1


@pytest.mark.asyncio
async def test_unknown_feature_is_unresolved(monkeypatch):
    free = _plan("free")
    stub = _RepoStub(plan=free, feature=None, entitlement=None)
    monkeypatch.setattr(
        "apps.api.services.entitlement_service.PlanRepository", stub
    )
    svc = EntitlementService(None, unresolved_default="allow")
    decision = await svc.get_decision(make_user(), "nope", "view")
    assert decision.status == "unresolved"
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_can_create_zero_limit_not_applied_to_unlimited(monkeypatch):
    """CUSTOM (unlimited) plans are not blocked by a None limit."""
    custom = _plan("CUSTOM")
    limit = _limit_row(saved=None, research=None)
    ent = _entitlement(can_view=True, can_create=True)
    stub = _RepoStub(plan=custom, feature=_feature("research_projects"),
                     entitlement=ent, limit=limit)
    monkeypatch.setattr(
        "apps.api.services.entitlement_service.PlanRepository", stub
    )
    svc = EntitlementService(None)
    assert await svc.can_create(make_user(), "research_projects") is True
# ════════════════════════════════════════════════════════════════════════════
# 3. DB-backed tests (auto-skip without TEST_DATABASE_URL)
# ════════════════════════════════════════════════════════════════════════════

# Importing the plan ORM models registers them on AstroBase.metadata so the
# conftest `db_session` fixture's create_all() includes the Phase 2 tables.
from apps.api.models.plan import (  # noqa: E402
    PlanModel,
    FeatureModel,
    PlanFeatureModel,
    PlanLimitModel,
    UserPlanModel,
)
from apps.api.models.base import AstroBase  # noqa: E402


async def _seed_one_minimal(db_session, plan_code="FREE", saved=5, research=0):
    """Insert an active plan + limit + the saved_horoscopes feature row."""
    existing = await RealPlanRepo.get_by_code(db_session, plan_code)
    if existing is not None:
        return existing
    plan = PlanModel(plan_code=plan_code, name=plan_code.title(), description="", is_active=True)
    db_session.add(plan)
    await db_session.flush()
    limit = PlanLimitModel(
        plan_id=plan.id, saved_horoscopes=saved, research_projects_monthly=research,
    )
    db_session.add(limit)
    feat = FeatureModel(
        feature_key="saved_horoscopes", name="Saved Horoscopes",
        description="", category="core", is_system=True,
    )
    db_session.add(feat)
    await db_session.flush()
    ent = PlanFeatureModel(
        plan_id=plan.id, feature_id=feat.id, can_view=True, can_create=True,
    )
    db_session.add(ent)
    await db_session.flush()
    return plan, limit, feat, ent


@pytest.mark.asyncio
async def test_db_resolve_default_free_plan(db_session):
    await _seed_one_minimal(db_session)
    svc = EntitlementService(db_session)
    plan = await svc.resolve_user_plan(make_user())
    assert plan.plan_code == "FREE"


@pytest.mark.asyncio
async def test_db_free_plan_limits(db_session):
    await _seed_one_minimal(db_session, saved=5, research=0)
    svc = EntitlementService(db_session)
    limits = await svc.get_plan_limits(make_user())
    assert limits.saved_horoscopes == 5
    assert limits.research_projects_monthly == 0


@pytest.mark.asyncio
async def test_db_can_create_saved_horoscope(db_session):
    await _seed_one_minimal(db_session)
    svc = EntitlementService(db_session)
    user = make_user()
    assert await svc.can_view(user, "saved_horoscopes") is True
    assert await svc.can_create(user, "saved_horoscopes") is True


@pytest.mark.asyncio
async def test_db_free_has_zero_research_limit_blocks_create(db_session):
    await _seed_one_minimal(db_session, saved=5, research=0)
    svc = EntitlementService(db_session)
    user = make_user()
    # Ensure the FREE plan's research_projects entitlement row exists (granted
    # create) so the ONLY thing blocking creation is the 0/month limit.
    plan = await svc.resolve_user_plan(user)
    feat = await RealPlanRepo.get_feature_by_key(db_session, "research_projects")
    if feat is None:
        feat = FeatureModel(
            feature_key="research_projects", name="Research Projects",
            description="", category="research", is_system=True,
        )
        db_session.add(feat)
        await db_session.flush()
    existing_ent = await RealPlanRepo.get_entitlement(db_session, plan.id, feat.id)
    if existing_ent is None:
        db_session.add(PlanFeatureModel(
            plan_id=plan.id, feature_id=feat.id, can_view=True, can_create=True,
        ))
        await db_session.flush()
    assert await svc.can_create(user, "research_projects") is False