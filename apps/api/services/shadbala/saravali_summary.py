"""
AstroOS — Saravali Shadbala Summary & Evaluation Engine

Implements the complete classical evaluation framework according to:
- Kalyana Varma's *Saravali* (Chapter on Shadbala)
- *Brihat Parashara Hora Shastra* (BPHS Chapter 27)
- Maitreya Astrology calculation and evaluation standard

This engine produces CANONICAL SHADBALA FACTS ONLY. All interpretation
(Dasa/Transit effects, auspiciousness ratings) must be performed
DOWNSTREAM by consumers of this engine's output.

Calculates:
1. Six-Fold Aggregate Balas (Sthana, Dig, Kala, Cheshta, Naisargika, Drig) in Virupas and Rupas.
2. Total Shadbala Pinda for the 7 classical planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn).
3. Minimum Total Shadbala Requirements Comparison (Rupas & Virupas) + Strength Ratios.
4. Individual Sub-Bala Requirements Matrix (Sthana, Dig, Kala, Cheshta, Ayana criteria) with Pass/Fail evaluation.
5. Ishta Bala (Benefic strength) & Kashta Bala (Malefic/Difficult strength).

Sub-Bala Breakdown (17 individually tracked sub-components):

  Sthana Bala (5 sub-components):
    1. Uchcha Bala (Exaltation)
    2. Saptavargaja Bala (dignity across 7 Vargas: D1, D2, D3, D7, D9, D12, D30)
    3. Ojayugmarasyamsa Bala (Odd/Even Sign & Navamsa)
    4. Kendradi Bala (Angular/Succedent/Cadent)
    5. Drekkana Bala (Decanate)

  Dig Bala (1 component):
    6. Directional Strength (4 cardinal quadrants)

  Kala Bala (6 sub-components):
    7.  Nathonnata Bala (Diurnal/Nocturnal)
    8.  Paksha Bala (Lunar Phase)
    9.  Tribhaga Bala (Day/Night Portions)
    10. Dina-Hora Bala (Weekday & Planetary Hour lords)
        NOTE: Varsha (year lord) and Masa (month lord) are NOT yet implemented.
        Classical sources group these as Varsha-Masa-Dina-Hora; only Dina & Hora
        are computed. See dina_hora_bala.py for details on the deferral.
    11. Ayana Bala (Declination/Equinoctial)
    12. Yuddha Bala (Planetary War)

  Cheshta Bala (1 component):
    13. Motional Strength (8 classical motion types for Mars–Saturn;
        Sun = Ayana Bala; Moon = Paksha Bala per Saravali rule)

  Naisargika Bala (1 component):
    14. Natural/Inherent Strength (fixed luminosity hierarchy)

  Drig Bala (1 component):
    15. Aspectual Strength (Sputa Drishti rectified: +125% Benefic, -75% Malefic)

  Ishta & Kashta Bala (2 derived):
    16. Ishta Bala = √(Uchcha × Cheshta)
    17. Kashta Bala = √((60 - Uchcha) × (60 - Cheshta))
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

from apps.api.domain.shadbala import BalaComponentResult

# Classical 7 planets in traditional order
CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# 1 Rupa = 60 Virupas (Shashtiamsas)
VIRUPAS_PER_RUPA = 60.0

# Minimum Total Shadbala Requirements (Virupas and Rupas) — BPHS Ch. 27 & Saravali
REQUIRED_SHADBALA_VIRUPAS: dict[str, float] = {
    "sun": 390.0,      # 6.5 Rupas
    "moon": 360.0,     # 6.0 Rupas
    "mars": 300.0,     # 5.0 Rupas
    "mercury": 420.0,  # 7.0 Rupas
    "jupiter": 390.0,  # 6.5 Rupas
    "venus": 330.0,    # 5.5 Rupas
    "saturn": 300.0,   # 5.0 Rupas
}

REQUIRED_SHADBALA_RUPAS: dict[str, float] = {
    p: v / VIRUPAS_PER_RUPA for p, v in REQUIRED_SHADBALA_VIRUPAS.items()
}

# Individual Sub-Bala Requirements in Virupas — Saravali & BPHS Ch. 27
INDIVIDUAL_SUB_BALA_REQUIREMENTS: dict[str, dict[str, float]] = {
    # Sun, Jupiter, Mercury group
    "sun": {"sthana_bala": 165.0, "dig_bala": 35.0, "kala_bala": 50.0, "chesta_bala": 112.0, "ayana_bala": 30.0},
    "jupiter": {"sthana_bala": 165.0, "dig_bala": 35.0, "kala_bala": 50.0, "chesta_bala": 112.0, "ayana_bala": 30.0},
    "mercury": {"sthana_bala": 165.0, "dig_bala": 35.0, "kala_bala": 50.0, "chesta_bala": 112.0, "ayana_bala": 30.0},
    # Moon, Venus group
    "moon": {"sthana_bala": 133.0, "dig_bala": 50.0, "kala_bala": 30.0, "chesta_bala": 100.0, "ayana_bala": 40.0},
    "venus": {"sthana_bala": 133.0, "dig_bala": 50.0, "kala_bala": 30.0, "chesta_bala": 100.0, "ayana_bala": 40.0},
    # Mars, Saturn group
    "mars": {"sthana_bala": 96.0, "dig_bala": 30.0, "kala_bala": 40.0, "chesta_bala": 67.0, "ayana_bala": 20.0},
    "saturn": {"sthana_bala": 96.0, "dig_bala": 30.0, "kala_bala": 40.0, "chesta_bala": 67.0, "ayana_bala": 20.0},
}


@dataclass(frozen=True)
class SubBalaCheck:
    bala_key: str
    bala_name: str
    obtained_virupas: float
    required_virupas: float
    passed: bool


@dataclass(frozen=True)
class SaravaliPlanetSummary:
    planet: str
    planet_display_name: str
    
    # 6 Main Balas in Virupas
    sthana_bala_virupas: float
    dig_bala_virupas: float
    kala_bala_virupas: float
    chesta_bala_virupas: float
    naisargika_bala_virupas: float
    drig_bala_virupas: float
    
    # Detailed Sthana Sub-components
    uchcha_bala_virupas: float
    saptavargaja_bala_virupas: float
    ojayugmarasyamsa_bala_virupas: float
    kendradi_bala_virupas: float
    drekkana_bala_virupas: float
    
    # Detailed Kala Sub-components
    nathonnata_bala_virupas: float
    paksha_bala_virupas: float
    tribhaga_bala_virupas: float
    dina_hora_bala_virupas: float
    ayana_bala_virupas: float
    yuddha_bala_virupas: float
    
    # Total Shadbala Pinda
    total_virupas: float
    total_rupas: float
    required_virupas: float
    required_rupas: float
    strength_ratio: float
    percentage: float
    is_strong: bool
    status_label: str  # "Strong", "Moderate", "Deficient"
    rank: int
    
    # Ishta / Kashta Bala
    ishta_bala_virupas: float
    kashta_bala_virupas: float
    
    # Individual Sub-Bala Criteria checks
    sub_bala_checks: tuple[SubBalaCheck, ...]
    all_sub_balas_passed: bool


@dataclass(frozen=True)
class SaravaliShadbalaReport:
    planets: tuple[SaravaliPlanetSummary, ...]
    strongest_planet: str
    weakest_planet: str
    average_strength_ratio: float
    chart_strength_score: float  # 0 to 100 normalized


class SaravaliShadbalaEvaluator:
    """Evaluates and aggregates all computed Shadbala components into the complete Saravali report."""

    @staticmethod
    def _map_by_planet(items: list[BalaComponentResult]) -> dict[str, float]:
        return {item.planet.lower(): item.value_shashtiamsas for item in items}

    @classmethod
    def evaluate(
        cls,
        *,
        naisargika: list[BalaComponentResult],
        dig: list[BalaComponentResult],
        drik: list[BalaComponentResult],
        chesta: list[BalaComponentResult],
        paksha: list[BalaComponentResult],
        ayana: list[BalaComponentResult],
        yuddha: list[BalaComponentResult],
        uchcha: list[BalaComponentResult],
        kendradi: list[BalaComponentResult],
        drekkana: list[BalaComponentResult],
        saptavargaja: list[BalaComponentResult],
        ojayugmarasyamsa: list[BalaComponentResult],
        tribhaga: list[BalaComponentResult],
        nathonnata: list[BalaComponentResult],
        dina_hora: list[BalaComponentResult],
        ishta: list[BalaComponentResult] | None = None,
        kashta: list[BalaComponentResult] | None = None,
    ) -> SaravaliShadbalaReport:
        # Build lookup dicts
        m_naisargika = cls._map_by_planet(naisargika)
        m_dig = cls._map_by_planet(dig)
        m_drik = cls._map_by_planet(drik)
        m_chesta = cls._map_by_planet(chesta)
        m_paksha = cls._map_by_planet(paksha)
        m_ayana = cls._map_by_planet(ayana)
        m_yuddha = cls._map_by_planet(yuddha)
        m_uchcha = cls._map_by_planet(uchcha)
        m_kendradi = cls._map_by_planet(kendradi)
        m_drekkana = cls._map_by_planet(drekkana)
        m_saptavargaja = cls._map_by_planet(saptavargaja)
        m_ojayugmarasyamsa = cls._map_by_planet(ojayugmarasyamsa)
        m_tribhaga = cls._map_by_planet(tribhaga)
        m_nathonnata = cls._map_by_planet(nathonnata)
        m_dina_hora = cls._map_by_planet(dina_hora)
        m_ishta = cls._map_by_planet(ishta or [])
        m_kashta = cls._map_by_planet(kashta or [])

        summaries: list[dict[str, Any]] = []

        for p in CLASSICAL_SEVEN:
            p_cap = p.capitalize()
            # 1. Sthana Bala sub-components
            v_uchcha = m_uchcha.get(p, 0.0)
            v_saptavargaja = m_saptavargaja.get(p, 0.0)
            v_ojayugmarasyamsa = m_ojayugmarasyamsa.get(p, 0.0)
            v_kendradi = m_kendradi.get(p, 0.0)
            v_drekkana = m_drekkana.get(p, 0.0)
            sthana_total = v_uchcha + v_saptavargaja + v_ojayugmarasyamsa + v_kendradi + v_drekkana

            # 2. Dig Bala
            v_dig = m_dig.get(p, 0.0)

            # 3. Kala Bala sub-components
            v_nathonnata = m_nathonnata.get(p, 0.0)
            v_paksha = m_paksha.get(p, 0.0)
            v_tribhaga = m_tribhaga.get(p, 0.0)
            v_dina_hora = m_dina_hora.get(p, 0.0)
            v_ayana = m_ayana.get(p, 0.0)
            v_yuddha = m_yuddha.get(p, 0.0)
            kala_total = v_nathonnata + v_paksha + v_tribhaga + v_dina_hora + v_ayana + v_yuddha

            # 4. Cheshta Bala (Saravali rule: Sun = Ayana Bala, Moon = Paksha Bala)
            if p == "sun":
                v_chesta = v_ayana
            elif p == "moon":
                v_chesta = v_paksha
            else:
                v_chesta = m_chesta.get(p, 0.0)

            # 5. Naisargika Bala
            v_naisargika = m_naisargika.get(p, 0.0)

            # 6. Drig Bala
            v_drik = m_drik.get(p, 0.0)

            # Total Shadbala Pinda in Virupas & Rupas
            total_virupas = sthana_total + v_dig + kala_total + v_chesta + v_naisargika + v_drik
            total_rupas = total_virupas / VIRUPAS_PER_RUPA

            req_virupas = REQUIRED_SHADBALA_VIRUPAS.get(p, 300.0)
            req_rupas = REQUIRED_SHADBALA_RUPAS.get(p, 5.0)
            ratio = total_virupas / req_virupas if req_virupas > 0 else 1.0
            percentage = round(ratio * 100.0, 2)
            is_strong = total_virupas >= req_virupas

            if ratio >= 1.15:
                status_label = "Strong"
            elif ratio >= 0.95:
                status_label = "Moderate"
            else:
                status_label = "Deficient"

            # Ishta and Kashta Bala
            if p in m_ishta and p in m_kashta:
                v_ishta = m_ishta[p]
                v_kashta = m_kashta[p]
            else:
                # Calculate classical Ishta/Kashta: sqrt(uchcha * chesta), sqrt((60-uchcha)*(60-chesta))
                u = max(0.0, min(60.0, v_uchcha))
                c = max(0.0, min(60.0, v_chesta))
                v_ishta = round(math.sqrt(u * c), 4)
                v_kashta = round(math.sqrt((60.0 - u) * (60.0 - c)), 4)

            # Individual Sub-Bala Criteria Checks
            sub_reqs = INDIVIDUAL_SUB_BALA_REQUIREMENTS.get(p, {})
            checks: list[SubBalaCheck] = []
            
            # Sthana Check
            s_req = sub_reqs.get("sthana_bala", 0.0)
            checks.append(SubBalaCheck("sthana_bala", "Sthana Bala", round(sthana_total, 2), s_req, sthana_total >= s_req))
            
            # Dig Check
            d_req = sub_reqs.get("dig_bala", 0.0)
            checks.append(SubBalaCheck("dig_bala", "Dig Bala", round(v_dig, 2), d_req, v_dig >= d_req))
            
            # Kala Check
            k_req = sub_reqs.get("kala_bala", 0.0)
            checks.append(SubBalaCheck("kala_bala", "Kala Bala", round(kala_total, 2), k_req, kala_total >= k_req))
            
            # Cheshta Check
            c_req = sub_reqs.get("chesta_bala", 0.0)
            checks.append(SubBalaCheck("chesta_bala", "Cheshta Bala", round(v_chesta, 2), c_req, v_chesta >= c_req))
            
            # Ayana Check
            a_req = sub_reqs.get("ayana_bala", 0.0)
            checks.append(SubBalaCheck("ayana_bala", "Ayana Bala", round(v_ayana, 2), a_req, v_ayana >= a_req))

            all_sub_passed = all(c.passed for c in checks)

            summaries.append({
                "planet": p,
                "planet_display_name": p_cap,
                "sthana_bala_virupas": round(sthana_total, 4),
                "dig_bala_virupas": round(v_dig, 4),
                "kala_bala_virupas": round(kala_total, 4),
                "chesta_bala_virupas": round(v_chesta, 4),
                "naisargika_bala_virupas": round(v_naisargika, 4),
                "drig_bala_virupas": round(v_drik, 4),
                "uchcha_bala_virupas": round(v_uchcha, 4),
                "saptavargaja_bala_virupas": round(v_saptavargaja, 4),
                "ojayugmarasyamsa_bala_virupas": round(v_ojayugmarasyamsa, 4),
                "kendradi_bala_virupas": round(v_kendradi, 4),
                "drekkana_bala_virupas": round(v_drekkana, 4),
                "nathonnata_bala_virupas": round(v_nathonnata, 4),
                "paksha_bala_virupas": round(v_paksha, 4),
                "tribhaga_bala_virupas": round(v_tribhaga, 4),
                "dina_hora_bala_virupas": round(v_dina_hora, 4),
                "ayana_bala_virupas": round(v_ayana, 4),
                "yuddha_bala_virupas": round(v_yuddha, 4),
                "total_virupas": round(total_virupas, 4),
                "total_rupas": round(total_rupas, 4),
                "required_virupas": req_virupas,
                "required_rupas": req_rupas,
                "strength_ratio": round(ratio, 4),
                "percentage": percentage,
                "is_strong": is_strong,
                "status_label": status_label,
                "ishta_bala_virupas": v_ishta,
                "kashta_bala_virupas": v_kashta,
                "sub_bala_checks": tuple(checks),
                "all_sub_balas_passed": all_sub_passed,
            })

        # Rank planets by total_virupas descending
        summaries.sort(key=lambda s: s["total_virupas"], reverse=True)
        for idx, s in enumerate(summaries, 1):
            s["rank"] = idx

        planet_summaries = [
            SaravaliPlanetSummary(
                planet=s["planet"],
                planet_display_name=s["planet_display_name"],
                sthana_bala_virupas=s["sthana_bala_virupas"],
                dig_bala_virupas=s["dig_bala_virupas"],
                kala_bala_virupas=s["kala_bala_virupas"],
                chesta_bala_virupas=s["chesta_bala_virupas"],
                naisargika_bala_virupas=s["naisargika_bala_virupas"],
                drig_bala_virupas=s["drig_bala_virupas"],
                uchcha_bala_virupas=s["uchcha_bala_virupas"],
                saptavargaja_bala_virupas=s["saptavargaja_bala_virupas"],
                ojayugmarasyamsa_bala_virupas=s["ojayugmarasyamsa_bala_virupas"],
                kendradi_bala_virupas=s["kendradi_bala_virupas"],
                drekkana_bala_virupas=s["drekkana_bala_virupas"],
                nathonnata_bala_virupas=s["nathonnata_bala_virupas"],
                paksha_bala_virupas=s["paksha_bala_virupas"],
                tribhaga_bala_virupas=s["tribhaga_bala_virupas"],
                dina_hora_bala_virupas=s["dina_hora_bala_virupas"],
                ayana_bala_virupas=s["ayana_bala_virupas"],
                yuddha_bala_virupas=s["yuddha_bala_virupas"],
                total_virupas=s["total_virupas"],
                total_rupas=s["total_rupas"],
                required_virupas=s["required_virupas"],
                required_rupas=s["required_rupas"],
                strength_ratio=s["strength_ratio"],
                percentage=s["percentage"],
                is_strong=s["is_strong"],
                status_label=s["status_label"],
                rank=s["rank"],
                ishta_bala_virupas=s["ishta_bala_virupas"],
                kashta_bala_virupas=s["kashta_bala_virupas"],
                sub_bala_checks=s["sub_bala_checks"],
                all_sub_balas_passed=s["all_sub_balas_passed"],
            )
            for s in summaries
        ]

        strongest = planet_summaries[0].planet_display_name if planet_summaries else "—"
        weakest = planet_summaries[-1].planet_display_name if planet_summaries else "—"
        avg_ratio = (
            sum(p.strength_ratio for p in planet_summaries) / len(planet_summaries)
            if planet_summaries
            else 1.0
        )
        # Normalized score: avg ratio clamped at 2.0 -> 0-100
        chart_score = round(min(100.0, (avg_ratio / 1.5) * 100.0), 1)

        return SaravaliShadbalaReport(
            planets=tuple(planet_summaries),
            strongest_planet=strongest,
            weakest_planet=weakest,
            average_strength_ratio=round(avg_ratio, 4),
            chart_strength_score=chart_score,
        )
