"""
AstroOS — Yoga Predicates (Module 8)

Shared, reusable low-level checks built directly on top of GrahaEngine,
HouseEngine, and AspectEngine. This is where the "reusable rule engine"
actually lives, per the Yoga Engine Design Audit §4 — individual yoga
evaluators are composed from these, not from ad-hoc duplicated logic.

YogaContext bundles everything one chart's worth of yoga evaluation needs,
computed once per chart rather than recomputed per yoga.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.house import HouseInfo
from apps.api.services.house_engine import HouseEngine
from packages.shared.constants import EXALTATION_DEGREES, SIGN_LORDS

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}

# Sign modality — identical membership to the "cardinal"/"fixed"/"mutable"
# classification seeded into the signs reference table (migration 0005),
# renamed here to the classical Jyotish terms used in Nabhasa Yoga naming
# (chara=movable, sthira=fixed, dwiswabhava=dual).
MOVABLE_SIGNS = {"aries", "cancer", "libra", "capricorn"}
FIXED_SIGNS = {"taurus", "leo", "scorpio", "aquarius"}
DUAL_SIGNS = {"gemini", "virgo", "sagittarius", "pisces"}

# The 7 classical grahas — used by Nabhasa Yogas, which predate and are
# not classically formulated with the shadow planets (Rahu/Ketu)
# included. Deliberately excludes them, unlike Neecha Bhanga (Phase 1),
# which does cover Rahu/Ketu debilitation since DEBILITATION_RASHIS
# already defines it for them.
CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Standard simplified Parashari benefic/malefic classification used for
# yoga rules that reference "malefic"/"benefic" generically (e.g.
# Papakartari Yoga, Adhi Yoga). Mercury and Moon are classically
# conditional (Mercury takes the nature of associated planets; Moon is
# benefic when waxing, malefic when waning) — this simplified static
# classification is the commonly-used default for yoga detection in v1;
# a conditional refinement is a Phase 3 concern, not a Phase 2 blocker.
NATURAL_BENEFICS = {"jupiter", "venus", "mercury", "moon"}
NATURAL_MALEFICS = {"sun", "mars", "saturn", "rahu", "ketu"}


def is_natural_benefic(planet: str) -> bool:
    """True if the planet is a natural benefic (Jupiter, Venus, Mercury, Moon)."""
    return planet in NATURAL_BENEFICS


def is_natural_malefic(planet: str) -> bool:
    """True if the planet is a natural malefic (Sun, Mars, Saturn, Rahu, Ketu)."""
    return planet in NATURAL_MALEFICS


@dataclass
class YogaContext:
    """
    Everything one chart's yoga evaluation needs, assembled once.
    Mirrors how HoroscopeEngine.generate_d1() assembles GrahaEngine/
    AspectEngine output once per chart rather than per caller.
    """
    chart: D1Chart
    houses: list[HouseInfo]
    planets_by_name: dict[str, SiderealPosition]
    houses_by_number: dict[int, HouseInfo]

    @classmethod
    def build(
        cls,
        chart: D1Chart,
        house_engine: HouseEngine,
    ) -> "YogaContext":
        houses = house_engine.build_house_summary(chart.houses, chart.planets)
        return cls(
            chart=chart,
            houses=houses,
            planets_by_name={p.planet: p for p in chart.planets},
            houses_by_number={h.house_number: h for h in houses},
        )


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------

def get_planet(ctx: YogaContext, name: str) -> SiderealPosition | None:
    """Return the sidereal position of the named planet, or None if absent."""
    return ctx.planets_by_name.get(name)


def get_house(ctx: YogaContext, house_number: int) -> HouseInfo:
    """Return house metadata (sign, lord) for the given house number (1-12)."""
    return ctx.houses_by_number[house_number]


def planets_in_house(ctx: YogaContext, house_number: int, exclude: tuple[str, ...] = ()) -> list[str]:
    """All planet names placed in a given house, optionally excluding some (e.g. Sun, for Sunapha/Anapha)."""
    return [
        name for name, pos in ctx.planets_by_name.items()
        if pos.house_number == house_number and name not in exclude
    ]


def houses_from(reference_house: int, offset: int) -> int:
    """
    The house number that is `offset` positions from `reference_house`,
    counted inclusively (offset=1 is the reference house itself, offset=7
    is directly opposite) and wrapping cyclically through 1-12.

    General-purpose — not specific to Moon or lagna. Used by Gajakesari
    (from Moon) in Phase 1, and by every Chandra Yoga / some Arishta Yoga
    in Phase 2 that also counts from Moon, per the Design Audit §3/§5.
    """
    return ((reference_house - 1 + offset - 1) % 12) + 1


def is_in_kendra_from(house_number: int, reference_house: int) -> bool:
    """Whether house_number is a kendra (1st/4th/7th/10th) counted from reference_house."""
    offsets_landing_on_house = {
        offset for offset in range(1, 13)
        if houses_from(reference_house, offset) == house_number
    }
    return bool(offsets_landing_on_house & {1, 4, 7, 10})


def house_of_lord(ctx: YogaContext, house_number: int) -> int | None:
    """
    Where the lord (ruling planet) of a house is CURRENTLY placed — not
    just who the lord is. This is the house-lordship *placement* lookup
    flagged as new shared infrastructure in the Design Audit §3 (first
    needed by Dhana Yoga, reused by every Raja Yoga after it).
    """
    house = get_house(ctx, house_number)
    lord_planet = house.lord
    lord_position = get_planet(ctx, lord_planet)
    return lord_position.house_number if lord_position is not None else None


def is_conjunct(ctx: YogaContext, planet_a: str, planet_b: str) -> bool:
    """True if both planets occupy the same house in this chart context."""
    a, b = get_planet(ctx, planet_a), get_planet(ctx, planet_b)
    if a is None or b is None:
        return False
    return a.house_number == b.house_number


def is_aspecting(ctx: YogaContext, from_planet: str, to_planet: str) -> bool:
    """True if from_planet casts a graha drishti aspect onto to_planet."""
    return any(
        asp.from_planet == from_planet and asp.to_planet == to_planet
        for asp in ctx.chart.aspects
    )


def is_associated(ctx: YogaContext, planet_a: str, planet_b: str) -> bool:
    """
    Conjunction OR either planet aspecting the other — the common
    "associated with" relationship used across most Raja/Dhana Yoga
    formulations (conjunction, mutual aspect, or one-way aspect are all
    classically accepted as forming the yoga).
    """
    return (
        is_conjunct(ctx, planet_a, planet_b)
        or is_aspecting(ctx, planet_a, planet_b)
        or is_aspecting(ctx, planet_b, planet_a)
    )


def is_exchange(ctx: YogaContext, house_a: int, house_b: int) -> bool:
    """
    Parivartana (mutual exchange): the lord of house_a sits in house_b
    AND the lord of house_b sits in house_a.
    """
    lord_a_placement = house_of_lord(ctx, house_a)
    lord_b_placement = house_of_lord(ctx, house_b)
    return lord_a_placement == house_b and lord_b_placement == house_a


def exalted_in_sign(rashi: str) -> str | None:
    """Which planet (if any) is exalted in the given sign — the inverse of EXALTATION_DEGREES."""
    for planet, (exalt_rashi, _) in EXALTATION_DEGREES.items():
        if exalt_rashi == rashi:
            return planet
    return None


def dispositor_of(rashi: str) -> str:
    """The planet ruling a sign — thin wrapper over SIGN_LORDS for readability in evaluators."""
    return SIGN_LORDS[rashi]
