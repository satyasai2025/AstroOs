"""
AstroOS — Fact Builder (Module 13)

The ONLY place in the Rule Engine pipeline that calls astrology
calculation engines. Translates their outputs into standardized Facts.
RuleEngine itself never touches an engine directly — this is the
boundary. Phase 1 scope: the fact vocabulary given in the review's
specification (planet.*, house.*, yoga.*, shadbala.*, ashtakavarga.*,
transit.*), not attempting exhaustive coverage of every possible fact
derivable from every engine.

Ordinary orchestration code, not itself under the "never perform
astrology calculations" constraint — that constraint applies to
RuleEngine, which only ever reads back out of the FactRegistry this
class produces.
"""

from __future__ import annotations

from datetime import datetime

from apps.api.domain.facts import Fact
from apps.api.domain.horoscope import D1Chart
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.house_engine import HouseEngine
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.yoga_engine import YogaEngine

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_ALL_NINE = _CLASSICAL_SEVEN + ["rahu", "ketu"]


class FactBuilder:
    """
    Needs every calculation engine it translates facts from. All are
    optional at construction except GrahaEngine/HouseEngine/YogaEngine
    (needed for facts computable from the D1 chart alone) — Shadbala's
    fuller component set and Transit both need extra dependencies
    (DivisionalEngine, EphemerisWrapper, a transit moment) that aren't
    always available, so their facts are built only when those
    dependencies are actually provided, exactly like those engines'
    own optional-dependency pattern.
    """

    def __init__(
        self,
        graha_engine: GrahaEngine | None = None,
        house_engine: HouseEngine | None = None,
        yoga_engine: YogaEngine | None = None,
        shadbala_engine: ShadbalaEngine | None = None,
        ashtakavarga_engine: AshtakavargaEngine | None = None,
        transit_engine: TransitEngine | None = None,
    ) -> None:
        self._graha_engine = graha_engine or GrahaEngine()
        self._house_engine = house_engine or HouseEngine()
        self._yoga_engine = yoga_engine or YogaEngine()
        self._shadbala_engine = shadbala_engine
        self._ashtakavarga_engine = ashtakavarga_engine or AshtakavargaEngine()
        self._transit_engine = transit_engine

    def _build_planet_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        for position in chart.planets:
            planet = position.planet
            registry.add_fact(Fact(f"planet.{planet}.house", position.house_number, "graha_engine"))
            registry.add_fact(Fact(f"planet.{planet}.rashi", position.rashi, "graha_engine"))
            registry.add_fact(Fact(f"planet.{planet}.retrograde", position.is_retrograde, "graha_engine"))
            registry.add_fact(Fact(f"planet.{planet}.combust", position.is_combust, "graha_engine"))
            if planet in _CLASSICAL_SEVEN:
                registry.add_fact(Fact(
                    f"planet.{planet}.exalted",
                    self._graha_engine.is_exalted(planet, position.rashi), "graha_engine",
                ))
                registry.add_fact(Fact(
                    f"planet.{planet}.own_sign",
                    self._graha_engine.is_own_sign(planet, position.rashi), "graha_engine",
                ))
                registry.add_fact(Fact(
                    f"planet.{planet}.debilitated",
                    self._graha_engine.is_debilitated(planet, position.rashi), "graha_engine",
                ))

    def _build_house_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        """
        house.{N}.lord_house is a small FactBuilder-side derivation (not
        a new astrology calculation) — resolving which house a house's
        already-computed lord currently occupies, so rules can express
        classically important house-lord-placement concepts (e.g. "10th
        lord in the 10th") without RuleEngine needing indirect/templated
        fact-key lookups, which the Condition model deliberately doesn't
        support (fact_key is always a fixed string).
        """
        planet_house_by_name = {p.planet: p.house_number for p in chart.planets}

        for house_cusp in chart.houses:
            lord = self._house_engine.get_house_lord(house_cusp.rashi)
            registry.add_fact(Fact(f"house.{house_cusp.house_number}.lord", lord, "house_engine"))
            registry.add_fact(Fact(f"house.{house_cusp.house_number}.rashi", house_cusp.rashi, "house_engine"))
            if lord in planet_house_by_name:
                registry.add_fact(Fact(
                    f"house.{house_cusp.house_number}.lord_house",
                    planet_house_by_name[lord], "house_engine",
                ))

    def _build_yoga_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        for result in self._yoga_engine.evaluate_all(chart):
            registry.add_fact(Fact(f"yoga.{result.yoga_id}.present", result.is_present, "yoga_engine"))
            registry.add_fact(Fact(
                f"yoga.{result.yoga_id}.strength",
                result.strength if result.strength is not None else "none", "yoga_engine",
            ))

    def _build_shadbala_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        """
        "Total" here means the sum of every component this
        ShadbalaEngine instance can currently compute — which depends on
        how it was wired (a plain ShadbalaEngine() can't compute
        Saptavargaja or the sunrise-dependent components). This is NOT
        classical-text-complete Shadbala (Varsha/Masa lord remain an
        unimplemented gap even in the fullest wiring, per Module 9's own
        documented scope) — it is exactly "sum of what this engine
        instance covers," made explicit here rather than implied.

        Reported in Rupas (Shashtiamsas / 60), not raw Shashtiamsas —
        classical "Required Bala" thresholds (the minimum a planet needs
        to be considered strong) are always stated in Rupas (typically
        single digits, e.g. Sun needs ~5, Saturn ~5), which is also the
        unit the review's own example condition implies
        ("shadbala.jupiter.total > 7" only makes sense as a Rupa-scale
        threshold — 7 raw Shashtiamsas would be a very low value).
        """
        if self._shadbala_engine is None:
            return

        totals: dict[str, float] = {p: 0.0 for p in _CLASSICAL_SEVEN}

        for result in self._shadbala_engine.compute_phase1_components(chart).values():
            for r in result:
                totals[r.planet] += r.value_shashtiamsas
        for result in self._shadbala_engine.compute_phase2_components(chart).values():
            for r in result:
                totals[r.planet] += r.value_shashtiamsas
        for result in self._shadbala_engine.compute_sthana_bala_components(chart).values():
            for r in result:
                totals[r.planet] += r.value_shashtiamsas

        _SHASHTIAMSAS_PER_RUPA = 60.0
        for planet, total_shashtiamsas in totals.items():
            rupas = total_shashtiamsas / _SHASHTIAMSAS_PER_RUPA
            registry.add_fact(Fact(f"shadbala.{planet}.total", round(rupas, 4), "shadbala_engine"))

    def _build_ashtakavarga_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        for result in self._ashtakavarga_engine.compute_bhinnashtakavarga(chart):
            planet_position = next(p for p in chart.planets if p.planet == result.target_planet)
            bindus = result.bindus_in_rashi(planet_position.rashi)
            registry.add_fact(Fact(f"ashtakavarga.{result.target_planet}.bindu", bindus, "ashtakavarga_engine"))

    def _build_transit_facts(
        self, chart: D1Chart, transit_datetime_utc: datetime, registry: FactRegistry
    ) -> None:
        if self._transit_engine is None:
            return
        for result in self._transit_engine.compute_transit(chart, transit_datetime_utc):
            registry.add_fact(Fact(f"transit.{result.planet}.house", result.house_from_natal_moon, "transit_engine"))
            registry.add_fact(Fact(f"transit.{result.planet}.rashi", result.transit_rashi, "transit_engine"))
            if result.planet == "saturn":
                registry.add_fact(Fact("transit.saturn.sade_sati", result.is_sade_sati, "transit_engine"))
                registry.add_fact(Fact("transit.saturn.ashtama_shani", result.is_ashtama_shani, "transit_engine"))

    def build_facts(
        self,
        chart: D1Chart,
        transit_datetime_utc: datetime | None = None,
    ) -> FactRegistry:
        """
        Builds every fact computable from what this FactBuilder was
        wired with. Shadbala facts are skipped entirely if no
        ShadbalaEngine was provided; Transit facts are skipped if no
        TransitEngine AND transit_datetime_utc were both provided —
        never a partial/broken fact, just an absent one.
        """
        registry = FactRegistry()

        self._build_planet_facts(chart, registry)
        self._build_house_facts(chart, registry)
        self._build_yoga_facts(chart, registry)
        self._build_shadbala_facts(chart, registry)
        self._build_ashtakavarga_facts(chart, registry)
        if transit_datetime_utc is not None:
            self._build_transit_facts(chart, transit_datetime_utc, registry)

        return registry
