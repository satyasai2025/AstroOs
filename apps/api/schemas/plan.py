
"""
AstroOS — Plan Feature Entitlement: Pydantic Schemas (Phase 2)
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanBase(BaseModel):
    plan_code: str = Field(..., example="FREE")
    name: str = Field(..., example="Free")
    description: Optional[str] = Field(default=None, example="Personal astrology essentials.")
    is_active: bool = Field(default=True)


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class PlanResponse(PlanBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureBase(BaseModel):
    feature_key: str = Field(..., example="saved_horoscopes")
    name: str = Field(..., example="Saved Horoscopes")
    description: Optional[str] = Field(default=None)
    category: str = Field(default="core", example="core")
    is_system: bool = Field(default=True)


class FeatureCreate(FeatureBase):
    pass


class FeatureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_system: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class FeatureResponse(FeatureBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanFeatureBase(BaseModel):
    can_view: bool = Field(default=False)
    can_create: bool = Field(default=False)
    can_edit: bool = Field(default=False)
    can_run: bool = Field(default=False)
    can_export: bool = Field(default=False)
    view_limit: Optional[int] = Field(default=None, ge=0)
    create_limit: Optional[int] = Field(default=None, ge=0)
    edit_limit: Optional[int] = Field(default=None, ge=0)
    run_limit: Optional[int] = Field(default=None, ge=0)


class PlanFeatureCreate(PlanFeatureBase):
    pass


class PlanFeatureUpdate(PlanFeatureBase):
    pass


class PlanFeatureResponse(PlanFeatureBase):
    plan_id: UUID
    feature_id: UUID

    model_config = ConfigDict(from_attributes=True)


class EntitlementDecisionResponse(BaseModel):
    feature_key: str
    action: str
    status: str
    reason: str
    allowed: bool
    fallback_allowed: bool


class PlanLimitsResponse(BaseModel):
    plan_code: str
    saved_horoscopes: Optional[int] = Field(default=None, example=5)
    research_projects_monthly: Optional[int] = Field(default=None, example=1)
    extra: dict[str, Optional[int]] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class UserPlanAssignment(BaseModel):
    plan_code: str = Field(..., example="PRO")
    expires_at: Optional[datetime] = Field(default=None)
    auto_renew: bool = Field(default=False)

    model_config = ConfigDict(from_attributes=True)


class UserPlanResponse(BaseModel):
    user_id: UUID
    plan_code: Optional[str] = Field(default=None)
    started_at: datetime
    expires_at: Optional[datetime] = None
    auto_renew: bool

    model_config = ConfigDict(from_attributes=True)


class UserEntitlementSummary(BaseModel):
    user_id: UUID
    plan: PlanResponse
    limits: PlanLimitsResponse
    features: List[FeatureResponse]
    entitlements: List[PlanFeatureResponse]

    model_config = ConfigDict(from_attributes=True)