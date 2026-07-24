"""
AstroOS — Research Router (Module 17 — HTTP surface)

HTTP adapter layer over ResearchEngine. No business logic lives here —
only request parsing, DTO<->schema conversion, and HTTP error mapping,
same convention as routers/events.py.

Snapshot capture only exposes chart_id + label (see
schemas/research.py's SnapshotCaptureRequest docstring for why — the
repository only round-trips that subset today). Full-engine-output
capture (yogas, shadbala, dasha_trees, etc.) remains an in-process
Python API for now, same "explicit gap, not silent" discipline as the
rest of this codebase.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session
from apps.api.domain.research import SnapshotCondition, SnapshotQuery
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.schemas.research import (
    ChartCompareRequest,
    FieldDiffResponse,
    PublicationResponse,
    ResearchExperimentAssignSnapshotsRequest,
    ResearchExperimentCompleteRequest,
    ResearchExperimentCreateRequest,
    ResearchExperimentListResponse,
    ResearchExperimentResponse,
    ResearchExperimentUpdateRequest,
    ResearchProjectCreateRequest,
    ResearchProjectListResponse,
    ResearchProjectResponse,
    ResearchProjectUpdateRequest,
    SnapshotCaptureRequest,
    SnapshotCompareRequest,
    SnapshotComparisonResponse,
    SnapshotListResponse,
    SnapshotQueryRequest,
    SnapshotQueryResponse,
    SnapshotResponse,
)
from apps.api.services.research_engine import ResearchEngine
from apps.api.services.publication_pipeline import PublicationError, generate_publication

router = APIRouter(prefix="/research", tags=["Research"])


async def _get_engine(session: AsyncSession = Depends(get_db_session)) -> ResearchEngine:
    return ResearchEngine(ResearchRepository(session))


def _project_response(p) -> ResearchProjectResponse:
    return ResearchProjectResponse(
        id=p.id, user_id=p.user_id, title=p.title, description=p.description,
        status=p.status, created_at=p.created_at, updated_at=p.updated_at,
    )


def _experiment_response(e) -> ResearchExperimentResponse:
    return ResearchExperimentResponse(
        id=e.id, project_id=e.project_id, title=e.title, hypothesis=e.hypothesis,
        methodology=e.methodology, status=e.status, snapshot_ids=list(e.snapshot_ids),
        findings=e.findings, created_at=e.created_at, updated_at=e.updated_at,
    )


def _snapshot_response(s) -> SnapshotResponse:
    return SnapshotResponse(
        id=s.id, project_id=s.project_id, chart_id=s.chart_id, label=s.label,
        captured_at=s.captured_at, snapshot_version=s.snapshot_version,
    )


def _comparison_response(c) -> SnapshotComparisonResponse:
    return SnapshotComparisonResponse(
        snapshot_a_id=c.snapshot_a_id, snapshot_b_id=c.snapshot_b_id,
        chart_id_a=c.chart_id_a, chart_id_b=c.chart_id_b,
        matching_fields=list(c.matching_fields),
        differing_fields=[
            FieldDiffResponse(field=d.field, value_a=d.value_a, value_b=d.value_b)
            for d in c.differing_fields
        ],
    )


# ── Projects ──────────────────────────────────────────────────────────────────


@router.post("/projects", response_model=ResearchProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ResearchProjectCreateRequest, engine: ResearchEngine = Depends(_get_engine)
) -> ResearchProjectResponse:
    project = await engine.create_project(**body.model_dump())
    return _project_response(project)


@router.get("/projects/{project_id}", response_model=ResearchProjectResponse)
async def get_project(
    project_id: uuid.UUID, engine: ResearchEngine = Depends(_get_engine)
) -> ResearchProjectResponse:
    project = await engine.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return _project_response(project)


@router.get("/projects", response_model=ResearchProjectListResponse)
async def list_projects(
    user_id: uuid.UUID, status_filter: str | None = None,
    engine: ResearchEngine = Depends(_get_engine),
) -> ResearchProjectListResponse:
    projects = await engine.list_projects(user_id, status=status_filter)
    return ResearchProjectListResponse(
        projects=[_project_response(p) for p in projects], total=len(projects)
    )


@router.patch("/projects/{project_id}", response_model=ResearchProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: ResearchProjectUpdateRequest,
    engine: ResearchEngine = Depends(_get_engine),
) -> ResearchProjectResponse:
    provided = body.model_dump(exclude_unset=True)
    project = await engine.update_project(project_id, **provided)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return _project_response(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID, engine: ResearchEngine = Depends(_get_engine)
) -> None:
    deleted = await engine.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")


# ── Experiments ───────────────────────────────────────────────────────────────


@router.post(
    "/projects/{project_id}/experiments",
    response_model=ResearchExperimentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_experiment(
    project_id: uuid.UUID,
    body: ResearchExperimentCreateRequest,
    engine: ResearchEngine = Depends(_get_engine),
) -> ResearchExperimentResponse:
    try:
        experiment = await engine.create_experiment(project_id=project_id, **body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _experiment_response(experiment)


@router.get("/experiments/{experiment_id}", response_model=ResearchExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID, engine: ResearchEngine = Depends(_get_engine)
) -> ResearchExperimentResponse:
    experiment = await engine.get_experiment(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")
    return _experiment_response(experiment)


@router.get("/projects/{project_id}/experiments", response_model=ResearchExperimentListResponse)
async def list_experiments(
    project_id: uuid.UUID, engine: ResearchEngine = Depends(_get_engine)
) -> ResearchExperimentListResponse:
    experiments = await engine.list_experiments(project_id)
    return ResearchExperimentListResponse(
        experiments=[_experiment_response(e) for e in experiments], total=len(experiments)
    )


@router.patch("/experiments/{experiment_id}", response_model=ResearchExperimentResponse)
async def update_experiment(
    experiment_id: uuid.UUID,
    body: ResearchExperimentUpdateRequest,
    engine: ResearchEngine = Depends(_get_engine),
) -> ResearchExperimentResponse:
    provided = body.model_dump(exclude_unset=True)
    experiment = await engine.update_experiment(experiment_id, **provided)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")
    return _experiment_response(experiment)


@router.post("/experiments/{experiment_id}/complete", response_model=ResearchExperimentResponse)
async def complete_experiment(
    experiment_id: uuid.UUID,
    body: ResearchExperimentCompleteRequest,
    engine: ResearchEngine = Depends(_get_engine),
) -> ResearchExperimentResponse:
    experiment = await engine.complete_experiment(experiment_id, body.findings)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")
    return _experiment_response(experiment)


@router.post(
    "/experiments/{experiment_id}/assign-snapshots", response_model=ResearchExperimentResponse
)
async def assign_snapshots(
    experiment_id: uuid.UUID,
    body: ResearchExperimentAssignSnapshotsRequest,
    engine: ResearchEngine = Depends(_get_engine),
) -> ResearchExperimentResponse:
    experiment = await engine.assign_snapshots_to_experiment(experiment_id, body.snapshot_ids)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")
    return _experiment_response(experiment)


# ── Snapshots ─────────────────────────────────────────────────────────────────


@router.post(
    "/projects/{project_id}/snapshots",
    response_model=SnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def capture_snapshot(
    project_id: uuid.UUID,
    body: SnapshotCaptureRequest,
    engine: ResearchEngine = Depends(_get_engine),
) -> SnapshotResponse:
    snapshot = await engine.capture_snapshot(
        project_id=project_id, chart_id=body.chart_id, label=body.label
    )
    return _snapshot_response(snapshot)


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: uuid.UUID, engine: ResearchEngine = Depends(_get_engine)
) -> SnapshotResponse:
    snapshot = await engine.get_snapshot(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found.")
    return _snapshot_response(snapshot)


@router.get("/projects/{project_id}/snapshots", response_model=SnapshotListResponse)
async def list_snapshots(
    project_id: uuid.UUID, engine: ResearchEngine = Depends(_get_engine)
) -> SnapshotListResponse:
    snapshots = await engine.list_snapshots(project_id)
    return SnapshotListResponse(
        snapshots=[_snapshot_response(s) for s in snapshots], total=len(snapshots)
    )


@router.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snapshot(
    snapshot_id: uuid.UUID, engine: ResearchEngine = Depends(_get_engine)
) -> None:
    deleted = await engine.delete_snapshot(snapshot_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found.")


# ── Query & Comparison ────────────────────────────────────────────────────────


@router.post("/projects/{project_id}/query", response_model=SnapshotQueryResponse)
async def query_snapshots(
    project_id: uuid.UUID,
    body: SnapshotQueryRequest,
    engine: ResearchEngine = Depends(_get_engine),
) -> SnapshotQueryResponse:
    query = SnapshotQuery(
        conditions=tuple(
            SnapshotCondition(
                field=c.field, operator=c.operator, value=c.value, description=c.description
            )
            for c in body.conditions
        )
    )
    snapshots = await engine.query_snapshots(project_id, query)
    return SnapshotQueryResponse(
        snapshots=[_snapshot_response(s) for s in snapshots], total=len(snapshots)
    )


@router.post("/snapshots/compare", response_model=SnapshotComparisonResponse)
async def compare_snapshots(
    body: SnapshotCompareRequest, engine: ResearchEngine = Depends(_get_engine)
) -> SnapshotComparisonResponse:
    comparison = await engine.compare_snapshots(body.snapshot_a_id, body.snapshot_b_id)
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="One or both snapshots not found."
        )
    return _comparison_response(comparison)


@router.post("/charts/compare", response_model=SnapshotComparisonResponse)
async def compare_charts(
    body: ChartCompareRequest, engine: ResearchEngine = Depends(_get_engine)
) -> SnapshotComparisonResponse:
    comparison = await engine.compare_charts(
        body.chart_id_a, body.chart_id_b, body.project_id
    )
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Both charts must have a snapshot in this project.",
        )
    return _comparison_response(comparison)


# ── Publication ────────────────────────────────────────────────────────────────


@router.post(
    "/{project_id}/publish",
    response_model=PublicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def publish_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> PublicationResponse:
    """Generate a LaTeX publication bundle for a research project.

    Produces paper.tex, references.bib, and chart-insert.tex files
    in data/publications/<project_id>/. Returns paths to the generated
    artifacts.
    """
    try:
        bundle = await generate_publication(project_id, session)
        return PublicationResponse(
            project_id=bundle.project_id,
            output_dir=bundle.output_dir,
            tex_path=bundle.tex_path,
            bib_path=bundle.bib_path,
            pdf_url=bundle.pdf_url,
            error=bundle.error,
            generated_at=bundle.generated_at,
        )
    except PublicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
