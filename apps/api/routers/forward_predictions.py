"""
AstroOS — Forward Predictions Router (Phase 1 & Phase 4 API)

Provides endpoint for forward scanning event predictions:
  POST /api/v1/predictions/forward-scan
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from apps.api.config import get_settings
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.forward_scanner import ForwardScanner, ForwardScanResult
from apps.api.services.horoscope_engine import HoroscopeEngine

router = APIRouter(prefix="/predictions", tags=["Forward Prediction Engine"])


class ForwardCandidateSchema(BaseModel):
    event_type: str
    signature_id: str
    timing_window_start: str
    timing_window_end: str
    peak_score: int
    confidence: float
    promise_status: str
    primary_drivers: list[str]
    supporting_factors: list[str]
    opposing_factors: list[str]
    classical_source: str
    evidence_fact_keys: list[str]
    uncertainty_disclosure: str


class ForwardScanRequest(BaseModel):
    birth_datetime_utc: Optional[str] = Field(None, description="ISO-8601 UTC birth datetime")
    latitude: Optional[float] = Field(28.6139, description="Birth latitude")
    longitude: Optional[float] = Field(77.2090, description="Birth longitude")
    target_start_date: Optional[date] = Field(None, description="Start of forward scan range")
    target_end_date: Optional[date] = Field(None, description="End of forward scan range")
    event_types: Optional[list[str]] = Field(
        default=["marriage", "job_change", "financial_gain", "relocation", "health", "progeny", "property"],
        description="Event types to evaluate",
    )
    min_confidence: Optional[float] = Field(0.0, description="Minimum confidence threshold (0.0 - 1.0)")


class ForwardScanResponse(BaseModel):
    chart_id: str
    target_start: str
    target_end: str
    event_types_evaluated: list[str]
    candidates_evaluated: int
    signatures_matched: int
    total_slices_evaluated: int
    deterministic_signature: str
    uncertainty_disclosure: str
    scan_version: str
    candidates: list[ForwardCandidateSchema]


@router.post(
    "/forward-scan",
    response_model=ForwardScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan natal chart for future timing windows and event signatures",
)
async def forward_scan_events(body: ForwardScanRequest) -> ForwardScanResponse:
    settings = get_settings()
    wrapper = EphemerisWrapper(settings.EPHEMERIS_PATH)
    horoscope_engine = HoroscopeEngine(wrapper)
    dasha_engine = DashaEngine(wrapper)

    dt = (
        datetime.fromisoformat(body.birth_datetime_utc)
        if body.birth_datetime_utc
        else datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc)
    )
    lat = body.latitude if body.latitude is not None else 28.6139
    lon = body.longitude if body.longitude is not None else 77.2090

    chart = horoscope_engine.generate_d1(dt, lat, lon, ayanamsa="lahiri")
    dasha_tree = dasha_engine.compute_vimshottari(dt, lat, lon, ayanamsa="lahiri")

    scanner = ForwardScanner()
    scan_res: ForwardScanResult = scanner.scan(
        chart=chart,
        dasha_tree=dasha_tree,
        event_types=body.event_types,
        target_start=body.target_start_date,
        target_end=body.target_end_date,
    )

    filtered_candidates = [
        c for c in scan_res.candidates
        if c.confidence >= (body.min_confidence or 0.0)
    ]

    return ForwardScanResponse(
        chart_id=scan_res.chart_id,
        target_start=scan_res.target_start.isoformat(),
        target_end=scan_res.target_end.isoformat(),
        event_types_evaluated=list(scan_res.event_types_evaluated),
        candidates_evaluated=scan_res.total_slices_evaluated,
        signatures_matched=len(filtered_candidates),
        total_slices_evaluated=scan_res.total_slices_evaluated,
        deterministic_signature=scan_res.deterministic_signature,
        uncertainty_disclosure=scan_res.uncertainty_disclosure,
        scan_version=scan_res.scan_version,
        candidates=[
            ForwardCandidateSchema(
                event_type=c.event_type,
                signature_id=c.signature_id,
                timing_window_start=c.timing_window_start.isoformat(),
                timing_window_end=c.timing_window_end.isoformat(),
                peak_score=c.peak_score,
                confidence=c.confidence,
                promise_status=c.promise_status,
                primary_drivers=list(c.primary_drivers),
                supporting_factors=list(c.supporting_factors),
                opposing_factors=list(c.opposing_factors),
                classical_source=c.classical_source,
                evidence_fact_keys=list(c.evidence_fact_keys),
                uncertainty_disclosure=c.uncertainty_disclosure,
            )
            for c in filtered_candidates
        ],
    )
