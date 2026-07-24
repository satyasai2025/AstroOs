"""
AstroOS — Avastha (Planetary State) Engine

Classical texts (starting with BPHS Ch. 6) describe several distinct
"Avastha" (state) systems for grading a planet's condition beyond raw
Shadbala. This engine implements exactly TWO of them — deliberately
not the rest:

1. **Baladi Avastha** (5-fold, degree-based) — IMPLEMENTED. A planet's
   30 degrees within its sign are divided into 5 equal 6-degree bands:
   Bala (infant) -> Kumara (child) -> Yuva (youth) -> Vriddha (old) ->
   Mrita (dead), each carrying progressively different classical
   effect. For odd-numbered signs (Aries, Gemini, Leo, Libra,
   Sagittarius, Aquarius) the bands run in that order from 0 degrees;
   for even-numbered signs the order reverses. This is a precise,
   universally-cited degree formula — low fabrication risk.

2. **Deeptadi Avastha** (dignity-based) — IMPLEMENTED, using this
   codebase's ALREADY-COMPUTED 7-level dignity
   (exalted/own/moolatrikona/friendly/neutral/enemy/debilitated, see
   domain/ephemeris.py's DignityType) plus is_combust, mapped to the
   commonly-cited Deeptadi state names (Deepta/Swastha/Pramudita/
   Shanta/Sama/Dukhita/Vikala/Kopa). Classical texts describe this
   system with 8-9 states and some naming/grouping variance across
   sources (e.g. whether "great friend" and "friend" are graded
   separately) — this implementation honestly maps onto the dignity
   granularity this codebase actually computes rather than inventing a
   finer split we can't back with real data.

**Jagradadi Avastha (Jagrat/Swapna/Sushupti) is explicitly NOT
implemented.** Classical texts derive it from the 12-fold Shayanadi
Avastha system (Shayana/Upaveshana/Netrapani/Prakasana/Gamana/Sabha/
Agamana/Bhojana/Nrityalipsa/Kautuka/Nidra/Sushupti), whose own
determination rules vary meaningfully across sources and need a level
of textual precision this implementation isn't confident enough in to
encode without risking a subtly-wrong classical claim. Better to omit
it honestly than fabricate a plausible-looking but unverified formula.
"""

from __future__ import annotations

from apps.api.domain.avastha import AvasthaResult
from apps.api.domain.ephemeris import SiderealPosition

_RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

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

    dignity_key = position.dignity.value if position.dignity else "neutral"
    state = _DEEPTADI_BY_DIGNITY.get(dignity_key, "Sama")
    trace = (
        f"Step 1: {position.planet} is not combust",
        f"Step 2: sign dignity = {dignity_key}",
        f"Step 3: dignity -> Deeptadi state = {state}",
    )
    return state, trace


class AvasthaEngine:
    """Stateless — needs only each planet's already-computed SiderealPosition."""

    def compute(self, position: SiderealPosition) -> AvasthaResult:
        baladi, baladi_trace = _compute_baladi(position)
        deeptadi, deeptadi_trace = _compute_deeptadi(position)
        return AvasthaResult(
            planet=position.planet,
            baladi_avastha=baladi,
            baladi_trace=baladi_trace,
            deeptadi_avastha=deeptadi,
            deeptadi_trace=deeptadi_trace,
        )

    def compute_all(self, planets: list[SiderealPosition]) -> list[AvasthaResult]:
        return [self.compute(p) for p in planets]
