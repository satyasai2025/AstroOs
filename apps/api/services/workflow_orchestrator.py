"""
AstroOS — Workflow Orchestrator (v2 Phase A)

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
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Optional

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult, SarvashtakavargaResult
from apps.api.domain.dasha import DashaTree
from apps.api.domain.divisional import VargaChart
from apps.api.domain.events import EventRecord, NatalSnapshot
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.knowledge import KnowledgeSearchQuery, KnowledgeSearchResult
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
from apps.api.services.report_engine import ReportEngine
from apps.api.services.research_engine import ResearchEngine
from apps.api.services.rule_engine import RuleEngine
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.timeline_engine import TimelineEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.verification_engine import VerificationEngine
from apps.api.services.yoga_engine import YogaEngine

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_SHASHTIAMSAS_PER_RUPA = 60.0


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
        self._wrapper = wrapper
        self._birth_chart_repo = birth_chart_repo
        self._event_repo = event_repo
        self._knowledge_engine = knowledge_engine
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

    async def analyze(
        self,
        request: WorkflowAnalysisRequest,
        *,
        user_id: Optional[uuid.UUID] = None,
    ) -> WorkflowAnalysisResult:
        transit_datetime_utc = request.transit_datetime_utc or datetime.now(timezone.utc)

        # ── Chart, Vargas, Dasha, Yoga, Shadbala, Ashtakavarga, Transit ──
        # All blocking pyswisseph/pure-Python calls, bundled into one
        # to_thread dispatch so the pipeline doesn't pay a thread-hop
        # per stage (the API contract review flagged exactly this
        # per-stage-double-dispatch pattern as wasted overhead earlier
        # this session).
        def _compute_natal_bundle():
            chart = self._horoscope_engine.generate_d1(
                birth_datetime_utc=request.birth_datetime_utc,
                latitude=request.latitude,
                longitude=request.longitude,
                ayanamsa=request.ayanamsa,
                house_system=request.house_system,
            )

            vargas: Optional[dict[str, VargaChart]] = None
            if request.include_vargas:
                vargas = self._divisional_engine.compute_all(
                    birth_datetime_utc=request.birth_datetime_utc,
                    latitude=request.latitude,
                    longitude=request.longitude,
                    ayanamsa=request.ayanamsa,
                    house_system=request.house_system,
                )

            dasha_compute_fn = getattr(self._dasha_engine, f"compute_{request.dasha_system}")
            dasha_tree = dasha_compute_fn(
                birth_datetime_utc=request.birth_datetime_utc,
                latitude=request.latitude,
                longitude=request.longitude,
                ayanamsa=request.ayanamsa,
                house_system=request.house_system,
            )

            yoga_results = self._yoga_engine.evaluate_all(chart)

            phase1 = self._shadbala_engine.compute_phase1_components(chart)
            phase2 = self._shadbala_engine.compute_phase2_components(chart)
            sthana = self._shadbala_engine.compute_sthana_bala_components(chart)
            shadbala_components = {**phase1, **phase2, **sthana}

            totals_shashtiamsas = {p: 0.0 for p in _CLASSICAL_SEVEN}
            for component_results in shadbala_components.values():
                for r in component_results:
                    totals_shashtiamsas[r.planet] += r.value_shashtiamsas
            shadbala_totals_rupas = {
                p: round(v / _SHASHTIAMSAS_PER_RUPA, 4) for p, v in totals_shashtiamsas.items()
            }

            bhinna_results = self._ashtakavarga_engine.compute_bhinnashtakavarga(chart)
            bhinna_reduced_results = self._ashtakavarga_engine.compute_reduced_bhinnashtakavarga(
                chart, bhinna_results
            )
            sarva_result = self._ashtakavarga_engine.compute_sarvashtakavarga(chart, bhinna_results)
            sarva_checksum_valid = self._ashtakavarga_engine.verify_checksum(chart, sarva_result)

            transit_results = self._transit_engine.compute_transit(chart, transit_datetime_utc)
            natal_moon_rashi = next(p.rashi for p in chart.planets if p.planet == "moon")

            facts = FactBuilder(
                yoga_engine=self._yoga_engine,
                shadbala_engine=self._shadbala_engine,
                ashtakavarga_engine=self._ashtakavarga_engine,
                transit_engine=self._transit_engine,
            ).build_facts(
                chart, transit_datetime_utc,
                dasha_tree=dasha_tree, vargas=vargas,
            )
            rule_results = self._rule_engine.evaluate_all(facts)

            return (
                chart, vargas, dasha_tree, yoga_results, shadbala_components,
                shadbala_totals_rupas, bhinna_results, bhinna_reduced_results,
                sarva_result, sarva_checksum_valid,
                transit_results, natal_moon_rashi, rule_results,
            )

        (
            chart, vargas, dasha_tree, yoga_results, shadbala_components,
            shadbala_totals_rupas, bhinna_results, bhinna_reduced_results,
            sarva_result, sarva_checksum_valid,
            transit_results, natal_moon_rashi, rule_results,
        ) = await asyncio.to_thread(_compute_natal_bundle)

        # ── Persistence (chart_id anchors everything else) ──────────────
        # request.persist=False is the recompute-only path: the caller
        # (chart detail page reload, chart comparison) already has a
        # saved chart_id and just wants its analysis reproduced for
        # display, not a new — or duplicate — birth_charts row. Schema
        # validation guarantees chart_id is set whenever persist is False.
        if request.persist:
            chart_id = await self._horoscope_engine.persist_d1(
                chart,
                birth_datetime_utc=request.birth_datetime_utc,
                latitude=request.latitude,
                longitude=request.longitude,
                ayanamsa=request.ayanamsa,
                house_system=request.house_system,
                subject_name=request.subject_name,
                user_id=user_id,
                place_name=request.place_name,
            )
            if vargas is not None:
                await self._divisional_engine.persist_all(
                    vargas,
                    birth_datetime_utc=request.birth_datetime_utc,
                    latitude=request.latitude,
                    longitude=request.longitude,
                    ayanamsa=request.ayanamsa,
                    house_system=request.house_system,
                    birth_chart_id=chart_id,
                )
        else:
            chart_id = request.chart_id

        # ── Knowledge: best-effort correlation against present yogas ────
        knowledge_citations = await self._gather_knowledge_citations(yoga_results)

        # ── Benchmark: validate against GC-MASTER golden reference ─────
        benchmark_result = None
        if self._benchmark_engine.is_loaded:
            benchmark_result = self._benchmark_engine.validate_chart(
                chart, subject_name=request.subject_name,
            )

        # ── Events + Verification + Timeline (only if events are already
        # recorded for this chart; computed once and reused for both the
        # verification result and the report's timeline section — not
        # recomputed twice) ──────────────────────────────────────────────
        timeline = None
        verification_findings: Optional[VerificationFindings] = None
        events = await self._event_repo.list_for_chart(chart_id)
        if events:
            _, timeline = await self._build_event_analyses(
                chart, dasha_system=request.dasha_system, dasha_tree=dasha_tree,
                yoga_results=yoga_results, shadbala_components=shadbala_components,
                bhinna_results=bhinna_results, sarva_result=sarva_result,
                chart_id=chart_id, events=events, vargas=vargas,
            )
            verification_findings = VerificationEngine.verify_timeline(timeline)

        report = ReportEngine.build_chart_report(
            chart,
            timeline=timeline,
            verification=verification_findings,
            stats=None,
            citations=tuple(knowledge_citations),
            title="Unified Analysis",
            subject_name=request.subject_name,
            generated_by=request.generated_by,
            chart_id=chart_id,
        )

        # ── Research Data correlation: only if the caller opted in by
        # supplying a project id — not every analysis is research, so
        # this stays off by default (M1 criterion 8) ────────────────────
        research_snapshot_id: Optional[uuid.UUID] = None
        if request.research_project_id is not None:
            project = await self._research_repo.get_project(request.research_project_id)
            if project is None:
                raise ValueError(f"Research project {request.research_project_id} not found")
            snapshot = await self._research_engine.capture_snapshot(
                project_id=request.research_project_id,
                chart_id=chart_id,
                chart_ref=chart,
                yogas=tuple(yoga_results),
                shadbala_components=shadbala_components,
                ashtakavarga_data=(tuple(bhinna_results), sarva_result),
                dasha_trees={request.dasha_system: dasha_tree},
                divisional_charts=tuple(vargas.values()) if vargas else None,
                timeline_ref=timeline,
                verification_ref=verification_findings,
                events=tuple(events) if events else None,
                dataset_id=project.dataset_id,
            )
            research_snapshot_id = snapshot.id

        return WorkflowAnalysisResult(
            chart_id=chart_id,
            chart=chart,
            vargas=vargas,
            dasha_tree=dasha_tree,
            yoga_results=yoga_results,
            shadbala_totals_rupas=shadbala_totals_rupas,
            bhinna_results=bhinna_results,
            bhinna_reduced_results=bhinna_reduced_results,
            sarva_result=sarva_result,
            sarva_checksum_valid=sarva_checksum_valid,
            transit_datetime_utc=transit_datetime_utc,
            natal_moon_rashi=natal_moon_rashi,
            transit_results=transit_results,
            rule_results=rule_results,
            knowledge_citations=knowledge_citations,
            verification_findings=verification_findings,
            report=report,
            research_snapshot_id=research_snapshot_id,
            benchmark_result=benchmark_result,
        )

    async def _gather_knowledge_citations(
        self, yoga_results: list[YogaResult]
    ) -> list[KnowledgeSearchResult]:
        """Best-effort keyword correlation, not a semantic citation
        engine — searches the Knowledge base by each present yoga's
        name and dedupes results. Module 20 (Knowledge) has no
        yoga-to-citation mapping today; this is the same "explicit,
        pragmatic gap, not silent" pattern used elsewhere (see
        routers/ai.py's docstring)."""
        seen: set[tuple[str, uuid.UUID]] = set()
        citations: list[KnowledgeSearchResult] = []
        for yoga in yoga_results:
            if not yoga.is_present:
                continue
            results = await self._knowledge_engine.search(
                KnowledgeSearchQuery(text=yoga.name, limit=3)
            )
            for r in results:
                key = (r.entity_type, r.entity_id)
                if key not in seen:
                    seen.add(key)
                    citations.append(r)
        return citations

    async def _build_event_analyses(
        self,
        chart: D1Chart,
        *,
        dasha_system: str,
        dasha_tree: DashaTree,
        yoga_results: list[YogaResult],
        shadbala_components,
        bhinna_results: list[BhinnashtakavargaResult],
        sarva_result: SarvashtakavargaResult,
        chart_id: uuid.UUID,
        events: list[EventRecord],
        vargas: Optional[dict[str, VargaChart]] = None,
    ):
        """Builds (natal_snapshot, timeline) for events already recorded
        against this chart. Unlike routers/timeline.py's placeholder
        NatalSnapshot, this orchestrator has real yogas/shadbala/
        ashtakavarga already computed for this exact chart, so the
        snapshot is genuinely complete, not a stand-in."""
        natal_snapshot = NatalSnapshot(
            chart_id=chart_id,
            chart=chart,
            yogas=tuple(yoga_results),
            shadbala_components=shadbala_components,
            bhinnashtakavarga=tuple(bhinna_results),
            sarvashtakavarga=sarva_result,
        )

        fact_registries = {}
        event_engine = EventEngine(transit_engine=self._transit_engine, rule_engine=self._rule_engine)
        for event in events:
            event_datetime_utc = datetime.combine(event.event_date, time.min, tzinfo=timezone.utc)
            fact_registries[event.id] = FactBuilder(
                yoga_engine=self._yoga_engine,
                shadbala_engine=self._shadbala_engine,
                ashtakavarga_engine=self._ashtakavarga_engine,
                transit_engine=self._transit_engine,
            ).build_facts(
                chart, event_datetime_utc,
                dasha_tree=dasha_tree, vargas=vargas,
            )

        batch_result = event_engine.analyze_batch(
            events,
            dasha_trees={dasha_system: dasha_tree},
            natal_snapshot=natal_snapshot,
            fact_registries=fact_registries,
        )
        timeline = TimelineEngine.build_timeline(tuple(batch_result.analyses))
        return natal_snapshot, timeline
