"""
AstroOS — Research Domain Objects (Module 17, Phase 1)

Research projects, experiments, astrological snapshots, and query types
for organizing and searching chart data.

Pure Python dataclasses — no ORM/Pydantic dependency, matching every
other domain module in this codebase.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult, SarvashtakavargaResult
from apps.api.domain.dasha import DashaTree
from apps.api.domain.divisional import VargaChart
from apps.api.domain.events import EventRecord
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.domain.timeline import Timeline
from apps.api.domain.verification import VerificationFindings
from apps.api.domain.yoga import YogaResult

if TYPE_CHECKING:
    from apps.api.services.fact_registry import FactRegistry


@dataclass(frozen=True)
class ResearchProject:
    """A container for related research activity, owned by a user."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str = "active"  # active | archived
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class ResearchExperiment:
    """
    A single hypothesis and its execution over one or more snapshots.

    Created as draft, snapshots assigned, then run, then findings recorded.
    """

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    hypothesis: str
    methodology: str
    status: str = "draft"  # draft | running | completed
    snapshot_ids: tuple[uuid.UUID, ...] = field(default_factory=tuple)
    findings: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class AstrologicalSnapshot:
    """
    The captured state of one chart at one point in time.

    Holds domain objects from every engine that computed data for this
    chart — wider than NatalSnapshot, which omits dasha/transit/event data.
    Optional fields are None when that engine's data was not captured.
    """

    id: uuid.UUID
    project_id: uuid.UUID
    chart_id: uuid.UUID
    label: Optional[str]
    captured_at: datetime

    # Core chart data
    chart_ref: D1Chart

    # Natal analyses (date-invariant)
    yogas: Optional[tuple[YogaResult, ...]] = None
    shadbala_components: Optional[dict[str, list[BalaComponentResult]]] = None
    bhinnashtakavarga: Optional[tuple[BhinnashtakavargaResult, ...]] = None
    sarvashtakavarga: Optional[SarvashtakavargaResult] = None
    dasha_trees: Optional[dict[str, DashaTree]] = None
    divisional_charts: Optional[tuple[VargaChart, ...]] = None
    fact_registry: Any = None  # Optional[FactRegistry] — TYPE_CHECKING guard above

    # Date-dependent analyses
    timeline_ref: Optional[Timeline] = None
    verification_ref: Optional[VerificationFindings] = None
    events: Optional[tuple[EventRecord, ...]] = None

    # Metadata
    snapshot_version: str = "1.0"


@dataclass(frozen=True)
class SnapshotCondition:
    """
    One atomic condition evaluated against an AstrologicalSnapshot.

    field is a dotted path navigable by SnapshotAccessor, e.g.
    "chart_ref.planets.0.house_number" or "yogas.0.is_present".
    """

    field: str
    operator: str  # "==", "!=", ">", "<", ">=", "<=", "in"
    value: Any
    description: str = ""


@dataclass(frozen=True)
class SnapshotQuery:
    """A set of conditions combined with AND logic."""

    conditions: tuple[SnapshotCondition, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FieldDiff:
    """One field-level difference between two snapshots."""

    field: str
    value_a: Any
    value_b: Any


@dataclass(frozen=True)
class SnapshotComparison:
    """Result of comparing two snapshots."""

    snapshot_a_id: uuid.UUID
    snapshot_b_id: uuid.UUID
    chart_id_a: uuid.UUID
    chart_id_b: uuid.UUID
    matching_fields: tuple[str, ...] = field(default_factory=tuple)
    differing_fields: tuple[FieldDiff, ...] = field(default_factory=tuple)
