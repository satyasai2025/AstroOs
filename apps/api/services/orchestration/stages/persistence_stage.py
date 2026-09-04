"""
AstroOS — Persistence Stage

request.persist=False is the recompute-only path: the caller (chart
detail page reload, chart comparison) already has a saved chart_id and
just wants its analysis reproduced for display, not a new — or
duplicate — birth_charts row. Schema validation guarantees chart_id is
set whenever persist is False.
"""

from __future__ import annotations

from apps.api.services.orchestration.stage import PipelineContext


class PersistenceStage:
    name = "persistence"

    def __init__(self, *, horoscope_engine, divisional_engine) -> None:
        self._horoscope_engine = horoscope_engine
        self._divisional_engine = divisional_engine

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        request = ctx.request
        if request.persist:
            ctx.chart_id = await self._horoscope_engine.persist_d1(
                ctx.chart,
                birth_datetime_utc=request.birth_datetime_utc,
                latitude=request.latitude,
                longitude=request.longitude,
                ayanamsa=request.ayanamsa,
                house_system=request.house_system,
                subject_name=request.subject_name,
                user_id=ctx.user_id,
                place_name=request.place_name,
                force_new=request.force_new,
            )
            if ctx.vargas is not None:
                await self._divisional_engine.persist_all(
                    ctx.vargas,
                    birth_datetime_utc=request.birth_datetime_utc,
                    latitude=request.latitude,
                    longitude=request.longitude,
                    ayanamsa=request.ayanamsa,
                    house_system=request.house_system,
                    birth_chart_id=ctx.chart_id,
                )
        else:
            ctx.chart_id = request.chart_id

        return ctx
