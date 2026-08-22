"""
AstroOS — Classical Rule Evidence Domain Objects (Module 19, Phase 3)

Defines domain dataclasses for:
1. Canonical Classical Source Citations (BPHS, Saravali, Jaimini, Brihat Jataka, Phaladeepika)
2. Atomic Astrological Condition Requirements (predicates & parameters)
3. Computed Chart Evidence Items (Grahas, Bhavas, Rashis, Dignities)
4. Deterministic 5-Stage Rule Evidence Chains
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EvidenceVerificationStatus(str, Enum):
    SATISFIED = "SATISFIED"
    PARTIALLY_SATISFIED = "PARTIALLY_SATISFIED"
    CANCELLED_AFFLICTED = "CANCELLED_AFFLICTED"
    NOT_PRESENT = "NOT_PRESENT"
    UNVERIFIED = "UNVERIFIED"


class ClassicalTradition(str, Enum):
    PARASHARI = "Parashari"
    JAIMINI = "Jaimini"
    VARAHAMIHIRA = "Varahamihira"
    MANTRISHA = "Mantreswara"
    GENERAL_CLASSICAL = "General Classical"


@dataclass(frozen=True)
class ClassicalSourceCitation:
    """
    Authentic canonical Sanskrit citation from recognized classical literature.
    Never fabricated. If unverified against source text, marked is_verified=False.
    """
    book_title: str  # e.g., "Brihat Parashara Hora Shastra", "Saravali", "Jaimini Upadesha Sutras"
    author: str  # e.g., "Maharishi Parashara", "Kalyanavarma", "Maharishi Jaimini"
    chapter: int  # Chapter number
    chapter_name: str  # Sanskrit chapter title
    sloka_range: str  # e.g., "Sloka 12-15" or "Sutra 1.3.15"
    sanskrit_iast: str  # Authentic IAST transliteration of Sanskrit verse
    sanskrit_devanagari: str  # Sanskrit Devanagari script
    translation_english: str  # Scholarly translation
    tradition: ClassicalTradition
    commentary_notes: Optional[str] = None
    is_verified: bool = True


@dataclass(frozen=True)
class ConditionRequirement:
    """
    Atomic condition that must be satisfied for the classical rule to manifest.
    """
    condition_id: str
    description: str
    condition_type: str  # "planet_in_house", "planet_in_sign", "mutual_aspect", "kendra_relationship", "argala", "dignity_threshold"
    required_parameters: dict[str, Any] = field(default_factory=dict)
    is_mandatory: bool = True


@dataclass(frozen=True)
class ChartEvidenceItem:
    """
    Actual computed chart condition extracted deterministically from the subject's D1 chart.
    """
    condition_id: str
    is_satisfied: bool
    actual_chart_value: str  # e.g., "Jupiter at 14°22' Cancer in 1st House (Exalted)"
    notes: str = ""
    contributing_planets: list[str] = field(default_factory=list)
    contributing_houses: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class CancellationFactor:
    """
    Classical condition that diminishes or cancels (bhanga) the yoga/rule.
    """
    factor_id: str
    description: str
    classical_reference: str
    is_active: bool
    impact_deduction: float  # Score penalty (e.g. -25%)


@dataclass(frozen=True)
class RuleEvidenceChain:
    """
    Complete deterministic 5-stage classical rule evidence chain:
      Step 1: Rule Definition & Taxonomy
      Step 2: Canonical Sanskrit Source Citation
      Step 3: Required Classical Conditions
      Step 4: Actual Computed Chart Evidence
      Step 5: Fructification Verdict, Strength Score (0-100), and Cancellation Factors
    """
    rule_id: str
    rule_name: str
    category: str  # "Raja Yoga", "Dhana Yoga", "Pancha Mahapurusha", "Arishta Yoga", "Neecha Bhanga", "Jaimini Karakamsha"
    brief_description: str
    citation: ClassicalSourceCitation
    required_conditions: list[ConditionRequirement]
    actual_evidence: list[ChartEvidenceItem]
    status: EvidenceVerificationStatus
    strength_score: float  # 0.0 to 100.0
    cancellation_factors: list[CancellationFactor]
    fructification_summary: str
    audit_trace: list[str]
