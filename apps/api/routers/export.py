"""
AstroOS — Export Router (Module 21 — HTTP surface)

HTTP adapter layer over ExportEngine. Builds the same Report objects
routers/report.py builds (reusing its private helpers — one report-
construction path, not two), then renders via ExportEngine and returns
the result as a downloadable file (Content-Disposition: attachment).

ExportResult.content is always a str (JSON/Markdown/HTML text) — PDF/DOCX
are explicitly Phase 2 in export_engine.py's ExportFormat enum and are
not exposed here.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.export_domain import ExportFormat
from apps.api.domain.research import AstrologicalSnapshot
from apps.api.routers.report import _build_statistics, _build_timeline, _build_verification
from apps.api.schemas.export import ChartExportRequest, ComparisonExportRequest, ResearchExportRequest
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.export_engine import ExportEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.report_engine import ReportEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])


def _result_response(result) -> Response:
    return Response(
        content=result.content,
        media_type=result.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )


@router.post("/chart", summary="Export a single-chart report to JSON/Markdown/HTML")
async def export_chart_report(
    body: ChartExportRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    horoscope_engine = HoroscopeEngine(wrapper)
    try:
        chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing chart for export: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute chart for export.",
        )

    report = ReportEngine.build_chart_report(
        chart,
        timeline=_build_timeline(body.timeline),
        verification=_build_verification(body.verification),
        stats=_build_statistics(body.statistics),
        title=body.title,
        subject_name=body.subject_name,
        generated_by=body.generated_by,
    )
    result = ExportEngine.export(report, ExportFormat(body.format))
    return _result_response(result)


@router.post("/research", summary="Export a research snapshot report to JSON/Markdown/HTML")
async def export_research_report(body: ResearchExportRequest) -> Response:
    snapshots = tuple(
        AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=body.project_id, chart_id=uuid.uuid4(),
            label=label, captured_at=datetime.now(timezone.utc), chart_ref=None,
        )
        for label in body.snapshot_labels
    )
    report = ReportEngine.build_research_report(
        body.project_id, snapshots,
        stats=_build_statistics(body.statistics),
        title=body.title,
        generated_by=body.generated_by,
    )
    result = ExportEngine.export(report, ExportFormat(body.format))
    return _result_response(result)


@router.post("/comparison", summary="Export a chart-comparison report to JSON/Markdown/HTML")
async def export_comparison_report(
    body: ComparisonExportRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    horoscope_engine = HoroscopeEngine(wrapper)

    async def _compute(c):
        return await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=c.birth_datetime_utc,
            latitude=c.latitude,
            longitude=c.longitude,
            ayanamsa=c.ayanamsa,
            house_system=c.house_system,
        )

    try:
        charts = tuple([await _compute(c) for c in body.charts])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing charts for comparison export: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute charts for comparison export.",
        )

    labels = tuple(c.label for c in body.charts)
    try:
        report = ReportEngine.build_comparison_report(
            charts, labels, title=body.title, generated_by=body.generated_by
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    result = ExportEngine.export(report, ExportFormat(body.format))
    return _result_response(result)
