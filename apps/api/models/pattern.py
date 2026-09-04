"""
AstroOS — Pattern Discovery Persistence Models (Module 27, Phase 3c)

Two tables:

  PatternDiscoveryRunModel — one row per /cases/patterns/discover invocation.
                             Drives "Recent Significant Patterns", per-pattern
                             confidence trend, and lets you tell which engine
                             version produced a given batch of patterns.
  DiscoveredPatternModel   — persisted DiscoveredPattern results, upserted by
                             pattern_id on every discovery run. Carries full
                             reproducibility metadata (algorithm/feature
                             version, contributing snapshot versions, and the
                             exact supporting/contradicting research case IDs)
                             so a pattern can be audited and reproduced later
                             even as the underlying engines evolve.

Inherits from AstroBase (UUID PK, created_at, updated_at, deleted_at).
JSON columns use JSONB (unlike research_case.py's snapshot blobs, which use
Text) since dimensions/case-ID lists need to stay queryable.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


class PatternDiscoveryRunModel(AstroBase):
    """One invocation of the pattern discovery engine."""

    __tablename__ = "pattern_discovery_runs"

    event_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, index=True,
        comment="KP Master event type this run targeted; null = all types.",
    )
    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    feature_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    patterns: Mapped[list["DiscoveredPatternModel"]] = relationship(
        back_populates="discovery_run", lazy="selectin"
    )


class DiscoveredPatternModel(AstroBase):
    """A persisted, reproducible pattern discovery result."""

    __tablename__ = "discovered_patterns"

    pattern_id: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False,
        comment="Stable sha1-derived ID, e.g. ptn-xxxxxxxxxx.",
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    lift_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    dimensions_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False,
        comment="list[PatternDimension]: dimension/value/frequency/count/expected_by_chance/significance.",
    )

    explanation: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="AI-generated explanation text; null until POST .../explain is called.",
    )
    explanation_generated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    classical_references_json: Mapped[Optional[list[str]]] = mapped_column(
        JSONB, nullable=True, comment="Curated citations matched against this pattern's dimensions."
    )

    supporting_case_ids_json: Mapped[list[str]] = mapped_column(
        JSONB, default=list, nullable=False,
        comment="research_cases.research_case_id values whose data produced this pattern.",
    )
    contradicting_case_ids_json: Mapped[list[str]] = mapped_column(
        JSONB, default=list, nullable=False,
        comment="Cases exhibiting every dimension/value pair but NOT this event_type.",
    )
    snapshot_versions_json: Mapped[list[str]] = mapped_column(
        JSONB, default=list, nullable=False,
        comment="Distinct event_snapshots.snapshot_version values among supporting cases.",
    )

    algorithm_version: Mapped[str] = mapped_column(
        String(20), default="1.0.0", nullable=False,
        comment="pattern_discovery.py ALGORITHM_VERSION at discovery time.",
    )
    feature_version: Mapped[str] = mapped_column(
        String(20), default="1.0.0", nullable=False,
        comment="feature_extraction.py FEATURE_VERSION at discovery time.",
    )

    discovery_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pattern_discovery_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Most recent run that (re)computed this pattern.",
    )

    discovery_run: Mapped[Optional["PatternDiscoveryRunModel"]] = relationship(
        back_populates="patterns"
    )
