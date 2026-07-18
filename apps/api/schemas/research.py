"""
AstroOS — Research API Schemas (Module 17, Phase 1)

Pydantic request/response models for the Research Engine — the hub
other analysis modules (Statistics, Visualization, AI, Report) build on.
Converts to/from the domain objects in apps/api/domain/research.py in
the router layer only; schemas never leak into ResearchEngine or
ResearchRepository, same DTO-boundary discipline as apps/api/schemas/events.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

ProjectStatus = Literal["active", "archived"]
QueryOperator = Literal["==", "!=", ">", "<", ">=", "<=", "in"]


# ── Projects ──────────────────────────────────────────────────────────────────


class ResearchProjectCreateRequest(BaseModel):
    user_id: uuid.UUID
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    dataset_id: Optional[uuid.UUID] = None


class ResearchProjectUpdateRequest(BaseModel):
    """
    All fields optional — a PATCH. The router forwards only fields
    actually present in the request body via `model_dump(exclude_unset=True)`,
    same convention as EventUpdateRequest.
    """

    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    dataset_id: Optional[uuid.UUID] = None


class ResearchProjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    dataset_id: Optional[uuid.UUID] = None


class ResearchProjectListResponse(BaseModel):
    projects: list[ResearchProjectResponse]
    total: int


# ── Experiments ───────────────────────────────────────────────────────────────


class ResearchExperimentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    hypothesis: str = Field(min_length=1)
    methodology: str = Field(min_length=1)


class ResearchExperimentUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    hypothesis: Optional[str] = None
    methodology: Optional[str] = None
    status: Optional[str] = None
    findings: Optional[str] = None


class ResearchExperimentCompleteRequest(BaseModel):
    findings: str = Field(min_length=1)


class ResearchExperimentAssignSnapshotsRequest(BaseModel):
    snapshot_ids: list[uuid.UUID] = Field(min_length=1)


class ResearchExperimentResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    hypothesis: str
    methodology: str
    status: str
    snapshot_ids: list[uuid.UUID]
    findings: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ResearchExperimentListResponse(BaseModel):
    experiments: list[ResearchExperimentResponse]
    total: int


# ── Snapshots ─────────────────────────────────────────────────────────────────


class SnapshotCaptureRequest(BaseModel):
    """
    Captures a snapshot referencing an already-computed chart.

    ResearchEngine.capture_snapshot() also accepts already-computed engine
    outputs (yogas, shadbala, dasha trees, etc.) to bundle in, but
    ResearchRepository.save_snapshot() only currently persists chart_id/
    label/yogas-summary/sarvashtakavarga-total to snapshot_json — round
    trips through get_snapshot()/list_snapshots() only ever rehydrate
    id/project_id/chart_id/label/captured_at/snapshot_version (chart_ref
    and every other section come back None). This endpoint exposes the
    subset of capture_snapshot() that is actually observable end-to-end
    over HTTP today.
    """

    chart_id: uuid.UUID
    label: Optional[str] = Field(default=None, max_length=300)


class SnapshotResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    chart_id: uuid.UUID
    label: Optional[str]
    captured_at: datetime
    snapshot_version: str


class SnapshotListResponse(BaseModel):
    snapshots: list[SnapshotResponse]
    total: int


# ── Query ─────────────────────────────────────────────────────────────────────


class SnapshotConditionSchema(BaseModel):
    field: str = Field(
        description=(
            "Dotted path navigable by SnapshotAccessor, e.g. "
            "'chart_ref.planets.0.house_number' or 'yogas.0.is_present'."
        )
    )
    operator: QueryOperator
    value: Any = None
    description: str = ""


class SnapshotQueryRequest(BaseModel):
    """A set of conditions combined with AND logic, evaluated in-memory."""

    conditions: list[SnapshotConditionSchema] = Field(default_factory=list)


class SnapshotQueryResponse(BaseModel):
    snapshots: list[SnapshotResponse]
    total: int


# ── Comparison ────────────────────────────────────────────────────────────────


class SnapshotCompareRequest(BaseModel):
    snapshot_a_id: uuid.UUID
    snapshot_b_id: uuid.UUID


class ChartCompareRequest(BaseModel):
    project_id: uuid.UUID = Field(
        description="Project both charts' snapshots must belong to."
    )
    chart_id_a: uuid.UUID
    chart_id_b: uuid.UUID


class FieldDiffResponse(BaseModel):
    field: str
    value_a: Any
    value_b: Any


class SnapshotComparisonResponse(BaseModel):
    snapshot_a_id: uuid.UUID
    snapshot_b_id: uuid.UUID
    chart_id_a: uuid.UUID
    chart_id_b: uuid.UUID
    matching_fields: list[str]
    differing_fields: list[FieldDiffResponse]
