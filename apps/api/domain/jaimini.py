"""
AstroOS — Jaimini Chara Karaka Domain Objects (Layer 6: Calculation Engine)

Chara Karaka ("movable/variable significator") is a Jaimini astrology
technique that ranks a fixed set of grahas by their degree of advancement
within their occupied rashi (0-30°), highest first. Unlike Parashari
karakas (fixed: Sun=father, Moon=mother, ...), Chara Karakas are
recomputed for every chart — whichever graha has moved furthest through
its sign becomes that native's Atmakaraka ("soul significator"), the
graha that has moved least becomes Darakaraka ("spouse significator"),
and so on.

Two schemes:
  - Sapta Karaka (7 karakas): the 7 classical grahas (Sun..Saturn),
    Rahu/Ketu excluded entirely.
  - Ashta Karaka (8 karakas): the same 7 plus Rahu (never Ketu — Ketu
    represents detachment/moksha and is never assigned a worldly karaka
    role in any classical scheme). Rahu's karaka degree is measured as
    (30 - rashi_degree), not rashi_degree directly — see
    jaimini_engine.py's _karaka_degree for why.

Pure Python dataclasses — no ORM/Pydantic dependency, matching the
convention in domain/horoscope.py, domain/yoga.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional

CharaKarakaScheme = Literal["sapta_karaka", "ashta_karaka"]

KARAKA_NAMES_SAPTA: tuple[str, ...] = (
    "Atmakaraka",
    "Amatyakaraka",
    "Bhratrikaraka",
    "Matrikaraka",
    "Putrakaraka",
    "Gnatikaraka",
    "Darakaraka",
)
"""7-karaka scheme rank names, highest karaka_degree (rank 1) to lowest (rank 7)."""

KARAKA_NAMES_ASHTA: tuple[str, ...] = (
    "Atmakaraka",
    "Amatyakaraka",
    "Bhratrikaraka",
    "Matrikaraka",
    "Pitrikaraka",
    "Putrakaraka",
    "Gnatikaraka",
    "Darakaraka",
)
"""8-karaka scheme rank names. Including Rahu inserts Pitrikaraka (father
significator) at rank 5, shifting Putrakaraka/Gnatikaraka down by one;
Darakaraka (least-advanced planet) stays last in both schemes."""

TiebreakRule = Literal["speed", "natural_benefic"]


@dataclass(frozen=True)
class CharaKaraka:
    """One ranked graha in a Chara Karaka result."""

    rank: int  # 1 = Atmakaraka ... N = Darakaraka
    karaka_name: str  # e.g. "Atmakaraka"
    planet: str  # e.g. "sun", "rahu"
    rashi: str
    rashi_degree: float  # raw 0-30° position in sign, as stored on the chart
    karaka_degree: float  # value actually ranked on (Rahu: 30 - rashi_degree)
    speed_deg_per_day: float
    is_retrograde: bool
    tiebreak_rule: Optional[TiebreakRule] = None
    """Set only when this planet's rank vs. its immediate neighbor was
    decided by a tie-breaker, and which rule broke it. None means its
    karaka_degree alone was already unique against both neighbors."""


@dataclass(frozen=True)
class CharaKarakaResult:
    """Full Chara Karaka ranking for one chart under one scheme."""

    scheme: CharaKarakaScheme
    karakas: tuple[CharaKaraka, ...]

    @property
    def atmakaraka(self) -> CharaKaraka:
        return self.karakas[0]

    @property
    def darakaraka(self) -> CharaKaraka:
        return self.karakas[-1]

    def by_name(self, karaka_name: str) -> CharaKaraka:
        for k in self.karakas:
            if k.karaka_name == karaka_name:
                return k
        raise KeyError(f"No karaka named {karaka_name!r} in this result.")


# ── Arudha Pada ─────────────────────────────────────────────────────────────
#
# Arudha Pada ("the risen image") — the reflection/perception point of a
# house, computed from where that house's lord sits. A1 (Arudha Lagna) is
# the most-used; Upapada Lagna (UL) is, by definition, A12 — not a
# separate formula. See services/arudha_engine.py for the full sutra.


@dataclass(frozen=True)
class ArudhaPada:
    house_number: int  # 1-12, the bhava this Arudha was computed for (whole-sign, from Lagna)
    pada_name: str  # e.g. "A1" (Arudha Lagna) ... "A12" (= Upapada Lagna)
    rashi: str  # final rashi, after the same/7th-house exception shift (if any)
    raw_rashi: str  # rashi before the exception check
    lord: str  # planet ruling house_number's occupied sign
    lord_rashi: str  # sign the lord currently occupies
    exception_applied: bool  # True if the "falls on itself or 7th from itself" shift fired


@dataclass(frozen=True)
class ArudhaResult:
    padas: tuple[ArudhaPada, ...]  # exactly 12 entries, house_number 1..12 in order

    @property
    def arudha_lagna(self) -> ArudhaPada:
        return self.padas[0]  # A1

    @property
    def upapada_lagna(self) -> ArudhaPada:
        return self.padas[11]  # A12, by definition

    def by_house(self, house_number: int) -> ArudhaPada:
        for p in self.padas:
            if p.house_number == house_number:
                return p
        raise KeyError(house_number)


# ── Rashi Aspect (Rashi Drishti) ─────────────────────────────────────────────
#
# Jaimini's sign-based aspect: fixed by sign NATURE, never by longitude —
# structurally different from Parashari Graha Drishti (aspect_engine.py),
# which aspects by house-offset from a planet's exact position. See
# services/rashi_aspect_engine.py for the full sutra.


@dataclass(frozen=True)
class RashiAspect:
    """One real, planet-relevant sign aspect: a graha occupying from_rashi
    casting a Jaimini Rashi Drishti onto to_rashi."""

    from_rashi: str
    to_rashi: str
    aspecting_planets: tuple[str, ...]  # grahas occupying from_rashi (never empty)
    aspected_planets: tuple[str, ...]  # grahas occupying to_rashi (may be empty)


@dataclass(frozen=True)
class RashiAspectResult:
    matrix: dict[str, tuple[str, ...]]
    """Pure structural lookup: matrix[sign] = every sign it aspects.
    Complete for all 12 signs regardless of occupancy — the 'clean
    boolean lookup matrix' (test `to_rashi in matrix[from_rashi]` for a
    boolean membership check)."""
    aspects: tuple[RashiAspect, ...]
    """Only entries where from_rashi is actually occupied by >=1 planet —
    the practically useful 'which real grahas cast an aspect on which
    sign' view for evidence panels."""

    def does_aspect(self, from_rashi: str, to_rashi: str) -> bool:
        return to_rashi in self.matrix[from_rashi]

    def aspects_on(self, target_rashi: str) -> tuple[RashiAspect, ...]:
        """All (occupied) aspects landing on target_rashi."""
        return tuple(a for a in self.aspects if a.to_rashi == target_rashi)


# ── Argala / Virodhargala ────────────────────────────────────────────────────
#
# Argala ("intervention") — supportive/obstructive influence cast on a
# reference sign from the 2nd/4th/5th/11th houses from it, each
# potentially nullified by its Virodhargala ("counter-argala") in the
# 12th/10th/9th/3rd respectively. See services/argala_engine.py for the
# full sutra, including why no Rahu/Ketu reverse-counting rule applies
# here (unlike Chara Karaka).


@dataclass(frozen=True)
class ArgalaPair:
    """One Argala/Virodhargala pair, counted from a single reference sign."""

    argala_house: int  # 2, 4, 5, or 11 (counted inclusively from the reference)
    virodhargala_house: int  # 12, 10, 9, or 3 respectively
    argala_rashi: str
    virodhargala_rashi: str
    argala_planets: tuple[str, ...]
    virodhargala_planets: tuple[str, ...]
    is_active: bool  # argala_planets is non-empty
    is_cancelled: bool  # is_active AND len(virodhargala_planets) >= len(argala_planets)
    strength_score: float
    """Net benefic occupancy of the argala house (benefic count - malefic
    count, natural classification). Positive = net-supportive argala,
    negative = net-obstructive. Reported regardless of is_cancelled so
    the evidence panel can show both the raw contribution and whether it
    actually applies."""


@dataclass(frozen=True)
class ArgalaResult:
    reference_rashi: str
    reference_label: str  # the planet or sign name originally passed to the engine
    pairs: tuple[ArgalaPair, ...]  # exactly 4 entries: (2,12), (4,10), (5,9), (11,3)

    @property
    def net_strength(self) -> float:
        return sum(p.strength_score for p in self.pairs if not p.is_cancelled)


# ── Karakamsa / Swamsa ────────────────────────────────────────────────────────
#
# Karakamsa — the Navamsa (D9) sign occupied by the Atmakaraka. Swamsa —
# the Navamsa sign occupied by the D1 Lagna itself (the D9 chart's own
# Ascendant). Always analyzed as a pair. See services/karakamsa_engine.py
# for the full definitions.


@dataclass(frozen=True)
class KarakamsaHouseEntry:
    """One house counted from Karakamsa, treating it as a Lagna — the
    standard 'Karakamsa chart' re-cast, used to read D9 placements
    relative to the soul significator rather than the D1 ascendant."""

    house_number: int  # 1-12, counted zodiacally from Karakamsa
    rashi: str
    planets: tuple[str, ...]  # D9 (varga) placements of grahas occupying this rashi


@dataclass(frozen=True)
class KarakamsaResult:
    scheme: CharaKarakaScheme  # which Chara Karaka scheme produced the Atmakaraka used here
    atmakaraka: str  # planet name
    karakamsa_rashi: str  # D9 sign occupied by Atmakaraka — THE Karakamsa (= Atmakaraka Navamsa sign)
    swamsa_rashi: str  # D9 sign occupied by the D1 Lagna, i.e. the Navamsa Lagna itself
    d1_atmakaraka_rashi: str  # traceability: Atmakaraka's D1 sign
    d1_lagna_rashi: str  # traceability: D1 Lagna sign
    relative_houses: tuple[KarakamsaHouseEntry, ...]  # exactly 12 entries, Karakamsa = house 1


# ── Chara / Narayana Dasha (re-shaping adapter over dasha_engine.py) ─────────
#
# NOT a new dasha calculation — dasha_engine.py's DashaEngine.compute_chara/
# compute_narayana already implement this (Neelakantha's rule, Scorpio/
# Aquarius dual-lord handling via JAIMINI_ALT_LORDS). These two dataclasses
# are purely a re-shaping of that existing DashaTree/DashaPeriod output into
# the same conventions the other Jaimini result objects use (a rashi-named
# field instead of the generic 'lord', an explicit lagna_rashi instead of
# the nakshatra-system-oriented 'trigger_planet') — see
# services/jaimini_dasha_adapter.py for the adapter itself.


@dataclass(frozen=True)
class JaiminiDashaPeriod:
    rashi: str  # the ruling sign for this period (DashaPeriod.lord, renamed for clarity)
    start_date: date
    end_date: date
    duration_days: int
    level: int
    sub_periods: tuple["JaiminiDashaPeriod", ...] = ()


@dataclass(frozen=True)
class JaiminiDashaResult:
    system: Literal["chara", "narayana"]
    lagna_rashi: str  # DashaTree.trigger_planet, renamed. Chara: the Lagna sign. Narayana: the dasha's seed sign (NOT necessarily Lagna) — see jaimini_dasha_adapter.py's module docstring.
    periods: tuple[JaiminiDashaPeriod, ...]  # DashaTree.mahadashas, renamed
    max_depth: int
    total_cycle_years: int
