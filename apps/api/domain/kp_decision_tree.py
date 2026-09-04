"""
AstroOS — KP Cuspal Sub-Lord Decision Tree Domain Objects (Module 19, Phase 4)

Pure dataclasses for:
1. 4-Tier Significator Matrix (Tiers A, B, C, D)
2. Cuspal Sub-Lord (CSL) Decision Node & Tree
3. 12th-from-Bhava Negation / Veto Analysis
4. Event-Specific Fructification Outcomes (Career, Marriage, Finance, Health)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class KPDecisionVerdict(str, Enum):
    PROMISED_FRUCTIFY = "PROMISED_FRUCTIFY"
    DELAYED_MODERATE = "DELAYED_MODERATE"
    VETOED_NEGATED = "VETOED_NEGATED"
    DENIED = "DENIED"


class KPEventDomain(str, Enum):
    CAREER = "Career"
    MARRIAGE = "Marriage"
    FINANCE = "Finance"
    HEALTH = "Health"
    GENERAL = "General"


@dataclass(frozen=True)
class KPTierSignificators:
    """4-Tier house significator structure per K.S. Krishnamurti."""
    house_number: int
    tier_a_planets: list[str]  # Planets in the constellation (star) of a planet occupying the house (STRONGEST)
    tier_b_planets: list[str]  # Planets occupying the house
    tier_c_planets: list[str]  # Planets in the constellation (star) of the house's sign lord
    tier_d_planets: list[str]  # House sign lord itself


@dataclass(frozen=True)
class KPCuspalSubLordDecisionNode:
    """
    Step-by-step decision node for a single house's Cuspal Sub-Lord.
    """
    house_number: int
    cusp_degree: float
    cusp_rashi: str
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    sub_lord_star_lord: str
    
    # 4-Tier houses signified by Sub-Lord
    primary_houses_signified: list[int]
    supporting_houses_signified: list[int]
    negating_houses_signified: list[int]  # 12th from primary house (e.g., 6th for marriage, 9th/5th for career)
    
    is_veto_active: bool
    verdict: KPDecisionVerdict
    verdict_explanation: str
    audit_chain: list[str]


@dataclass(frozen=True)
class KPEventDecisionTreeResult:
    """
    Event-specific KP Cuspal Sub-Lord analysis.
    """
    event_domain: KPEventDomain
    primary_cusp: int
    supporting_cusps: list[int]
    negating_cusps: list[int]
    
    cusp_node: KPCuspalSubLordDecisionNode
    supporting_significators: list[str]
    ruling_planets_agreement: list[str]
    
    fructification_verdict: KPDecisionVerdict
    summary_verdict: str
    technical_calculation_steps: list[str]
