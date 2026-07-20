"""
AstroOS — Research Tools Router (Phase I.4)

New endpoints for Phase I.4 Research Tools:
  1. Research mode toggle (query logging for reproducibility)
  2. Hypothesis validation workflow (flag/confirm/reject AI sources)
  3. CSV/JSON research export with knowledge citations

All endpoints require researcher or admin role.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_current_user_from_bearer
from apps.api.domain.user import User
from apps.api.schemas.research_tools import (
    HypothesisValidationCreateRequest,
    HypothesisValidationListResponse,
    HypothesisValidationResponse,
    HypothesisValidationUpdateRequest,
    QueryLogListResponse,
    QueryLogResponse,
    ResearchExportRequest,
    ResearchModeResponse,
    ResearchModeUpdateRequest,
)
from apps.api.services.hypothesis_validation_service import HypothesisValidationService
from apps.api.services.query_log_service import QueryLogService
from apps.api.services.research_csv_exporter import CsvResearchExporter, JsonResearchExporter

router = APIRouter(prefix="/research-tools", tags=["Research Tools"])


def _log_to_response(log) -> QueryLogResponse:
    return QueryLogResponse(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        request_payload=json.loads(log.request_payload) if log.request_payload else {},
        response_summary=log.response_summary,
        duration_ms=log.duration_ms,
        created_at=log.created_at,
    )


def _validation_to_response(v: Any) -> HypothesisValidationResponse:
    return HypothesisValidationResponse(
        id=v.id,
        hypothesis_id=v.hypothesis_id,
        chart_id=v.chart_id,
        project_id=v.project_id,
        title=v.title,
        description=v.description,
        domain=v.domain,
        ai_generated=v.ai_generated,
        status=v.status,
        reviewed_by=v.reviewed_by,
        reviewed_at=v.reviewed_at,
        reviewer_notes=v.reviewer_notes,
        created_at=v.created_at,
        updated_at=v.updated_at,
    )


# ── Research Mode Toggle ─────────────────────────────────────────────────────


@router.get("/mode", response_model=ResearchModeResponse)
async def get_research_mode(
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchModeResponse:
    """Check if research mode is enabled for the current user."""
    service = QueryLogService(session)
    enabled = await service.is_research_mode(current_user.id)
    count = await service.count_logs(user_id=current_user.id)
    return ResearchModeResponse(
        enabled=enabled,
        user_id=current_user.id,
        total_logged_queries=count,
    )


@router.put("/mode", response_model=ResearchModeResponse)
async def set_research_mode(
    body: ResearchModeUpdateRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchModeResponse:
    """Enable or disable research mode for the current user."""
    service = QueryLogService(session)
    await service.set_research_mode(current_user.id, body.enabled)
    enabled = await service.is_research_mode(current_user.id)
    count = await service.count_logs(user_id=current_user.id)
    return ResearchModeResponse(
        enabled=enabled,
        user_id=current_user.id,
        total_logged_queries=count,
    )


@router.get("/logs", response_model=QueryLogListResponse)
async def list_query_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> QueryLogListResponse:
    """List query logs for the current user."""
    service = QueryLogService(session)
    logs = await service.get_logs(
        user_id=current_user.id, action=action, limit=limit, offset=offset
    )
    total = await service.count_logs(user_id=current_user.id, action=action)
    return QueryLogListResponse(
        logs=[_log_to_response(l) for l in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/logs", status_code=status.HTTP_204_NO_CONTENT)
async def clear_query_logs(
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Clear all query logs for the current user."""
    service = QueryLogService(session)
    await service.clear_logs(user_id=current_user.id)


# ── Hypothesis Validation ──────────────────────────────────────────────────


@router.post(
    "/validations",
    response_model=HypothesisValidationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def flag_hypothesis(
    body: HypothesisValidationCreateRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> HypothesisValidationResponse:
    """Flag an AI-generated hypothesis for human confirmation."""
    service = HypothesisValidationService(session)
    validation = await service.flag_hypothesis(
        hypothesis_id=body.hypothesis_id,
        chart_id=body.chart_id,
        project_id=body.project_id,
        title=body.title,
        description=body.description,
        domain=body.domain,
        hypothesis_data=body.hypothesis_data,
        ai_generated=body.ai_generated,
    )
    return _validation_to_response(validation)


@router.get("/validations", response_model=HypothesisValidationListResponse)
async def list_validations(
    project_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> HypothesisValidationListResponse:
    """List hypothesis validations with optional filters."""
    service = HypothesisValidationService(session)
    validations = await service.list_validations(
        project_id=project_id, status=status, limit=limit, offset=offset
    )
    total = await service.count_validations(project_id=project_id, status=status)
    return HypothesisValidationListResponse(
        validations=[_validation_to_response(v) for v in validations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/validations/{validation_id}",
    response_model=HypothesisValidationResponse,
)
async def get_validation(
    validation_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> HypothesisValidationResponse:
    """Get a single hypothesis validation record."""
    service = HypothesisValidationService(session)
    validation = await service.get_validation(validation_id)
    if validation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation record not found.",
        )
    return _validation_to_response(validation)


@router.patch(
    "/validations/{validation_id}",
    response_model=HypothesisValidationResponse,
)
async def update_validation(
    validation_id: uuid.UUID,
    body: HypothesisValidationUpdateRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> HypothesisValidationResponse:
    """Confirm or reject a flagged hypothesis."""
    service = HypothesisValidationService(session)
    if body.status == "confirmed":
        validation = await service.confirm_hypothesis(
            validation_id, current_user.id, notes=body.reviewer_notes
        )
    elif body.status == "rejected":
        validation = await service.reject_hypothesis(
            validation_id, current_user.id, notes=body.reviewer_notes
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{body.status}'. Use 'confirmed' or 'rejected'.",
        )
    if validation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation record not found.",
        )
    return _validation_to_response(validation)


@router.delete(
    "/validations/{validation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_validation(
    validation_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a hypothesis validation record."""
    service = HypothesisValidationService(session)
    deleted = await service.delete_validation(validation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation record not found.",
        )


# ── Research Export with Citations ───────────────────────────────────────────


@router.post("/export/{project_id}")
async def export_research_data(
    project_id: uuid.UUID,
    body: ResearchExportRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """
    Export research project data as CSV or JSON with knowledge citations.

    Each exported row/data point includes references to its knowledge source
    (book titles, verse references, relevance scores).

    Args:
        project_id: The research project to export.
        body: Export configuration (format, include_detail).
    """
    from apps.api.repositories.research_repository import ResearchRepository
    from apps.api.repositories.knowledge_repository import KnowledgeRepository

    # Fetch project snapshots
    research_repo = ResearchRepository(session)
    snapshots = await research_repo.list_snapshots(project_id)

    if not snapshots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No snapshots found in this project.",
        )

    # Build citation map (best-effort: look up knowledge matches per chart)
    citations: dict[uuid.UUID, tuple[Any, ...]] = {}
    try:
        knowledge_repo = KnowledgeRepository(session)
        for snap in snapshots:
            if snap.chart_ref and snap.yogas:
                from apps.api.services.knowledge_engine import KnowledgeEngine
                from apps.api.domain.knowledge import KnowledgeSearchQuery

                engine = KnowledgeEngine(knowledge_repo)
                snap_citations: list[Any] = []
                for yoga in snap.yogas:
                    if yoga.is_present:
                        results = await engine.search(
                            KnowledgeSearchQuery(text=yoga.name, limit=2)
                        )
                        snap_citations.extend(results)
                citations[snap.id] = tuple(snap_citations)
    except Exception:
        # Knowledge search is best-effort; proceed without citations
        pass

    # Get project info for filename
    project = await research_repo.get_project(project_id)
    project_title = project.title.replace(" ", "_") if project else "research_export"

    # Export in requested format
    if body.format == "csv":
        if body.include_detail:
            result = CsvResearchExporter.export_snapshots(
                snapshots, citations, project_title
            )
        else:
            result = CsvResearchExporter.export_snapshot_summary(
                snapshots, citations, project_title
            )
    else:
        result = JsonResearchExporter.export_snapshots(
            snapshots, citations, project_title
        )

    return Response(
        content=result.content,
        media_type=result.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        },
    )
