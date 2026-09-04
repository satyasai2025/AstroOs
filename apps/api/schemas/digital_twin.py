"""
AstroOS — Digital Twin Pydantic Schemas

Request/response schemas for the Digital Twin API endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

class TwinModificationRequest(BaseModel):
    """Schema for creating a single modification."""
    modification_type: str = Field(..., description="Type of modification (e.g. planet_position, house_cusp)")
    target_id: str = Field(..., description="Target element (e.g. 'Mars', 'house_1', 'ascendant')")
    new_value: Any = Field(..., description="New value for the target")
    reason: Optional[str] = Field(None, description="Optional reason for this modification")


class DigitalTwinUpdateRequest(BaseModel):
    """Schema for adding modifications to an existing twin."""
    modifications: list[TwinModificationRequest] = Field(..., description="Modifications to apply")

class TwinModificationResponse(BaseModel):
    """Schema for a single modification in responses."""
    id: uuid.UUID
    modification_type: str
    target_id: str
    old_value: Any = None
    new_value: Any = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None

class DigitalTwinCreate(BaseModel):
    """Schema for creating a new digital twin."""
    name: str = Field(..., description="Name for this digital twin scenario")
    description: Optional[str] = Field(None, description="Description of the scenario")
    original_chart_id: uuid.UUID = Field(..., description="ID of the original birth chart")
    modifications: list[TwinModificationRequest] = Field(default_factory=list)

class DigitalTwinResponse(BaseModel):
    """Schema for a digital twin in responses."""
    id: uuid.UUID
    original_chart_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    version: int
    modifications: list[TwinModificationResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class TwinComparisonRequest(BaseModel):
    """Schema for comparing a twin to its original chart."""
    include_details: bool = Field(True, description="Include field-by-field comparison")

class TwinComparisonResponse(BaseModel):
    """Schema for twin comparison results."""
    twin_id: uuid.UUID
    original_chart_id: uuid.UUID
    total_modifications: int
    field_diffs: list[dict[str, Any]] = Field(default_factory=list)
    metrics_before: Optional[dict[str, Any]] = None
    metrics_after: Optional[dict[str, Any]] = None
    summary: Optional[str] = None

class DigitalTwinListResponse(BaseModel):
    """Schema for listing digital twins."""
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    original_chart_id: uuid.UUID
    status: str
    version: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class TwinOperationResult(BaseModel):
    """Schema for a single simulation operation result."""
    operation_type: str
    applied_at: Optional[datetime] = None
    success: bool = True
    changes: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class TwinSimulationRequest(BaseModel):
    """Schema for running simulation operations on a twin."""
    operations: list[dict[str, Any]] = Field(..., description="List of simulation operations to apply sequentially")
