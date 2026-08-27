"""
AstroOS — Event Category Tree ORM Model (Research Module)

Self-referencing adjacency-list tree for research-event categorization,
replacing the flat `LifeEventModel.category` free-text field's lack of
structure with a real hierarchy — same `parent_id` self-FK + `level`
pattern already used by DashaModel (Mahadasha -> Antardasha -> Pratyantar)
in astrology.py, reused here rather than inventing nested-set/closure-table.

Open vocabulary: unlike the fixed `_EventType` enum, nodes here are
created on demand (by import or by a researcher) — there is no fixed seed
list to maintain. Vedic house/karaka tagging is optional metadata a
researcher attaches to any node over time; nodes are untagged by default.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


class EventCategoryModel(AstroBase):
    """One node in the research-event category tree."""

    __tablename__ = "event_categories"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_categories.id", ondelete="CASCADE"),
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
    house_number: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        doc="Optional Vedic bhava (1-12) this category has been researcher-tagged with. Unset by default.",
    )
    karaka_planet: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Optional significator planet this category has been researcher-tagged with. Unset by default.",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="import",
        doc="'import' (auto-created from data) vs 'manual' (researcher-created/curated).",
    )
    source_doc_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Real usage-frequency count carried over from a bulk-seed source (e.g. category doc counts), if any.",
    )

    parent: Mapped[Optional["EventCategoryModel"]] = relationship(
        "EventCategoryModel", remote_side="EventCategoryModel.id", back_populates="children",
    )
    children: Mapped[list["EventCategoryModel"]] = relationship(
        "EventCategoryModel", back_populates="parent", cascade="all, delete-orphan",
    )
