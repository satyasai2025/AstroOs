"""
AstroOS — Timeline Domain Objects (Module 15, Phase 1)

Chronological timeline models that compose EventAnalysis objects into an
ordered, annotated view — sorted by date, grouped by Dasha period, and
enriched with density and cluster analysis.

Pure Python dataclasses — no ORM/Pydantic dependency, matching the
convention in every other domain module in this codebase
(domain/events.py, domain/dasha.py, domain/yoga.py, etc.).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Optional

from apps.api.domain.dasha import DashaPeriod
from apps.api.domain.events import EventAnalysis


@dataclass(frozen=True)
class TimelineEntry:
    """
    One event positioned on a timeline.

    Wraps an EventAnalysis with sort-relevant fields denormalised for O(1)
    chronological ordering. The full analysis is accessible through the
    `analysis` field — callers who need RuleResult details, active Dashas,
    or Transit data can traverse into it; callers who only need to render
    a timeline list can read the flat fields without touching EventAnalysis.
    """

    event_id: uuid.UUID
    event_date: date
    title: str
    category: Optional[str]
    is_verified: bool
    sort_key: str  # ISO-8601 date string, enables reliable tuple sorting
    analysis: EventAnalysis  # full per-event context, accessible on demand

    def __lt__(self, other: TimelineEntry) -> bool:
        """Default sort by (event_date, title) for stable ordering."""
        if self.event_date != other.event_date:
            return self.event_date < other.event_date
        return self.title < other.title


@dataclass(frozen=True)
class TimelineDashaPeriodSpan:
    """
    One contiguous Dasha period with the events that fell within it.

    Generated per Dasha system during timeline construction. A span is
    uniquely identified by (system, lord, level, start_date, end_date).
    """

    system: str  # e.g. "vimshottari"
    lord: str  # e.g. "jupiter"
    level: int  # 1 = Mahadasha .. 5 = Prana
    start_date: date
    end_date: date
    event_ids: tuple[uuid.UUID, ...]
    event_count: int


@dataclass(frozen=True)
class TemporalCluster:
    """
    A statistically dense period where events cluster beyond background
    density. Detected via sliding-window analysis — windows with event
    density above the configured threshold are merged into contiguous
    cluster regions.

    The center_date is the midpoint of the densest window within the
    cluster region. active_dashas records which Dasha periods were
    running across the cluster's midpoint date (not averaged across
    the cluster's full span).
    """

    start_date: date
    end_date: date
    center_date: date
    events: tuple[TimelineEntry, ...]
    event_count: int
    density: float  # events per year within the cluster span
    active_dashas: dict[str, tuple[DashaPeriod, ...]]  # system -> chain at center_date


@dataclass(frozen=True)
class TimelineSummary:
    """Aggregate statistics across the full timeline."""

    total_events: int
    date_range: tuple[date, date]  # (earliest, latest) — both equal if single event
    events_per_category: dict[str, int]  # category name -> count
    events_per_dasha_system: dict[str, int]  # system name -> total event assignments
    verified_count: int
    unverified_count: int


@dataclass(frozen=True)
class Timeline:
    """
    Top-level container for one chart's fully-built event timeline.

    entries are always sorted chronologically (by event_date, stable
    tie-breaking by title). All derived fields (summary, dasha_breakdown,
    clusters) are computed once at construction and stored; the timeline
    itself is immutable.

    timeline_version identifies which version of TimelineEngine's build
    logic produced this Timeline — same auditability convention as
    EventAnalysis.analysis_version and YogaResult.rule_version.
    """

    chart_id: uuid.UUID
    entries: tuple[TimelineEntry, ...]
    summary: TimelineSummary
    dasha_breakdown: dict[str, tuple[TimelineDashaPeriodSpan, ...]]  # system -> spans
    clusters: tuple[TemporalCluster, ...]
    timeline_version: str = "1.0"

    @property
    def total_events(self) -> int:
        return self.summary.total_events

    @property
    def date_range(self) -> tuple[date, date]:
        return self.summary.date_range

    @property
    def is_empty(self) -> bool:
        return len(self.entries) == 0
