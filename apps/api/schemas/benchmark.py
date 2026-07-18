"""
AstroOS — Benchmark API Schemas (Phase C)

Request/response contracts for the standalone benchmark validation endpoint.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BenchmarkValidateRequest(BaseModel):
    """Validate a chart against GC-MASTER by providing birth data."""
    birth_datetime_utc: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    ayanamsa: str = "lahiri"
    house_system: str = "W"
    subject_name: str = ""
    reference_id: Optional[str] = None
    include_houses: bool = True
    include_vargas: bool = True


class BenchmarkValidateAllRequest(BaseModel):
    """Run validation against all GC-MASTER references at once."""
    ayanamsa: str = "lahiri"
    include_houses: bool = True
    include_vargas: bool = True


class PlanetBenchmarkResultResponse(BaseModel):
    planet: str
    computed_longitude: float
    expected_longitude: float
    error_degrees: float
    within_tolerance: bool


class HouseCuspBenchmarkResponse(BaseModel):
    house_number: int
    house_system: str
    computed_cusp: float
    expected_cusp: float
    error_degrees: float
    within_tolerance: bool


class VargaBenchmarkResponse(BaseModel):
    varga_code: str
    planet: str
    computed_rashi: str
    expected_rashi: str
    matched: bool


class BenchmarkDetailResponse(BaseModel):
    """One chart's validation detail."""
    reference_id: str
    reference_name: str
    calc_passed: bool
    calc_mean_error: float
    calc_max_error: float


class BenchmarkSummaryResponse(BaseModel):
    """Aggregate result across one or more reference charts."""
    total_charts: int
    passed: int
    failed: int
    overall_mean_error: float
    family_summary: dict  # {"calc": {"passed": N, "failed": N}, "house": ..., "varga": ...}
    details: list[BenchmarkDetailResponse]
    timestamp: datetime


class BenchmarkValidateResponse(BaseModel):
    status: str  # "passed" | "failed"
    summary: BenchmarkSummaryResponse
