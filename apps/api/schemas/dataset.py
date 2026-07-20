"""Pydantic schemas for the Dataset API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DatasetCreateRequest(BaseModel):
    """Request payload for dataset create operations."""
    dataset_id: str = Field(
        ..., pattern=r"^ASTRO-[A-Z]{2}-[A-Z]+-v\d+\.\d+\.\d+$",
        description="External dataset identifier",
    )
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    source_file: Optional[str] = None
    format: Optional[str] = None
    record_count: int = 0
    field_count: int = 0
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    quality_tier: Optional[str] = None
    lifecycle_stage: str = "Draft"
    checksum_sha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    file_path: Optional[str] = None


class DatasetUpdateRequest(BaseModel):
    """Request payload for dataset update operations."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    record_count: Optional[int] = None
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    quality_tier: Optional[str] = None
    lifecycle_stage: Optional[str] = Field(
        default=None,
        pattern=r"^(Draft|Candidacy|Stable|Deprecated|Archived)$",
    )
    checksum_sha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    file_path: Optional[str] = None


class DatasetResponse(BaseModel):
    """Response payload describing dataset data."""
    id: uuid.UUID
    dataset_id: str
    name: str
    description: Optional[str] = None
    source_file: Optional[str] = None
    format: Optional[str] = None
    record_count: int = 0
    field_count: int = 0
    quality_score: Optional[float] = None
    quality_tier: Optional[str] = None
    lifecycle_stage: str
    checksum_sha256: Optional[str] = None
    file_path: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    """Response payload describing dataset list data."""
    datasets: list[DatasetResponse]
    total: int
