"""
AstroOS — Research Case Domain Objects (Module 27)

Pure-Python dataclasses for the event-centric research pipeline:
ResearchCase (person + life events), LifeEvent, EventSnapshot (the
immutable per-moment astrological snapshot), Attachment, plus the DTOs
the import service and pattern-discovery engine return
(CaseImportResult, ExtractedFeature, PatternDimension, DiscoveredPattern).

No ORM/Pydantic dependency — matching every other domain module
(domain/events.py, domain/research.py, domain/dasha.py, ...).

Nothing here performs an astrology calculation. Every Dasha/Transit/
Shadbala/Yoga value on an EventSnapshot is produced by the import/snapshot
service (using DashaEngine/TransitEngine/ShadbalaEngine/YogaEngine) and
carried as-is. Snapshots are immutable by contract: a changed algorithm
appends a new snapshot_version, never overwrites an existing snapshot.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class PersonInfo:
    """Birth and identity data for one research subject."""

    name: Optional[str]
    gender: str
    dob: date
    tob: Optional[str]
    place: str
    latitude: float
    longitude: float
    timezone: str
    source: str
    birth_time_confidence: str = "medium"
    country: Optional[str] = None
    """Free-text country/region, added after the initial Module 27 rollout —
    optional so older callers/imports are unaffected."""


@dataclass(frozen=True)
class Attachment:
    """A file/document attached to a research case or life event."""

    type: str = "notes"
    filename: str = ""
    url: Optional[str] = None
    content_type: Optional[str] = None


@dataclass(frozen=True)
class DashaSnapshot:
    """Dasha state at a point in time."""

    mahadasha: str
    antardasha: str
    pratyantar: Optional[str] = None


@dataclass(frozen=True)
class EventSnapshot:
    """One immutable astrological snapshot at a moment within an event window."""

    snapshot_date: date
    snapshot_version: str = "1.0"
    current_dasha: Optional[DashaSnapshot] = None
    transits: dict[str, bool] = field(default_factory=dict)
    shadbala: dict[str, float] = field(default_factory=dict)
    active_yogas: list[str] = field(default_factory=list)
    varga_activations: dict[str, str] = field(default_factory=dict)
    nakshatra_activations: list[str] = field(default_factory=list)
    house_lord_statuses: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LifeEvent:
    """One recorded life event within a research case."""

    id: Optional[str]
    type: str
    event_date: date
    event_time: Optional[str] = None
    event_place: Optional[str] = None
    severity: str = "moderate"
    category: str = "Other"
    verified: bool = False
    confidence: str = "medium"
    source: str = "self-report"
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    event_window_days: int = 30
    notes: Optional[str] = None
    snapshots: list[EventSnapshot] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)


@dataclass(frozen=True)
class ResearchCase:
    """Top-level container: one person + their life events + attachments."""

    id: Optional[str]
    person: PersonInfo
    ayanamsa: str
    house_system: str
    divisional_charts: list[str]
    rectified: bool
    rectification_notes: Optional[str]
    life_events: list[LifeEvent]
    research_notes: Optional[str] = None
    attachments: list[Attachment] = field(default_factory=list)
    source_batch: Optional[str] = None


# ── Import service DTOs ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class CaseImportResult:
    """Result of importing one case."""

    research_case_id: str
    person_name: Optional[str]
    dob: date
    total_events: int
    total_snapshots_created: int
    duplicate: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SnapshotRebuildResult:
    """Result of a bulk snapshot rebuild (Advanced Research tool)."""

    cases_processed: int
    snapshots_created: int
    snapshot_version: str
    errors: list[str] = field(default_factory=list)


# ── Feature extraction / pattern discovery DTOs ─────────────────────────────


@dataclass(frozen=True)
class ExtractedFeature:
    """One normalised feature extracted from an event snapshot."""

    feature_name: str
    feature_value: str | float | bool
    feature_category: str  # yoga, dasha, transit, shadbala, house, nakshatra, varga
    event_type: str
    research_case_id: str
    event_date: date
    confidence: float = 1.0


@dataclass(frozen=True)
class PatternDimension:
    """One dimension of a discovered pattern."""

    dimension: str  # mahadasha, transit_house, yoga, etc.
    value: str  # "Jupiter", "7th_house", "Gajakesari"
    frequency: float  # 0.0 - 1.0 (proportion of cases)
    count: int
    expected_by_chance: float = 0.0
    significance: float = 0.0

    @property
    def lift_score(self) -> float:
        """How many times more common this dimension-value is than chance."""
        return self.frequency / self.expected_by_chance if self.expected_by_chance > 0 else 0.0


@dataclass(frozen=True)
class DiscoveredPattern:
    """One discovered pattern combination for an event type."""

    event_type: str
    pattern_id: str
    dimensions: list[PatternDimension]
    sample_size: int
    confidence_score: float
    description: str
    supporting_case_ids: frozenset[str] = frozenset()
    """The exact research_case_id set whose data produced this pattern —
    the pattern's reproducibility/evidence trail."""

    @property
    def lift_score(self) -> float:
        """The strongest single dimension's lift, as this pattern's headline lift."""
        return max((d.lift_score for d in self.dimensions), default=0.0)
