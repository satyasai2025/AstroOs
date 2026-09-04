"""
AstroOS — Orchestration Stage protocol + PipelineContext + Pipeline runner

PipelineContext is the promoted, named version of what used to be a long
chain of local variables threaded through WorkflowOrchestrator.analyze()
via tuple-unpacking. Every field here corresponds 1:1 to one of those
variables — nothing new, just given a name and a home.

Stage is deliberately minimal (a name plus one async method) so adding a
new stage means writing one small class and inserting it into the
ordered list in workflow_orchestrator.py, not editing a large procedural
method body.

Pipeline.run() is the same per-stage tracing that Phase 10's lightweight
R1 pass added directly inside analyze() (logs each stage's duration and
success/failure) — moved here so it wraps every Stage.run() call
uniformly instead of being hand-repeated at each call site.
"""

from __future__ import annotations

import logging
import time as time_module
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult, SarvashtakavargaResult
from apps.api.domain.dasha import DashaTree
from apps.api.domain.divisional import VargaChart
from apps.api.domain.events import EventRecord
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.knowledge import KnowledgeSearchResult
from apps.api.domain.report import ChartReport
from apps.api.domain.rules import RuleResult
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.verification import VerificationFindings
from apps.api.domain.yoga import YogaResult
from apps.api.schemas.workflow import WorkflowAnalysisRequest

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """Mutable state threaded through every Stage. Stages read the
    fields they need and write the fields they produce; nothing here is
    hidden behind tuple position the way analyze()'s locals used to be."""

    request: WorkflowAnalysisRequest
    user_id: Optional[uuid.UUID]
    transit_datetime_utc: datetime

    chart: Optional[D1Chart] = None
    vargas: Optional[dict[str, VargaChart]] = None
    dasha_tree: Optional[DashaTree] = None
    yoga_results: list[YogaResult] = field(default_factory=list)
    shadbala_components: dict = field(default_factory=dict)
    shadbala_totals_rupas: dict[str, float] = field(default_factory=dict)
    bhinna_results: list[BhinnashtakavargaResult] = field(default_factory=list)
    bhinna_reduced_results: list[BhinnashtakavargaResult] = field(default_factory=list)
    sarva_result: Optional[SarvashtakavargaResult] = None
    sarva_checksum_valid: Optional[bool] = None
    transit_results: list[TransitPlanetResult] = field(default_factory=list)
    natal_moon_rashi: Optional[str] = None
    rule_results: list[RuleResult] = field(default_factory=list)

    chart_id: Optional[uuid.UUID] = None

    knowledge_citations: list[KnowledgeSearchResult] = field(default_factory=list)

    benchmark_result: Any = None

    events: list[EventRecord] = field(default_factory=list)
    timeline: Any = None
    verification_findings: Optional[VerificationFindings] = None

    report: Optional[ChartReport] = None

    research_snapshot_id: Optional[uuid.UUID] = None


class Stage(Protocol):
    """One named step in the analysis pipeline. `run` receives the
    context produced by every prior stage and returns the context to
    hand to the next one (same object, mutated in place — returned
    explicitly so a stage could, in principle, swap in a new context)."""

    name: str

    async def run(self, ctx: PipelineContext) -> PipelineContext: ...


class Pipeline:
    """Runs an ordered list of Stages against one PipelineContext,
    tracing each stage's duration and success/failure the same way
    Phase 10's lightweight-R1 pass logged it inline in analyze()."""

    def __init__(self, stages: list[Stage]) -> None:
        self._stages = stages

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        for stage in self._stages:
            started = time_module.monotonic()
            try:
                ctx = await stage.run(ctx)
            except Exception:
                elapsed = time_module.monotonic() - started
                logger.exception(
                    "workflow stage '%s' failed after %.3fs", stage.name, elapsed
                )
                raise
            else:
                elapsed = time_module.monotonic() - started
                logger.info(
                    "workflow stage '%s' completed in %.3fs", stage.name, elapsed
                )
        return ctx
