"""
AstroOS — Natal Bundle Stage

Chart -> Vargas -> Dasha -> Yoga -> Shadbala -> Ashtakavarga -> Transit ->
Facts -> Rule, all in one asyncio.to_thread dispatch. Kept as a single
stage (not split one-stage-per-engine) deliberately: these are all
blocking pyswisseph/pure-Python calls, and splitting them into separate
to_thread dispatches would reintroduce the exact per-stage thread-hop
overhead the original analyze() docstring flagged as wasted cost. This
stage's body is that same bundle, moved verbatim.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.divisional import VargaChart
from apps.api.services.orchestration.stage import PipelineContext

import asyncio

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_SHASHTIAMSAS_PER_RUPA = 60.0


class NatalBundleStage:
    name = "chart_vargas_dasha_yoga_shadbala_ashtakavarga_transit_rule"

    def __init__(
        self,
        *,
        horoscope_engine,
        divisional_engine,
        dasha_engine,
        yoga_engine,
        shadbala_engine,
        ashtakavarga_engine,
        transit_engine,
        rule_engine,
        fact_builder_cls,
    ) -> None:
        self._horoscope_engine = horoscope_engine
        self._divisional_engine = divisional_engine
        self._dasha_engine = dasha_engine
        self._yoga_engine = yoga_engine
        self._shadbala_engine = shadbala_engine
        self._ashtakavarga_engine = ashtakavarga_engine
        self._transit_engine = transit_engine
        self._rule_engine = rule_engine
        self._fact_builder_cls = fact_builder_cls

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        request = ctx.request
        transit_datetime_utc = ctx.transit_datetime_utc

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

            facts = self._fact_builder_cls(
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
            ctx.chart, ctx.vargas, ctx.dasha_tree, ctx.yoga_results, ctx.shadbala_components,
            ctx.shadbala_totals_rupas, ctx.bhinna_results, ctx.bhinna_reduced_results,
            ctx.sarva_result, ctx.sarva_checksum_valid,
            ctx.transit_results, ctx.natal_moon_rashi, ctx.rule_results,
        ) = await asyncio.to_thread(_compute_natal_bundle)

        return ctx
