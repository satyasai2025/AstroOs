"""
AstroOS — Statistics API Schemas (Module 18 — HTTP surface)

Pydantic request/response models for the Statistics Engine. Every
endpoint operates over the snapshots already captured for a Research
project (see routers/research.py) — StatisticsEngine itself never calls
another engine or the database, so the router is the one that fetches
`tuple[AstrologicalSnapshot, ...]` via ResearchRepository first.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# ── Shared request base ─────────────────────────────────────────────────────────


class ProjectScopedRequest(BaseModel):
    """Request payload for project scoped operations."""
    project_id: uuid.UUID = Field(description="Snapshots in this project are analyzed.")


class PlanetDistributionRequest(ProjectScopedRequest):
    """Request payload for planet distribution operations."""
    planet: str = "jupiter"


class CrosstabRequest(ProjectScopedRequest):
    """Request payload for crosstab operations."""
    row_field: str = Field(
        description="Dotted SnapshotAccessor path, e.g. 'chart_ref.ascendant.rashi'."
    )
    col_field: str = Field(description="Dotted SnapshotAccessor path.")


class FullReportRequest(ProjectScopedRequest):
    """Request payload for full report operations."""
    title: str = "Statistical Analysis"
    experiment_id: Optional[uuid.UUID] = None
    filtered_sample_size: Optional[int] = None


# ── Response ──────────────────────────────────────────────────────────────────


class DistributionResponse(BaseModel):
    """Response payload describing distribution data."""
    label: str
    variable: str
    bins: list[str]
    counts: list[int]
    total: int


class NumericSummaryResponse(BaseModel):
    """Response payload describing numeric summary data."""
    label: str
    variable: str
    count: int
    mean: float
    std_dev: float
    min: float
    max: float
    median: float
    q1: float
    q3: float
    sum: float


class CrosstabResponse(BaseModel):
    """Response payload describing crosstab data."""
    label: str
    row_variable: str
    column_variable: str
    row_labels: list[str]
    column_labels: list[str]
    cells: list[list[int]]
    row_totals: list[int]


class DatasetMetadataResponse(BaseModel):
    """Response payload describing dataset metadata data."""
    sample_size: int
    snapshot_count: int
    filtered_sample_size: Optional[int]
    experiment_id: Optional[uuid.UUID]
    engine_version: str
    generated_at: Optional[datetime]


class AggregateReportResponse(BaseModel):
    """Response payload describing aggregate report data."""
    title: str
    metadata: DatasetMetadataResponse
    distributions: list[DistributionResponse]
    numeric_summaries: list[NumericSummaryResponse]
    report_version: str
