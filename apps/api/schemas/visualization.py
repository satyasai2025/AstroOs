"""
AstroOS — Visualization API Schemas (Module 22 — HTTP surface)

Pydantic request/response models for the Visualization Engine.

VisualizationEngine.visualize() dispatches on a `source_data` dict of
raw domain objects (D1Chart, Distribution, Crosstab, snapshots tuple).
This router builds those domain objects itself (same orchestration
pattern as routers/statistics.py and routers/horoscope.py) rather than
asking the client to reconstruct them — a client should never have to
know VisualizationEngine's internal object shapes.

Scope note: chart_wheel, distribution, crosstab, snapshot_comparison,
and relationship_graph are wired. `timeline` visualization (the sixth
type VisualizationEngine supports) is not — it requires the same
multi-engine NatalSnapshot/EventEngine orchestration as
POST /timeline/build, and is left for a follow-up rather than
duplicating that orchestration a second time here. See
VisualizationEngine.available_visualizations() for the full type list;
GET /visualization/types reports this gap explicitly (not silently).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput


class VisualizationOptionsMixin(BaseModel):
    """Mixin providing shared visualization options fields."""
    theme_name: str = "light"
    width: int = Field(default=800, ge=100, le=4000)
    height: int = Field(default=600, ge=100, le=4000)


class ChartWheelRequest(VisualizationOptionsMixin, BirthDataInput):
    """Request payload for chart wheel operations."""


class DistributionVisualizationRequest(VisualizationOptionsMixin):
    """Request payload for distribution visualization operations."""
    project_id: uuid.UUID
    distribution_type: Literal["planet-house", "planet-rashi", "yoga", "verification-strength"]
    planet: str = "jupiter"


class CrosstabVisualizationRequest(VisualizationOptionsMixin):
    """Request payload for crosstab visualization operations."""
    project_id: uuid.UUID
    row_field: str
    col_field: str


class SnapshotGroupVisualizationRequest(VisualizationOptionsMixin):
    """Request payload for snapshot group visualization operations."""
    project_id: uuid.UUID


class VisualizationResultResponse(BaseModel):
    """Response payload describing visualization result data."""
    visualization_type: str
    renderer: str
    version: str
    theme: str
    data: dict[str, Any]
    metadata: dict[str, Any]
    generated_at: str


class AvailableVisualizationResponse(BaseModel):
    """Response payload describing available visualization data."""
    type: str
    renderer: str
    description: str
    required_source: list[str]
    adapter: str
    wired: bool = Field(description="Whether this router currently exposes this type.")


class AvailableVisualizationsResponse(BaseModel):
    """Response payload describing available visualizations data."""
    visualizations: list[AvailableVisualizationResponse]
