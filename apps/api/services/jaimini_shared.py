"""
AstroOS — Jaimini Shared Primitives (Layer 6: Calculation Engine)

Small, dependency-free helpers reused across every Jaimini sub-engine
(Chara Karaka, Arudha Pada, Rashi Aspect, Argala): rashi-index
arithmetic, whole-sign house resolution, sign-nature (Chara/Sthira/
Dvisvabhava) classification, and natural benefic/malefic classification.

Kept here rather than duplicated per engine, and rather than added to
packages/shared/constants.py, because these groupings (sign nature,
Jaimini-specific benefic/malefic reads) have no use outside the Jaimini
module — packages/shared is for constants used across the whole app.
"""

from __future__ import annotations

from typing import Literal

from apps.api.domain.horoscope import D1Chart
from packages.shared.enums import Rashi
from packages.shared.rashi_offset import house_offset

RASHI_LIST: tuple[str, ...] = tuple(r.value for r in Rashi)
"""Zodiacal order, index 0 = Aries ... 11 = Pisces."""

SignNature = Literal["chara", "sthira", "dvisvabhava"]

_CHARA_RASHIS: frozenset[str] = frozenset({"aries", "cancer", "libra", "capricorn"})
_STHIRA_RASHIS: frozenset[str] = frozenset({"taurus", "leo", "scorpio", "aquarius"})
_DVISVABHAVA_RASHIS: frozenset[str] = frozenset({"gemini", "virgo", "sagittarius", "pisces"})

NATURAL_BENEFICS: frozenset[str] = frozenset({"jupiter", "venus", "mercury"})
"""Moon is conditionally benefic (see is_benefic) so it is deliberately
excluded from this fixed set."""
NATURAL_MALEFICS: frozenset[str] = frozenset({"sun", "mars", "saturn", "rahu", "ketu"})


def rashi_index(rashi: str) -> int:
    return RASHI_LIST.index(rashi)


def rashi_at(index: int) -> str:
    return RASHI_LIST[index % 12]


def signs_from(start_rashi: str, offset: int) -> str:
    """The rashi `offset` signs forward (zodiacally) from start_rashi.
    offset=0 returns start_rashi itself; offset=1 the next sign, etc.
    Negative offsets count backward — Python's modulo on a negative
    index already wraps correctly (e.g. -1 % 12 == 11)."""
    return rashi_at(rashi_index(start_rashi) + offset)


def house_count(from_rashi: str, to_rashi: str) -> int:
    """
    Classical inclusive house count: from_rashi counted as 1, the next
    sign as 2, ... up to and including to_rashi. Always 1-12 (never 0),
    matching how every Vedic "count from X to Y" sutra works.
    """
    return house_offset(rashi_index(from_rashi), rashi_index(to_rashi))


def is_kendra(from_rashi: str, to_rashi: str) -> bool:
    """Whether to_rashi is a Kendra (1st/4th/7th/10th) counted inclusively from from_rashi."""
    return house_count(from_rashi, to_rashi) in (1, 4, 7, 10)


def is_trikona(from_rashi: str, to_rashi: str) -> bool:
    """Whether to_rashi is a Trikona (1st/5th/9th) counted inclusively from from_rashi."""
    return house_count(from_rashi, to_rashi) in (1, 5, 9)


def is_movable(rashi: str) -> bool:
    return rashi.lower() in _CHARA_RASHIS


def is_fixed(rashi: str) -> bool:
    return rashi.lower() in _STHIRA_RASHIS


def is_dual(rashi: str) -> bool:
    return rashi.lower() in _DVISVABHAVA_RASHIS


def sign_nature(rashi: str) -> SignNature:
    r = rashi.lower()
    if r in _CHARA_RASHIS:
        return "chara"
    if r in _STHIRA_RASHIS:
        return "sthira"
    if r in _DVISVABHAVA_RASHIS:
        return "dvisvabhava"
    raise ValueError(f"Unrecognized rashi: {rashi!r}")


def lagna_rashi(chart: D1Chart) -> str:
    return chart.ascendant.rashi


def whole_sign_house_rashi(chart: D1Chart, house_number: int) -> str:
    """
    The rashi occupying `house_number` (1-12) under WHOLE-SIGN house
    counting from the Lagna — the house system every Jaimini technique
    (Arudha, Argala, Rashi Drishti) universally uses. Deliberately
    distinct from the Bhava Chalit cuspal house_number already on
    SiderealPosition (a Parashari convention this module never reads).
    """
    if not 1 <= house_number <= 12:
        raise ValueError(f"house_number must be 1-12, got {house_number}")
    return signs_from(lagna_rashi(chart), house_number - 1)


def planets_in_rashi(chart: D1Chart, rashi: str) -> list[str]:
    """Every graha (of the 9) currently occupying this sign, by name."""
    return [p.planet for p in chart.planets if p.rashi == rashi]


def is_benefic(planet: str, chart: D1Chart) -> bool:
    """
    Natural benefic/malefic classification, per the classical baseline
    rule — contextual affliction (e.g. Mercury conjunct malefics turning
    malefic) is a separate, deeper technique and out of scope here.

    Moon is the one planet whose natural status is conditional: benefic
    in Shukla Paksha (waxing), malefic in Krishna Paksha (waning) — read
    directly off the chart's already-computed panchanga rather than
    re-deriving it from Sun/Moon longitudes.
    """
    if planet == "moon":
        return chart.panchanga.tithi.paksha == "shukla"
    return planet in NATURAL_BENEFICS
