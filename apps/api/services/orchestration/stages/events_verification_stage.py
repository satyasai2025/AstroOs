"""
AstroOS — Events + Verification Stage

Only runs its real work if events are already recorded for this chart;
the timeline it builds is computed once and reused for both the
verification result and the report's timeline section — not recomputed
twice.
"""

from __future__ import annotations

from datetime import datetime, time, timezone

from apps.api.domain.events import NatalSnapshot
from apps.api.services.orchestration.stage import PipelineContext
from apps.api.services.timeline_engine import TimelineEngine
from apps.api.services.verification_engine import VerificationEngine


class EventsVerificationStage:
    name = "events_verification"

    def __init__(
        self,
        *,
        event_repo,
        transit_engine,
        rule_engine,
        yoga_engine,
        shadbala_engine,
        ashtakavarga_engine,
        fact_builder_cls,
        event_engine_cls,
    ) -> None:
        self._event_repo = event_repo
        self._transit_engine = transit_engine
        self._rule_engine = rule_engine
        self._yoga_engine = yoga_engine
        self._shadbala_engine = shadbala_engine
        self._ashtakavarga_engine = ashtakavarga_engine
        self._fact_builder_cls = fact_builder_cls
        self._event_engine_cls = event_engine_cls

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.events = await self._event_repo.list_for_chart(ctx.chart_id)
        if not ctx.events:
            return ctx

        request = ctx.request
        natal_snapshot = NatalSnapshot(
            chart_id=ctx.chart_id,
            chart=ctx.chart,
            yogas=tuple(ctx.yoga_results),
            shadbala_components=ctx.shadbala_components,
            bhinnashtakavarga=tuple(ctx.bhinna_results),
            sarvashtakavarga=ctx.sarva_result,
        )

        fact_registries = {}
        event_engine = self._event_engine_cls(
            transit_engine=self._transit_engine, rule_engine=self._rule_engine
        )
        for event in ctx.events:
            event_datetime_utc = datetime.combine(event.event_date, time.min, tzinfo=timezone.utc)
            fact_registries[event.id] = self._fact_builder_cls(
                yoga_engine=self._yoga_engine,
                shadbala_engine=self._shadbala_engine,
                ashtakavarga_engine=self._ashtakavarga_engine,
                transit_engine=self._transit_engine,
            ).build_facts(
                ctx.chart, event_datetime_utc,
                dasha_tree=ctx.dasha_tree, vargas=ctx.vargas,
            )

        batch_result = event_engine.analyze_batch(
            ctx.events,
            dasha_trees={request.dasha_system: ctx.dasha_tree},
            natal_snapshot=natal_snapshot,
            fact_registries=fact_registries,
        )
        ctx.timeline = TimelineEngine.build_timeline(tuple(batch_result.analyses))
        ctx.verification_findings = VerificationEngine.verify_timeline(ctx.timeline)
        return ctx
