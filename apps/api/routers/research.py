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

import json
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.dependencies import get_db_session, require_researcher
from apps.api.domain.research import SnapshotCondition, SnapshotQuery
from apps.api.domain.research_case import CaseImportResult, DiscoveredPattern
from apps.api.domain.user import User
from apps.api.models.pattern import DiscoveredPatternModel, PatternDiscoveryRunModel
from apps.api.models.research_case import EventSnapshotModel, LifeEventModel, ResearchCaseModel
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
from apps.api.schemas.research_case import (
    EVENT_TYPE_TO_BACKEND,
    ConfidenceBucketSchema,
    ConfidenceDistributionResponseSchema,
    DatasetValidationReportSchema,
    EventType,
    EvidenceRecalculationResultSchema,
    ExtractedFeatureSchema,
    FeatureExtractionResponseSchema,
    LifeEventDetailSchema,
    LifeEventSnapshotSchema,
    PatternDetailSchema,
    PatternDimensionSchema,
    PatternDiscoveryRequestSchema,
    PatternDiscoveryResponseSchema,
    PatternExploreRequestSchema,
    PatternQuestionRequestSchema,
    PatternQuestionResponseSchema,
    PatternExplainAllResponseSchema,
    PatternExplainResponseSchema,
    PatternGraphEdgeSchema,
    PatternGraphNodeSchema,
    PatternGraphResponseSchema,
    PatternHypothesisResponseSchema,
    PatternHypothesisSchema,
    PatternListItemSchema,
    PatternListResponseSchema,
    PatternSummarySchema,
    PatternTrendPointSchema,
    PatternTrendResponseSchema,
    ResearchCaseBatchImportSchema,
    ResearchCaseBatchValidationSchema,
    ResearchCaseDetailSchema,
    ResearchCaseImportResponseSchema,
    ResearchCaseImportResultSchema,
    ResearchCaseListResponseSchema,
    ResearchCaseSummarySchema,
    SnapshotRebuildResultSchema,
    TopFactorSchema,
    TopFactorsResponseSchema,
)
from apps.api.services.classical_references import get_references_for_pattern
from apps.api.services.dataset_validation import DatasetValidationService
from apps.api.services.feature_extraction import FeatureExtractionService, summarize
from apps.api.services.import_service import ResearchCaseImportService, SnapshotComputer
from apps.api.services.pattern_discovery import PatternDiscoveryService
from apps.api.services.pattern_explainer import PatternExplainer, PatternExplanationError
from apps.api.services.pattern_graph import PatternGraphInput, build_network_graph, infer_category
from apps.api.services.pattern_persistence import PatternPersistenceService, dimensions_from_json
from apps.api.services.pattern_query_assistant import PatternQueryAssistant, PatternQueryError
from apps.api.services.publication_pipeline import PublicationError, generate_publication
from apps.api.services.research_engine import ResearchEngine
from apps.api.services.research_validation import validate_research_case_batch

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


# ── Ownership checks (Projects/Experiments/Snapshots are private per-user) ────
#
# Every project/experiment/snapshot in this module belongs to exactly one
# user. Router-level `require_researcher` (see main.py) only proves the
# caller is SOME authenticated researcher — it says nothing about whether
# they own the specific project_id/experiment_id/snapshot_id in the URL.
# These helpers close that gap: fetch the object, then verify ownership
# before the caller can read or write it. 404 (not 403) on mismatch, so a
# caller can't distinguish "doesn't exist" from "exists but isn't yours."

async def _owned_project(engine: ResearchEngine, project_id: uuid.UUID, user_id: uuid.UUID):
    project = await engine.get_project(project_id)
    if project is None or project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


async def _owned_experiment(engine: ResearchEngine, experiment_id: uuid.UUID, user_id: uuid.UUID):
    experiment = await engine.get_experiment(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")
    await _owned_project(engine, experiment.project_id, user_id)
    return experiment


async def _owned_snapshot(engine: ResearchEngine, snapshot_id: uuid.UUID, user_id: uuid.UUID):
    snapshot = await engine.get_snapshot(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found.")
    await _owned_project(engine, snapshot.project_id, user_id)
    return snapshot


# ── Projects ──────────────────────────────────────────────────────────────────


@router.post("/projects", response_model=ResearchProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ResearchProjectCreateRequest,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchProjectResponse:
    project = await engine.create_project(user_id=_user.id.value, **body.model_dump())
    return _project_response(project)


@router.get("/projects/{project_id}", response_model=ResearchProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchProjectResponse:
    project = await _owned_project(engine, project_id, _user.id.value)
    return _project_response(project)


@router.get("/projects", response_model=ResearchProjectListResponse)
async def list_projects(
    status_filter: str | None = None,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchProjectListResponse:
    projects = await engine.list_projects(_user.id.value, status=status_filter)
    return ResearchProjectListResponse(
        projects=[_project_response(p) for p in projects], total=len(projects)
    )


@router.patch("/projects/{project_id}", response_model=ResearchProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: ResearchProjectUpdateRequest,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchProjectResponse:
    await _owned_project(engine, project_id, _user.id.value)
    provided = body.model_dump(exclude_unset=True)
    project = await engine.update_project(project_id, **provided)
    return _project_response(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> None:
    await _owned_project(engine, project_id, _user.id.value)
    await engine.delete_project(project_id)


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
    _user: User = Depends(require_researcher),
) -> ResearchExperimentResponse:
    await _owned_project(engine, project_id, _user.id.value)
    experiment = await engine.create_experiment(project_id=project_id, **body.model_dump())
    return _experiment_response(experiment)


@router.get("/experiments/{experiment_id}", response_model=ResearchExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchExperimentResponse:
    experiment = await _owned_experiment(engine, experiment_id, _user.id.value)
    return _experiment_response(experiment)


@router.get("/projects/{project_id}/experiments", response_model=ResearchExperimentListResponse)
async def list_experiments(
    project_id: uuid.UUID,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchExperimentListResponse:
    await _owned_project(engine, project_id, _user.id.value)
    experiments = await engine.list_experiments(project_id)
    return ResearchExperimentListResponse(
        experiments=[_experiment_response(e) for e in experiments], total=len(experiments)
    )


@router.patch("/experiments/{experiment_id}", response_model=ResearchExperimentResponse)
async def update_experiment(
    experiment_id: uuid.UUID,
    body: ResearchExperimentUpdateRequest,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchExperimentResponse:
    await _owned_experiment(engine, experiment_id, _user.id.value)
    provided = body.model_dump(exclude_unset=True)
    experiment = await engine.update_experiment(experiment_id, **provided)
    return _experiment_response(experiment)


@router.post("/experiments/{experiment_id}/complete", response_model=ResearchExperimentResponse)
async def complete_experiment(
    experiment_id: uuid.UUID,
    body: ResearchExperimentCompleteRequest,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchExperimentResponse:
    await _owned_experiment(engine, experiment_id, _user.id.value)
    experiment = await engine.complete_experiment(experiment_id, body.findings)
    return _experiment_response(experiment)


@router.post(
    "/experiments/{experiment_id}/assign-snapshots", response_model=ResearchExperimentResponse
)
async def assign_snapshots(
    experiment_id: uuid.UUID,
    body: ResearchExperimentAssignSnapshotsRequest,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> ResearchExperimentResponse:
    await _owned_experiment(engine, experiment_id, _user.id.value)
    # Every snapshot being linked in must also belong to the caller —
    # otherwise a researcher could pull someone else's snapshot into their
    # own experiment by guessing its ID.
    for snapshot_id in body.snapshot_ids:
        await _owned_snapshot(engine, snapshot_id, _user.id.value)
    experiment = await engine.assign_snapshots_to_experiment(experiment_id, body.snapshot_ids)
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
    _user: User = Depends(require_researcher),
) -> SnapshotResponse:
    await _owned_project(engine, project_id, _user.id.value)
    snapshot = await engine.capture_snapshot(
        project_id=project_id, chart_id=body.chart_id, label=body.label
    )
    return _snapshot_response(snapshot)


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: uuid.UUID,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> SnapshotResponse:
    snapshot = await _owned_snapshot(engine, snapshot_id, _user.id.value)
    return _snapshot_response(snapshot)


@router.get("/projects/{project_id}/snapshots", response_model=SnapshotListResponse)
async def list_snapshots(
    project_id: uuid.UUID,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> SnapshotListResponse:
    await _owned_project(engine, project_id, _user.id.value)
    snapshots = await engine.list_snapshots(project_id)
    return SnapshotListResponse(
        snapshots=[_snapshot_response(s) for s in snapshots], total=len(snapshots)
    )


@router.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snapshot(
    snapshot_id: uuid.UUID,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> None:
    await _owned_snapshot(engine, snapshot_id, _user.id.value)
    await engine.delete_snapshot(snapshot_id)


# ── Query & Comparison ────────────────────────────────────────────────────────


@router.post("/projects/{project_id}/query", response_model=SnapshotQueryResponse)
async def query_snapshots(
    project_id: uuid.UUID,
    body: SnapshotQueryRequest,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> SnapshotQueryResponse:
    await _owned_project(engine, project_id, _user.id.value)
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
    body: SnapshotCompareRequest,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> SnapshotComparisonResponse:
    await _owned_snapshot(engine, body.snapshot_a_id, _user.id.value)
    await _owned_snapshot(engine, body.snapshot_b_id, _user.id.value)
    comparison = await engine.compare_snapshots(body.snapshot_a_id, body.snapshot_b_id)
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="One or both snapshots not found."
        )
    return _comparison_response(comparison)


@router.post("/charts/compare", response_model=SnapshotComparisonResponse)
async def compare_charts(
    body: ChartCompareRequest,
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> SnapshotComparisonResponse:
    await _owned_project(engine, body.project_id, _user.id.value)
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
    engine: ResearchEngine = Depends(_get_engine),
    _user: User = Depends(require_researcher),
) -> PublicationResponse:
    """Generate a LaTeX publication bundle for a research project.

    Produces paper.tex, references.bib, and chart-insert.tex files
    in data/publications/<project_id>/. Returns paths to the generated
    artifacts.
    """
    await _owned_project(engine, project_id, _user.id.value)
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


# ── Feature Extraction + Pattern Discovery (Module 27, Phase 3) ───────────────


# Reverse map: backend lowercase event type ("job_change") -> schema EventType.
_BACKEND_TO_EVENT_TYPE = {v: EventType(k) for k, v in EVENT_TYPE_TO_BACKEND.items()}


def _feature_to_schema(f) -> ExtractedFeatureSchema:
    """Convert a domain ExtractedFeature into its schema form."""
    return ExtractedFeatureSchema(
        feature_name=f.feature_name,
        feature_value=f.feature_value,
        feature_category=f.feature_category,
        event_type=_BACKEND_TO_EVENT_TYPE.get(f.event_type, EventType.OTHER),
        research_case_id=f.research_case_id,
        event_date=f.event_date,
        confidence=f.confidence,
    )


@router.post(
    "/cases/features/extract",
    response_model=FeatureExtractionResponseSchema,
    summary="Extract normalised research features from event snapshots.",
    tags=["Research Cases"],
)
async def extract_features(
    session: AsyncSession = Depends(get_db_session),
) -> FeatureExtractionResponseSchema:
    """Run feature extraction across all imported research cases.

    Every astrological observation inside each immutable EventSnapshot is
    normalised into a flat, searchable feature row (see
    apps/api/services/feature_extraction.py). Output feeds pattern discovery.
    """
    features = await FeatureExtractionService(session).extract_all()
    return FeatureExtractionResponseSchema(
        total_features=len(features),
        features_by_category=summarize(features),
        features=[_feature_to_schema(f) for f in features],
    )


@router.post(
    "/cases/patterns/discover",
    response_model=PatternDiscoveryResponseSchema,
    summary="Discover statistically significant astrological patterns.",
    tags=["Research Cases"],
)
async def discover_patterns(
    body: PatternDiscoveryRequestSchema,
    session: AsyncSession = Depends(get_db_session),
) -> PatternDiscoveryResponseSchema:
    """Discover patterns (dasha, transits, yogas, shadbala, ...) behind events.

    Extracts features on-the-fly from snapshots, then runs the pattern
    discovery engine (apps/api/services/pattern_discovery.py) over them.
    Results are also persisted (upserted by pattern_id) to
    discovered_patterns/pattern_discovery_runs — this is how the
    /cases/patterns* read-only dashboard endpoints get populated; they
    never recompute from snapshots themselves.
    """
    start = time.perf_counter()
    extraction = FeatureExtractionService(session)
    features = await extraction.extract_all(date_from=body.date_from, date_to=body.date_to)

    engine = PatternDiscoveryService()
    backend_type = (
        EVENT_TYPE_TO_BACKEND[body.event_type.value] if body.event_type else None
    )
    discovered = engine.discover(
        features, event_type=backend_type, top_combos=body.top_combos
    )

    # Group into the response shape: one pattern per event type.
    patterns_by_type: dict[str, list] = {}
    for pattern in discovered:
        patterns_by_type.setdefault(pattern.event_type, []).append(pattern)

    # Reconstruct response from the first (or only) event type.
    if body.event_type:
        event_type_schema = body.event_type
        total_cases = len({f.research_case_id for f in features if f.event_type == backend_type})
        total_events = sum(1 for f in features if f.event_type == backend_type)
        patterns = patterns_by_type.get(backend_type, [])
    else:
        # When no event type is given, report the aggregate across all types.
        event_type_schema = EventType.OTHER
        total_cases = len({f.research_case_id for f in features})
        total_events = len(features)
        patterns = [p for group in patterns_by_type.values() for p in group]

    def _dimension_to_schema(d):
        from apps.api.schemas.research_case import PatternDimensionSchema
        return PatternDimensionSchema(
            dimension=d.dimension,
            value=d.value,
            frequency=d.frequency,
            count=d.count,
            expected_by_chance=d.expected_by_chance,
            significance=d.significance,
        )

    execution_time_ms = int((time.perf_counter() - start) * 1000)
    await PatternPersistenceService(session).persist_discovery(
        patterns,
        all_features=features,
        event_type=backend_type,
        total_cases=total_cases,
        total_events=total_events,
        execution_time_ms=execution_time_ms,
    )

    from apps.api.schemas.research_case import DiscoveredPatternSchema
    return PatternDiscoveryResponseSchema(
        event_type=event_type_schema,
        total_cases=total_cases,
        total_events=total_events,
        patterns=[
            DiscoveredPatternSchema(
                event_type=_BACKEND_TO_EVENT_TYPE.get(p.event_type, EventType.OTHER),
                pattern_id=p.pattern_id,
                dimensions=[_dimension_to_schema(d) for d in p.dimensions],
                sample_size=p.sample_size,
                confidence_score=p.confidence_score,
                description=p.description,
            )
            for p in patterns
        ],
        execution_time_ms=execution_time_ms,
    )


@router.post(
    "/cases/patterns/explore",
    response_model=PatternDiscoveryResponseSchema,
    summary="Personal pattern exploration with custom thresholds (never persisted).",
    tags=["Research Cases"],
)
async def explore_patterns(
    body: PatternExploreRequestSchema,
    session: AsyncSession = Depends(get_db_session),
) -> PatternDiscoveryResponseSchema:
    """A researcher's own 'what-if' lens over the same shared dataset and
    formulas as /cases/patterns/discover — only the significance/
    frequency/Wilson-z thresholds are theirs to set. Results are computed
    live and returned directly; nothing is written to
    discovered_patterns/pattern_discovery_runs, so this can never change
    what any other researcher sees on the shared dashboard.
    """
    start = time.perf_counter()
    extraction = FeatureExtractionService(session)
    features = await extraction.extract_all(date_from=body.date_from, date_to=body.date_to)

    engine = PatternDiscoveryService(
        min_significance=body.min_significance,
        min_frequency=body.min_frequency,
        wilson_z=body.wilson_z,
    )
    backend_type = (
        EVENT_TYPE_TO_BACKEND[body.event_type.value] if body.event_type else None
    )
    discovered = engine.discover(
        features, event_type=backend_type, top_combos=body.top_combos
    )

    patterns_by_type: dict[str, list] = {}
    for pattern in discovered:
        patterns_by_type.setdefault(pattern.event_type, []).append(pattern)

    if body.event_type:
        event_type_schema = body.event_type
        total_cases = len({f.research_case_id for f in features if f.event_type == backend_type})
        total_events = sum(1 for f in features if f.event_type == backend_type)
        patterns = patterns_by_type.get(backend_type, [])
    else:
        event_type_schema = EventType.OTHER
        total_cases = len({f.research_case_id for f in features})
        total_events = len(features)
        patterns = [p for group in patterns_by_type.values() for p in group]

    def _dimension_to_schema(d):
        from apps.api.schemas.research_case import PatternDimensionSchema
        return PatternDimensionSchema(
            dimension=d.dimension,
            value=d.value,
            frequency=d.frequency,
            count=d.count,
            expected_by_chance=d.expected_by_chance,
            significance=d.significance,
        )

    execution_time_ms = int((time.perf_counter() - start) * 1000)

    from apps.api.schemas.research_case import DiscoveredPatternSchema
    return PatternDiscoveryResponseSchema(
        event_type=event_type_schema,
        total_cases=total_cases,
        total_events=total_events,
        patterns=[
            DiscoveredPatternSchema(
                event_type=_BACKEND_TO_EVENT_TYPE.get(p.event_type, EventType.OTHER),
                pattern_id=p.pattern_id,
                dimensions=[_dimension_to_schema(d) for d in p.dimensions],
                sample_size=p.sample_size,
                confidence_score=p.confidence_score,
                description=p.description,
            )
            for p in patterns
        ],
        execution_time_ms=execution_time_ms,
    )


def _pattern_query_assistant(request: Request) -> PatternQueryAssistant:
    settings = get_settings()
    return PatternQueryAssistant(
        http_client=request.app.state.http_client,
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        base_url=settings.OPENAI_BASE_URL,
    )


def _pattern_row_to_list_item(r) -> PatternListItemSchema:
    return PatternListItemSchema(
        pattern_id=r.pattern_id,
        event_type=_BACKEND_TO_EVENT_TYPE.get(r.event_type, EventType.OTHER),
        description=r.description,
        sample_size=r.sample_size,
        confidence_score=r.confidence_score,
        lift_score=r.lift_score,
        has_explanation=r.explanation is not None,
        dimension_count=len(r.dimensions_json),
        categories=sorted({infer_category(d["dimension"]) for d in r.dimensions_json}),
        discovered_at=r.updated_at,
    )


@router.post(
    "/cases/patterns/ask",
    response_model=PatternQuestionResponseSchema,
    summary="Ask a plain-language question about the shared discovered patterns.",
    tags=["Research Cases"],
)
async def ask_about_patterns(
    body: PatternQuestionRequestSchema,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> PatternQuestionResponseSchema:
    """Answer a question like "what correlates with Marriage?" grounded
    in the real, already-persisted discovered_patterns table.

    Read-only: never runs discovery, never persists anything. The LLM
    never touches the database — it only (1) picks an event_type from
    the fixed, validated LOKPA list, which the router uses to query real
    rows, then (2) summarizes those real rows. It cannot introduce a
    pattern or statistic that wasn't actually fetched.
    """
    start = time.perf_counter()
    assistant = _pattern_query_assistant(request)
    valid_event_types = [e.value for e in EventType]

    try:
        matched_type = await assistant.parse_event_type(body.question, valid_event_types)
    except PatternQueryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    query = select(DiscoveredPatternModel).order_by(DiscoveredPatternModel.confidence_score.desc())
    if matched_type:
        query = query.where(
            DiscoveredPatternModel.event_type == EVENT_TYPE_TO_BACKEND[matched_type]
        )
    rows = (await session.execute(query.limit(8))).scalars().all()

    try:
        answer = await assistant.summarize(
            body.question,
            [
                {
                    "description": r.description,
                    "confidence_score": r.confidence_score,
                    "sample_size": r.sample_size,
                }
                for r in rows
            ],
        )
    except PatternQueryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    execution_time_ms = int((time.perf_counter() - start) * 1000)
    return PatternQuestionResponseSchema(
        question=body.question,
        matched_event_type=EventType(matched_type) if matched_type else None,
        answer=answer,
        patterns=[_pattern_row_to_list_item(r) for r in rows],
        execution_time_ms=execution_time_ms,
    )


@router.post(
    "/cases/patterns/hypothesis",
    response_model=PatternHypothesisResponseSchema,
    summary="Test a custom astrological hypothesis against the snapshot data.",
    tags=["Research Cases"],
)
async def test_pattern_hypothesis(
    body: PatternHypothesisSchema,
    session: AsyncSession = Depends(get_db_session),
) -> PatternHypothesisResponseSchema:
    """Given dimension->value filters, report how many cases match.

    e.g. hypothesis={"mahadasha": "Ju", "transit_Sa_7th_house": "True"} for
    the Marriage event type.
    """
    backend_type = EVENT_TYPE_TO_BACKEND[body.event_type.value]
    features = await FeatureExtractionService(session).extract_all()
    matching, total, proportion, supporting = PatternDiscoveryService().test_hypothesis(
        features,
        event_type=backend_type,
        conditions=body.conditions,
    )
    confidence = min(1.0, proportion * (matching / max(total, 1)) * 10)
    return PatternHypothesisResponseSchema(
        event_type=body.event_type,
        hypothesis=body.conditions,
        matching_cases=matching,
        total_cases=total,
        proportion=round(proportion, 4),
        confidence_score=round(confidence, 4),
        supporting_events=supporting,
    )


# ── Research Cases (Module 27) ────────────────────────────────────────────────


def _case_result_to_schema(r: CaseImportResult) -> ResearchCaseImportResultSchema:
    return ResearchCaseImportResultSchema(
        research_case_id=r.research_case_id,
        person_name=r.person_name,
        dob=r.dob,
        total_events=r.total_events,
        total_snapshots_created=r.total_snapshots_created,
        duplicate=r.duplicate,
        errors=list(r.errors),
    )


@router.get(
    "/cases/import/schema",
    summary="JSON schema for a research case batch import.",
    tags=["Research Cases"],
)
async def research_case_import_schema() -> dict:
    """Return the JSON Schema describing a valid batch import payload.

    Frontend uses this to validate a dropped JSON file before uploading.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ResearchCaseBatchImport",
        **ResearchCaseBatchImportSchema.model_json_schema(),
    }


@router.post(
    "/cases/validate",
    response_model=ResearchCaseBatchValidationSchema,
    tags=["Research Cases"],
)
async def validate_research_cases(
    payload: ResearchCaseBatchImportSchema,
) -> ResearchCaseBatchValidationSchema:
    """Validate a batch of research cases without persisting anything."""
    return validate_research_case_batch(payload.cases)


@router.post(
    "/cases/import",
    response_model=ResearchCaseImportResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Import research cases (validate, compute snapshots, persist).",
    tags=["Research Cases"],
)
async def import_research_cases(
    payload: ResearchCaseBatchImportSchema,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    _user: User = Depends(require_researcher),
) -> ResearchCaseImportResponseSchema:
    """Validate, snapshot-compute, and persist a batch of research cases.

    Per-case results are returned in input order; invalid cases are
    reported with their validation errors and do not abort the batch.
    """
    wrapper = getattr(request.app.state, "ephemeris_wrapper", None)
    if wrapper is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ephemeris wrapper not initialised.",
        )

    validations = validate_research_case_batch(payload.cases)
    valid_schemas = [
        c for c, v in zip(payload.cases, validations.validations) if v.valid
    ]
    persisted = await ResearchCaseImportService(
        session, SnapshotComputer(wrapper)
    ).import_cases([c.to_domain() for c in valid_schemas], user_id=_user.id.value)

    # Re-merge per-case results in input order (invalid cases get error results)
    persisted_iter = iter(persisted)
    results: list[CaseImportResult] = []
    for case, validation in zip(payload.cases, validations.validations):
        if validation.valid:
            results.append(next(persisted_iter))
        else:
            results.append(
                CaseImportResult(
                    research_case_id=case.id or "",
                    person_name=case.person.name,
                    dob=case.person.dob,
                    total_events=len(case.life_events),
                    total_snapshots_created=0,
                    duplicate=validation.duplicate_case,
                    errors=[
                        f"{issue.field}: {issue.message}"
                        for issue in validation.issues
                        if issue.severity == "error"
                    ],
                )
            )

    succeeded = sum(1 for r in results if not r.errors and not r.duplicate)
    return ResearchCaseImportResponseSchema(
        total_cases=len(payload.cases),
        succeeded=succeeded,
        failed=len(payload.cases) - succeeded,
        results=[_case_result_to_schema(r) for r in results],
    )


@router.get(
    "/cases",
    response_model=ResearchCaseListResponseSchema,
    summary="List imported research cases.",
    tags=["Research Cases"],
)
async def list_research_cases(
    session: AsyncSession = Depends(get_db_session),
) -> ResearchCaseListResponseSchema:
    """List research cases (summary: id, person, dob, event count)."""
    cases = (
        await session.execute(
            select(ResearchCaseModel)
            .where(ResearchCaseModel.deleted_at.is_(None))
            .order_by(ResearchCaseModel.created_at.desc())
            .limit(200)
        )
    ).scalars().all()

    return ResearchCaseListResponseSchema(
        total=len(cases),
        cases=[
            ResearchCaseSummarySchema(
                research_case_id=c.research_case_id,
                person_name=c.person_name,
                dob=c.dob.date() if c.dob else None,
                gender=c.gender,
                total_events=len(c.life_events),
                validation_status=c.validation_status,
                duplicate_of_id=c.duplicate_of_id,
                created_at=c.created_at,
            )
            for c in cases
        ],
    )


# ── Pattern Discovery Dashboard (Module 27, Phase 3c) ─────────────────────────
#
# Everything below reads from discovered_patterns/pattern_discovery_runs
# (populated by /cases/patterns/discover above) — none of these endpoints
# recompute from snapshots. Literal-path routes (summary, top-factors,
# confidence-distribution, graph) are registered before the /{pattern_id}
# routes so FastAPI's path matching doesn't swallow them as a pattern_id.


def _dimension_schema_from_json(d: dict) -> PatternDimensionSchema:
    return PatternDimensionSchema(
        dimension=d["dimension"],
        value=d["value"],
        frequency=d["frequency"],
        count=d["count"],
        expected_by_chance=d.get("expected_by_chance", 0.0),
        significance=d.get("significance", 0.0),
    )


def _pattern_explainer(request: Request) -> PatternExplainer:
    settings = get_settings()
    return PatternExplainer(
        http_client=request.app.state.http_client,
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        base_url=settings.OPENAI_BASE_URL,
    )


async def _matching_case_ids(
    session: AsyncSession,
    *,
    gender: str | None,
    country: str | None,
    dataset: str | None,
) -> set[str] | None:
    """None means "no demographic filter given" (no restriction); otherwise
    the set of research_case_id values satisfying every given filter."""
    if not any([gender, country, dataset]):
        return None
    query = select(ResearchCaseModel.research_case_id)
    if gender:
        query = query.where(ResearchCaseModel.gender == gender.lower())
    if country:
        query = query.where(ResearchCaseModel.country == country)
    if dataset:
        query = query.where(ResearchCaseModel.source_batch == dataset)
    rows = await session.execute(query)
    return {r[0] for r in rows.all()}


@router.get(
    "/cases/patterns/summary",
    response_model=PatternSummarySchema,
    summary="KPI numbers for the pattern discovery dashboard.",
    tags=["Research Cases"],
)
async def pattern_summary(
    session: AsyncSession = Depends(get_db_session),
) -> PatternSummarySchema:
    total_cases_row = await session.execute(
        select(ResearchCaseModel.id).where(ResearchCaseModel.deleted_at.is_(None))
    )
    total_cases = len(total_cases_row.all())
    total_events_row = await session.execute(select(LifeEventModel.id))
    total_events = len(total_events_row.all())
    total_snapshots_row = await session.execute(select(EventSnapshotModel.id))
    total_snapshots = len(total_snapshots_row.all())

    patterns = (await session.execute(select(DiscoveredPatternModel))).scalars().all()
    return PatternSummarySchema(
        total_cases=total_cases,
        total_events=total_events,
        total_snapshots=total_snapshots,
        patterns_found=len(patterns),
        high_confidence_patterns=sum(1 for p in patterns if p.confidence_score >= 0.75),
        knowledge_records=sum(1 for p in patterns if p.explanation is not None),
    )


_PLANET_CODE_TO_NAME = {
    "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
    "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu",
}
_PLANET_NAME_TOKEN_TO_NAME = {name.lower(): name for name in _PLANET_CODE_TO_NAME.values()}


def _extract_planet(dimension: str, value: str) -> str | None:
    """Normalise a dimension's planet reference to a canonical full name.

    Dasha dimension values are 2-letter lord codes ("Ju"). Transit/shadbala
    dimension NAMES instead embed the full lowercase planet name
    ("transit_mars_cancer", "shadbala_venus") — the 2-letter-code check
    that used to run here for every dimension type never matched those,
    silently leaving the Planets tab empty despite transit-based patterns
    existing. Both forms are recognised here and mapped to one canonical
    name so "Mars" from a dasha and "Mars" from a transit count together.
    """
    if dimension.startswith("dasha_"):
        return _PLANET_CODE_TO_NAME.get(value)
    for part in dimension.split("_"):
        if part in _PLANET_NAME_TOKEN_TO_NAME:
            return _PLANET_NAME_TOKEN_TO_NAME[part]
        if part in _PLANET_CODE_TO_NAME:
            return _PLANET_CODE_TO_NAME[part]
    return None


@router.get(
    "/cases/patterns/top-factors",
    response_model=TopFactorsResponseSchema,
    summary="Top contributing dimension values within a category.",
    tags=["Research Cases"],
)
async def pattern_top_factors(
    category: str = "planet",
    session: AsyncSession = Depends(get_db_session),
) -> TopFactorsResponseSchema:
    """``category`` is one of planet, yoga, dasha, house, transit, shadbala,
    varga, nakshatra. ``planet`` is derived (not a raw feature_category) by
    parsing planet codes out of dasha/transit/shadbala dimension names.
    """
    patterns = (await session.execute(select(DiscoveredPatternModel))).scalars().all()
    counter: Counter[str] = Counter()
    for row in patterns:
        for d in row.dimensions_json:
            if category == "planet":
                planet = _extract_planet(d["dimension"], str(d["value"]))
                if planet:
                    counter[planet] += d.get("count", 1)
            elif _infer_matches(d["dimension"], category):
                counter[_factor_label(d["dimension"], str(d["value"]))] += d.get("count", 1)

    factors = [TopFactorSchema(value=v, count=c) for v, c in counter.most_common(20)]
    return TopFactorsResponseSchema(category=category, factors=factors)


def _factor_label(dimension: str, value: str) -> str:
    """The meaningful label to bucket a top-factor row by.

    Most dimensions carry the informative part in `value` (a dasha lord like
    "Ju", a house-lord status like "strong"). Boolean-presence dimensions
    (active_yogas, transit_features — both stored as {feature: True} maps)
    carry it in the dimension name instead, since `value` is always the
    literal string "True" there and would otherwise collapse every distinct
    yoga/transit into one meaningless "True" bucket.
    """
    if value.strip().lower() not in ("true", "false"):
        return value
    if dimension.startswith("nakshatra activation_"):
        rest = dimension[len("nakshatra activation_"):]
        planet_token, _, nak_token = rest.partition("_")
        planet = _PLANET_NAME_TOKEN_TO_NAME.get(planet_token, planet_token.title())
        return f"{planet} in {nak_token.title()}"
    for prefix in ("active yoga_", "transit_"):
        if dimension.startswith(prefix):
            return dimension[len(prefix):]
    return dimension


def _infer_matches(dimension: str, category: str) -> bool:
    return infer_category(dimension) == category


@router.get(
    "/cases/patterns/confidence-distribution",
    response_model=ConfidenceDistributionResponseSchema,
    summary="Bucketed histogram of persisted pattern confidence scores.",
    tags=["Research Cases"],
)
async def pattern_confidence_distribution(
    session: AsyncSession = Depends(get_db_session),
) -> ConfidenceDistributionResponseSchema:
    patterns = (await session.execute(select(DiscoveredPatternModel))).scalars().all()
    bucket_labels = ["0-20", "20-40", "40-60", "60-80", "80-100"]
    counts = {label: 0 for label in bucket_labels}
    for row in patterns:
        pct = row.confidence_score * 100
        index = min(int(pct // 20), 4)
        counts[bucket_labels[index]] += 1
    return ConfidenceDistributionResponseSchema(
        buckets=[ConfidenceBucketSchema(bucket=label, count=counts[label]) for label in bucket_labels]
    )


@router.get(
    "/cases/patterns/graph",
    response_model=PatternGraphResponseSchema,
    summary="Pattern dimension co-occurrence network (radial layout).",
    tags=["Research Cases"],
)
async def pattern_graph(
    session: AsyncSession = Depends(get_db_session),
) -> PatternGraphResponseSchema:
    patterns = (await session.execute(select(DiscoveredPatternModel))).scalars().all()
    graph_input = [
        PatternGraphInput(
            pattern_id=row.pattern_id,
            dimensions=[(d["dimension"], str(d["value"])) for d in row.dimensions_json],
        )
        for row in patterns
    ]
    nodes, edges = build_network_graph(graph_input)
    return PatternGraphResponseSchema(
        nodes=[
            PatternGraphNodeSchema(id=n.id, label=n.label, x=n.x, y=n.y, size=n.size, category=n.category)
            for n in nodes
        ],
        edges=[PatternGraphEdgeSchema(from_=e.from_, to=e.to) for e in edges],
    )


@router.get(
    "/cases/patterns/trend/{pattern_id}",
    response_model=PatternTrendResponseSchema,
    summary="Confidence-over-time for one pattern across discovery runs.",
    tags=["Research Cases"],
)
async def pattern_trend(
    pattern_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> PatternTrendResponseSchema:
    """Populates once >=2 discovery runs have (re)computed this pattern_id;
    a single point otherwise — the response doesn't hide this, the caller
    should render a flat/short trend rather than treating it as an error.
    """
    row = (
        await session.execute(
            select(DiscoveredPatternModel).where(DiscoveredPatternModel.pattern_id == pattern_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found.")

    points = [PatternTrendPointSchema(run_at=row.updated_at, confidence_score=row.confidence_score)]
    return PatternTrendResponseSchema(pattern_id=pattern_id, points=points)


@router.get(
    "/cases/patterns",
    response_model=PatternListResponseSchema,
    summary="List persisted patterns (read-only, filterable).",
    tags=["Research Cases"],
)
async def list_patterns(
    event_type: EventType | None = None,
    min_confidence: float = 0.0,
    min_support: int = 0,
    gender: str | None = None,
    country: str | None = None,
    dataset: str | None = None,
    chart: str | None = None,
    category: str | None = None,
    min_dimensions: int = 0,
    dimension: str | None = None,
    value: str | None = None,
    sort: str = "confidence_score",
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
) -> PatternListResponseSchema:
    query = select(DiscoveredPatternModel)
    if event_type is not None:
        query = query.where(DiscoveredPatternModel.event_type == EVENT_TYPE_TO_BACKEND[event_type.value])
    if min_confidence > 0:
        query = query.where(DiscoveredPatternModel.confidence_score >= min_confidence)
    if min_support > 0:
        query = query.where(DiscoveredPatternModel.sample_size >= min_support)

    rows = (await session.execute(query)).scalars().all()

    case_filter = await _matching_case_ids(session, gender=gender, country=country, dataset=dataset)
    if case_filter is not None:
        rows = [r for r in rows if set(r.supporting_case_ids_json) & case_filter]
    if chart:
        rows = [r for r in rows if any(d["dimension"].startswith(f"varga_{chart}") for d in r.dimensions_json)]
    if category:
        rows = [r for r in rows if any(infer_category(d["dimension"]) == category for d in r.dimensions_json)]
    if min_dimensions > 0:
        rows = [r for r in rows if len(r.dimensions_json) >= min_dimensions]
    if dimension and value:
        rows = [
            r for r in rows
            if any(d["dimension"] == dimension and str(d["value"]) == value for d in r.dimensions_json)
        ]

    reverse = sort not in ("event_type",)
    rows.sort(key=lambda r: getattr(r, sort, r.confidence_score), reverse=reverse)
    rows = rows[:limit]

    return PatternListResponseSchema(
        total=len(rows),
        patterns=[
            PatternListItemSchema(
                pattern_id=r.pattern_id,
                event_type=_BACKEND_TO_EVENT_TYPE.get(r.event_type, EventType.OTHER),
                description=r.description,
                sample_size=r.sample_size,
                confidence_score=r.confidence_score,
                lift_score=r.lift_score,
                has_explanation=r.explanation is not None,
                dimension_count=len(r.dimensions_json),
                categories=sorted({infer_category(d["dimension"]) for d in r.dimensions_json}),
                discovered_at=r.updated_at,
            )
            for r in rows
        ],
    )


@router.get(
    "/cases/patterns/{pattern_id}",
    response_model=PatternDetailSchema,
    summary="Read-only pattern detail — never triggers an AI explanation call.",
    tags=["Research Cases"],
)
async def get_pattern_detail(
    pattern_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> PatternDetailSchema:
    row = (
        await session.execute(
            select(DiscoveredPatternModel).where(DiscoveredPatternModel.pattern_id == pattern_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found.")

    return PatternDetailSchema(
        pattern_id=row.pattern_id,
        event_type=_BACKEND_TO_EVENT_TYPE.get(row.event_type, EventType.OTHER),
        description=row.description,
        dimensions=[_dimension_schema_from_json(d) for d in row.dimensions_json],
        sample_size=row.sample_size,
        confidence_score=row.confidence_score,
        lift_score=row.lift_score,
        supporting_case_ids=list(row.supporting_case_ids_json),
        contradicting_case_ids=list(row.contradicting_case_ids_json),
        algorithm_version=row.algorithm_version,
        feature_version=row.feature_version,
        snapshot_versions=list(row.snapshot_versions_json),
        explanation=row.explanation,
        explanation_generated_at=row.explanation_generated_at,
        classical_references=list(row.classical_references_json or []),
        discovered_at=row.updated_at,
    )


async def _explain_one(request: Request, row: DiscoveredPatternModel) -> str:
    """Shared by the single and bulk explain endpoints. Raises
    PatternExplanationError (mapped to HTTP 503 by callers) on failure."""
    pattern = DiscoveredPattern(
        event_type=row.event_type,
        pattern_id=row.pattern_id,
        dimensions=dimensions_from_json(row.dimensions_json),
        sample_size=row.sample_size,
        confidence_score=row.confidence_score,
        description=row.description,
    )
    explanation = await _pattern_explainer(request).explain(pattern)
    row.explanation = explanation
    row.explanation_generated_at = datetime.now(timezone.utc)
    return explanation


@router.post(
    "/cases/patterns/{pattern_id}/explain",
    response_model=PatternExplainResponseSchema,
    summary="Generate (or regenerate) one pattern's AI explanation.",
    tags=["Research Cases"],
)
async def explain_pattern(
    pattern_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> PatternExplainResponseSchema:
    """The only endpoint that ever calls the OpenAI API for a pattern
    explanation — GET /cases/patterns/{pattern_id} never does."""
    row = (
        await session.execute(
            select(DiscoveredPatternModel).where(DiscoveredPatternModel.pattern_id == pattern_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found.")

    try:
        explanation = await _explain_one(request, row)
    except PatternExplanationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return PatternExplainResponseSchema(
        pattern_id=pattern_id,
        explanation=explanation,
        explanation_generated_at=row.explanation_generated_at,
    )


@router.post(
    "/cases/patterns/explanations/regenerate-all",
    response_model=PatternExplainAllResponseSchema,
    summary="Advanced Research: bulk-regenerate every pattern's AI explanation.",
    tags=["Research Cases"],
)
async def regenerate_all_explanations(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> PatternExplainAllResponseSchema:
    rows = (await session.execute(select(DiscoveredPatternModel))).scalars().all()
    succeeded = 0
    errors: list[str] = []
    for row in rows:
        try:
            await _explain_one(request, row)
            succeeded += 1
        except PatternExplanationError as exc:
            errors.append(f"{row.pattern_id}: {exc}")

    return PatternExplainAllResponseSchema(
        total_patterns=len(rows),
        succeeded=succeeded,
        failed=len(rows) - succeeded,
        errors=errors,
    )


@router.get(
    "/cases/dataset/validate",
    response_model=DatasetValidationReportSchema,
    summary="Advanced Research: dataset integrity report.",
    tags=["Research Cases"],
)
async def validate_dataset(
    session: AsyncSession = Depends(get_db_session),
) -> DatasetValidationReportSchema:
    report = await DatasetValidationService(session).validate()
    return DatasetValidationReportSchema(
        total_cases=report.total_cases,
        cases_without_snapshots=report.cases_without_snapshots,
        life_events_without_snapshots=report.life_events_without_snapshots,
        stale_snapshot_case_ids=report.stale_snapshot_case_ids,
        duplicate_case_ids=report.duplicate_case_ids,
    )


@router.post(
    "/cases/snapshots/rebuild",
    response_model=SnapshotRebuildResultSchema,
    summary="Advanced Research: recompute snapshots for the caller's own imported cases.",
    tags=["Research Cases"],
)
async def rebuild_snapshots(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    _user: User = Depends(require_researcher),
) -> SnapshotRebuildResultSchema:
    wrapper = getattr(request.app.state, "ephemeris_wrapper", None)
    if wrapper is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ephemeris wrapper not initialised.",
        )
    # Owner-only write: only rebuild (and thus create new snapshot rows
    # for) cases the caller themselves imported, never another user's.
    result = await ResearchCaseImportService(session, SnapshotComputer(wrapper)).rebuild_all_snapshots(
        user_id=_user.id.value
    )
    return SnapshotRebuildResultSchema(
        cases_processed=result.cases_processed,
        snapshots_created=result.snapshots_created,
        snapshot_version=result.snapshot_version,
        errors=result.errors,
    )


@router.post(
    "/cases/patterns/evidence/recalculate",
    response_model=EvidenceRecalculationResultSchema,
    summary="Advanced Research: refresh evidence for existing patterns (no new discovery).",
    tags=["Research Cases"],
)
async def recalculate_evidence(
    session: AsyncSession = Depends(get_db_session),
) -> EvidenceRecalculationResultSchema:
    refreshed = await PatternPersistenceService(session).recalculate_evidence()
    return EvidenceRecalculationResultSchema(patterns_refreshed=refreshed)


# ── Case detail (event timeline) ───────────────────────────────────────────
#
# Registered LAST and matched against a single path segment
# ({research_case_id}) — every literal /cases/... route above (patterns,
# import, validate, dataset/validate, snapshots/rebuild, ...) must stay
# registered before this one, same reasoning as the pattern_id routes
# noted near the top of the Pattern Discovery section: Starlette matches
# routes in registration order, not by specificity, so a dynamic
# single-segment route registered first would swallow requests meant for
# a literal path like /cases/patterns.


def _plain_event_type(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


@router.get(
    "/cases/{research_case_id}",
    response_model=ResearchCaseDetailSchema,
    summary="One research case's full life-event timeline, with astrological snapshots.",
    tags=["Research Cases"],
)
async def get_research_case_detail(
    research_case_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ResearchCaseDetailSchema:
    """Powers the interactive event timeline: every life event for this
    case in date order, each with its description/notes and — where a
    snapshot has been computed — the astrological positions captured for
    it (dasha, active yogas, transits, house-lord dignity, nakshatra
    placements).
    """
    case = (
        await session.execute(
            select(ResearchCaseModel).where(
                ResearchCaseModel.research_case_id == research_case_id,
                ResearchCaseModel.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research case not found.")

    life_events: list[LifeEventDetailSchema] = []
    for event in sorted(case.life_events, key=lambda e: e.event_date):
        latest_snapshot = max(event.snapshots, key=lambda s: s.created_at, default=None)
        snapshot_schema = None
        if latest_snapshot is not None:
            snapshot_schema = LifeEventSnapshotSchema(
                mahadasha=latest_snapshot.mahadasha,
                antardasha=latest_snapshot.antardasha,
                pratyantar=latest_snapshot.pratyantar,
                active_yogas=json.loads(latest_snapshot.active_yogas) if latest_snapshot.active_yogas else [],
                transit_features=json.loads(latest_snapshot.transit_features) if latest_snapshot.transit_features else {},
                house_lord_statuses=json.loads(latest_snapshot.house_lord_statuses) if latest_snapshot.house_lord_statuses else {},
                nakshatra_activations=json.loads(latest_snapshot.nakshatra_activations) if latest_snapshot.nakshatra_activations else [],
                snapshot_version=latest_snapshot.snapshot_version,
            )
        event_date = event.event_date.date() if hasattr(event.event_date, "date") else event.event_date
        life_events.append(
            LifeEventDetailSchema(
                id=event.id,
                event_type=_BACKEND_TO_EVENT_TYPE.get(_plain_event_type(event.event_type), EventType.OTHER),
                event_date=event_date,
                event_time=event.event_time,
                event_place=event.event_place,
                category=event.category,
                severity=event.severity,
                description=event.description,
                notes=event.notes,
                tags=json.loads(event.tags) if event.tags else [],
                snapshot=snapshot_schema,
            )
        )

    dob = case.dob.date() if hasattr(case.dob, "date") else case.dob
    return ResearchCaseDetailSchema(
        research_case_id=case.research_case_id,
        person_name=case.person_name,
        dob=dob,
        gender=case.gender,
        life_events=life_events,
    )
