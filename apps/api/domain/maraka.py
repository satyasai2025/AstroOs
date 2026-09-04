"""
AstroOS — Domain Models for Maraka, Badhaka, and Sambandha
===========================================================
Source: Vinay Jha's Kundalee (Phalit.kkk - A16_Sambandh, A10_Aayu, frmPhalaadesh, frmArgala)
and BPHS Chapters 44, 46, 50.

Configurable (Flexible / Non-hardcoded) architecture:
  - Configurable Maraka tier threshold (5-tier strict vs 4-tier / 3-tier crisis)
  - Configurable inclusion of Trik lords (6th, 8th, 12th)
  - Configurable Saturn Ayushkaraka absorption rule
  - Configurable Badhaka modality rules
  - Configurable Sambandha types (Parivartana, Yuti, Drishti, Dispositorship)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class SambandhaType(str, Enum):
    PARIVARTANA = "parivartana"      # Mutual Reception / Exchange of houses
    YUTI = "yuti"                    # Conjunction in same house
    MUTUAL_DRISHTI = "mutual_drishti"# Mutual aspect
    DRISHTI = "drishti"              # One-way aspect
    DISPOSITOR = "dispositor"        # Placed in the other's sign


class LagnaModality(str, Enum):
    CHARA = "chara"          # Movable (Aries, Cancer, Libra, Capricorn)
    STHIRA = "sthira"        # Fixed (Taurus, Leo, Scorpio, Aquarius)
    DVISVABHAVA = "dvisvabhava" # Dual (Gemini, Virgo, Sagittarius, Pisces)


@dataclass(frozen=True)
class MarakaConfig:
    """Flexible configuration parameters for Maraka and Death timing."""
    include_2nd_7th: bool = True               # Primary classical Marakas (2H & 7H)
    include_trik_lords: bool = True            # Secondary Marakas (6H, 8H, 12H lords)
    include_saturn_override: bool = True       # Saturn conjunct/aspecting Maraka acts as Maraka
    min_tiers_for_death_risk: int = 5          # Strict Jha rule: all 5 tiers (MD..PrD)
    min_tiers_for_health_crisis: int = 3       # Configurable warning threshold (e.g. 3 or 4)
    require_distinct_grahas: bool = True       # Jha axiom: 5 lords should be distinct planets
    min_distinct_grahas: int = 4               # At least 4 distinct planets if require_distinct is True
    tatkalika_enemy_weight_multiplier: float = 1.25 # Risk elevated if MD and AD lords are Tatkalika Shatru


@dataclass(frozen=True)
class BadhakaConfig:
    """Flexible configuration for Badhaka obstruction rules."""
    chara_badhaka_house: int = 11   # 11th from Chara Lagna
    sthira_badhaka_house: int = 9    # 9th from Sthira Lagna
    dvi_badhaka_house: int = 7       # 7th from Dvisvabhava Lagna
    enable_rajayoga_badha: bool = True # Badhakesh can obstruct Kendresh-Trikonesh Rajayogas


@dataclass(frozen=True)
class MarakaEvaluationResult:
    is_maraka_active: bool
    risk_level: str                 # "CRITICAL_MORTALITY_RISK", "SEVERE_HEALTH_CRISIS", "MODERATE_OBSTRUCTION", "SAFE"
    active_tier_count: int          # Number of tiers matching Maraka criteria (0..5)
    matched_tiers: dict[str, str]   # {"MD": "saturn", "AD": "mars", ...}
    distinct_graha_count: int       # Number of unique planets in the 5-tier window
    are_grahas_distinct: bool
    tatkalika_relation_md_ad: str   # "mitra", "sama", "shatru"
    saturn_absorbed_maraka: bool
    d30_confirmation: bool
    trace: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BadhakaEvaluationResult:
    lagna_rashi: str
    lagna_modality: LagnaModality
    badhaka_house: int
    badhakesh_planet: str
    is_badhakesh_in_dasha: bool
    obstructed_houses: list[int]
    obstructed_rajayogas: list[str]
    trace: list[str] = field(default_factory=list)