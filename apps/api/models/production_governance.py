"""
AstroOS — Production Governance SQLAlchemy ORM Models

Defines persistence schema for production profile versions and experiment sign-offs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class ProductionProfileVersionModel(AstroBase):
    """Stores versioned production consensus profiles and active baseline status."""

    __tablename__ = "production_profile_versions"

    profile_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    benchmark_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    is_active_baseline: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    promoted_from_experiment_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    promoted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ExperimentSignoffModel(AstroBase):
    """Stores formal human review sign-offs on benchmark experiments."""

    __tablename__ = "experiment_signoffs"

    signoff_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    experiment_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # PENDING, APPROVED, REJECTED
    reviewer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))