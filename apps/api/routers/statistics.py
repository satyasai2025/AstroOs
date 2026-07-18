"""
AstroOS — Statistics Router (Module 18 — HTTP surface)

HTTP adapter layer over StatisticsEngine. Every endpoint first fetches
the target project's snapshots via ResearchRepository (StatisticsEngine
itself never touches the database), then delegates the actual
computation to StatisticsEngine's stateless static methods.

Note: AstrologicalSnapshot.chart_ref currently always round-trips as
None from ResearchRepository (see schemas/research.py's docstring) —
distributions that read chart_ref (planet/house, planet/rashi) will
report zero counts until that persistence gap is closed. This is an
existing data-completeness limitation, not something this router papers
over silently.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.schemas.statistics import (
    AggregateReportResponse,
    CrosstabRequest,
    CrosstabResponse,
    DatasetMetadataResponse,
    DistributionResponse,
    FullReportRequest,
    NumericSummaryResponse,
    PlanetDistributionRequest,
    ProjectScopedRequest,
)
from apps.api.services.statistics_engine import StatisticsEngine

router = APIRouter(prefix="/statistics", tags=["Statistics"])


async def _get_repo(session: AsyncSession = Depends(get_db_session)) -> ResearchRepository:
    return ResearchRepository(session)


def _distribution_response(d) -> DistributionResponse:
    return DistributionResponse(
        label=d.label, variable=d.variable, bins=list(d.bins),
        counts=list(d.counts), total=d.total,
    )


def _numeric_response(n) -> NumericSummaryResponse:
    return NumericSummaryResponse(
        label=n.label, variable=n.variable, count=n.count, mean=n.mean,
        std_dev=n.std_dev, min=n.min, max=n.max, median=n.median,
        q1=n.q1, q3=n.q3, sum=n.sum,
    )


@router.post("/distributions/planet-house", response_model=DistributionResponse)
async def planet_house_distribution(
    body: PlanetDistributionRequest, repo: ResearchRepository = Depends(_get_repo)
) -> DistributionResponse:
    snapshots = await repo.list_snapshots(body.project_id)
    return _distribution_response(
        StatisticsEngine.compute_planet_house_distribution(snapshots, body.planet)
    )


@router.post("/distributions/planet-rashi", response_model=DistributionResponse)
async def planet_rashi_distribution(
    body: PlanetDistributionRequest, repo: ResearchRepository = Depends(_get_repo)
) -> DistributionResponse:
    snapshots = await repo.list_snapshots(body.project_id)
    return _distribution_response(
        StatisticsEngine.compute_planet_rashi_distribution(snapshots, body.planet)
    )


@router.post("/distributions/yoga", response_model=DistributionResponse)
async def yoga_distribution(
    body: ProjectScopedRequest, repo: ResearchRepository = Depends(_get_repo)
) -> DistributionResponse:
    snapshots = await repo.list_snapshots(body.project_id)
    return _distribution_response(StatisticsEngine.compute_yoga_distribution(snapshots))


@router.post("/distributions/verification-strength", response_model=DistributionResponse)
async def verification_strength_distribution(
    body: ProjectScopedRequest, repo: ResearchRepository = Depends(_get_repo)
) -> DistributionResponse:
    snapshots = await repo.list_snapshots(body.project_id)
    return _distribution_response(
        StatisticsEngine.compute_verification_strength_distribution(snapshots)
    )


@router.post("/summary/planet-house", response_model=NumericSummaryResponse)
async def planet_house_summary(
    body: PlanetDistributionRequest, repo: ResearchRepository = Depends(_get_repo)
) -> NumericSummaryResponse:
    snapshots = await repo.list_snapshots(body.project_id)
    return _numeric_response(
        StatisticsEngine.compute_planet_house_summary(snapshots, body.planet)
    )


@router.post("/crosstab", response_model=CrosstabResponse)
async def crosstab(
    body: CrosstabRequest, repo: ResearchRepository = Depends(_get_repo)
) -> CrosstabResponse:
    snapshots = await repo.list_snapshots(body.project_id)
    ct = StatisticsEngine.compute_crosstab(snapshots, body.row_field, body.col_field)
    return CrosstabResponse(
        label=ct.label, row_variable=ct.row_variable, column_variable=ct.column_variable,
        row_labels=list(ct.row_labels), column_labels=list(ct.column_labels),
        cells=[list(row) for row in ct.cells], row_totals=list(ct.row_totals),
    )


@router.post("/report", response_model=AggregateReportResponse)
async def full_report(
    body: FullReportRequest, repo: ResearchRepository = Depends(_get_repo)
) -> AggregateReportResponse:
    snapshots = await repo.list_snapshots(body.project_id)
    report = StatisticsEngine.compute_full_report(
        snapshots,
        title=body.title,
        experiment_id=body.experiment_id,
        filtered_sample_size=body.filtered_sample_size,
    )
    return AggregateReportResponse(
        title=report.title,
        metadata=DatasetMetadataResponse(
            sample_size=report.metadata.sample_size,
            snapshot_count=report.metadata.snapshot_count,
            filtered_sample_size=report.metadata.filtered_sample_size,
            experiment_id=report.metadata.experiment_id,
            engine_version=report.metadata.engine_version,
            generated_at=report.metadata.generated_at,
        ),
        distributions=[_distribution_response(d) for d in report.distributions],
        numeric_summaries=[_numeric_response(n) for n in report.numeric_summaries],
        report_version=report.report_version,
    )
