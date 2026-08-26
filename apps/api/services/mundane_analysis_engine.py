"""
AstroOS — Mundane Analysis & National Forecasting Engine
Synthesizes:
  1. Chaitra Shukla Pratipada National Ingress Chart
  2. Planetary Cabinet (Nava Nayakas)
  3. Standalone Mundane Eclipses (Grahanas)
  4. Kurma Chakra Geopolitical & Seismic Sectors
To generate comprehensive national and global forecasts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.mundane import (
    KurmaChakraState,
    MundaneBhavaEvaluation,
    MundaneEclipse,
    MundaneIngressChart,
    NationalForecast,
    PlanetaryCabinet,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.kurma_chakra_engine import KurmaChakraEngine
from apps.api.services.mundane_eclipse_engine import MundaneEclipseEngine
from apps.api.services.mundane_ingress_engine import MundaneIngressEngine
from apps.api.services.planetary_cabinet_engine import PlanetaryCabinetEngine
from apps.api.services.synastry_engine import _RASHI_LORDS, _RASHI_ORDER

_BHAVA_SIGNIFICATIONS = {
    1: "General Well-being, Public Health & National Identity",
    2: "National Treasury, Banking, Revenue & Inflation",
    3: "Communications, Media, Transportation & Neighbors",
    4: "Agriculture, Real Estate, Domestic Peace & Opposition Parties",
    5: "Education, National Stock Exchange & Birth Rates",
    6: "Defense Preparedness, Armed Forces & Public Epidemics",
    7: "Foreign Relations, International Treaties & Geopolitical Conflict",
    8: "National Debt, Mortality Rates & Public Crises",
    9: "Judiciary, Supreme Court, Religion & International Trade",
    10: "Head of State, Prime Minister, Executive Prestige & Governance",
    11: "Parliament, National Revenue & International Allies",
    12: "Secret Enemies, Espionage, External Debt & Institutional Losses",
}

_BENEFICS = {"jupiter", "venus", "mercury", "moon"}


class MundaneAnalysisEngine:
    """
    Orchestrates mundane astrological synthesis across Ingress, Cabinet, Eclipses, and Kurma Chakra.
    """

    def __init__(
        self,
        wrapper: Optional[EphemerisWrapper] = None,
        ingress_engine: Optional[MundaneIngressEngine] = None,
        cabinet_engine: Optional[PlanetaryCabinetEngine] = None,
        eclipse_engine: Optional[MundaneEclipseEngine] = None,
        kurma_engine: Optional[KurmaChakraEngine] = None,
    ) -> None:
        self._wrapper = wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._ingress_engine = ingress_engine or MundaneIngressEngine(self._wrapper)
        self._cabinet_engine = cabinet_engine or PlanetaryCabinetEngine(self._ingress_engine)
        self._eclipse_engine = eclipse_engine or MundaneEclipseEngine(self._wrapper)
        self._kurma_engine = kurma_engine or KurmaChakraEngine(self._wrapper)

    def generate_forecast(
        self,
        country_name: str,
        capital_city: str,
        latitude: float,
        longitude: float,
        year: int,
        ayanamsa: str = "lahiri",
    ) -> NationalForecast:
        # 1. Ingress Chart (Chaitra Shukla Pratipada)
        chaitra_moment = self._ingress_engine.find_chaitra_shukla_pratipada(year, ayanamsa)
        ingress_chart = self._ingress_engine.generate_ingress_chart(
            moment=chaitra_moment,
            country_name=country_name,
            capital_city=capital_city,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )

        # 2. Planetary Cabinet
        cabinet = self._cabinet_engine.calculate_cabinet(year, ayanamsa)

        # 3. Eclipses
        eclipses = self._eclipse_engine.find_eclipses_for_year(year, ayanamsa)

        # 4. Kurma Chakra State at Ingress moment
        kurma_state = self._kurma_engine.evaluate_state(chaitra_moment.timestamp_utc, ayanamsa)

        # 5. Evaluate 12 Mundane Bhavas
        chart = ingress_chart.chart
        asc_rashi = chart.ascendant.rashi.lower() if chart.ascendant else "aries"
        asc_idx = _RASHI_ORDER.index(asc_rashi)

        bhava_evals: list[MundaneBhavaEvaluation] = []

        # Find planet occupants by house
        planets_by_house: dict[int, list[str]] = {h: [] for h in range(1, 13)}
        for p in chart.planets:
            h = p.house_number
            if 1 <= h <= 12:
                planets_by_house[h].append(p.planet.capitalize())

        for h_num in range(1, 13):
            r_idx = (asc_idx + h_num - 1) % 12
            r_name = _RASHI_ORDER[r_idx]
            lord = _RASHI_LORDS.get(r_name, "sun")
            occupants = tuple(planets_by_house.get(h_num, []))

            # Score house
            score = 65.0  # Baseline
            for occ in occupants:
                if occ.lower() in _BENEFICS:
                    score += 15.0
                else:
                    score -= 12.0

            if lord in _BENEFICS:
                score += 10.0

            score = min(100.0, max(10.0, score))

            outlook = (
                f"{'Highly Favorable' if score >= 75 else 'Stable / Constructive' if score >= 55 else 'Stressed / Challenging'} "
                f"conditions for {_BHAVA_SIGNIFICATIONS[h_num].lower()}."
            )

            bhava_evals.append(MundaneBhavaEvaluation(
                house_number=h_num,
                signification=_BHAVA_SIGNIFICATIONS[h_num],
                rashi=r_name.capitalize(),
                lord=lord.capitalize(),
                occupants=occupants,
                strength_score=round(score, 1),
                outlook=outlook,
            ))

        # 6. Aggregate Key Indices
        h_dict = {b.house_number: b.strength_score for b in bhava_evals}

        # Economic Index: House 2 (40%) + House 11 (30%) + House 5 (15%) + Cabinet (15%)
        eco_index = round((h_dict[2] * 0.40) + (h_dict[11] * 0.30) + (h_dict[5] * 0.15) + (cabinet.overall_balance_score * 0.15), 1)

        # Defense & Security Index: House 6 (40%) + House 7 (30%) + House 8 (15%) + Cabinet Senadhipati (15%)
        sen_bonus = 80.0 if cabinet.senadhipati.is_benefic else 50.0
        def_index = round((h_dict[6] * 0.40) + (h_dict[7] * 0.30) + (h_dict[8] * 0.15) + (sen_bonus * 0.15), 1)

        # Political Stability Index: House 10 (45%) + House 1 (30%) + House 4 (15%) + Cabinet Raja (10%)
        raja_bonus = 85.0 if cabinet.raja.is_benefic else 45.0
        pol_index = round((h_dict[10] * 0.45) + (h_dict[1] * 0.30) + (h_dict[4] * 0.15) + (raja_bonus * 0.10), 1)

        # Public Health Index: House 1 (50%) + House 6 (30%) + House 8 (20%)
        health_index = round((h_dict[1] * 0.50) + (h_dict[6] * 0.30) + (h_dict[8] * 0.20), 1)

        exec_summary = (
            f"National Forecast for {country_name} ({capital_city}) — Astrological Year {year}: "
            f"Political Stability Index: {pol_index:.1f}/100, Economic Growth Index: {eco_index:.1f}/100, "
            f"Defense Security Index: {def_index:.1f}/100, Public Health Index: {health_index:.1f}/100. "
            f"Planetary Cabinet King: {cabinet.raja.planet}, Minister: {cabinet.mantri.planet}. "
            f"Active Mundane Eclipses: {len(eclipses)}. Kurma Alert Sectors: {len(kurma_state.highest_risk_directions)}."
        )

        return NationalForecast(
            country_name=country_name,
            capital_city=capital_city,
            year=year,
            chaitra_chart=ingress_chart,
            planetary_cabinet=cabinet,
            active_eclipses=eclipses,
            kurma_state=kurma_state,
            bhava_evaluations=tuple(bhava_evals),
            economic_index=eco_index,
            defense_security_index=def_index,
            political_stability_index=pol_index,
            public_health_index=health_index,
            executive_summary=exec_summary,
        )
