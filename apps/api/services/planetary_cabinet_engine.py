"""
AstroOS — Planetary Cabinet Engine (Nava Nayakas)
Classical Reference: Brihat Samhita (Varahamihira), Bhavishya Phala Bhaskara.
Computes the 9 Cosmic Ministers governing the astrological year based on ingress weekday rulers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.mundane import CabinetMinister, IngressType, PlanetaryCabinet
from apps.api.services.mundane_ingress_engine import MundaneIngressEngine

_NATURAL_BENEFICS = {"jupiter", "venus", "mercury", "moon"}


class PlanetaryCabinetEngine:
    """
    Computes the 9-minister cosmic governance council (Nava Nayakas) for any given year.
    """

    def __init__(self, ingress_engine: Optional[MundaneIngressEngine] = None) -> None:
        self._ingress_engine = ingress_engine or MundaneIngressEngine()

    def calculate_cabinet(self, year: int, ayanamsa: str = "lahiri") -> PlanetaryCabinet:
        # 1. Solve all key ingress moments
        chaitra = self._ingress_engine.find_chaitra_shukla_pratipada(year, ayanamsa)
        mesha = self._ingress_engine.find_solar_ingress(year, 0.0, IngressType.MESHA_SANKRANTI, 4, 14, ayanamsa)
        simha = self._ingress_engine.find_solar_ingress(year, 120.0, IngressType.MESHA_SANKRANTI, 8, 17, ayanamsa)
        karka = self._ingress_engine.find_solar_ingress(year, 90.0, IngressType.KARKA_SANKRANTI, 7, 16, ayanamsa)
        dhanu = self._ingress_engine.find_solar_ingress(year, 240.0, IngressType.MESHA_SANKRANTI, 12, 16, ayanamsa)
        mithuna = self._ingress_engine.find_solar_ingress(year, 60.0, IngressType.MESHA_SANKRANTI, 6, 15, ayanamsa)
        aridra = self._ingress_engine.find_solar_ingress(year, 66.6667, IngressType.ARIDRA_PRAVESHA, 6, 22, ayanamsa)
        tula = self._ingress_engine.find_solar_ingress(year, 180.0, IngressType.TULA_SANKRANTI, 10, 17, ayanamsa)
        makara = self._ingress_engine.find_solar_ingress(year, 270.0, IngressType.MAKARA_SANKRANTI, 1, 14, ayanamsa)

        portfolios_data = [
            ("Raja (King / Head of State)", chaitra.weekday_lord, "Chaitra Shukla Pratipada", "Overall leadership, sovereign governance, and executive decisions."),
            ("Mantri (Prime Minister / Chief Advisor)", mesha.weekday_lord, "Mesha Sankranti", "Administrative policies, cabinet unity, and diplomatic wisdom."),
            ("Senadhipati (Defense & Armed Forces)", simha.weekday_lord, "Simha Sankranti", "National security, border defense, and strategic posture."),
            ("Sasyeshadhipati (Lord of Kharif Agriculture)", karka.weekday_lord, "Karka Sankranti", "Summer monsoon harvests, grain production, and food security."),
            ("Dhanyadhipati (Lord of Rabi Cereals)", dhanu.weekday_lord, "Dhanu Sankranti", "Winter crops, financial reserves, and general prosperity."),
            ("Arghyadhipati (Lord of Finance & Commodities)", mithuna.weekday_lord, "Mithuna Sankranti", "Price stability, trade balance, inflation, and market liquidity."),
            ("Meghadhipati (Lord of Clouds & Monsoon)", aridra.weekday_lord, "Aridra Pravesha", "Monsoon rainfall distribution, water tables, and climate patterns."),
            ("Raseshadhipati (Lord of Liquids & Petroleum)", tula.weekday_lord, "Tula Sankranti", "Petroleum, milk, medicinal chemicals, and fluid resources."),
            ("Nireshadhipati (Lord of Metals & Minerals)", makara.weekday_lord, "Makara Sankranti", "Gold, gems, precious minerals, and heavy industrial metals."),
        ]

        ministers: list[CabinetMinister] = []
        for port, planet, basis, desc in portfolios_data:
            is_ben = planet.lower() in _NATURAL_BENEFICS
            summary = (
                f"{port}: {planet.capitalize()} ({'Auspicious / Benefic' if is_ben else 'Challenging / Malefic'}). "
                f"Governs {desc} Based on {basis} on a {planet.capitalize()} day."
            )
            ministers.append(CabinetMinister(
                portfolio=port,
                planet=planet.capitalize(),
                basis_ingress=basis,
                is_benefic=is_ben,
                impact_summary=summary,
            ))

        raja = ministers[0]
        mantri = ministers[1]
        senadhipati = ministers[2]
        meghadhipati = ministers[6]

        # Scoring: Benefics in portfolio give +10 pts, Benefic King gives +25 pts, Benefic Minister gives +20 pts
        score = 0.0
        for m in ministers:
            if m.is_benefic:
                score += 8.0
        if raja.is_benefic:
            score += 15.0
        if mantri.is_benefic:
            score += 13.0

        score = min(100.0, max(0.0, score))

        if raja.is_benefic and mantri.is_benefic:
            climate = "Highly Auspicious — Harmonious Sovereign & Progressive Administration."
        elif raja.is_benefic and not mantri.is_benefic:
            climate = "Mixed — Benevolent Leadership facing Administrative Friction or Stricter Measures."
        elif not raja.is_benefic and mantri.is_benefic:
            climate = "Reformative — Firm / Aggressive Head of State guided by Wise Counsellors."
        else:
            climate = "Challenging / Volatile — Stringent Governance, Heightened National Security, and Strict Reforms."

        classical_summary = (
            f"Year {year} Planetary Cabinet (Nava Nayakas): King is {raja.planet}, Prime Minister is {mantri.planet}, "
            f"Commander-in-Chief is {senadhipati.planet}, Lord of Monsoon is {meghadhipati.planet}. "
            f"Overall Cosmic Harmony Score: {score:.1f}/100 ({climate}). "
            "Derived from Brihat Samhita (Ch. 19-20) and Bhavishya Phala Bhaskara."
        )

        return PlanetaryCabinet(
            year=year,
            ministers=tuple(ministers),
            raja=raja,
            mantri=mantri,
            senadhipati=senadhipati,
            meghadhipati=meghadhipati,
            overall_balance_score=round(score, 1),
            governance_climate=climate,
            classical_summary=classical_summary,
        )
