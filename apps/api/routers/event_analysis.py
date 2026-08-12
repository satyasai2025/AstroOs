"""
AstroOS — Event Analysis Router (Event Chart → Event Analysis workflow)

The Event Analysis workflow turns a person's natal chart + a chosen event
moment (business launch, marriage, house purchase, ...) into a consultation:
an event-moment chart cast (muhurta), an event-moment transit read, the
active dasha chain, and a structured report.

This router is adapter-only — it validates input, orchestrates the
single-request create (create row → run engine → persist artifact refs →
complete), and maps domain objects onto HTTP responses. All calculation
lives in EventAnalysisEngine / ReportEngine / the sub-engines; all
persistence lives in EventAnalysisRepository.

Endpoints
---------
  POST   /event-analysis                 create + run + persist + return (one request)
  GET    /event-analysis/{id}            fetch one (report + artifact refs)
  GET    /event-analysis?birth_chart_id= list for a chart
  DELETE /event-analysis/{id}            soft-delete
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    get_ephemeris_wrapper,
)
from apps.api.domain.event_analysis import EventAnalysisStatus
from apps.api.domain.user import User
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.event_analysis_repository import EventAnalysisRepository
from apps.api.schemas.event_analysis import (
    EventAnalysisCreateRequest,
    EventAnalysisListResponse,
    EventAnalysisResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.event_analysis_engine import (
    EventAnalysisEngine,
    serialize_dasha_chain,
    serialize_event_chart,
    serialize_transits,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/event-analysis", tags=["event-analysis"])


def _get_event_analysis_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    session: AsyncSession = Depends(get_db_session),
) -> EventAnalysisEngine:
    """Build an EventAnalysisEngine sharing the process-wide EphemerisWrapper
    and a request-scoped birth-chart repository (same lifecycle as the
    horoscope engine factory)."""
    return EventAnalysisEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(session),
    )


def _report_to_dict(report) -> dict:
    """Serialize a ChartReport domain object into a JSON-safe dict."""
    return {
        "metadata": {
            "report_id": str(report.metadata.report_id),
            "report_type": report.metadata.report_type,
            "report_version": report.metadata.report_version,
            "generated_at": report.metadata.generated_at.isoformat(),
            "engine_versions": report.metadata.engine_versions,
            "chart_id": str(report.metadata.chart_id) if report.metadata.chart_id else None,
        },
        "title": report.title,
        "subject_name": report.subject_name,
        "sections": [
            {
                "title": s.title,
                "section_type": s.section_type,
                "content": {
                    "section_type": s.content.section_type,
                    "data": s.content.data,
                },
            }
            for s in report.sections
        ],
    }


def _record_to_response(record, artifacts: Optional[dict] = None) -> EventAnalysisResponse:
    return EventAnalysisResponse(
        id=record.id,
        birth_chart_id=record.birth_chart_id,
        person_id=record.person_id,
        user_id=record.user_id,
        event_name=record.event_name,
        category=record.category,
        event_datetime_utc=record.event_datetime_utc,
        latitude=record.event_latitude,
        longitude=record.event_longitude,
        place_name=record.place_name,
        timezone_iana=record.timezone_iana,
        scope=sorted(record.scope),
        status=record.status.value,
        event_chart_id=record.event_chart_id,
        transit_chart_id=record.transit_chart_id,
        dasha_snapshot_id=record.dasha_snapshot_id,
        overall_score=record.overall_score,
        analysis_report_json=record.analysis_report_json,
        artifacts=artifacts,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


async def _rehydrate_artifacts(record, repo: EventAnalysisRepository) -> dict[str, Optional[dict]]:
    """Lazily pull the artifact payloads referenced by the record's snapshot ids."""
    artifacts: dict[str, Optional[dict]] = {}
    for field in ("event_chart_id", "transit_chart_id", "dasha_snapshot_id"):
        snapshot_id = getattr(record, field)
        artifacts[field] = await repo.get_snapshot_payload(snapshot_id) if snapshot_id else None
    return artifacts


@router.post(
    "",
    response_model=EventAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def create_event_analysis(
    payload: EventAnalysisCreateRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    session: AsyncSession = Depends(get_db_session),
) -> EventAnalysisResponse:
    """
    Create + run + persist + return an Event Analysis in a single request
    (approved change #8). The returned response is COMPLETED — the engine ran
    during this call, its artifacts are stored, and the score/report are set.
    """
    repo = EventAnalysisRepository(session)
    birth_repo = BirthChartRepository(session)

    birth_model = await birth_repo.get_by_id(payload.birth_chart_id)
    if birth_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Birth chart {payload.birth_chart_id} not found.",
        )
    try:
        scope = payload.validate_scope()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    record = await repo.create_event(
        birth_chart_id=payload.birth_chart_id,
        user_id=current_user.id.value,
        event_name=payload.event_name,
        category=payload.category,
        event_datetime_utc=payload.event_datetime_utc,
        event_latitude=payload.latitude,
        event_longitude=payload.longitude,
        place_name=payload.place_name,
        timezone_iana=payload.timezone_iana,
        scope=scope,
        status=EventAnalysisStatus.ANALYZING,
    )
    await session.commit()

    try:
        engine = _get_event_analysis_engine(wrapper=wrapper, session=session)
        result = await engine.analyze(record)
    except ValueError as exc:
        await repo.update_status(record.id, EventAnalysisStatus.FAILED)
        await session.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface as a failed analysis, not a 500
        logger.exception("Event analysis %s failed", record.id)
        await repo.update_status(record.id, EventAnalysisStatus.FAILED)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Event analysis computation failed: {exc}",
        ) from exc

    event_chart_id = await repo.create_snapshot(
        birth_chart_id=record.birth_chart_id,
        snapshot_type="event_chart",
        label=f"{record.event_name} — event chart",
    )
    transit_chart_id = await repo.create_snapshot(
        birth_chart_id=record.birth_chart_id,
        snapshot_type="transit",
        label=f"{record.event_name} — transit",
    )
    dasha_snapshot_id = await repo.create_snapshot(
        birth_chart_id=record.birth_chart_id,
        snapshot_type="dasha",
        label=f"{record.event_name} — dasha chain",
    )
    await repo.set_snapshot_payload(event_chart_id, serialize_event_chart(result.event_chart))
    await repo.set_snapshot_payload(transit_chart_id, serialize_transits(result.transit_results))
    await repo.set_snapshot_payload(dasha_snapshot_id, serialize_dasha_chain(result.dasha_chain))

    completed = await repo.complete_event(
        record.id,
        event_chart_id=event_chart_id,
        transit_chart_id=transit_chart_id,
        dasha_snapshot_id=dasha_snapshot_id,
        analysis_report_json=_report_to_dict(result.report),
        overall_score=result.overall_score,
    )
    await session.commit()

    return _record_to_response(
        completed or record,
        artifacts={
            "report_generated": True,
            "sections": len(result.report.sections),
        },
    )


@router.get(
    "/{event_id}",
    response_model=EventAnalysisResponse,
)
async def get_event_analysis(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> EventAnalysisResponse:
    repo = EventAnalysisRepository(session)
    record = await repo.get_by_id(event_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event analysis not found.")
    if record.user_id != current_user.id.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your analysis.")
    artifacts = await _rehydrate_artifacts(record, repo)
    return _record_to_response(record, artifacts=artifacts)


@router.get(
    "",
    response_model=EventAnalysisListResponse,
)
async def list_event_analyses(
    birth_chart_id: Optional[uuid.UUID] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> EventAnalysisListResponse:
    repo = EventAnalysisRepository(session)
    if birth_chart_id is not None:
        analyses = await repo.list_for_chart(birth_chart_id, limit=limit, offset=offset)
    else:
        analyses = []
    return EventAnalysisListResponse(
        analyses=[_record_to_response(r) for r in analyses],
        total=len(analyses),
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_analysis(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    repo = EventAnalysisRepository(session)
    record = await repo.get_by_id(event_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event analysis not found.")
    if record.user_id != current_user.id.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your analysis.")
    await repo.soft_delete(event_id)
    await session.commit()