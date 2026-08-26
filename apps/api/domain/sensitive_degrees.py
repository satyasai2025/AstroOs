"""
AstroOS — Sensitive Degrees Domain Objects

Models for:
1. 64th Navamsha (from Moon and Lagna) & Khara Lord (D9)
2. 22nd Drekkana & Khara Lord (D3)
3. Mrityu Bhaga (Fatal degree evaluation)
4. Pushkara Bhaga & Pushkara Navamsha
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class KharaLordsResult:
    """64th Navamsha and 22nd Drekkana calculation results."""
    moon_64th_navamsha_rashi: str
    moon_64th_navamsha_lord: str
    moon_64th_navamsha_longitude: float

    lagna_64th_navamsha_rashi: str
    lagna_64th_navamsha_lord: str
    lagna_64th_navamsha_longitude: float

    lagna_22nd_drekkana_rashi: str
    lagna_22nd_drekkana_lord: str
    lagna_22nd_drekkana_longitude: float


@dataclass(frozen=True)
class MrityuBhagaEvaluation:
    """Evaluation of a single planet / lagna for Mrityu Bhaga fatal degree."""
    point: str  # planet name or "lagna"
    rashi: str
    rashi_degree: float
    mrityu_degree: float
    orb_distance: float
    is_in_mrityu_bhaga: bool  # True if within specified orb (default 1.0 deg)


@dataclass(frozen=True)
class PushkaraEvaluation:
    """Evaluation of a single planet / lagna for Pushkara Navamsha and Pushkara Bhaga."""
    point: str
    rashi: str
    rashi_degree: float
    navamsha_rashi: str
    navamsha_lord: str
    is_pushkara_navamsha: bool
    pushkara_bhaga_degree: float
    orb_distance_to_bhaga: float
    is_in_pushkara_bhaga: bool  # True if within 1.0 deg of pushkara bhaga


@dataclass(frozen=True)
class SensitiveDegreesSnapshot:
    """Comprehensive sensitive degrees analysis for a chart."""
    khara_lords: KharaLordsResult
    mrityu_bhagas: tuple[MrityuBhagaEvaluation, ...]
    pushkara_evaluations: tuple[PushkaraEvaluation, ...]
    rule_version: str = "1.0"
