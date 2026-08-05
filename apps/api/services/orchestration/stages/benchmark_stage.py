"""
AstroOS — Benchmark Stage

Validates against the GC-MASTER golden reference when the current chart
matches one of AstroOS's 5 internal reference subjects. Benchmark
validation (the 8th pipeline stage in the AstroOS v2 vision) has no
BM-* execution engine beyond this reference-chart check (v2 Phase C has
not started) — represented as an explicit not_applicable result
downstream, not silently skipped.
"""

from __future__ import annotations

from apps.api.services.orchestration.stage import PipelineContext


class BenchmarkStage:
    name = "benchmark"

    def __init__(self, *, benchmark_engine) -> None:
        self._benchmark_engine = benchmark_engine

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if self._benchmark_engine.is_loaded:
            ctx.benchmark_result = self._benchmark_engine.validate_chart(
                ctx.chart, subject_name=ctx.request.subject_name,
            )
        return ctx
