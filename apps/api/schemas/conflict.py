"""
AstroOS — Conflict API Schemas (Phase D)

Pydantic response models for doctrinal conflict endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel


class ConflictPositionResponse(BaseModel):
    tradition: str
    source_ref: str
    position: str
    arguments: list[str] = []
    adherents: list[str] = []


class ConflictEvidenceResponse(BaseModel):
    analysis: str = ""
    for_parashari: list[str] = []
    for_kp: list[str] = []
    for_jaimini: list[str] = []


class ConflictResolutionResponse(BaseModel):
    status: str
    resolution: str = ""
    recommended_position: str = ""
    weight_of_evidence: str = ""


class ConflictSummaryResponse(BaseModel):
    id: str
    name: str
    domain: str = ""
    status: str = "active"
    resolution_status: str = "unresolved"


class ConflictListResponse(BaseModel):
    conflicts: list[ConflictSummaryResponse]
    total: int


class ConflictDetailResponse(BaseModel):
    id: str
    name: str
    topic: str = ""
    domain: str = ""
    status: str = "active"
    confidence: str = "high"
    positions: list[ConflictPositionResponse] = []
    evidence: ConflictEvidenceResponse | None = None
    resolution: ConflictResolutionResponse | None = None
    related_conflicts: list[str] = []
