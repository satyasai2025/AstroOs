"""
AstroOS — House Domain Objects (Module 6)

Typed domain objects for bhava (house) analysis. Pure Python dataclasses
— no ORM or Pydantic dependencies, matching the convention in
domain/horoscope.py and domain/ephemeris.py.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class HouseClassification:
    """
    Classical house-type classification for one bhava (1-12).

    `quadrant` is mutually exclusive and covers all 12 houses in groups
    of 4 (every house is exactly one of kendra/panapara/apoklima).
    `is_trikona`, `is_dusthana`, and `is_upachaya` are separate,
    non-exclusive auspicious/growth/difficulty designations — a house can
    be both a panapara house AND trikona (e.g. house 5), or both apoklima
    AND upachaya (e.g. house 3).
    """
    house_number: int
    quadrant: str          # "kendra" | "panapara" | "apoklima"
    is_trikona: bool        # Houses 1, 5, 9 — auspicious trine houses
    is_dusthana: bool       # Houses 6, 8, 12 — difficult houses
    is_upachaya: bool       # Houses 3, 6, 10, 11 — houses that improve over time


@dataclass(frozen=True)
class HouseInfo:
    """
    Full analysis for one bhava (house) in a D1 chart: its sign, lord,
    which planets occupy it, and its classical classification.
    """
    house_number: int
    rashi: str
    lord: str
    occupants: list[str] = field(default_factory=list)
    classification: Optional[HouseClassification] = None
