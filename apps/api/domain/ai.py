"""
AstroOS — AI Domain Objects (Module 24, Phase 1)

Natural language generation from existing domain objects.
Template-based — no external LLM, no network calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class Citation:
    """A reference to a classical text or knowledge base entry."""

    source: str
    reference: str
    text: str
    relevance: float = 0.0


@dataclass(frozen=True)
class AIResponse:
    """
    Shared return type for all generators.

    Contains structured natural language output with citations,
    sources, recommendations, and deterministic confidence.
    """

    response_type: str
    title: str
    summary: str
    body: str
    citations: tuple[Citation, ...] = field(default_factory=tuple)
    sources: tuple[str, ...] = field(default_factory=tuple)
    recommendations: tuple[str, ...] = field(default_factory=tuple)
    confidence: str = "medium"
    version: str = "1.0"


@dataclass(frozen=True)
class ExplanationRequest:
    """What to explain and how."""

    topic: str
    source_data: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    style: str = "concise"
    max_length: int = 500
