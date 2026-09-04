"""
AstroOS — Canonical Drishti Engine
===================================
Source: Vinay Jha's Canonical Methodology (bhaavachalita.md, strength-of-a-house.md,
prediction-of-death.md, and Phalit.kkk A45_ShodashDrishti, frmDrishti).

Implements:
  1. Sphuta Drishti (0 to 60 Virupas / 100% scale) via Parashari piecewise trigonometry.
  2. Maitri Filtering: Benefic traits transferred to Friends, Malefic traits to Enemies.
  3. Sambandha Amplification: Aspects amplified when aspecting planet is in sambandha.
  4. Bhavesha 50% Baseline Law: Lord's baseline influence is at least 30 virupas (50%)
     even when direct aspect is zero, per Jha's empirical finding from rainfall data.
  5. Divisional Drishti: Computes aspects across D-1, D-9, D-10, D-30 charts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.canonical_aspect import (
    BhaveshaDrishti,
    DrishtiConfig,
    DrishtiNature,
    SphutaDrishti,
    VargaDrishtiMatrix,
)
from packages.shared.constants import SIGN_LORDS
from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Natural Friendship tables (Naisargika Maitri)
_NAISARGIKA_FRIENDS: dict[str, set[str]] = {
    "sun": {"moon", "mars", "jupiter"},
    "moon": {"sun", "mercury"},
    "mars": {"sun", "moon", "jupiter"},
    "mercury": {"sun", "venus"},
    "jupiter": {"sun", "moon", "mars"},
    "venus": {"mercury", "saturn"},
    "saturn": {"mercury", "venus"},
}

_NAISARGIKA_ENEMIES: dict[str, set[str]] = {
    "sun": {"venus", "saturn"},
    "moon": set(),
    "mars": {"mercury"},
    "mercury": {"moon"},
    "jupiter": {"mercury", "venus"},
    "venus": {"sun", "moon"},
    "saturn": {"sun", "moon", "mars"},
}


def _calculate_piecewise_virupas(angle: float, aspecting_planet: str) -> Tuple[float, str, bool]:
    """
    Piecewise continuous Sphuta Drishti formula (BPHS / Jha).
    Returns: (virupas, aspect_type, is_special)
    """
    theta = angle % 360.0
    val = 0.0
    aspect_type = "partial"
    is_special = False

    if 0.0 <= theta < 30.0:
        val = 0.0
    elif 30.0 <= theta < 60.0:
        val = 0.5 * (theta - 30.0)
    elif 60.0 <= theta < 90.0:
        val = (theta - 60.0) + 15.0
        if aspecting_planet == "saturn":
            val += 45.0
            is_special = True
            aspect_type = "saturn_3rd_special"
    elif 90.0 <= theta < 120.0:
        val = 0.5 * (120.0 - theta) + 30.0
        if aspecting_planet == "mars":
            val += 15.0
            is_special = True
            aspect_type = "mars_4th_special"
    elif 120.0 <= theta < 150.0:
        val = 150.0 - theta
        if aspecting_planet == "jupiter":
            val += 30.0
            is_special = True
            aspect_type = "jupiter_5th_special"
    elif 150.0 <= theta < 180.0:
        val = 2.0 * (theta - 150.0)
        aspect_type = "universal_7th"
    elif 180.0 <= theta < 300.0:
        val = 0.5 * (300.0 - theta)
        if aspecting_planet == "mars" and 210.0 <= theta < 240.0:
            val += 15.0
            is_special = True
            aspect_type = "mars_8th_special"
        elif aspecting_planet == "jupiter" and 240.0 <= theta < 270.0:
            val += 30.0
            is_special = True
            aspect_type = "jupiter_9th_special"
        elif aspecting_planet == "saturn" and 270.0 <= theta < 300.0:
            val += 45.0
            is_special = True
            aspect_type = "saturn_10th_special"
        elif 180.0 <= theta < 190.0:
            aspect_type = "universal_7th"
    else:
        val = 0.0

    virupas = min(max(val, 0.0), 60.0)
    return virupas, aspect_type, is_special


class CanonicalDrishtiEngine:
    """Calculates Sphuta Drishti, Bhavesha Protection, and Maitri-filtered aspects."""

    def __init__(self, config: DrishtiConfig | None = None) -> None:
        self._config = config or DrishtiConfig()

    def calculate_panchadha_maitri(
        self,
        p1: str,
        p2: str,
        planet_rashis: dict[str, str],
    ) -> str:
        """Panchadha Maitri: Naisargika + Tatkalika synthesis."""
        p1_l = p1.lower()
        p2_l = p2.lower()
        if p1_l == p2_l:
            return "svakshetra"

        # 1. Naisargika (Natural) score: Friend (+1), Enemy (-1), Neutral (0)
        if p2_l in _NAISARGIKA_FRIENDS.get(p1_l, set()):
            n_score = 1
        elif p2_l in _NAISARGIKA_ENEMIES.get(p1_l, set()):
            n_score = -1
        else:
            n_score = 0

        # 2. Tatkalika (Temporal) score: 2,3,4,10,11,12 (+1), 1,5,6,7,8,9 (-1)
        r1 = planet_rashis.get(p1_l)
        r2 = planet_rashis.get(p2_l)
        if r1 and r2 and r1.lower() in _RASHI_LIST and r2.lower() in _RASHI_LIST:
            idx1 = _RASHI_LIST.index(r1.lower())
            idx2 = _RASHI_LIST.index(r2.lower())
            diff = (idx2 - idx1) % 12 + 1
            t_score = 1 if diff in (2, 3, 4, 10, 11, 12) else -1
        else:
            t_score = 0

        net = n_score + t_score
        if net == 2:
            return "adhimitra"
        elif net == 1:
            return "mitra"
        elif net == 0:
            return "sama"
        elif net == -1:
            return "shatru"
        else:
            return "adhishatru"

    def compute_sphuta_drishti_between(
        self,
        from_planet: str,
        to_planet: str,
        from_longitude: float,
        to_longitude: float,
        planet_rashis: dict[str, str],
        is_sambandha: bool = False,
    ) -> SphutaDrishti:
        """Computes exact continuous aspect between two planetary positions."""
        cfg = self._config
        angle = (to_longitude - from_longitude) % 360.0
        virupas, aspect_type, is_special = _calculate_piecewise_virupas(angle, from_planet.lower())
        percentage = (virupas / 60.0) * 100.0

        # Panchadha Maitri & Maitri Filtering
        maitri = self.calculate_panchadha_maitri(from_planet, to_planet, planet_rashis)

        if cfg.enable_maitri_filtering:
            if maitri in ("adhimitra", "mitra"):
                nature = DrishtiNature.BENEFIC_TRANSFER
            elif maitri in ("adhishatru", "shatru"):
                nature = DrishtiNature.MALEFIC_TRANSFER
            else:
                nature = DrishtiNature.NEUTRAL_TRANSFER
        else:
            nature = DrishtiNature.BENEFIC_TRANSFER if virupas > 0 else DrishtiNature.NEUTRAL_TRANSFER

        # Sambandha Amplification
        eff_virupas = virupas
        if cfg.enable_sambandha_amplification and is_sambandha:
            eff_virupas = min(virupas * cfg.sambandha_amplification_factor, 60.0)

        return SphutaDrishti(
            from_planet=from_planet.lower(),
            to_planet=to_planet.lower(),
            angle_deg=round(angle, 4),
            virupas=round(virupas, 4),
            percentage=round(percentage, 2),
            aspect_type=aspect_type,
            is_special=is_special,
            panchadha_relation=maitri,
            transferred_nature=nature,
            is_sambandha_amplified=is_sambandha,
            effective_virupas=round(eff_virupas, 4),
        )

    def compute_all_sphuta_aspects(
        self,
        planet_longitudes: dict[str, float],
        sambandha_pairs: set[tuple[str, str]] | None = None,
    ) -> list[SphutaDrishti]:
        """Computes pairwise Sphuta Drishti among all classical 7 planets."""
        planet_rashis = {
            p: _RASHI_LIST[int(lon // 30.0) % 12]
            for p, lon in planet_longitudes.items()
        }
        sambandha = sambandha_pairs or set()
        results: list[SphutaDrishti] = []

        for p1 in _CLASSICAL_SEVEN:
            if p1 not in planet_longitudes:
                continue
            lon1 = planet_longitudes[p1]
            for p2 in _CLASSICAL_SEVEN:
                if p1 == p2 or p2 not in planet_longitudes:
                    continue
                lon2 = planet_longitudes[p2]
                has_sambandha = (p1, p2) in sambandha or (p2, p1) in sambandha
                aspect = self.compute_sphuta_drishti_between(
                    from_planet=p1,
                    to_planet=p2,
                    from_longitude=lon1,
                    to_longitude=lon2,
                    planet_rashis=planet_rashis,
                    is_sambandha=has_sambandha,
                )
                if aspect.virupas > 0.0:
                    results.append(aspect)

        return results

    def compute_bhavesha_drishti_protection(
        self,
        lagna_rashi: str,
        planet_longitudes: dict[str, float],
        house_midpoints: dict[int, float] | None = None,
    ) -> dict[int, BhaveshaDrishti]:
        """
        Applies Jha's 50% Baseline Law for Bhavesha Drishti:
        Lord protects its own house 100% when aspecting. If direct aspect is 0,
        it maintains an empirical 50% baseline presence (30 virupas).
        """
        cfg = self._config
        lagna_idx = _RASHI_LIST.index(lagna_rashi.lower())
        results: dict[int, BhaveshaDrishti] = {}

        for h in range(1, 13):
            r_idx = (lagna_idx + h - 1) % 12
            r_name = _RASHI_LIST[r_idx]
            lord = SIGN_LORDS[r_name]

            # House midpoint
            if house_midpoints and h in house_midpoints:
                h_lon = house_midpoints[h]
            else:
                h_lon = (r_idx * 30.0 + 15.0) % 360.0

            lord_lon = planet_longitudes.get(lord)
            if lord_lon is None:
                direct_virupas = 0.0
            else:
                angle = (h_lon - lord_lon) % 360.0
                direct_virupas, _, _ = _calculate_piecewise_virupas(angle, lord)

            # Apply 50% baseline law
            if direct_virupas > 0.0:
                eff_protection = max(direct_virupas, cfg.bhavesha_baseline_virupas if cfg.enable_bhavesha_50_percent_baseline else 0.0)
                is_baseline = direct_virupas < cfg.bhavesha_baseline_virupas and cfg.enable_bhavesha_50_percent_baseline
                trace = f"{lord.capitalize()} directly aspects {h}H ({r_name.capitalize()}) with {direct_virupas:.2f} virupas."
            else:
                if cfg.enable_bhavesha_50_percent_baseline:
                    eff_protection = cfg.bhavesha_baseline_virupas
                    is_baseline = True
                    trace = f"{lord.capitalize()} has 0 direct aspect on {h}H -> Jha 50% baseline applied ({cfg.bhavesha_baseline_virupas:.1f} virupas)."
                else:
                    eff_protection = 0.0
                    is_baseline = False
                    trace = f"{lord.capitalize()} has 0 direct aspect on {h}H."

            results[h] = BhaveshaDrishti(
                house_number=h,
                rashi=r_name,
                lord=lord,
                direct_aspect_virupas=round(direct_virupas, 4),
                is_50_percent_baseline_active=is_baseline,
                effective_protection_virupas=round(eff_protection, 4),
                trace=trace,
            )

        return results

    def compute_varga_drishti(
        self,
        varga_name: str,
        varga_longitudes: dict[str, float],
    ) -> VargaDrishtiMatrix:
        """Computes Shodasha Varga Drishti for any divisional chart (D1, D9, D10, D30)."""
        aspects = self.compute_all_sphuta_aspects(varga_longitudes)
        benefic_v = sum(a.effective_virupas for a in aspects if a.transferred_nature == DrishtiNature.BENEFIC_TRANSFER)
        malefic_v = sum(a.effective_virupas for a in aspects if a.transferred_nature == DrishtiNature.MALEFIC_TRANSFER)

        return VargaDrishtiMatrix(
            varga_name=varga_name,
            sphuta_aspects=aspects,
            total_benefic_virupas=round(benefic_v, 4),
            total_malefic_virupas=round(malefic_v, 4),
        )