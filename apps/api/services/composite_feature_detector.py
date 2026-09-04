"""
AstroOS — Structured Composite Feature Detector (Module 27)

Detects classical multi-fact astrological signatures and co-occurrences
against a case's Fact list, emitting structured CompositeFeature records
with full FactReference provenance (key, value, source).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Optional

from apps.api.domain.facts import Fact
from apps.api.domain.research_case import (
    CompositeFeature,
    ExtractedFeature,
    FactReference,
)


@dataclass(frozen=True)
class CompositeTemplate:
    """A pre-registered template defining a classical multi-factor pattern."""

    name: str
    description: str
    matcher: Callable[[dict[str, Fact]], Optional[list[FactReference]]]


def _match_dasha_maraka(facts: dict[str, Fact]) -> Optional[list[FactReference]]:
    """Dasha lord is currently a Maraka lord."""
    dasha_lord_fact = facts.get("dasha.current_lord")
    if not dasha_lord_fact or not dasha_lord_fact.value:
        return None
    lord = str(dasha_lord_fact.value).lower()
    maraka_fact = facts.get(f"maraka.lord.{lord}")
    if maraka_fact and maraka_fact.value is True:
        return [
            FactReference(dasha_lord_fact.key, dasha_lord_fact.value, dasha_lord_fact.source),
            FactReference(maraka_fact.key, maraka_fact.value, maraka_fact.source),
        ]
    return None


def _match_dasha_badhaka(facts: dict[str, Fact]) -> Optional[list[FactReference]]:
    """Dasha lord is currently the Badhaka lord."""
    dasha_lord_fact = facts.get("dasha.current_lord")
    badhaka_lord_fact = facts.get("badhaka.lord")
    if not dasha_lord_fact or not badhaka_lord_fact:
        return None
    if str(dasha_lord_fact.value).lower() == str(badhaka_lord_fact.value).lower():
        return [
            FactReference(dasha_lord_fact.key, dasha_lord_fact.value, dasha_lord_fact.source),
            FactReference(badhaka_lord_fact.key, badhaka_lord_fact.value, badhaka_lord_fact.source),
        ]
    return None


def _match_dasha_yogakaraka(facts: dict[str, Fact]) -> Optional[list[FactReference]]:
    """Dasha lord is currently a Yogakaraka."""
    dasha_lord_fact = facts.get("dasha.current_lord")
    if not dasha_lord_fact or not dasha_lord_fact.value:
        return None
    lord = str(dasha_lord_fact.value).lower()
    yk_fact = facts.get(f"functional.{lord}.yogakaraka")
    if yk_fact and yk_fact.value is True:
        return [
            FactReference(dasha_lord_fact.key, dasha_lord_fact.value, dasha_lord_fact.source),
            FactReference(yk_fact.key, yk_fact.value, yk_fact.source),
        ]
    return None


def _match_varga_dasha_kendra(facts: dict[str, Fact]) -> Optional[list[FactReference]]:
    """Dasha lord is placed in a Kendra (1, 4, 7, 10) in D9 Navamsha."""
    dasha_lord_fact = facts.get("dasha.current_lord")
    if not dasha_lord_fact or not dasha_lord_fact.value:
        return None
    lord = str(dasha_lord_fact.value).lower()
    varga_house_fact = facts.get(f"varga.{lord}.D9.house")
    if varga_house_fact and varga_house_fact.value in (1, 4, 7, 10):
        return [
            FactReference(dasha_lord_fact.key, dasha_lord_fact.value, dasha_lord_fact.source),
            FactReference(varga_house_fact.key, varga_house_fact.value, varga_house_fact.source),
        ]
    return None


def _match_sbc_active_vedha(facts: dict[str, Fact]) -> Optional[list[FactReference]]:
    """Transiting planet has active Sarvatobhadra Chakra Vedha ray."""
    for key, fact in facts.items():
        if key.startswith("sbc.") and key.endswith(".vedha.active") and fact.value is True:
            planet = key.split(".")[1]
            pos_fact = facts.get(f"sbc.{planet}.position")
            refs = [FactReference(fact.key, fact.value, fact.source)]
            if pos_fact:
                refs.append(FactReference(pos_fact.key, pos_fact.value, pos_fact.source))
            return refs
    return None


DEFAULT_COMPOSITE_TEMPLATES: list[CompositeTemplate] = [
    CompositeTemplate(
        name="dasha_maraka_activation",
        description="Dasha lord is simultaneously a classical Maraka lord",
        matcher=_match_dasha_maraka,
    ),
    CompositeTemplate(
        name="dasha_badhaka_activation",
        description="Dasha lord is simultaneously the Badhaka lord",
        matcher=_match_dasha_badhaka,
    ),
    CompositeTemplate(
        name="dasha_yogakaraka_activation",
        description="Dasha lord is simultaneously a functional Yogakaraka",
        matcher=_match_dasha_yogakaraka,
    ),
    CompositeTemplate(
        name="dasha_varga_kendra_confluence",
        description="Dasha lord occupies a Kendra house in D9 Navamsha",
        matcher=_match_varga_dasha_kendra,
    ),
    CompositeTemplate(
        name="sbc_active_vedha_transit",
        description="Transiting planet casts an active SBC Vedha ray",
        matcher=_match_sbc_active_vedha,
    ),
]


class CompositeFeatureDetector:
    """Detects multi-fact composite signatures across case facts."""

    def __init__(
        self,
        templates: list[CompositeTemplate] | None = None,
    ) -> None:
        self._templates = templates or list(DEFAULT_COMPOSITE_TEMPLATES)

    def detect_for_facts(
        self,
        facts: list[Fact],
        *,
        research_case_id: str,
        event_type: str,
        event_date: date,
    ) -> list[CompositeFeature]:
        facts_by_key = {f.key: f for f in facts}
        results: list[CompositeFeature] = []

        for template in self._templates:
            matched_components = template.matcher(facts_by_key)
            if matched_components:
                results.append(
                    CompositeFeature(
                        composite_name=template.name,
                        components=matched_components,
                        research_case_id=research_case_id,
                        event_type=event_type,
                        event_date=event_date,
                    )
                )
        return results

    @staticmethod
    def to_extracted_features(
        composite_features: list[CompositeFeature],
    ) -> list[ExtractedFeature]:
        """Maps structured CompositeFeatures into ExtractedFeatures for PatternDiscoveryEngine."""
        features: list[ExtractedFeature] = []
        for comp in composite_features:
            features.append(
                ExtractedFeature(
                    feature_name=f"composite_{comp.composite_name}",
                    feature_value=True,
                    feature_category="composite",
                    event_type=comp.event_type,
                    research_case_id=comp.research_case_id,
                    event_date=comp.event_date,
                    confidence=comp.confidence,
                )
            )
        return features
