"""
Unit tests for Provenance Integrity and Traceability in Knowledge Reliability Framework.
"""

import uuid
import pytest

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    ProvenanceIntegrityError,
    ReviewStatus,
    ScholarlyEvaluation,
    SourceProvenance,
    SourceReliabilityTier,
    TechniqueFramework,
)
from apps.api.services.knowledge_reliability_engine import KnowledgeReliabilityEngine


@pytest.fixture
def engine():
    return KnowledgeReliabilityEngine()


@pytest.fixture
def sample_source(engine):
    src_id = uuid.uuid4()
    prov = SourceProvenance(
        edition_title="Brihat Jataka (V. Subrahmanya Sastri Ed.)",
        publisher="Mysore Government Press",
        publication_year=1929,
        editor_or_translator="V. Subrahmanya Sastri",
        is_critical_edition=True,
    )
    scholarly = ScholarlyEvaluation(
        tradition="Classical / Varahamihira",
        methodology_clarity_notes="Rigorous astronomical and astrological treatise.",
    )
    return engine.register_source(
        source_id=src_id,
        source_name="Brihat Jataka",
        tier=SourceReliabilityTier.AUTHENTICATED_CLASSICAL,
        provenance=prov,
        scholarly_eval=scholarly,
        review_status=ReviewStatus.PEER_REVIEWED,
    )


def test_provenance_traceability_query(engine, sample_source):
    """
    Answers: 'Where did this rule come from?'
    Verifies full end-to-end extraction metadata.
    """
    rule = engine.document_rule(
        rule_id="RULE-BJ-001",
        rule_name="Sun in 10th House Dignity",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=sample_source.source_id,
        passage_reference="Brihat Jataka Chapter 20, Sloka 3",
        original_text_excerpt="dashame ravi sthite...",
        extracted_by_actor_id="curator-ramesh",
        extracted_by_role=ActorRole.HUMAN_CURATOR,
        rule_definition_id="DEF-SUN-10H",
        source_name="Brihat Jataka",
    )

    trace = engine.get_rule_provenance_trace(rule.rule_id)

    assert trace["rule_id"] == "RULE-BJ-001"
    assert trace["source_name"] == "Brihat Jataka"
    assert trace["passage_reference"] == "Brihat Jataka Chapter 20, Sloka 3"
    assert trace["extracted_by_actor_id"] == "curator-ramesh"
    assert trace["extracted_by_role"] == ActorRole.HUMAN_CURATOR.value
    assert trace["rule_definition_id"] == "DEF-SUN-10H"


def test_missing_passage_or_excerpt_raises_provenance_error(engine, sample_source):
    """
    Ensures that empty or missing provenance fields reject rule documentation.
    """
    # Empty passage reference
    with pytest.raises(ProvenanceIntegrityError):
        engine.document_rule(
            rule_id="RULE-FAIL-01",
            rule_name="Bad Rule",
            technique_framework=TechniqueFramework.PARASHARI,
            source_id=sample_source.source_id,
            passage_reference="",
            original_text_excerpt="Some excerpt",
            extracted_by_actor_id="curator",
            extracted_by_role=ActorRole.HUMAN_CURATOR,
            rule_definition_id="DEF-01",
        )

    # Empty text excerpt
    with pytest.raises(ProvenanceIntegrityError):
        engine.document_rule(
            rule_id="RULE-FAIL-02",
            rule_name="Bad Rule 2",
            technique_framework=TechniqueFramework.PARASHARI,
            source_id=sample_source.source_id,
            passage_reference="Chapter 1, Sloka 1",
            original_text_excerpt="   ",
            extracted_by_actor_id="curator",
            extracted_by_role=ActorRole.HUMAN_CURATOR,
            rule_definition_id="DEF-02",
        )
