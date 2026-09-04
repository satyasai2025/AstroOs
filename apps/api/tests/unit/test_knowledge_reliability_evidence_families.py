"""
Unit tests for Evidence Families and Anti-Double Counting in Knowledge Reliability Framework.
"""

import uuid
import pytest

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    SourceProvenance,
    SourceReliabilityTier,
    TechniqueFramework,
)
from apps.api.services.knowledge_reliability_engine import KnowledgeReliabilityEngine


@pytest.fixture
def engine():
    eng = KnowledgeReliabilityEngine()
    src_id = uuid.uuid4()
    eng.register_source(
        source_id=src_id,
        source_name="Brihat Parashara Hora Shastra",
        tier=SourceReliabilityTier.AUTHENTICATED_CLASSICAL,
        provenance=SourceProvenance(
            edition_title="BPHS Santhanam",
            publisher="Ranjan",
        ),
        scholarly_eval=None,
    )
    return eng, src_id


def test_evidence_family_collapses_derivative_rules_to_one_dof(engine):
    """
    Multiple derivative rules sharing the same underlying astrological principle
    must not count as separate independent confirmations.
    """
    eng, src_id = engine

    # Register evidence family for Jupiter-Moon mutual angles (Gajakesari core principle)
    fam = eng.register_evidence_family(
        family_id="FAM-JUP-MOON-KENDRA",
        name="Jupiter-Moon Angular Mutual Kendra Family",
        underlying_principle="Jupiter and Moon in mutual kendras generate public prominence and clarity.",
        tradition=TechniqueFramework.PARASHARI,
        member_rule_ids=[
            "RULE-GK-1H-4H",
            "RULE-GK-1H-7H",
            "RULE-GK-1H-10H",
            "RULE-GK-MOON-LAGNA",
        ],
        max_independent_dof=1,
    )

    # Document 4 rules belonging to this family
    for r_id, name, pass_ref in [
        ("RULE-GK-1H-4H", "Jupiter 4th from Moon", "BPHS Ch 35, Sloka 1"),
        ("RULE-GK-1H-7H", "Jupiter 7th from Moon", "BPHS Ch 35, Sloka 1"),
        ("RULE-GK-1H-10H", "Jupiter 10th from Moon", "BPHS Ch 35, Sloka 2"),
        ("RULE-GK-MOON-LAGNA", "Jupiter 1st with Moon", "BPHS Ch 35, Sloka 2"),
    ]:
        eng.document_rule(
            rule_id=r_id,
            rule_name=name,
            technique_framework=TechniqueFramework.PARASHARI,
            source_id=src_id,
            passage_reference=pass_ref,
            original_text_excerpt="kendrasthite devagurau...",
            extracted_by_actor_id="curator",
            extracted_by_role=ActorRole.HUMAN_CURATOR,
            rule_definition_id=f"DEF-{r_id}",
            evidence_family_id=fam.family_id,
        )

    # Document a 5th standalone rule from a completely different principle
    eng.document_rule(
        rule_id="RULE-SUN-10H-DIGBALA",
        rule_name="Sun in 10th Digbala",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=src_id,
        passage_reference="BPHS Ch 3, Sloka 25",
        original_text_excerpt="dashame surya...",
        extracted_by_actor_id="curator",
        extracted_by_role=ActorRole.HUMAN_CURATOR,
        rule_definition_id="DEF-SUN-DIGBALA",
        evidence_family_id=None,  # Standalone
    )

    matched_rules = [
        "RULE-GK-1H-4H",
        "RULE-GK-1H-7H",
        "RULE-GK-1H-10H",
        "RULE-GK-MOON-LAGNA",
        "RULE-SUN-10H-DIGBALA",
    ]

    analysis = eng.calculate_independent_confirmations(matched_rules)

    assert analysis["total_rules_matched"] == 5
    # 4 family rules collapsed to 1 DOF + 1 standalone rule = 2 independent confirmations
    assert analysis["independent_confirmations_dof"] == 2
    assert analysis["standalone_rules_count"] == 1
    assert "FAM-JUP-MOON-KENDRA" in analysis["family_breakdown"]
    assert analysis["family_breakdown"]["FAM-JUP-MOON-KENDRA"]["matched_rules_count"] == 4
    assert analysis["family_breakdown"]["FAM-JUP-MOON-KENDRA"]["contributed_independent_dof"] == 1
