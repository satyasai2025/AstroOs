"""
AstroOS — Event Type Tree ORM Model (Research Module)

Self-referencing adjacency-list tree for research life-event typing —
mirrors event_category.py's EventCategoryModel exactly (same rationale:
the closed 22-value `_EventType` enum on LifeEventModel.event_type can't
express real hierarchical event data; this open tree, auto-created on
demand, replaces it for the manual-entry / import path only — the enum
column and the pattern-discovery/assistant endpoints that key off it are
left untouched, see routers/research.py).
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


class EventTypeModel(AstroBase):
    """One node in the research-event type tree."""

    __tablename__ = "event_types"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_types.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    path: Mapped[str] = mapped_column(
        String(600),
        nullable=False,
        index=True,
        doc="Denormalized full 'A / B / C' path for fast display and de-dup lookups without walking parents.",
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="import",
        doc="'import' (auto-created from data) vs 'manual' (researcher-created/curated).",
    )

    parent: Mapped[Optional["EventTypeModel"]] = relationship(
        "EventTypeModel", remote_side="EventTypeModel.id", back_populates="children",
    )
    children: Mapped[list["EventTypeModel"]] = relationship(
        "EventTypeModel", back_populates="parent", cascade="all, delete-orphan",
    )
