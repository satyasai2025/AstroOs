"""
AstroOS — Research Stage

Only runs if the caller opts in with request.research_project_id — most
analyses aren't research and shouldn't silently accumulate snapshots in
someone's project (M1 criterion 8).
"""

from __future__ import annotations

from apps.api.services.orchestration.stage import PipelineContext


class ResearchStage:
    name = "research"

    def __init__(self, *, research_repo, research_engine) -> None:
        self._research_repo = research_repo
        self._research_engine = research_engine

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        request = ctx.request
        if request.research_project_id is None:
            return ctx

        project = await self._research_repo.get_project(request.research_project_id)
        if project is None:
            raise ValueError(f"Research project {request.research_project_id} not found")

        snapshot = await self._research_engine.capture_snapshot(
            project_id=request.research_project_id,
            chart_id=ctx.chart_id,
            chart_ref=ctx.chart,
            yogas=tuple(ctx.yoga_results),
            shadbala_components=ctx.shadbala_components,
            ashtakavarga_data=(tuple(ctx.bhinna_results), ctx.sarva_result),
            dasha_trees={request.dasha_system: ctx.dasha_tree},
            divisional_charts=tuple(ctx.vargas.values()) if ctx.vargas else None,
            timeline_ref=ctx.timeline,
            verification_ref=ctx.verification_findings,
            events=tuple(ctx.events) if ctx.events else None,
            dataset_id=project.dataset_id,
        )
        ctx.research_snapshot_id = snapshot.id
        return ctx
