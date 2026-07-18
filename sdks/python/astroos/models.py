"""AstroOS Python SDK — Models (Phase G)"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class ChartReportRequest(BaseModel):
    birth_datetime_utc: str
    latitude: float
    longitude: float
    ayanamsa: str = "lahiri"
    house_system: str = "placidus"
    title: Optional[str] = None
    subject_name: Optional[str] = None


class ChartReportResponse(BaseModel):
    title: str
    subject_name: str
    sections: list[dict]


class HealthResponse(BaseModel):
    status: str
    checks: dict
    uptime_seconds: int


class MetricsResponse(BaseModel):
    chart_computation_duration_seconds: dict
    api_request_duration_seconds: dict
    db_pool_usage: dict