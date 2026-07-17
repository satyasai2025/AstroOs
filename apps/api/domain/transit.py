"""
AstroOS — Transit Domain Objects (Module 11)

Transit (Gochara) analysis compares a natal chart against planetary
positions at any other moment — structurally different from every
module before it, which all operate on a single fixed chart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TransitPlanetResult:
    """
    One transiting planet's position and classical Gochara (transit)
    read, at a specified moment, against a specific natal chart.
    """
    planet: str
    transit_rashi: str
    house_from_natal_moon: int  # 1-12, Gochara's standard reference point
    ashtakavarga_bindus: Optional[int]  # None for Rahu/Ketu — not covered by classical Ashtakavarga
    is_sade_sati: bool = False  # only meaningful for Saturn
    is_ashtama_shani: bool = False  # only meaningful for Saturn
    # Added in Module 11 Phase 2 (Vedha). is_favorable_house: True if the
    # current house is one of this planet's classical good houses (subject
    # to Vedha obstruction), False if a classical bad house (subject to
    # Vipreet Vedha relief), None if this source states no rule for this
    # house at all. has_vedha: the good-house effect is currently
    # obstructed by vedha_planet. has_vipreet_vedha: the bad-house effect
    # is currently relieved by vedha_planet. See
    # packages/shared/transit_vedha_table.py for sourcing.
    is_favorable_house: Optional[bool] = None
    has_vedha: bool = False
    has_vipreet_vedha: bool = False
    vedha_planet: Optional[str] = None
    rule_version: str = "1.0"
