"""
AstroOS — Fact Builder (Module 13, Phase B — Expanded)

The ONLY place in the Rule Engine pipeline that calls astrology
calculation engines. Translates their outputs into standardized Facts.
RuleEngine itself never touches an engine directly — this is the
boundary.

Expanded Scope:
- Core: planet.*, house.*, yoga.*, shadbala.*, ashtakavarga.*, transit.*, dasha.*, varga.*
- Canonical Extensions:
  - maraka.*, badhaka.* (BadhakaMarakaEngine)
  - aspect.* (AspectEngine)
  - friendship.* (Natural, Tatkalika, and Panchadha Maitri)
  - functional.* (FunctionalLordshipEngine — Parashari BPHS Ch. 19 & Yogakaraka)
  - guna.* (Nakshatra Guna mapping)
  - transit.*.gati (exact classical speed state string from gati_classifier)
  - vedha.* (Gochara/Rashi & Nakshatra Vedha)
  - sbc.* (Sarvatobhadra Chakra 28-nakshatra positions & active vedha rays)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from apps.api.domain.dasha import DashaTree
from apps.api.domain.divisional import VargaChart
from apps.api.domain.facts import Fact
from apps.api.domain.horoscope import D1Chart
from apps.api.services.aspect_engine import AspectEngine
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.badhaka_maraka_engine import BadhakaMarakaEngine
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.functional_lordship_engine import FunctionalLordshipEngine
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.house_engine import HouseEngine
from apps.api.services.nakshatra_vedha_calculator import NakshatraVedhaCalculator
from apps.api.services.sbc_report_service import SBCReportService
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.vedha_calculator import VedhaCalculator
from apps.api.services.yoga_engine import YogaEngine
from packages.shared.enums import Rashi
from packages.shared.rashi_offset import house_offset
from packages.shared.tatkalika_friendship import compute_combined_friendship

_RASHI_INDEX = {r.value: i for i, r in enumerate(Rashi)}

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_ALL_NINE = _CLASSICAL_SEVEN + ["rahu", "ketu"]

NAKSHATRA_GUNA: dict[str, str] = {
    "ashvini": "sattvic",
    "ashwini": "sattvic",
    "bharani": "rajasic",
    "krittika": "rajasic-tamasic",
    "rohini": "sattvic",
    "mrigashira": "rajasic",
    "ardra": "tamasic",
    "punarvasu": "sattvic",
    "pushya": "sattvic",
    "ashlesha": "tamasic",
    "magha": "rajasic",
    "purva_phalguni": "rajasic",
    "purvaphalguni": "rajasic",
    "uttara_phalguni": "tamasic",
    "uttaraphalguni": "tamasic",
    "hasta": "sattvic",
    "chitra": "rajasic",
    "swati": "rajasic",
    "vishakha": "rajasic",
    "anuradha": "sattvic",
    "jyeshtha": "tamasic",
    "mula": "tamasic",
    "moola": "tamasic",
    "purva_ashadha": "rajasic",
    "purvashadha": "rajasic",
    "uttara_ashadha": "rajasic",
    "uttarashadha": "rajasic",
    "abhijit": "sattvic",
    "shravana": "sattvic",
    "dhanishtha": "rajasic",
    "dhanishta": "rajasic",
    "shatabhisha": "rajasic",
    "purva_bhadrapada": "rajasic",
    "purvabhadrapada": "rajasic",
    "uttara_bhadrapada": "tamasic",
    "uttarabhadrapada": "tamasic",
    "revati": "sattvic",
}


class FactBuilder:
    """
    Translates output from canonical calculation engines into standardized Facts.
    All engines are optional at construction except core stateless engines.
    """

    def __init__(
        self,
        graha_engine: GrahaEngine | None = None,
        house_engine: HouseEngine | None = None,
        yoga_engine: YogaEngine | None = None,
        shadbala_engine: ShadbalaEngine | None = None,
        ashtakavarga_engine: AshtakavargaEngine | None = None,
        transit_engine: TransitEngine | None = None,
        badhaka_maraka_engine: BadhakaMarakaEngine | None = None,
        aspect_engine: AspectEngine | None = None,
        functional_lordship_engine: FunctionalLordshipEngine | None = None,
        vedha_calculator: VedhaCalculator | None = None,
        nakshatra_vedha_calculator: NakshatraVedhaCalculator | None = None,
        sbc_report_service: SBCReportService | None = None,
    ) -> None:
        self._graha_engine = graha_engine or GrahaEngine()
        self._house_engine = house_engine or HouseEngine()
        self._yoga_engine = yoga_engine or YogaEngine()
        self._shadbala_engine = shadbala_engine
        self._ashtakavarga_engine = ashtakavarga_engine or AshtakavargaEngine()
        self._transit_engine = transit_engine
        self._badhaka_maraka_engine = badhaka_maraka_engine or BadhakaMarakaEngine()
        self._aspect_engine = aspect_engine or AspectEngine()
        self._functional_lordship_engine = (
            functional_lordship_engine or FunctionalLordshipEngine()
        )
        self._vedha_calculator = vedha_calculator or VedhaCalculator()
        self._nakshatra_vedha_calculator = (
            nakshatra_vedha_calculator or NakshatraVedhaCalculator()
        )
        self._sbc_report_service = sbc_report_service

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

    def _build_maraka_badhaka_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        bm = self._badhaka_maraka_engine.compute(chart)
        registry.add_fact(Fact("badhaka.house", bm.badhaka_house, "badhaka_maraka_engine"))
        registry.add_fact(Fact("badhaka.lord", bm.badhaka_lord, "badhaka_maraka_engine"))
        registry.add_fact(Fact("maraka.house_2", bm.maraka_signs[0], "badhaka_maraka_engine"))
        registry.add_fact(Fact("maraka.house_7", bm.maraka_signs[1], "badhaka_maraka_engine"))
        for planet in _ALL_NINE:
            registry.add_fact(Fact(
                f"maraka.lord.{planet}",
                planet in bm.maraka_lords,
                "badhaka_maraka_engine",
            ))

    def _build_aspect_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        aspects = self._aspect_engine.compute(chart.planets)
        for aspect in aspects:
            registry.add_fact(Fact(
                f"aspect.{aspect.from_planet}.{aspect.to_planet}.present",
                True,
                "aspect_engine",
            ))
            registry.add_fact(Fact(
                f"aspect.{aspect.from_planet}.{aspect.to_planet}.type",
                aspect.aspect_type,
                "aspect_engine",
            ))

    def _build_friendship_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        planet_rashis = {p.planet: p.rashi for p in chart.planets}
        for p1 in _CLASSICAL_SEVEN:
            r1 = planet_rashis.get(p1)
            if not r1:
                continue
            for p2 in _CLASSICAL_SEVEN:
                if p1 == p2:
                    continue
                r2 = planet_rashis.get(p2)
                if not r2:
                    continue
                nat, temp, panch = compute_combined_friendship(p1, r1, p2, r2)
                registry.add_fact(Fact(f"friendship.natural.{p1}.{p2}", nat, "friendship"))
                registry.add_fact(Fact(f"friendship.temporary.{p1}.{p2}", temp, "friendship"))
                registry.add_fact(Fact(f"friendship.panchadha.{p1}.{p2}", panch, "friendship"))

    def _build_functional_lordship_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        res = self._functional_lordship_engine.compute(chart)
        for planet, p_res in res.planets.items():
            registry.add_fact(Fact(
                f"functional.{planet}.lordship",
                p_res.lordship,
                "functional_lordship_engine",
            ))
            registry.add_fact(Fact(
                f"functional.{planet}.yogakaraka",
                p_res.is_yogakaraka,
                "functional_lordship_engine",
            ))

    def _build_guna_facts(self, chart: D1Chart, registry: FactRegistry) -> None:
        for p in chart.planets:
            nak = p.nakshatra.lower() if p.nakshatra else ""
            if nak in NAKSHATRA_GUNA:
                registry.add_fact(Fact(f"guna.nakshatra.{nak}", NAKSHATRA_GUNA[nak], "nakshatra"))

    def _build_transit_facts(
        self, chart: D1Chart, transit_datetime_utc: datetime, registry: FactRegistry
    ) -> None:
        if self._transit_engine is None:
            return
        venus_rashi = next(
            (p.rashi for p in chart.planets if p.planet == "venus"), None
        )
        venus_index = _RASHI_INDEX.get(venus_rashi) if venus_rashi else None
        transit_results = self._transit_engine.compute_transit(chart, transit_datetime_utc)
        for result in transit_results:
            registry.add_fact(Fact(f"transit.{result.planet}.house", result.house_from_natal_moon, "transit_engine"))
            registry.add_fact(Fact(f"transit.{result.planet}.rashi", result.transit_rashi, "transit_engine"))
            registry.add_fact(Fact(f"transit.{result.planet}.retrograde", result.is_retrograde, "transit_engine"))
            registry.add_fact(Fact(f"transit.{result.planet}.gati", result.gati, "transit_engine"))

            if venus_index is not None and result.transit_rashi in _RASHI_INDEX:
                registry.add_fact(Fact(
                    f"transit.{result.planet}.house_from_venus",
                    house_offset(venus_index, _RASHI_INDEX[result.transit_rashi]),
                    "fact_builder",
                ))
            if result.planet == "saturn":
                registry.add_fact(Fact("transit.saturn.sade_sati", result.is_sade_sati, "transit_engine"))
                registry.add_fact(Fact("transit.saturn.ashtama_shani", result.is_ashtama_shani, "transit_engine"))

            # Vedha facts
            if result.has_vedha and result.vedha_planet:
                registry.add_fact(Fact(f"vedha.{result.planet}.{result.vedha_planet}.active", True, "vedha_calculator"))
                registry.add_fact(Fact(f"vedha.{result.planet}.{result.vedha_planet}.type", "rashi_vedha", "vedha_calculator"))
            elif result.has_vipreet_vedha and result.vedha_planet:
                registry.add_fact(Fact(f"vedha.{result.planet}.{result.vedha_planet}.active", True, "vedha_calculator"))
                registry.add_fact(Fact(f"vedha.{result.planet}.{result.vedha_planet}.type", "vipreet_vedha", "vedha_calculator"))

            if result.has_nakshatra_vedha and result.nakshatra_vedha_planet:
                registry.add_fact(Fact(f"vedha.{result.planet}.{result.nakshatra_vedha_planet}.active", True, "nakshatra_vedha_calculator"))
                registry.add_fact(Fact(
                    f"vedha.{result.planet}.{result.nakshatra_vedha_planet}.type",
                    result.nakshatra_vedha_type or "nakshatra_vedha",
                    "nakshatra_vedha_calculator",
                ))

            # SBC facts
            if result.transit_nakshatra_sbc:
                registry.add_fact(Fact(f"sbc.{result.planet}.position", result.transit_nakshatra_sbc, "sbc"))
                registry.add_fact(Fact(f"sbc.{result.planet}.vedha.active", result.has_nakshatra_vedha, "sbc"))

    def _build_dasha_facts(
        self,
        dasha_tree: DashaTree | None,
        transit_datetime_utc: datetime | None,
        registry: FactRegistry,
    ) -> None:
        """Produce dasha.* facts for the active dasha period."""
        if dasha_tree is None:
            return

        registry.add_fact(Fact(
            "dasha.active_system", dasha_tree.system, "dasha_engine",
        ))
        registry.add_fact(Fact(
            "dasha.trigger_planet", dasha_tree.trigger_planet, "dasha_engine",
        ))

        target = (
            transit_datetime_utc.date()
            if transit_datetime_utc is not None
            else date.today()
        )
        for md in dasha_tree.mahadashas:
            if md.start_date <= target <= md.end_date:
                registry.add_fact(Fact(
                    "dasha.current_lord", md.lord, "dasha_engine",
                ))
                registry.add_fact(Fact(
                    "dasha.current_mahadasha", md.lord, "dasha_engine",
                ))
                for ad in md.sub_periods:
                    if ad.start_date <= target <= ad.end_date:
                        registry.add_fact(Fact(
                            "dasha.antardasha_lord", ad.lord, "dasha_engine",
                        ))
                        break
                break

    def _build_varga_facts(
        self,
        vargas: dict[str, VargaChart] | None,
        registry: FactRegistry,
    ) -> None:
        """Produce varga.* facts: planet's rashi and house in each divisional."""
        if vargas is None:
            return

        for varga_code, varga_chart in vargas.items():
            for pos in varga_chart.planet_positions:
                planet = pos.planet
                registry.add_fact(Fact(
                    f"varga.{planet}.{varga_code}.rashi",
                    pos.varga_rashi, "divisional_engine",
                ))
                registry.add_fact(Fact(
                    f"varga.{planet}.{varga_code}.house",
                    pos.varga_house_number, "divisional_engine",
                ))

    def build_facts(
        self,
        chart: D1Chart,
        transit_datetime_utc: datetime | None = None,
        dasha_tree: DashaTree | None = None,
        vargas: dict[str, VargaChart] | None = None,
    ) -> FactRegistry:
        """
        Builds every fact computable from what this FactBuilder was wired with.
        """
        registry = FactRegistry()

        # Natal chart facts
        self._build_planet_facts(chart, registry)
        self._build_house_facts(chart, registry)
        self._build_yoga_facts(chart, registry)
        self._build_shadbala_facts(chart, registry)
        self._build_ashtakavarga_facts(chart, registry)
        self._build_maraka_badhaka_facts(chart, registry)
        self._build_aspect_facts(chart, registry)
        self._build_friendship_facts(chart, registry)
        self._build_functional_lordship_facts(chart, registry)
        self._build_guna_facts(chart, registry)

        # Time/event-scoped facts
        if transit_datetime_utc is not None:
            self._build_transit_facts(chart, transit_datetime_utc, registry)
        self._build_dasha_facts(dasha_tree, transit_datetime_utc, registry)
        self._build_varga_facts(vargas, registry)

        return registry
