"""
AstroOS — Avastha (Planetary State) Engine

Classical texts (BPHS Ch. 45) describe 4 distinct "Avastha" systems:

1. **Baladi Avastha** (5-fold, degree-based):
   Bala (infant) -> Kumara (child) -> Yuva (youth) -> Vriddha (old) -> Mrita (dead)
   For odd signs: forward order; for even signs: reversed order.

2. **Deeptadi Avastha** (8-fold, dignity & combustion based):
   Deepta (exalted), Swastha (own sign), Pramudita (moolatrikona), Shanta (friendly),
   Sama (neutral), Dukhita (enemy), Vikala (debilitated), Kopa (combust).

3. **Jagradadi Avastha** (3-fold, alertness/consciousness based):
   - Jagrata (Awake/Alert): Exalted or Own sign (100% full auspicious results)
   - Swapna (Dreaming): Friendly or Neutral sign (50% medium results)
   - Sushupti (Sleeping/Inactive): Inimical or Debilitated sign (0-25% results)

4. **Sayanadi Avastha** (12-fold activity/state system, BPHS Ch. 45):
   1. Shayana (Lying down/resting)
   2. Upaveshana (Sitting)
   3. Netrapani (Hand on eyes)
   4. Prakasana (Radiant/illuminating)
   5. Gamana (Moving/traveling)
   6. Agamana (Returning/arriving)
   7. Sabha (In assembly/court)
   8. Bhojana (Feasting/eating)
   9. Nrityalipsa (Desiring to dance)
   10. Kautuka (Playful/eager)
   11. Nidra (Sleeping)
   12. Sushupti (Deep slumber)

   Formula: V = (Planet_Nakshatra * Planet_Idx * Navamsha_Num) + Moon_Nakshatra + Ghati_From_Sunrise + Lagna_Num
   Rem = V mod 12 (1=Shayana .. 11=Nidra, 0/12=Sushupti)
"""

from __future__ import annotations

import math
from typing import Optional

from apps.api.domain.avastha import AvasthaResult
from apps.api.domain.ephemeris import SiderealPosition
from packages.shared.enums import Nakshatra, Rashi

_RASHI_LIST = [r.value for r in Rashi]
_NAKSHATRA_LIST = [n.value for n in Nakshatra]

_BALADI_STATES = ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]

_DEEPTADI_BY_DIGNITY: dict[str, str] = {
    "exalted": "Deepta",
    "own": "Swastha",
    "moolatrikona": "Pramudita",
    "friendly": "Shanta",
    "neutral": "Sama",
    "enemy": "Dukhita",
    "debilitated": "Vikala",
}

_COMBUST_STATE = "Kopa"

# BPHS Planet order (1-indexed for Sayanadi: Sun=1..Saturn=7, Rahu=8, Ketu=9)
_PLANET_INDEX_MAP: dict[str, int] = {
    "sun": 1,
    "moon": 2,
    "mars": 3,
    "mercury": 4,
    "jupiter": 5,
    "venus": 6,
    "saturn": 7,
    "rahu": 8,
    "ketu": 9,
}

_SAYANADI_STATES: list[str] = [
    "Sushupti",    # 0 or 12
    "Shayana",     # 1
    "Upaveshana",  # 2
    "Netrapani",   # 3
    "Prakasana",   # 4
    "Gamana",      # 5
    "Agamana",     # 6
    "Sabha",       # 7
    "Bhojana",     # 8
    "Nrityalipsa", # 9
    "Kautuka",     # 10
    "Nidra",       # 11
]

_SAYANADI_DESCRIPTIONS: dict[str, str] = {
    "Shayana": "Lying down / resting — moderate physical vitality and introspective nature",
    "Upaveshana": "Sitting comfortably — good intellect, administrative ease, and dignity",
    "Netrapani": "Hand on eyes — occasional obstacles, sorrow, or eye strain if afflicted",
    "Prakasana": "Radiant / illuminating — royal honor, virtues, brilliance, and high renown",
    "Gamana": "Moving / traveling — dynamic pursuits, distant journeys, and active vigor",
    "Agamana": "Returning / arriving — acquisition of wealth, family joy, and fulfilled travel",
    "Sabha": "Presiding in assembly — eloquence, social respect, scholarly prestige, and governance",
    "Bhojana": "Feasting / dining — wealth, love for fine foods, comfort, and physical nourishment",
    "Nrityalipsa": "Desiring to dance / celebration — artistic flair, celebratory spirit, and happiness",
    "Kautuka": "Playful / eager — curiosity, happiness, victory, and affectionate temperament",
    "Nidra": "Sleeping — sluggishness, delays in fructification, or unharnessed potential",
    "Sushupti": "Deep slumber / dissolution — latent energy, spiritual detachment, or dormancy",
}


def _compute_baladi(position: SiderealPosition) -> tuple[str, tuple[str, ...]]:
    rashi_index = _RASHI_LIST.index(position.rashi.lower())
    sign_number = rashi_index + 1  # 1-indexed, Aries=1
    is_odd_sign = sign_number % 2 == 1

    band = min(4, int(position.rashi_degree // 6.0))
    state = _BALADI_STATES[band] if is_odd_sign else _BALADI_STATES[4 - band]

    trace = (
        f"Step 1: {position.planet} is at {position.rashi_degree:.2f}° "
        f"within {position.rashi} (sign #{sign_number}, {'odd' if is_odd_sign else 'even'})",
        f"Step 2: degree band = floor({position.rashi_degree:.2f} / 6) = {band} (0-4)",
        f"Step 3: {'odd sign, forward order' if is_odd_sign else 'even sign, reversed order'} "
        f"-> {state}",
    )
    return state, trace


def _compute_deeptadi(position: SiderealPosition) -> tuple[str, tuple[str, ...]]:
    if position.is_combust:
        trace = (
            f"Step 1: {position.planet} is combust (orb {position.combustion_orb:.2f}° from Sun)"
            if position.combustion_orb is not None
            else f"Step 1: {position.planet} is combust",
            f"Step 2: combustion overrides sign-dignity state -> {_COMBUST_STATE}",
        )
        return _COMBUST_STATE, trace

    dignity_key = position.dignity.value if hasattr(position.dignity, "value") else (str(position.dignity).lower() if position.dignity else "neutral")
    state = _DEEPTADI_BY_DIGNITY.get(dignity_key, "Sama")
    trace = (
        f"Step 1: {position.planet} is not combust",
        f"Step 2: sign dignity = {dignity_key}",
        f"Step 3: dignity -> Deeptadi state = {state}",
    )
    return state, trace


def _compute_jagradadi(position: SiderealPosition) -> tuple[str, tuple[str, ...]]:
    dignity_key = position.dignity.value if hasattr(position.dignity, "value") else (str(position.dignity).lower() if position.dignity else "neutral")

    if dignity_key in ("exalted", "own", "moolatrikona"):
        state = "Jagrata"
        desc = "Awake / Alert — 100% full auspicious capacity"
    elif dignity_key in ("friendly", "neutral"):
        state = "Swapna"
        desc = "Dreaming — 50% medium capacity"
    else:  # enemy, debilitated
        state = "Sushupti"
        desc = "Deep Sleep / Dormant — 0-25% minimal or adverse capacity"

    trace = (
        f"Step 1: {position.planet} dignity in {position.rashi} is '{dignity_key}'",
        f"Step 2: Jagradadi classification: {state} ({desc})",
    )
    return state, trace



def _compute_sayanadi(
    position: SiderealPosition,
    moon_nakshatra_num: int = 1,
    lagna_rashi_num: int = 1,
    ghati_from_sunrise: float = 1.0,
) -> tuple[str, tuple[str, ...]]:
    planet_idx = _PLANET_INDEX_MAP.get(position.planet.lower(), 1)

    # 1-indexed Nakshatra number
    planet_nak = getattr(position.nakshatra, "nakshatra", "")
    if isinstance(planet_nak, str) and planet_nak.lower() in [n.lower() for n in _NAKSHATRA_LIST]:
        nak_idx = [n.lower() for n in _NAKSHATRA_LIST].index(planet_nak.lower()) + 1
    else:
        nak_idx = int(position.sidereal_longitude / (360.0 / 27.0)) + 1

    # Navamsha index within sign (1 to 9)
    navamsha_num = min(9, int((position.rashi_degree / (30.0 / 9.0))) + 1)

    ghati_int = max(1, int(round(ghati_from_sunrise)))

    v = (nak_idx * planet_idx * navamsha_num) + moon_nakshatra_num + ghati_int + lagna_rashi_num
    rem = v % 12
    state = _SAYANADI_STATES[rem]
    desc = _SAYANADI_DESCRIPTIONS.get(state, "")

    trace = (
        f"Step 1: Planet {position.planet} (idx={planet_idx}), Nakshatra={nak_idx}, Navamsha={navamsha_num}",
        f"Step 2: Moon Nakshatra={moon_nakshatra_num}, Lagna sign={lagna_rashi_num}, Ghati={ghati_int}",
        f"Step 3: Value = ({nak_idx} * {planet_idx} * {navamsha_num}) + {moon_nakshatra_num} + {ghati_int} + {lagna_rashi_num} = {v}",
        f"Step 4: {v} mod 12 = {rem} -> {state} ({desc})",
    )
    return state, trace


class AvasthaEngine:
    """Computes Baladi, Deeptadi, Jagradadi, and Sayanadi Avasthas."""

    def compute(
        self,
        position: SiderealPosition,
        moon_nakshatra_num: int = 1,
        lagna_rashi_num: int = 1,
        ghati_from_sunrise: float = 1.0,
    ) -> AvasthaResult:
        baladi, baladi_trace = _compute_baladi(position)
        deeptadi, deeptadi_trace = _compute_deeptadi(position)
        jagradadi, jagradadi_trace = _compute_jagradadi(position)
        sayanadi, sayanadi_trace = _compute_sayanadi(
            position,
            moon_nakshatra_num=moon_nakshatra_num,
            lagna_rashi_num=lagna_rashi_num,
            ghati_from_sunrise=ghati_from_sunrise,
        )
        return AvasthaResult(
            planet=position.planet,
            baladi_avastha=baladi,
            baladi_trace=baladi_trace,
            deeptadi_avastha=deeptadi,
            deeptadi_trace=deeptadi_trace,
            jagradadi_avastha=jagradadi,
            jagradadi_trace=jagradadi_trace,
            sayanadi_avastha=sayanadi,
            sayanadi_trace=sayanadi_trace,
        )

    def compute_all(
        self,
        planets: list[SiderealPosition],
        moon_nakshatra_num: int = 1,
        lagna_rashi_num: int = 1,
        ghati_from_sunrise: float = 1.0,
    ) -> list[AvasthaResult]:
        # Extract Moon Nakshatra number if Moon is present
        moon_pos = next((p for p in planets if p.planet.lower() == "moon"), None)
        if moon_pos:
            moon_nak = getattr(moon_pos.nakshatra, "nakshatra", "")
            if isinstance(moon_nak, str) and moon_nak.lower() in [n.lower() for n in _NAKSHATRA_LIST]:
                moon_nakshatra_num = [n.lower() for n in _NAKSHATRA_LIST].index(moon_nak.lower()) + 1
            else:
                moon_nakshatra_num = int(moon_pos.sidereal_longitude / (360.0 / 27.0)) + 1

        return [
            self.compute(
                p,
                moon_nakshatra_num=moon_nakshatra_num,
                lagna_rashi_num=lagna_rashi_num,
                ghati_from_sunrise=ghati_from_sunrise,
            )
            for p in planets
        ]

