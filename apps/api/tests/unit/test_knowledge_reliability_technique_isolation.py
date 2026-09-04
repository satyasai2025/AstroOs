"""
Unit tests for Technique Framework Boundary Isolation in Knowledge Reliability Framework.
"""

import uuid
import pytest

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    SourceProvenance,
    SourceReliabilityTier,
    TechniqueFramework,
    TechniqueIsolationError,
)
from apps.api.services.knowledge_reliability_engine import KnowledgeReliabilityEngine


def test_technique_framework_isolation_raises_error_on_cross_framework_mixing():
    """
    Ensures that evaluating rules from different technique frameworks without an adapter raises TechniqueIsolationError.
    """
    engine = KnowledgeReliabilityEngine()
    src_id = uuid.uuid4()
    engine.register_source(
        source_id=src_id,
        source_name="KP Readers 1-6",
        tier=SourceReliabilityTier.SCHOLARLY_COMMENTARY,
        provenance=SourceProvenance(edition_title="KP Reader", publisher="Krishnamurti Publications"),
        scholarly_eval=None,
    )

    # Document a KP System rule (sub-lord cuspal principle)
    engine.document_rule(
        rule_id="RULE-KP-SUB-01",
        rule_name="7th Cusp Sub-Lord Signification",
        technique_framework=TechniqueFramework.KP_SYSTEM,
        source_id=src_id,
        passage_reference="KP Reader 4, Page 45",
        original_text_excerpt="7th cusp sub lord signifies 2, 7, 11...",
        extracted_by_actor_id="curator",
        extracted_by_role=ActorRole.HUMAN_CURATOR,
        rule_definition_id="DEF-KP-SUB-01",
    )

    # Document a Jaimini rule (Chara Karaka replacement)
    engine.document_rule(
        rule_id="RULE-JAIMINI-DK-01",
        rule_name="Dara Karaka Marriage Signification",
        technique_framework=TechniqueFramework.JAIMINI,
        source_id=src_id,
        passage_reference="Jaimini Sutras 1.2",
        original_text_excerpt="darakaraka sambandha...",
        extracted_by_actor_id="curator",
        extracted_by_role=ActorRole.HUMAN_CURATOR,
        rule_definition_id="DEF-JM-DK-01",
    )

    # 1. Compatible check for KP alone -> Passes
    assert engine.validate_technique_compatibility(["RULE-KP-SUB-01"], TechniqueFramework.KP_SYSTEM) is True

    # 2. Incompatible check: Attempting to evaluate KP rule under Jaimini framework -> Fails
    with pytest.raises(TechniqueIsolationError) as exc_info:
        engine.validate_technique_compatibility(["RULE-KP-SUB-01"], TechniqueFramework.JAIMINI)
    assert "cannot be evaluated under target framework 'Jaimini'" in str(exc_info.value)

    # 3. Mixing KP rule and Jaimini rule under Parashari -> Fails
    with pytest.raises(TechniqueIsolationError):
        engine.validate_technique_compatibility(
            ["RULE-KP-SUB-01", "RULE-JAIMINI-DK-01"],
            TechniqueFramework.PARASHARI,
        )
