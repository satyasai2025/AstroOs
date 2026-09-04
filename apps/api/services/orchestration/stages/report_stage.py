"""AstroOS — Report Stage: composes the ChartReport, merging Knowledge
citations directly into its own sections (not just returned alongside it)."""

from __future__ import annotations

from apps.api.services.orchestration.stage import PipelineContext
from apps.api.services.report_engine import ReportEngine


class ReportStage:
    name = "report"

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        request = ctx.request
        ctx.report = ReportEngine.build_chart_report(
            ctx.chart,
            timeline=ctx.timeline,
            verification=ctx.verification_findings,
            stats=None,
            citations=tuple(ctx.knowledge_citations),
            title="Unified Analysis",
            subject_name=request.subject_name,
            generated_by=request.generated_by,
            chart_id=ctx.chart_id,
        )
        return ctx
