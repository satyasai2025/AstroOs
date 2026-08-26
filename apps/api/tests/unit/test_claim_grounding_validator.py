"""
AstroOS - Unit Tests for ClaimGroundingValidator
"""

import uuid
import pytest
from datetime import datetime, timezone

from apps.api.domain.knowledge_ingestion import (
    EvidencePackage,
    RetrievalFilter,
    RetrievalMethod,
    RetrievedEvidenceItem,
)
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    RuleLifecycleState,
    TechniqueFramework,
)
from apps.api.services.claim_grounding_validator import ClaimGroundingValidator


@pytest.fixture
def sample_evidence_package():
    item1 = RetrievedEvidenceItem(
        item_id="CHK-BPHS-001",
        content="When Jupiter is in a Kendra (1st, 4th, 7th, or 10th house) from Moon, Gaja Kesari Yoga is formed.",
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
    return EvidencePackage(
        package_id="EP-TEST-001",
        query="Gaja Kesari Yoga",
        retrieval_method=RetrievalMethod.HYBRID_RRF,
        filters_applied={},
        retrieved_items=(item1,),
        warnings=(),
        total_items_matched=1,
        generated_at=datetime.now(timezone.utc),
    )


def test_grounded_synthesis_passes_validation(sample_evidence_package):
    grounded_text = (
        "According to classical sources [1], Gaja Kesari Yoga is formed when Jupiter occupies a Kendra "
        "house from Moon (1st, 4th, 7th, or 10th). This is documented in Brihat Parashara Hora Shastra."
    )
    eval_result = ClaimGroundingValidator.validate_grounding(grounded_text, sample_evidence_package)
    assert eval_result.is_grounded is True
    assert eval_result.faithfulness_score >= 0.85
    assert len(eval_result.unsupported_claims) == 0


def test_hallucinated_unsupported_claim_fails_validation(sample_evidence_package):
    hallucinated_text = (
        "According to passage [1], Jupiter in 10th gives Gaja Kesari. "
        "Furthermore, Rahu in the 8th house causes immediate financial ruin [5], "
        "and Saturn aspecting Venus creates a powerful Dhana Yoga."
    )
    eval_result = ClaimGroundingValidator.validate_grounding(hallucinated_text, sample_evidence_package)
    assert eval_result.is_grounded is False
    assert eval_result.faithfulness_score < 0.80
    assert len(eval_result.unsupported_claims) > 0
    assert "[5]" in eval_result.citation_validity
    assert eval_result.citation_validity["[5]"] is False
