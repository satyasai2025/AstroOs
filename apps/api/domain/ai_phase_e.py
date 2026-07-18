"""
AstroOS — Phase E AI Domain Models

Extended domain objects for the AI Layer: chart comparison, research
assistant queries, and hypothesis generation.

All pure Python dataclasses — no ORM/Pydantic dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ChartComparisonRequest:
    """Two birth charts to compare side-by-side."""

    chart_a: Any  # D1Chart
    chart_b: Any  # D1Chart
    aspects_to_compare: tuple[str, ...] = (
        "ascendant", "planets", "houses", "yogas", "dashas", "strengths",
    )
    style: str = "concise"


@dataclass(frozen=True)
class ComparisonDimension:
    """One dimension of comparison between two charts."""

    dimension: str  # e.g. "ascendant", "sun", "moon", "yoga.ruchaka"
    chart_a_value: str
    chart_b_value: str
    similarity: float  # 0.0 = completely different, 1.0 = identical
    significance: str  # "high", "medium", "low"
    commentary: str = ""


@dataclass(frozen=True)
class ChartComparisonResult:
    """Side-by-side chart comparison with AI-generated insights."""

    summary: str
    overall_similarity: float
    key_differences: tuple[ComparisonDimension, ...]
    key_similarities: tuple[ComparisonDimension, ...]
    compatibility_notes: str = ""
    relationship_potential: str = ""
    timing_synergies: str = ""


@dataclass(frozen=True)
class ResearchQuery:
    """A natural language research query over the knowledge base."""

    question: str
    domain_filter: Optional[str] = None  # "graha", "bhava", "yoga", "dasha", etc.
    tradition_filter: Optional[str] = None  # "parashari", "jaimini", "kp", etc.
    max_results: int = 10


@dataclass(frozen=True)
class ResearchEvidence:
    """One piece of evidence supporting a research answer."""

    source: str
    reference: str
    text: str
    relevance: float
    entity_type: str  # "book", "verse", "rule", "karakatva", "conflict"
    tradition: Optional[str] = None


@dataclass(frozen=True)
class ResearchAnswer:
    """Answer to a natural language research query."""

    question: str
    summary: str
    body: str
    evidence: tuple[ResearchEvidence, ...] = field(default_factory=tuple)
    related_conflicts: tuple[str, ...] = field(default_factory=tuple)
    confidence: str = "medium"
    unanswered_aspects: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HypothesisTemplate:
    """A template for generating testable astrological hypotheses."""

    hypothesis_id: str
    title: str
    description: str
    domain: str
    conditions: tuple[str, ...]
    expected_outcome: str
    test_method: str
    classical_references: tuple[str, ...] = field(default_factory=tuple)
    priority: int = 5  # 1-10, higher = more important to test


@dataclass(frozen=True)
class GeneratedHypothesis:
    """A specific, testable hypothesis generated from chart data."""

    hypothesis_id: str
    title: str
    description: str
    domain: str
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    testable_prediction: str
    suggested_dataset: str  # e.g. "GC-MASTER", "RS-EVENT", "custom"
    priority: int
    related_rules: tuple[str, ...] = field(default_factory=tuple)
    related_yogas: tuple[str, ...] = field(default_factory=tuple)
    confidence: str = "medium"