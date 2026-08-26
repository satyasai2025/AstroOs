"""
AstroOS — Usage Tracking Models (Phase 4)

Tracks quota consumption per user per feature per billing period (month).
Used by QuotaService to enforce plan limits at the entitlement layer.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import ForeignKey, Integer, String, DateTime, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


class UsageRecordModel(AstroBase):
    """
    Tracks usage of a quota-limited feature for one user in one billing period.
    
    Billing period is stored as "YYYY-MM" string for easy monthly resets.
    Unique constraint on (user_id, feature_key, period) ensures one row per combo.
    """

    __tablename__ = "usage_records"

    __table_args__ = (
        UniqueConstraint("user_id", "feature_key", "period", name="uc_usage_user_feature_period"),
        Index("ix_usage_user_period", "user_id", "period"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_key: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        doc="Feature being tracked: saved_horoscopes, research_projects",
    )
    period: Mapped[str] = mapped_column(
        String(7),           # "YYYY-MM"
        nullable=False,
        index=True,
        doc="Billing period in YYYY-MM format",
    )
    count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of usages consumed in this period",
    )
    last_incremented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last usage increment",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<UsageRecord {self.user_id} {self.feature_key} {self.period}={self.count}>"