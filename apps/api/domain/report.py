"""
AstroOS — Report Domain Objects (Module 20, Phase 1)

Structured report assembly — composes existing domain objects into
report sections without performing any calculations.

Pure Python dataclasses — no ORM/Pydantic dependency.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class ReportContent:
    """
    Lightweight serialization boundary for report section data.

    section_type determines the schema of data. Each type has a fixed
    set of documented fields. Serializers operate on data, never on
    raw dicts or domain objects.
    """

    section_type: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReportSection:
    """One named section in a report."""

    title: str
    section_type: str
    content: ReportContent
    order: int = 0


@dataclass(frozen=True)
class ReportMetadata:
    """
    Report identification, provenance, and versioning.

    Contains no report data — only metadata.
    """

    report_id: uuid.UUID
    report_type: str  # "chart" | "research" | "comparison"
    report_version: str
    generated_at: datetime
    engine_versions: dict[str, str] = field(default_factory=dict)
    chart_id: Optional[uuid.UUID] = None
    research_project_id: Optional[uuid.UUID] = None
    generated_by: Optional[str] = None


@dataclass(frozen=True)
class ChartReport:
    """Full astrological analysis for one chart."""

    metadata: ReportMetadata
    title: str
    subject_name: str
    sections: tuple[ReportSection, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ResearchReport:
    """Statistical findings across a snapshot collection."""

    metadata: ReportMetadata
    title: str
    snapshot_count: int
    sections: tuple[ReportSection, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ComparisonReport:
    """Side-by-side comparison of two or more charts."""

    metadata: ReportMetadata
    title: str
    chart_ids: tuple[uuid.UUID, ...]
    chart_labels: tuple[str, ...]
    sections: tuple[ReportSection, ...] = field(default_factory=tuple)
