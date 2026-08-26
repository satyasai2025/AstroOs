"""
AstroOS - Unit Tests for AIEvaluationFramework
"""

import uuid
import pytest
from datetime import datetime, timezone

from apps.api.domain.knowledge_ingestion import (
    EvidencePackage,
    GroundedQAResponse,
    RetrievalMethod,
    RetrievedEvidenceItem,
)
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    RuleLifecycleState,
    TechniqueFramework,
)
from apps.api.services.ai_evaluation_framework import AIEvaluationFramework


@pytest.fixture
def sample_grounded_qa_response():
    item1 = RetrievedEvidenceItem(
        item_id="CHK-BPHS-001",
        content="When Jupiter is in a Kendra (1, 4, 7, 10) from Moon, Gaja Kesari Yoga is formed.",
        source_title="Brihat Parashara Hora Shastra",
        source_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        passage_reference="BPHS:Ch35:v3-4",
        provenance_chain={"document_id": "doc-1", "chapter_section": "Ch35", "page_location": "p200"},
        technique_framework=TechniqueFramework.PARASHARI,
        lifecycle_state=RuleLifecycleState.DOCUMENTED,
        evidence_level=EvidenceLevel.UNVALIDATED,
        relevance_score=0.95,
        retrieval_metadata={"grahas": ["jupiter", "moon"], "bhavas": [1, 4, 7, 10]},
    )
    pkg = EvidencePackage(
        package_id="EP-TEST-001",
        query="Gaja Kesari Yoga",
        retrieval_method=RetrievalMethod.HYBRID_RRF,
        filters_applied={},
        retrieved_items=(item1,),
        warnings=(),
        total_items_matched=1,
        generated_at=datetime.now(timezone.utc),
    )
    return GroundedQAResponse(
        response_id="QA-TEST-001",
        question="How is Gaja Kesari Yoga formed?",
        evidence_package=pkg,
        source_facts=("[1] BPHS:Ch35:v3-4 (DOCUMENTED): When Jupiter is in a Kendra from Moon...",),
        grounded_synthesis="Based on classical text [1], Gaja Kesari Yoga is formed when Jupiter is placed in a Kendra (1st, 4th, 7th, 10th house) from Moon.",
        governance_disclosure="GOVERNANCE DISCLOSURE: IMPORTANT: This response is NOT an astrological prediction.",
        is_astrological_prediction=False,
    )


def test_ai_evaluation_benchmark_pass(sample_grounded_qa_response):
    """A fully grounded, cited, anti-contaminated QA response passes all 5 benchmark criteria."""
    result = AIEvaluationFramework.evaluate_qa_response(
        qa_response=sample_grounded_qa_response,
        expected_technique=TechniqueFramework.PARASHARI,
    )
    assert result.overall_pass is True
    assert result.faithfulness_score >= 0.80
    assert result.citation_precision == 1.0
    assert result.technique_isolation_passed is True
    assert result.anti_contamination_verified is True
    assert "PASS" in result.summary


def test_ai_evaluation_fails_on_contamination_violation(sample_grounded_qa_response):
    """If an AI response attempts to claim it is an astrological prediction, it is rejected."""
    bad_qa = GroundedQAResponse(
        response_id="QA-BAD",
        question=sample_grounded_qa_response.question,
        evidence_package=sample_grounded_qa_response.evidence_package,
        source_facts=sample_grounded_qa_response.source_facts,
        grounded_synthesis=sample_grounded_qa_response.grounded_synthesis,
        governance_disclosure="",
        is_astrological_prediction=True,  # VIOLATION
    )
    result = AIEvaluationFramework.evaluate_qa_response(bad_qa)
    assert result.overall_pass is False
    assert result.anti_contamination_verified is False
