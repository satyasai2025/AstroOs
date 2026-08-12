"""
AstroOS — Event Analysis Domain Objects

The Event Analysis workflow turns a person's natal chart + a chosen event
moment (business launch, marriage, house purchase, ...) into an astrological
consultation: an event-moment chart cast (muhurta), an event-moment transit
read, the active dasha chain, the natal promise, and a structured report.

This module holds the domain objects only — no astrology is calculated here.
The engine (services/event_analysis_engine.py) computes everything and the
router persists it; the shapes here are pure dataclasses mirroring the
persisted rows, plus an operation-result container for the engine.

Object layout
-------------
  - EventAnalysisStatus      — lifecycle enum for an analysis row.
  - EVENT_ANALYSIS_SCOPE_FLAGS — the user-selectable analysis dimensions,
    persisted so any report is reproducible (see design decision).
  - EventAnalysisRecord      — one persisted analysis row (`event_analyses`
    table). Stores REFERENCES (ids) to generated event/transit/dasha
    artifacts rather than embedding large chart JSON blobs; only the compact
    report JSON and the overall score live on the row itself.
  - EventAnalysisResult      — the engine's output container: the computed
    domain objects, NOT yet serialized. The router reads this to persist the
    artifact snapshots and assemble the response.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.events import EventAnalysis, NatalSnapshot
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.report import ChartReport
from apps.api.domain.transit import TransitPlanetResult


class EventAnalysisStatus(str, Enum):
    """Lifecycle of one event analysis row."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


# The user-selectable dimensions of an Event Analysis. Default is all seven.
# Each maps onto a ReportEngine section (see ReportEngine.build_event_report).
# Persisted with the analysis so a stored report is always reproducible from
# the flags that produced it.
EVENT_ANALYSIS_SCOPE_FLAGS = frozenset(
    {
        "muhurta",            # event-moment (muhurta) fitness
        "natal_promise",      # relevant houses/lords for the event category
        "dasha_support",      # active dasha chain support
        "transit_influence",  # event-moment transits
        "planetary_strength", # shadbala / planet strength
        "yogas_activated",    # natal + event-chart yogas
        "overall_score",      # overall success score
    }
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EventAnalysisRecord:
    """
    One persisted event analysis. Mirrors the `event_analyses` table.

    Approved storage decision: REFERENCES, not chart JSON blobs. The cast
    event chart, the event-moment transit, and the active dasha chain are
    stored as artifact snapshot rows (see EventChartSnapshotModel) and this
    row keeps only their ids (`event_chart_id`, `transit_chart_id`,
    `dasha_snapshot_id`). The compact structured report is the one JSON kept
    here, plus the numeric `overall_score`.

    `person_id` and `birth_chart_id` both reference `birth_charts.id`. The
    app has no separate Person table — the saved natal chart IS the person;
    `person_id` reserves the field for a future Person entity while
    `birth_chart_id` is the natal chart FK the engine actually loads.
    """

    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    person_id: Optional[uuid.UUID]
    birth_chart_id: uuid.UUID

    event_name: str
    category: Optional[str]
    event_datetime_utc: datetime
    # Coordinates default to the natal place when the event happens there
    # (the create request leaves them unset). Nullable, not float, to match
    # the model column and the optional request fields.
    event_latitude: Optional[float]
    event_longitude: Optional[float]
    place_name: Optional[str]
    timezone_iana: Optional[str]

    scope: frozenset[str]

    status: EventAnalysisStatus
    event_chart_id: Optional[uuid.UUID] = None
    transit_chart_id: Optional[uuid.UUID] = None
    dasha_snapshot_id: Optional[uuid.UUID] = None
    analysis_report_json: Optional[dict] = None
    overall_score: Optional[float] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def event_date(self):
        """Convenience: the event's date component (for display)."""
        return self.event_datetime_utc.date()


@dataclass(frozen=True)
class EventAnalysisResult:
    """
    Engine output — the computed domain objects BEFORE persistence/serialization.

    The router persists the event/transit/dasha artifacts (as snapshot rows
    referenced by id) and the report JSON, then maps this onto the HTTP
    response. `event_analysis` is the EventEngine.analyze() result (context +
    facts + rule results); `dasha_chain` is the active chain resolved at the
    event date; `dasha_tree` is the full tree it was resolved from.
    """

    event_record: EventAnalysisRecord
    natal_snapshot: NatalSnapshot
    event_chart: D1Chart
    transit_results: tuple[TransitPlanetResult, ...]
    dasha_tree: DashaTree
    dasha_chain: tuple[DashaPeriod, ...]
    event_analysis: EventAnalysis
    report: ChartReport
    overall_score: Optional[float]
    scope: frozenset[str] = field(default_factory=frozenset)