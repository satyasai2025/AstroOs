"""
AstroOS — Event Analysis API Schemas

Request/response models for /api/v1/event-analysis. Converts quickly to/from
the domain EventAnalysisRecord in the router layer — schemas never leak into
EventAnalysisRepository or EventAnalysisEngine, same DTO-boundary discipline
as schemas/events.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from apps.api.domain.event_analysis import EVENT_ANALYSIS_SCOPE_FLAGS


class EventAnalysisCreateRequest(BaseModel):
    """Request payload for running (and persisting) an Event Analysis."""
    birth_chart_id: uuid.UUID
    event_name: str = Field(min_length=1, max_length=300)
    category: Optional[str] = None
    event_datetime_utc: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_name: Optional[str] = None
    timezone_iana: Optional[str] = None
    scope: list[str] = Field(
        default_factory=lambda: sorted(EVENT_ANALYSIS_SCOPE_FLAGS)
    )

    def validate_scope(self) -> frozenset[str]:
        """Return the requested scope as a frozenset, rejecting unknown flags."""
        unknown = set(self.scope) - EVENT_ANALYSIS_SCOPE_FLAGS
        if unknown:
            raise ValueError(f"Unknown Event Analysis scope flag(s): {sorted(unknown)}")
        return frozenset(self.scope)


class EventAnalysisResponse(BaseModel):
    """Full persisted Event Analysis, plus (optionally) its artifacts."""
    id: uuid.UUID
    birth_chart_id: uuid.UUID
    person_id: Optional[uuid.UUID]
    user_id: Optional[uuid.UUID]

    event_name: str
    category: Optional[str]
    event_datetime_utc: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    place_name: Optional[str]
    timezone_iana: Optional[str]

    scope: list[str]
    status: str

    event_chart_id: Optional[uuid.UUID]
    transit_chart_id: Optional[uuid.UUID]
    dasha_snapshot_id: Optional[uuid.UUID]
    overall_score: Optional[float]

    analysis_report_json: Optional[dict[str, Any]] = None

    # Artifact payloads — populated by the router after a fresh create, or
    # lazily when a GET requests ?include_artifacts=true.
    artifacts: Optional[dict[str, Any]] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EventAnalysisListResponse(BaseModel):
    """Response payload describing a list of Event Analyses."""
    analyses: list[EventAnalysisResponse]
    total: int