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
    # Added in Module 11 Phase 3 (Nakshatra Vedha / Sarvatobhadra Chakra).
    # A DIFFERENT system from the Rashi Vedha fields above — nakshatra-
    # based, not house-based, and not classified favorable/unfavorable
    # (Saravali presents it as a general obstruction relationship, not a
    # good/bad-house judgment). transit_nakshatra_sbc is the 28-system
    # (Abhijit-aware) nakshatra, scoped only to this feature — every
    # other nakshatra field in this app stays on the standard 27-system.
    # See packages/shared/sarvatobhadra_grid.py for sourcing.
    transit_nakshatra_sbc: str = ""
    has_nakshatra_vedha: bool = False
    nakshatra_vedha_planet: Optional[str] = None
    nakshatra_vedha_type: Optional[str] = None  # "forward" (direct) or "backward" (retrograde)
    nakshatra_vedha_target: Optional[str] = None  # the SBC nakshatra this planet's ray points at
    rule_version: str = "1.0"
