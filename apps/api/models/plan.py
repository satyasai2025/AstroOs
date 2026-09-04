"""
AstroOS — Plan Feature Entitlement: ORM Models
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import (
    ForeignKey, Integer, String, Text, Boolean, DateTime, func, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


class PlanModel(AstroBase):
    """Plan tier definition: Free, Pro, Research, Custom."""

    __tablename__ = "plans"

    plan_code: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False,
        doc="Human-readable code: FREE, PRO, RESEARCH, CUSTOM",
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    plan_features: Mapped[List["PlanFeatureModel"]] = relationship(
        "PlanFeatureModel", back_populates="plan", cascade="all, delete-orphan",
    )
    plan_limits: Mapped["PlanLimitModel"] = relationship(
        "PlanLimitModel", back_populates="plan", cascade="all, delete-orphan",
        uselist=False,
    )
    user_plans: Mapped[List["UserPlanModel"]] = relationship(
        "UserPlanModel", back_populates="plan",
    )
    # One-sided read convenience (subscription-side deliberately declares no
    # mirror property — see apps/api/models/subscription.py's Phase-5 notes),
    # so no back_populates here; adding one breaks mapper configuration.
    subscriptions: Mapped[List["SubscriptionModel"]] = relationship(
        "SubscriptionModel",
    )

    def __repr__(self) -> str:
        return f"<Plan {self.plan_code}: {self.name}>"


class FeatureModel(AstroBase):
    """Catalog of all possible features AstroOS can offer."""

    __tablename__ = "features"

    feature_key: Mapped[str] = mapped_column(
        String(80), unique=True, index=True, nullable=False,
        doc="Machine-readable key matching AstroOS feature routes and UI modules",
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="core",
        doc="UI/UX module grouping: core, premium, research, enterprise",
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    plan_features: Mapped[List["PlanFeatureModel"]] = relationship(
        "PlanFeatureModel", back_populates="feature", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Feature {self.feature_key}>"


class PlanFeatureModel(AstroBase):
    """Entitlement mapping: which plan can do what with which feature."""

    __tablename__ = "plan_features"

    __table_args__ = (
        UniqueConstraint("plan_id", "feature_id", name="uc_plan_feature"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("features.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Granular action flags
    can_view: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_create: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_export: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Action-specific limits (future use for granular quota)
    view_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    create_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    edit_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    plan: Mapped[PlanModel] = relationship("PlanModel", back_populates="plan_features")
    feature: Mapped[FeatureModel] = relationship("FeatureModel", back_populates="plan_features")

    def __repr__(self) -> str:
        return f"<PlanFeature {self.plan_id} -> {self.feature_id}>"


class PlanLimitModel(AstroBase):
    """Runtime limit definitions per plan (e.g., saved_horoscopes = 5)."""

    __tablename__ = "plan_limits"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    saved_horoscopes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    research_projects_monthly: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra_limits_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped[PlanModel] = relationship("PlanModel", back_populates="plan_limits")

    def __repr__(self) -> str:
        return f"<PlanLimit {self.plan_id}>"


class UserPlanModel(AstroBase):
    """Association: which plan a user is currently subscribed to (null = default Free)."""

    __tablename__ = "user_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="SET NULL"),
        nullable=True,
        doc="NULL means user is on default Free plan (no explicit upgrade)",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="NULL = perpetual lifetime upgrade; set for subscription end",
    )
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    plan: Mapped[PlanModel | None] = relationship("PlanModel", back_populates="user_plans")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="user_plan")

    def __repr__(self) -> str:
        return f"<UserPlan user={self.user_id} plan={self.plan_id}>"
