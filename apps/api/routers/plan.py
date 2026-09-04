
"""
AstroOS — Plan / Entitlement API Router (Phase 2)

Public endpoints (any authenticated user):
  GET  /api/v1/plans                       — list all active plans
  GET  /api/v1/plans/{code}                — one plan + limits + entitlements
  GET  /api/v1/features                    — full feature catalog
  GET  /api/v1/entitlements/me             — current user's plan + entitlements + limits
  GET  /api/v1/entitlements/me/{feature}   — check one feature for current user
  GET  /api/v1/entitlements/me/limits      — current user's numeric limits

Admin-only endpoints (admin token required):
  POST /api/v1/admin/plans                 — create a plan
  PUT  /api/v1/admin/plans/{plan_id}       — update a plan
  POST /api/v1/admin/features              — create a feature
  PUT  /api/v1/admin/features/{feature_id} — update a feature
  POST /api/v1/admin/plans/{plan_id}/features/{feature_id} — set entitlement

Phase 2 explicitly does NOT include: checkout, payment, subscription lifecycle,
webhooks, billing UI, quota consumption.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_current_user_from_bearer, require_admin
from apps.api.domain.user import User
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.schemas.plan import (
    PlanCreate, PlanUpdate, PlanResponse,
    FeatureCreate, FeatureUpdate, FeatureResponse,
    PlanFeatureCreate, PlanFeatureResponse,
    PlanLimitsResponse,
    EntitlementDecisionResponse,
    UserPlanResponse,
    UserEntitlementSummary,
)
from apps.api.services.entitlement_service import EntitlementService
from apps.api.services.feature_catalog import ACTION_COLUMNS

router = APIRouter(prefix="/api/v1", tags=["Plans"])

# ── Public ──────────────────────────────────────────────────────────────────

@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db_session)):
    """List all active plans."""
    plans = await PlanRepository.list_all(db)
    return plans


@router.get("/plans/{plan_code}", response_model=PlanResponse)
async def get_plan(plan_code: str, db: AsyncSession = Depends(get_db_session)):
    """Get one plan by code."""
    plan = await PlanRepository.get_by_code(db, plan_code.upper())
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    return plan


@router.get("/features", response_model=list[FeatureResponse])
async def list_features(db: AsyncSession = Depends(get_db_session)):
    """Full feature catalog."""
    features = await PlanRepository.list_features(db)
    return features


@router.get("/entitlements/me", response_model=UserEntitlementSummary)
async def get_my_entitlements(
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Current user's full entitlement summary: plan, limits, features, entitlements."""
    svc = EntitlementService(db)
    plan = await svc.resolve_user_plan(user)
    limits = await svc.get_plan_limits(user)
    all_features = await PlanRepository.list_features(db)
    ents = await PlanRepository.get_entitlements_for_plan(db, plan.id)
    return UserEntitlementSummary(
        user_id=user.id.value,
        plan=PlanResponse.model_validate(plan),
        limits=PlanLimitsResponse(
            plan_code=limits.plan_code,
            saved_horoscopes=limits.saved_horoscopes,
            research_projects_monthly=limits.research_projects_monthly,
            extra=limits.extra,
        ),
        features=[FeatureResponse.model_validate(f) for f in all_features],
        entitlements=[PlanFeatureResponse.model_validate(e) for e in ents],
    )


@router.get("/entitlements/me/limits", response_model=PlanLimitsResponse)
async def get_my_limits(
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Current user's numeric plan limits."""
    svc = EntitlementService(db)
    limits = await svc.get_plan_limits(user)
    return PlanLimitsResponse(
        plan_code=limits.plan_code,
        saved_horoscopes=limits.saved_horoscopes,
        research_projects_monthly=limits.research_projects_monthly,
        extra=limits.extra,
    )


@router.get("/entitlements/me/{feature_key}/{action}", response_model=EntitlementDecisionResponse)
async def check_entitlement(
    feature_key: str,
    action: str,
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Check one Feature x Action entitlement for the current user."""
    svc = EntitlementService(db)
    decision = await svc.get_decision(user, feature_key, action)
    return EntitlementDecisionResponse(
        feature_key=feature_key,
        action=action,
        status=decision.status,
        reason=decision.reason,
        allowed=decision.allowed,
        fallback_allowed=decision.fallback_allowed,
    )


@router.get("/entitlements/me/{feature_key}", response_model=EntitlementDecisionResponse)
async def check_feature_enabled(
    feature_key: str,
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Check whether any action is enabled for a feature (is_feature_enabled)."""
    svc = EntitlementService(db)
    allowed = await svc.is_feature_enabled(user, feature_key)
    return EntitlementDecisionResponse(
        feature_key=feature_key,
        action="any",
        status="granted" if allowed else "unresolved",
        reason=f"Feature '{feature_key}' is {'enabled' if allowed else 'not explicitly granted'}.",
        allowed=allowed,
        fallback_allowed=allowed,
    )


@router.get("/users/me/plan", response_model=UserPlanResponse)
async def get_my_plan(
    user: User = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """Current user's plan assignment (null plan_code = default FREE)."""
    assignment = await PlanRepository.get_user_plan(db, user.id.value)
    if assignment is None:
        return UserPlanResponse(
            user_id=user.id.value,
            plan_code=None,
            started_at=user.created_at,
            expires_at=None,
            auto_renew=False,
        )
    plan_code = None
    if assignment.plan_id is not None:
        plan = await PlanRepository.get_by_id(db, assignment.plan_id)
        if plan:
            plan_code = plan.plan_code
        return UserPlanResponse(
        user_id=user.id.value,
        plan_code=plan_code,
        started_at=assignment.started_at,
        expires_at=assignment.expires_at,
        auto_renew=assignment.auto_renew,
    )
# ── Admin ─────────────────────────────────────────────────────────────────────
# All admin endpoints require admin role (require_admin dependency).


@router.post(
    "/admin/plans",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_plan(
    payload: PlanCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new plan tier."""
    existing = await PlanRepository.get_by_code(db, payload.plan_code.upper())
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Plan with code '{payload.plan_code}' already exists.",
        )
    plan = await PlanRepository.create_plan(
        db,
        plan_code=payload.plan_code,
        name=payload.name,
        description=payload.description or "",
        is_active=payload.is_active,
    )
    return plan


@router.put(
    "/admin/plans/{plan_id}",
    response_model=PlanResponse,
    dependencies=[Depends(require_admin)],
)
async def update_plan(
    plan_id: UUID,
    payload: PlanUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Update an existing plan."""
    plan = await PlanRepository.get_by_id(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found."
        )
    if payload.name is not None:
        plan.name = payload.name
    if payload.description is not None:
        plan.description = payload.description
    if payload.is_active is not None:
        plan.is_active = payload.is_active
    await db.commit()
    await db.refresh(plan)
    return plan


@router.post(
    "/admin/features",
    response_model=FeatureResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_feature(
    payload: FeatureCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new feature entry."""
    feature = await PlanRepository.create_feature(
        db,
        feature_key=payload.feature_key,
        name=payload.name,
        description=payload.description or "",
        category=payload.category,
        is_system=payload.is_system,
    )
    return feature


@router.put(
    "/admin/features/{feature_id}",
    response_model=FeatureResponse,
    dependencies=[Depends(require_admin)],
)
async def update_feature(
    feature_id: UUID,
    payload: FeatureUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Update an existing feature."""
    feature = await PlanRepository.get_feature_by_id(db, feature_id)
    if feature is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found."
        )
    if payload.name is not None:
        feature.name = payload.name
    if payload.description is not None:
        feature.description = payload.description
    if payload.category is not None:
        feature.category = payload.category
    if payload.is_system is not None:
        feature.is_system = payload.is_system
    await db.commit()
    await db.refresh(feature)
    return feature


@router.post(
    "/admin/plans/{plan_id}/features/{feature_id}",
    response_model=PlanFeatureResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def set_plan_entitlement(
    plan_id: UUID,
    feature_id: UUID,
    payload: PlanFeatureCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Create or update a plan-feature entitlement row (upsert)."""
    plan = await PlanRepository.get_by_id(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found."
        )
    feature = await PlanRepository.get_feature_by_id(db, feature_id)
    if feature is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found."
        )
    entitlement = await PlanRepository.set_entitlement(
        db,
        plan_id=plan_id,
        feature_id=feature_id,
        can_view=payload.can_view,
        can_create=payload.can_create,
        can_edit=payload.can_edit,
        can_run=payload.can_run,
        can_export=payload.can_export,
        view_limit=payload.view_limit,
        create_limit=payload.create_limit,
        edit_limit=payload.edit_limit,
        run_limit=payload.run_limit,
    )
    return entitlement


@router.put(
    "/admin/plans/{plan_id}/limits",
    response_model=PlanLimitsResponse,
    dependencies=[Depends(require_admin)],
)
async def update_plan_limits(
    plan_id: UUID,
    payload: PlanLimitsResponse,
    db: AsyncSession = Depends(get_db_session),
):
    """Update numeric limits for a plan."""
    plan = await PlanRepository.get_by_id(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found."
        )
    limits = await PlanRepository.get_or_create_limits(db, plan_id)
    limits.saved_horoscopes = payload.saved_horoscopes
    limits.research_projects_monthly = payload.research_projects_monthly
    limits.extra_limits_json = payload.extra
    await db.commit()
    await db.refresh(limits)
    return PlanLimitsResponse(
        plan_code=plan.plan_code,
        saved_horoscopes=limits.saved_horoscopes,
        research_projects_monthly=limits.research_projects_monthly,
        extra=limits.extra_limits_json,
    )