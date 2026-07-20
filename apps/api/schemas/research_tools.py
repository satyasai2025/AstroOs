"""
AstroOS — Research Tools API Schemas (Phase I.4)

Pydantic request/response models for:
  - Research mode toggle
  - Query logging
  - Hypothesis validation workflow
  - CSV/JSON research export
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Research Mode ──────────────────────────────────────────────────────────


class ResearchModeUpdateRequest(BaseModel):
    """Request to update research mode status."""
    enabled: bool = Field(
        description="When true, all queries are logged for reproducibility."
    )


class ResearchModeResponse(BaseModel):
    """Response describing research mode status."""
    enabled: bool
    user_id: uuid.UUID
    total_logged_queries: int = 0


# ── Query Logs ──────────────────────────────────────────────────────────────


class QueryLogResponse(BaseModel):
    """Response describing a query log entry."""
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    request_payload: dict[str, Any] = {}
    response_summary: str = ""
    duration_ms: int = 0
    created_at: Optional[datetime] = None


class QueryLogListResponse(BaseModel):
    """Response describing query log list data."""
    logs: list[QueryLogResponse]
    total: int
    limit: int
    offset: int


# ── Hypothesis Validation ────────────────────────────────────────────────────


class HypothesisValidationCreateRequest(BaseModel):
    """Request to flag a hypothesis for human review."""
    hypothesis_id: str = Field(
        min_length=1, max_length=50,
        description="The hypothesis template ID (e.g. 'HYP-001').",
    )
    chart_id: uuid.UUID
    project_id: uuid.UUID
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1)
    domain: str = Field(min_length=1, max_length=50)
    hypothesis_data: dict[str, Any] = Field(
        default_factory=dict,
        description="The full hypothesis object as a dict.",
    )
    ai_generated: bool = True


class HypothesisValidationUpdateRequest(BaseModel):
    """Request to confirm or reject a flagged hypothesis."""
    status: str = Field(
        pattern="^(confirmed|rejected)$",
        description="'confirmed' or 'rejected'",
    )
    reviewer_notes: Optional[str] = Field(
        default=None, max_length=2000,
        description="Notes from the human reviewer.",
    )


class HypothesisValidationResponse(BaseModel):
    """Response describing a hypothesis validation record."""
    id: uuid.UUID
    hypothesis_id: str
    chart_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str
    domain: str
    ai_generated: bool
    status: str
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class HypothesisValidationListResponse(BaseModel):
    """Response describing hypothesis validation list data."""
    validations: list[HypothesisValidationResponse]
    total: int
    limit: int
    offset: int


# ── Research Export ──────────────────────────────────────────────────────────


class ResearchExportRequest(BaseModel):
    """Request to export research data with citations."""

    format: str = Field(
        default="csv", pattern="^(csv|json)$",
        description="Export format: 'csv' or 'json'.",
    )
    include_detail: bool = Field(
        default=True,
        description="If true, include per-planet and per-yoga detail rows. "
                    "If false, one row per snapshot only.",
    )
