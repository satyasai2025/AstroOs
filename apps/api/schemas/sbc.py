"""
AstroOS — Sarvatobhadra Chakra (SBC) API Schemas
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator


class SBCReportRequest(BaseModel):
    moment_utc: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description=(
                "UTC moment to compute the SBC grid at (ISO-8601, must "
                "include timezone offset). Defaults to the current UTC time."
            ),
        ),
    ] = None
    janma_nakshatra: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "28-system (Abhijit-aware) nakshatra token of the natal/"
                "Janma element to check Vedha hits against, e.g. "
                "'ashwini' or 'abhijit'. Omit to get the grid snapshot only."
            ),
        ),
    ] = None

    @field_validator("moment_utc")
    @classmethod
    def _require_tz(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            raise ValueError("moment_utc must include a timezone offset")
        return v


class SBCGridPlanetResponse(BaseModel):
    planet: str
    nakshatra: str
    cellnum: int
    rashi: str
    rashi_degree: float
    is_retrograde: bool
    is_combust: bool
    speed_deg_per_day: float


class SBCVedhaHitResponse(BaseModel):
    planet: str
    direction: str
    from_nakshatra: str
    score: float


class SBCVedhaResultResponse(BaseModel):
    hits: list[SBCVedhaHitResponse]
    total_score: float
    zeroed_by_malefic_conjunction: bool


class SBCReportResponse(BaseModel):
    moment_utc: datetime
    tithi_number: int
    positions: list[SBCGridPlanetResponse]
    janma_nakshatra: Optional[str] = None
    vedha_result: Optional[SBCVedhaResultResponse] = None


class SBCScanRequest(BaseModel):
    janma_nakshatra: Annotated[
        str,
        Field(description="28-system (Abhijit-aware) nakshatra token of the natal/Janma element to scan for."),
    ]
    start_utc: Annotated[datetime, Field(description="UTC start of the scan range (ISO-8601, must include timezone offset).")]
    end_utc: Annotated[datetime, Field(description="UTC end of the scan range (ISO-8601, must include timezone offset).")]
    step_days: Annotated[
        int,
        Field(default=1, ge=1, le=30, description="Days between samples. Daily by default; see SBCScanEngine's granularity caveat."),
    ] = 1

    @field_validator("start_utc", "end_utc")
    @classmethod
    def _require_tz_scan(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("start_utc/end_utc must include a timezone offset")
        return v


class SBCScanHitResponse(BaseModel):
    moment_utc: datetime
    vedha_result: SBCVedhaResultResponse


class SBCScanResponse(BaseModel):
    janma_nakshatra: str
    start_utc: datetime
    end_utc: datetime
    step_days: int
    hits: list[SBCScanHitResponse]
