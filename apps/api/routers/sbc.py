"""
AstroOS — Sarvatobhadra Chakra (SBC) Router

Endpoints
---------
POST /api/v1/sbc/report — Full 9x9 grid snapshot (all 9 grahas' current
                           SBC nakshatra/cell) at a moment, plus
                           (optionally) the Vedha result onto a
                           specified Janma element.
POST /api/v1/sbc/scan   — Scan a date range for every day a Janma
                           element receives a benefic Vedha hit (see
                           sbc_scan_engine.py's granularity caveat).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.sbc import (
    SBCGridPlanetResponse,
    SBCReportRequest,
    SBCReportResponse,
    SBCScanHitResponse,
    SBCScanRequest,
    SBCScanResponse,
    SBCVedhaHitResponse,
    SBCVedhaResultResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.sbc_report_service import SBCReport, SBCReportService
from apps.api.services.sbc_scan_engine import SBCScanEngine

router = APIRouter(prefix="/sbc", tags=["Sarvatobhadra Chakra"])


def _get_sbc_report_service(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> SBCReportService:
    return SBCReportService(wrapper)


def _get_sbc_scan_engine(
    service: SBCReportService = Depends(_get_sbc_report_service),
) -> SBCScanEngine:
    return SBCScanEngine(service)


def _serialise(report: SBCReport) -> SBCReportResponse:
    vedha_response = None
    if report.vedha_result is not None:
        vedha_response = SBCVedhaResultResponse(
            hits=[
                SBCVedhaHitResponse(
                    planet=h.planet,
                    direction=h.direction,
                    from_nakshatra=h.from_nakshatra,
                    score=h.score,
                )
                for h in report.vedha_result.hits
            ],
            total_score=report.vedha_result.total_score,
            zeroed_by_malefic_conjunction=report.vedha_result.zeroed_by_malefic_conjunction,
        )

    return SBCReportResponse(
        moment_utc=report.moment_utc,
        tithi_number=report.tithi_number,
        positions=[
            SBCGridPlanetResponse(
                planet=p.planet,
                nakshatra=p.nakshatra,
                cellnum=p.cellnum,
                rashi=p.rashi,
                rashi_degree=p.rashi_degree,
                is_retrograde=p.is_retrograde,
                is_combust=p.is_combust,
                speed_deg_per_day=p.speed_deg_per_day,
            )
            for p in report.positions
        ],
        janma_nakshatra=report.janma_nakshatra,
        vedha_result=vedha_response,
    )


@router.post("/report", response_model=SBCReportResponse)
async def get_sbc_report(
    request: SBCReportRequest,
    service: SBCReportService = Depends(_get_sbc_report_service),
) -> SBCReportResponse:
    moment_utc = request.moment_utc or datetime.now(timezone.utc)
    report = service.build_report(moment_utc, janma_nakshatra=request.janma_nakshatra)
    return _serialise(report)


@router.post("/scan", response_model=SBCScanResponse)
async def scan_sbc(
    request: SBCScanRequest,
    engine: SBCScanEngine = Depends(_get_sbc_scan_engine),
) -> SBCScanResponse:
    hits = engine.scan(
        request.janma_nakshatra,
        request.start_utc,
        request.end_utc,
        step_days=request.step_days,
    )
    return SBCScanResponse(
        janma_nakshatra=request.janma_nakshatra,
        start_utc=request.start_utc,
        end_utc=request.end_utc,
        step_days=request.step_days,
        hits=[
            SBCScanHitResponse(moment_utc=h.moment_utc, vedha_result=_serialise(h.report).vedha_result)
            for h in hits
        ],
    )
