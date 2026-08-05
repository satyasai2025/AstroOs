"""
AstroOS — Workflow Orchestrator (v2 Phase A; stage pipeline since Phase 10 R1)

Composes the existing chart/dasha/yoga/shadbala/ashtakavarga/transit/
rule/knowledge/verification/report/research engines into a single
vertical-slice pipeline: Chart -> Vargas -> Dasha -> Yoga -> Shadbala ->
Ashtakavarga -> Transit -> Facts -> Rule -> Knowledge -> Verification ->
Report -> Research (optional). Knowledge citations are merged directly
into the report's own sections (not just returned alongside it). The
Research stage only runs if the caller opts in with
request.research_project_id — most analyses aren't research and
shouldn't silently accumulate snapshots in someone's project.

This is the first genuine cross-engine *service*-layer orchestrator in
the codebase (earlier per-request compositions, e.g. routers/timeline.py,
kept their multi-engine sequencing inline in the router — flagged during
this session's API contract review as orchestration logic sitting one
layer too shallow). This class exists so that logic has a home outside
the HTTP layer: apps/api/routers/workflow.py stays a thin adapter that
only builds this orchestrator, calls analyze(), and serializes the
result — same division of responsibility as every *_engine.py class
already in this codebase.

Benchmark validation (the 8th pipeline stage in the AstroOS v2 vision)
is not implemented here — no BM-* execution engine exists yet (v2 Phase
C has not started, see ASTROOS_V2_ROADMAP.md). It is represented as an
explicit placeholder result, not silently skipped.

Since Phase 10 R1 (2026-08-06), analyze()'s body is a declared,
ordered list of Stage objects (apps/api/services/orchestration/) run by
a Pipeline that traces each stage's duration and success/failure — this
class itself is now a thin wrapper: build a PipelineContext from the
request, run the pipeline, map the resulting context onto
WorkflowAnalysisResult. Every stage's logic is the same engine calls
this class used to make inline; this refactor moved code, it did not
rewrite any domain logic.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult, SarvashtakavargaResult
from apps.api.domain.dasha import DashaTree
from apps.api.domain.divisional import VargaChart
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.knowledge import KnowledgeSearchResult
from apps.api.domain.report import ChartReport
from apps.api.domain.rules import RuleResult
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.verification import VerificationFindings
from apps.api.domain.yoga import YogaResult
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.divisional_chart_repository import DivisionalChartRepository
from apps.api.repositories.divisional_planet_repository import DivisionalPlanetRepository
from apps.api.repositories.event_repository import EventRepository
from apps.api.repositories.house_repository import HouseRepository
from apps.api.repositories.planet_position_repository import PlanetPositionRepository
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.schemas.workflow import WorkflowAnalysisRequest
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.benchmark_engine import BenchmarkEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.event_engine import EventEngine
from apps.api.services.fact_builder import FactBuilder
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.knowledge_engine import KnowledgeEngine
from apps.api.services.orchestration.stage import Pipeline, PipelineContext
from apps.api.services.orchestration.stages.benchmark_stage import BenchmarkStage
from apps.api.services.orchestration.stages.events_verification_stage import (
    EventsVerificationStage,
)
from apps.api.services.orchestration.stages.knowledge_stage import KnowledgeStage
from apps.api.services.orchestration.stages.natal_bundle_stage import NatalBundleStage
from apps.api.services.orchestration.stages.persistence_stage import PersistenceStage
from apps.api.services.orchestration.stages.report_stage import ReportStage
from apps.api.services.orchestration.stages.research_stage import ResearchStage
from apps.api.services.research_engine import ResearchEngine
from apps.api.services.rule_engine import RuleEngine
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.yoga_engine import YogaEngine


@dataclass
class WorkflowAnalysisResult:
    """Raw domain objects from every pipeline stage. Serialization to
    HTTP response schemas happens in the router, reusing each engine's
    own existing router-level serializer functions."""

    chart_id: uuid.UUID
    chart: D1Chart
    vargas: Optional[dict[str, VargaChart]]
    dasha_tree: DashaTree
    yoga_results: list[YogaResult]
    shadbala_totals_rupas: dict[str, float]
    bhinna_results: list[BhinnashtakavargaResult]
    bhinna_reduced_results: list[BhinnashtakavargaResult]
    sarva_result: SarvashtakavargaResult
    sarva_checksum_valid: bool
    transit_datetime_utc: datetime
    natal_moon_rashi: str
    transit_results: list[TransitPlanetResult]
    rule_results: list[RuleResult]
    knowledge_citations: list[KnowledgeSearchResult]
    verification_findings: Optional[VerificationFindings]
    report: ChartReport
    research_snapshot_id: Optional[uuid.UUID]
    benchmark_result: Any = None  # BenchmarkResult or None


class WorkflowOrchestrator:
    """
    Constructed per-request with the process-wide EphemerisWrapper and
    request-scoped repositories — same lifecycle as every other engine
    factory in apps/api/dependencies.py.
    """

    def __init__(
        self,
        wrapper: EphemerisWrapper,
        birth_chart_repo: BirthChartRepository,
        planet_position_repo: PlanetPositionRepository,
        house_repo: HouseRepository,
        divisional_chart_repo: DivisionalChartRepository,
        divisional_planet_repo: DivisionalPlanetRepository,
        event_repo: EventRepository,
        knowledge_engine: KnowledgeEngine,
        research_repo: ResearchRepository,
    ) -> None:
        self._event_repo = event_repo
        self._research_repo = research_repo
        self._research_engine = ResearchEngine(research_repo)

        self._horoscope_engine = HoroscopeEngine(
            wrapper,
            birth_chart_repo=birth_chart_repo,
            planet_position_repo=planet_position_repo,
            house_repo=house_repo,
        )
        self._divisional_engine = DivisionalEngine(
            wrapper,
            birth_chart_repo=birth_chart_repo,
            divisional_chart_repo=divisional_chart_repo,
            divisional_planet_repo=divisional_planet_repo,
        )
        self._dasha_engine = DashaEngine(wrapper)
        self._yoga_engine = YogaEngine()
        self._shadbala_engine = ShadbalaEngine()
        self._ashtakavarga_engine = AshtakavargaEngine()
        self._transit_engine = TransitEngine(wrapper, ashtakavarga_engine=self._ashtakavarga_engine)
        self._rule_engine = RuleEngine()
        self._benchmark_engine = BenchmarkEngine()
        self._knowledge_engine = knowledge_engine

        self._pipeline = Pipeline(
            [
                NatalBundleStage(
                    horoscope_engine=self._horoscope_engine,
                    divisional_engine=self._divisional_engine,
                    dasha_engine=self._dasha_engine,
                    yoga_engine=self._yoga_engine,
                    shadbala_engine=self._shadbala_engine,
                    ashtakavarga_engine=self._ashtakavarga_engine,
                    transit_engine=self._transit_engine,
                    rule_engine=self._rule_engine,
                    fact_builder_cls=FactBuilder,
                ),
                PersistenceStage(
                    horoscope_engine=self._horoscope_engine,
                    divisional_engine=self._divisional_engine,
                ),
                KnowledgeStage(knowledge_engine=self._knowledge_engine),
                BenchmarkStage(benchmark_engine=self._benchmark_engine),
                EventsVerificationStage(
                    event_repo=self._event_repo,
                    transit_engine=self._transit_engine,
                    rule_engine=self._rule_engine,
                    yoga_engine=self._yoga_engine,
                    shadbala_engine=self._shadbala_engine,
                    ashtakavarga_engine=self._ashtakavarga_engine,
                    fact_builder_cls=FactBuilder,
                    event_engine_cls=EventEngine,
                ),
                ReportStage(),
                ResearchStage(
                    research_repo=self._research_repo,
                    research_engine=self._research_engine,
                ),
            ]
        )

    async def analyze(
        self,
        request: WorkflowAnalysisRequest,
        *,
        user_id: Optional[uuid.UUID] = None,
    ) -> WorkflowAnalysisResult:
        transit_datetime_utc = request.transit_datetime_utc or datetime.now(timezone.utc)

        ctx = PipelineContext(
            request=request,
            user_id=user_id,
            transit_datetime_utc=transit_datetime_utc,
        )
        ctx = await self._pipeline.run(ctx)

        return WorkflowAnalysisResult(
            chart_id=ctx.chart_id,
            chart=ctx.chart,
            vargas=ctx.vargas,
            dasha_tree=ctx.dasha_tree,
            yoga_results=ctx.yoga_results,
            shadbala_totals_rupas=ctx.shadbala_totals_rupas,
            bhinna_results=ctx.bhinna_results,
            bhinna_reduced_results=ctx.bhinna_reduced_results,
            sarva_result=ctx.sarva_result,
            sarva_checksum_valid=ctx.sarva_checksum_valid,
            transit_datetime_utc=ctx.transit_datetime_utc,
            natal_moon_rashi=ctx.natal_moon_rashi,
            transit_results=ctx.transit_results,
            rule_results=ctx.rule_results,
            knowledge_citations=ctx.knowledge_citations,
            verification_findings=ctx.verification_findings,
            report=ctx.report,
            research_snapshot_id=ctx.research_snapshot_id,
            benchmark_result=ctx.benchmark_result,
        )
