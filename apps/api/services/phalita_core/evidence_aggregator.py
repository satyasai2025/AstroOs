"""
AstroOS — Evidence Aggregator & Provenance Registry
===================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md (Step 9 & Provenance Tracking)
Aggregates fired rules, planetary coordinates, and varga diagnostics into verifiable Evidence Packages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.phalita_core.canonical_facts_generator import CanonicalFacts
from apps.api.services.phalita_core.shastric_rule_engine import (
    RuleEngineEvaluationResult,
    RuleEvaluationItem,
)


@dataclass(frozen=True)
class ProvenanceFactLink:
    fact_type: str              # "PLANET", "BHAVA", "VARGA", "CHARA_KARAKA", "UPAGRAHA"
    identifier: str             # e.g., "Jupiter", "House 10", "D9 Moon", "AK Saturn"
    recorded_value: str         # e.g., "Leo 29.65°", "28 SAV Bindus"
    supporting_rule_id: str


@dataclass(frozen=True)
class DomainEvidencePackage:
    domain: str
    target_date_iso: str
    primary_astronomical_anchors: Tuple[ProvenanceFactLink, ...]
    supporting_shastric_rules: Tuple[RuleEvaluationItem, ...]
    inhibiting_shastric_rules: Tuple[RuleEvaluationItem, ...]
    total_evidence_weight: float
    is_sufficient_for_prediction: bool
    evidence_provenance_hash: str


class EvidenceAggregator:
    """
    Constructs verifiable, audit-traceable DomainEvidencePackages.
    """

    @classmethod
    def aggregate_evidence(
        cls,
        facts: CanonicalFacts,
        rule_result: RuleEngineEvaluationResult,
    ) -> DomainEvidencePackage:
        """
        Builds domain evidence package linking every rule to its exact underlying facts.
        """
        fact_links: List[ProvenanceFactLink] = []

        for rule in rule_result.positive_promisers + rule_result.inhibiting_factors:
            fact_links.append(
                ProvenanceFactLink(
                    fact_type=rule.rule_category,
                    identifier=rule.rule_name,
                    recorded_value=rule.astronomical_evidence,
                    supporting_rule_id=rule.rule_id,
                )
            )

        total_weight = sum(r.confidence_weight * abs(r.signal_delta) for r in rule_result.positive_promisers + rule_result.inhibiting_factors)
        is_sufficient = len(rule_result.positive_promisers) + len(rule_result.inhibiting_factors) >= 2

        prov_hash = f"PROV-{facts.birth_datetime_utc.strftime('%Y%m%d')}-{rule_result.domain.upper()}-{len(fact_links)}"

        return DomainEvidencePackage(
            domain=rule_result.domain,
            target_date_iso=facts.target_evaluation_date.isoformat(),
            primary_astronomical_anchors=tuple(fact_links),
            supporting_shastric_rules=rule_result.positive_promisers,
            inhibiting_shastric_rules=rule_result.inhibiting_factors,
            total_evidence_weight=round(total_weight, 2),
            is_sufficient_for_prediction=is_sufficient,
            evidence_provenance_hash=prov_hash,
        )
