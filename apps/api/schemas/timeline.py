"""
AstroOS — Timeline API Schemas (Module 15 — HTTP surface)

Pydantic request/response models for the Timeline endpoint.

TimelineEngine.build_timeline() consumes tuple[EventAnalysis, ...], built
from EventEngine.analyze_batch() against a NatalSnapshot + Dasha trees.
Neither EventAnalysis nor NatalSnapshot is modelled in full here — the
router only reads/serialises the flat fields TimelineEngine's own
aggregation logic (_build_summary, _build_dasha_breakdown, _find_clusters)
actually consumes: event_date, title, category, is_verified, and each
entry's active_dashas. Same "don't model unread nested graphs" convention
established in schemas/report.py.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]


# ── Request ───────────────────────────────────────────────────────────────────


class TimelineBuildRequest(BaseModel):
    """
    Builds a Timeline from the events already recorded (via POST /events)
    against the birth chart identified by this same birth data — chart
    identity is derived the same way dasha/divisional do (deduped on
    birth moment + location + ayanamsa + house system), not passed as a
    separate chart_id, so this endpoint never drifts from the chart_id
    those events were actually recorded under.
    """

    birth_datetime_utc: Annotated[
        datetime,
        Field(description="UTC birth datetime (ISO-8601, must include timezone offset)."),
    ]
    latitude: Annotated[float, Field(ge=-90.0, le=90.0, description="Geographic latitude.")]
    longitude: Annotated[float, Field(ge=-180.0, le=180.0, description="Geographic longitude.")]
    ayanamsa: Annotated[AyanamsaCode, Field(default="lahiri")] = "lahiri"
    house_system: Annotated[HouseSystemCode, Field(default="W")] = "W"
    category: Optional[str] = Field(default=None, description="Filter events by category.")
    limit: Annotated[int, Field(default=500, ge=1, le=2000)] = 500
    offset: Annotated[int, Field(default=0, ge=0)] = 0
    window_days: Annotated[
        int, Field(default=365, ge=1, description="Cluster-detection sliding window, in days.")
    ] = 365
    min_events: Annotated[
        int, Field(default=2, ge=1, description="Minimum events for a cluster candidate window.")
    ] = 2

    @field_validator("birth_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware.")
        return v


# ── Response ──────────────────────────────────────────────────────────────────


class TimelineEntryResponse(BaseModel):
    """Response payload describing timeline entry data."""
    event_id: uuid.UUID
    event_date: date
    title: str
    category: Optional[str]
    is_verified: bool
    active_dasha_systems: list[str] = Field(
        default_factory=list,
        description="Dasha systems with an active chain at this event's date.",
    )


class TimelineSummaryResponse(BaseModel):
    """Response payload describing timeline summary data."""
    total_events: int
    date_range: tuple[date, date]
    events_per_category: dict[str, int]
    events_per_dasha_system: dict[str, int]
    verified_count: int
    unverified_count: int


class TimelineDashaPeriodSpanResponse(BaseModel):
    """Response payload describing timeline dasha period span data."""
    system: str
    lord: str
    level: int
    start_date: date
    end_date: date
    event_ids: list[uuid.UUID]
    event_count: int


class TemporalClusterResponse(BaseModel):
    """Response payload describing temporal cluster data."""
    start_date: date
    end_date: date
    center_date: date
    event_ids: list[uuid.UUID]
    event_count: int
    density: float


class TimelineResponse(BaseModel):
    """Response payload describing timeline data."""
    chart_id: uuid.UUID
    entries: list[TimelineEntryResponse]
    summary: TimelineSummaryResponse
    dasha_breakdown: dict[str, list[TimelineDashaPeriodSpanResponse]]
    clusters: list[TemporalClusterResponse]
    timeline_version: str
