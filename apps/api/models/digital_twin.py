"""
AstroOS — Digital Twin ORM Models

SQLAlchemy models for the digital_twins and twin_modifications tables.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Index,
    Integer,
    JSON,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase

class DigitalTwinModel(AstroBase):
    """ORM model storing a digital twin configuration."""
    __tablename__ = "digital_twins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_chart_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    modifications_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cached_chart_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cached_strengths_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cached_yoga_names: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    # AstroBase provides: created_at, updated_at, deleted_at

    # Relationships
    modifications: Mapped[list[TwinModificationModel]] = relationship(
        "TwinModificationModel",
        back_populates="twin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_digital_twins_user_id", "user_id"),
        Index("ix_digital_twins_chart_id", "original_chart_id"),
        Index("ix_digital_twins_status", "status"),
        Index("ix_digital_twins_user_chart_status", "user_id", "original_chart_id", "status"),
    )


class TwinModificationModel(AstroBase):
    """ORM model for a single modification applied to a twin."""
    __tablename__ = "twin_modifications"

    twin_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("digital_twins.id", ondelete="CASCADE"),
        nullable=False,
    )
    modification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AstroBase provides: created_at, updated_at, deleted_at

    # Relationships
    twin: Mapped[DigitalTwinModel] = relationship("DigitalTwinModel", back_populates="modifications")

    __table_args__ = (
        Index("ix_twin_modifications_twin_id", "twin_id"),
        Index("ix_twin_modifications_type", "modification_type"),
    )
