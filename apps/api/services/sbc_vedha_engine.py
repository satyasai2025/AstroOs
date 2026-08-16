"""
AstroOS — Sarvatobhadra Chakra (SBC) CellNum Vedha Engine

**Sourcing.** Mechanism (who casts, which single direction, the scoring
formula) is confirmed directly from a real working SBC tool's VBA
module (`modSBC_Vedha.bas`, referenced in that tool's `Vedha_Map` sheet
header) — not inferred or fabricated. See
packages/shared/sbc_cellnum_table.py for the CellNum grid/path data this
engine looks up.

**Mechanism.**
1. Only benefic planets cast a Vedha at all: Jupiter and Venus always;
   Moon only when Tithi is 6-20 (centred on full moon — a SBC-specific
   rule, distinct from the Tithi<=15 rule used elsewhere in this
   codebase for general Paksha Bala); Mercury via the same same-
   nakshatra-with-a-malefic conjunction check already used for its
   general functional-nature flip elsewhere in this app. Sun, Mars,
   Saturn, Rahu, and Ketu never cast a Vedha in this engine.
2. Each casting planet aspects exactly ONE direction, chosen by its own
   motion state: Normal speed -> Front, Fast/High speed -> Left,
   Retrograde -> Right. Moon is the sole exception and always casts all
   three directions regardless of its own speed.
3. A hit occurs when the natal/Janma element's CellNum appears anywhere
   in the casting planet's current-nakshatra path for that one
   direction (packages.shared.sbc_cellnum_table.vedha_path).
4. Score per hit = 5 x dignity multiplier (Own=1, Friendly=0.75,
   Neutral=0.5, Enemy=0.25, Exalted=3, Debilitated=0.5; Moolatrikona
   treated as Own — not separately listed in the source tool's 6-tier
   scale), doubled if the casting planet is retrograde, zeroed if it is
   combust. If any benefic that cast a hit shares its own nakshatra
   (hence CellNum) with any malefic planet, the ENTIRE total score for
   this Janma element becomes 0 — an all-or-nothing override per the
   source tool, not a partial deduction.

**Known open caveat, carried over from the source doc.** The Front-
target pairing itself (which nakshatra points to which) is the source
tool builder's own best-effort application of the standard published
pair-list, independently confirmed against JHora for Dhanishtha and
Shatabhisha in this project (see docs/sarvatobhadra_vedha_table.md) but
not for every one of the 28 nakshatras. Treat the *mechanism* below as
solid; treat any specific score as only as trustworthy as the
underlying CellNum table's per-nakshatra paths.

**Known contradiction in the source material, not silently resolved.**
An earlier "confirmed working example" from the same tool's real audit
log (Janma Rasi Pisces at CellNum 39, Shatabhisha's Left path, Rahu
transiting -> Hit) predates this benefic-only mechanism and used a
simpler "any transiting body, check all 3 paths" rule under which Rahu
(a non-benefic) could still register a hit. That simpler rule is
superseded here per the later correction (sourced directly from VBA,
not inferred), so this engine's `NakshatraVedhaCasterCheck` will NOT
flag Rahu as a caster — see test_sbc_vedha_engine.py, where that example
is reused only to regression-test the CellNum path-lookup itself
(`vedha_path`), not the benefic gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from packages.shared.dignity import compute_dignity_value
from packages.shared.sbc_cellnum_table import cellnum_for_nakshatra, vedha_path
from apps.api.services.gati_classifier import classify_gati

_ALWAYS_BENEFIC = {"jupiter", "venus"}
_NEVER_BENEFIC = {"sun", "mars", "saturn", "rahu", "ketu"}

_DIGNITY_MULTIPLIER: dict[str, float] = {
    "exalted": 3.0,
    "own": 1.0,
    "moolatrikona": 1.0,  # not a distinct tier in the source tool's scale; treated as Own.
    "friendly": 0.75,
    "neutral": 0.5,
    "enemy": 0.25,
    "debilitated": 0.5,
}


@dataclass
class SBCTransitPlanet:
    planet: str
    nakshatra: str  # 28-system token (incl. "abhijit")
    rashi: str
    rashi_degree: float
    speed_deg_per_day: float
    is_retrograde: bool
    is_combust: bool
    tithi: Optional[int] = None  # only required to evaluate Moon's benefic status


@dataclass
class SBCVedhaHit:
    planet: str
    direction: str  # "front" | "left" | "right"
    from_nakshatra: str
    score: float


@dataclass
class SBCVedhaResult:
    hits: list[SBCVedhaHit]
    total_score: float
    zeroed_by_malefic_conjunction: bool


def _is_benefic_caster(planet: SBCTransitPlanet, all_planets: list[SBCTransitPlanet]) -> bool:
    if planet.planet in _ALWAYS_BENEFIC:
        return True
    if planet.planet in _NEVER_BENEFIC:
        return False
    if planet.planet == "moon":
        return planet.tithi is not None and 6 <= planet.tithi <= 20
    if planet.planet == "mercury":
        malefics_here = {
            p.planet
            for p in all_planets
            if p.planet in _NEVER_BENEFIC and p.nakshatra == planet.nakshatra
        }
        return not malefics_here
    return False


def _direction_for(planet: SBCTransitPlanet) -> str:
    if planet.planet == "moon":
        return "all"
    if planet.is_retrograde:
        return "right"
    gati = classify_gati(planet.planet, planet.speed_deg_per_day, planet.is_retrograde)
    if gati in ("chara", "atichara"):
        return "left"
    return "front"


def _score_for_hit(planet: SBCTransitPlanet) -> float:
    if planet.is_combust:
        return 0.0
    dignity = compute_dignity_value(planet.planet, planet.rashi, planet.rashi_degree)
    multiplier = _DIGNITY_MULTIPLIER.get(dignity, 0.5) if dignity else 0.5
    score = 5.0 * multiplier
    if planet.is_retrograde:
        score *= 2.0
    return score


class SBCVedhaEngine:
    """Stateless. Computes Vedha hits from a set of transiting planets
    onto a single natal/Janma element (identified by its SBC nakshatra
    or, for non-nakshatra Janma elements such as a Rasi point, directly
    by CellNum via `check_cellnum`)."""

    def check(
        self,
        janma_nakshatra: str,
        transiting_planets: list[SBCTransitPlanet],
    ) -> SBCVedhaResult:
        return self.check_cellnum(cellnum_for_nakshatra(janma_nakshatra), transiting_planets)

    def check_cellnum(
        self,
        janma_cellnum: int,
        transiting_planets: list[SBCTransitPlanet],
    ) -> SBCVedhaResult:
        hits: list[SBCVedhaHit] = []

        for planet in transiting_planets:
            if not _is_benefic_caster(planet, transiting_planets):
                continue

            direction = _direction_for(planet)
            directions = ("front", "left", "right") if direction == "all" else (direction,)

            for d in directions:
                path = vedha_path(planet.nakshatra, d)
                if janma_cellnum in path:
                    hits.append(
                        SBCVedhaHit(
                            planet=planet.planet,
                            direction=d,
                            from_nakshatra=planet.nakshatra,
                            score=_score_for_hit(planet),
                        )
                    )
                    break  # one hit per casting planet is enough to register it

        zeroed = False
        for hit in hits:
            caster = next(p for p in transiting_planets if p.planet == hit.planet)
            same_cell_malefics = [
                p
                for p in transiting_planets
                if p.planet in _NEVER_BENEFIC and p.nakshatra == caster.nakshatra
            ]
            if same_cell_malefics:
                zeroed = True
                break

        total = 0.0 if zeroed else sum(h.score for h in hits)
        return SBCVedhaResult(hits=hits, total_score=total, zeroed_by_malefic_conjunction=zeroed)
