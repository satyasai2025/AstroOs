"""
AstroOS — Relocation Analysis API Schemas

DTO boundary for POST /api/v1/relocation/analyze. Converts domain objects
(Fact, TechniqueExecutionResult, RuleTrigger) to/from HTTP in the router
layer; no domain types leak through here. Mirrors the discipline of
schemas/technique.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class RelocationAnalyzeRequest(BaseModel):
    birth_utc: datetime = Field(description="ISO 8601 UTC birth datetime")
    birth_lat: float = Field(ge=-90.0, le=90.0)
    birth_lon: float = Field(ge=-180.0, le=180.0)
    target_lat: float = Field(ge=-90.0, le=90.0)
    target_lon: float = Field(ge=-180.0, le=180.0)
    ayanamsa: str = "lahiri"
    house_system: str = "P"


class RelocationAngleSchema(BaseModel):
    degree: float
    sign: str
    label: float
    harmonic_family: str


class RelocationTriggerSchema(BaseModel):
    rule_id: str
    rule_name: str
    role: str
    status: str
    provenance: str
    matched_conditions: list[str] = Field(default_factory=list)
    failed_conditions: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    explanation: str


class RelocationTechniqueSchema(BaseModel):
    technique_id: str
    technique_name: str
    confidence: int
    confidence_basis: str
    is_matched: bool
    triggers: list[RelocationTriggerSchema] = Field(default_factory=list)


class RelocationAnalyzeResponse(BaseModel):
    birth: dict[str, float]
    target: dict[str, float]
    angles: dict[str, RelocationAngleSchema]
    techniques: list[RelocationTechniqueSchema]
    facts: dict[str, Any] = Field(default_factory=dict)
