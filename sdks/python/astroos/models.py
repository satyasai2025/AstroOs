"""AstroOS Python SDK — Models (v2.2.0)

Pydantic request/response models for AstroOS API.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class ChartReportRequest(BaseModel):
    birth_datetime_utc: str
    latitude: float
    longitude: float
    ayanamsa: str = "lahiri"
    house_system: str = "W"  # "W"hole-sign, "P"lacidus, "K"och, "E"qual
    title: Optional[str] = None
    subject_name: Optional[str] = None


class ChartReportResponse(BaseModel):
    title: str
    subject_name: str
    sections: list[dict[str, Any]]


class BirthDataRequest(BaseModel):
    birth_datetime_utc: str
    latitude: float
    longitude: float
    ayanamsa: str = "lahiri"
    house_system: str = "W"


class YogaEvaluationResponse(BaseModel):
    yoga_id: str
    yoga_name: str
    present: bool
    strength_score: Optional[int] = None
    counter_examples: list[str] = []


class JobStatusResponse(BaseModel):
    job_id: str
    pool: str
    status: str
    progress: dict[str, int]
    error: Optional[str] = None
