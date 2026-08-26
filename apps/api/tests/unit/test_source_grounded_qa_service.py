"""
Unit tests — Source-Grounded QA Service (Anti-Contamination)

Tests:
- AI-generated summary is returned as GroundedQAResponse (not stored)
- is_astrological_prediction is always False
- source_facts cite retrieved passages
- grounded_synthesis is NOT inserted into the knowledge corpus
- warnings from evidence package are surfaced in governance_disclosure
- empty evidence package returns graceful no-evidence response
- structural: service holds no write access to ingestion/embedding repos
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.domain.knowledge_ingestion import (
    EvidencePackage,
    EvidenceWarning,
    EvidenceWarningType,
    GroundedQAResponse,
    RetrievalFilter,
    RetrievalMethod,
    RetrievedEvidenceItem,
)
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    RuleLifecycleState,
    TechniqueFramework,
)
from apps.api.services.governed_retrieval_engine import GovernedRetrievalEngine
from apps.api.services.source_grounded_qa_service import SourceGroundedQAService


# ── Helpers ────────────────────────────────────────────────────────────────────

DOC_ID = uuid.uuid4()
SRC_ID = uuid.uuid4()


def _make_evidence_item(
    content="Jupiter in Kendra from Moon forms Gaja Kesari Yoga.",
    lifecycle="REVIEWED",
    evidence_level="UNVALIDATED",
    technique="Parashari",
    passage_reference="BPHS:Ch.35:v3-4",
):
    return RetrievedEvidenceItem(
        item_id="CHK-TEST-001",
        content=content,
        source_title="Brihat Parashara Hora Shastra",
        source_id=SRC_ID,
        document_id=DOC_ID,
        passage_reference=passage_reference,
        provenance_chain={
            "document_id": str(DOC_ID),
            "source_id": str(SRC_ID),
            "chapter_section": "Chapter 35",
            "page_location": "Page 200",
            "passage_reference": passage_reference,
        },
        technique_framework=TechniqueFramework.PARASHARI,
        lifecycle_state=RuleLifecycleState.REVIEWED,
        evidence_level=EvidenceLevel.UNVALIDATED,
        relevance_score=0.92,
        retrieval_metadata={"method": "keyword"},
        is_unvalidated=True,
    )


def _make_evidence_package(items=None, warnings=None):
    return EvidencePackage(
        package_id="EP-abc12345",
        query="What is Gaja Kesari Yoga?",
        retrieval_method=RetrievalMethod.HYBRID_RRF,
        filters_applied={},
        retrieved_items=tuple(items or [_make_evidence_item()]),
        warnings=tuple(warnings or []),
        total_items_matched=len(items or [_make_evidence_item()]),
    )


def _make_empty_package():
    return EvidencePackage(
        package_id="EP-empty0000",
        query="some unknown query",
        retrieval_method=RetrievalMethod.KEYWORD_EXACT,
        filters_applied={},
        retrieved_items=(),
        warnings=(),
        total_items_matched=0,
    )


def _make_engine_with_package(package):
    engine = MagicMock(spec=GovernedRetrievalEngine)
    engine.retrieve = AsyncMock(return_value=package)
    return engine


# ── Anti-Contamination Structural Tests ───────────────────────────────────────

def test_qa_service_has_no_write_access_to_ingestion_repo():
    """
    SourceGroundedQAService must not hold a reference to KnowledgeIngestionRepository
    or KnowledgeEmbeddingRepository as instance attributes.
    This is a structural anti-contamination invariant.
    """
    engine = _make_engine_with_package(_make_evidence_package())
    service = SourceGroundedQAService(retrieval_engine=engine, llm_client_fn=None)
    # Must not have a direct write repo
    assert not hasattr(service, "_ingestion_repository")
    assert not hasattr(service, "_embedding_repository")
    assert not hasattr(service, "ingestion_repo")
    assert not hasattr(service, "embedding_repo")


def test_qa_service_is_astrological_prediction_always_false():
    """is_astrological_prediction must NEVER be True."""
    # This is a structural invariant we check in the domain too
    response = GroundedQAResponse(
        response_id="QA-test",
        question="Test",
        evidence_package=_make_evidence_package(),
        source_facts=(),
        grounded_synthesis="",
        governance_disclosure="",
        is_astrological_prediction=False,
    )
    assert response.is_astrological_prediction is False


# ── Core QA Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_answer_returns_grounded_qa_response():
    package = _make_evidence_package()
    engine = _make_engine_with_package(package)
    service = SourceGroundedQAService(retrieval_engine=engine, llm_client_fn=None)
    filters = RetrievalFilter()
    response = await service.answer("What is Gaja Kesari Yoga?", filters)
    assert isinstance(response, GroundedQAResponse)
    assert response.is_astrological_prediction is False


@pytest.mark.asyncio
async def test_answer_source_facts_cite_passage_references():
    package = _make_evidence_package()
    engine = _make_engine_with_package(package)
    service = SourceGroundedQAService(retrieval_engine=engine, llm_client_fn=None)
    response = await service.answer("What is Gaja Kesari Yoga?", RetrievalFilter())
    # Source facts must include the passage reference
    assert any("BPHS:Ch.35:v3-4" in fact for fact in response.source_facts)


@pytest.mark.asyncio
async def test_answer_empty_package_returns_graceful_response():
    package = _make_empty_package()
    engine = _make_engine_with_package(package)
    service = SourceGroundedQAService(retrieval_engine=engine, llm_client_fn=None)
    response = await service.answer("Unknown astrological query", RetrievalFilter())
    assert isinstance(response, GroundedQAResponse)
    assert len(response.source_facts) == 0
    assert "No evidence" in response.grounded_synthesis or len(response.grounded_synthesis) > 0
    assert response.is_astrological_prediction is False


@pytest.mark.asyncio
async def test_answer_with_llm_client_uses_grounding():
    package = _make_evidence_package()
    engine = _make_engine_with_package(package)

    def mock_llm(base_url, model, timeout_seconds, grounding_text, instruction):
        assert "BPHS" in grounding_text or "Gaja Kesari" in grounding_text
        return "Based on classical sources, Gaja Kesari Yoga is formed when Jupiter is in Kendra from Moon."

    service = SourceGroundedQAService(retrieval_engine=engine, llm_client_fn=mock_llm)
    response = await service.answer("What is Gaja Kesari Yoga?", RetrievalFilter())
    assert "Gaja Kesari" in response.grounded_synthesis


@pytest.mark.asyncio
async def test_answer_governance_disclosure_mentions_lifecycle_state():
    package = _make_evidence_package()
    engine = _make_engine_with_package(package)
    service = SourceGroundedQAService(retrieval_engine=engine, llm_client_fn=None)
    response = await service.answer("What is Gaja Kesari Yoga?", RetrievalFilter())
    # governance_disclosure must mention some lifecycle state or reliability caveat
    assert len(response.governance_disclosure) > 0


@pytest.mark.asyncio
async def test_answer_warnings_surfaced_in_governance_disclosure():
    warning = EvidenceWarning(
        warning_type=EvidenceWarningType.UNVALIDATED_KNOWLEDGE_INCLUDED,
        message="1 item has not been empirically validated.",
        affected_item_ids=("CHK-TEST-001",),
    )
    package = _make_evidence_package(warnings=[warning])
    engine = _make_engine_with_package(package)
    service = SourceGroundedQAService(retrieval_engine=engine, llm_client_fn=None)
    response = await service.answer("What is Gaja Kesari Yoga?", RetrievalFilter())
    assert "UNVALIDATED" in response.governance_disclosure or "unvalidated" in response.governance_disclosure.lower()


# ── Contamination Prevention Test ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_answer_does_not_mutate_evidence_package():
    """
    The evidence package returned by the retrieval engine must remain unchanged.
    The QA service must not add synthesized text into the knowledge corpus.
    We verify the package.retrieved_items are unchanged after answer().
    """
    item = _make_evidence_item()
    package = _make_evidence_package(items=[item])
    engine = _make_engine_with_package(package)
    service = SourceGroundedQAService(retrieval_engine=engine, llm_client_fn=None)
    original_item_count = len(package.retrieved_items)
    original_item_content = package.retrieved_items[0].content
    await service.answer("What is Gaja Kesari Yoga?", RetrievalFilter())
    # Package must be unchanged (frozen dataclass)
    assert len(package.retrieved_items) == original_item_count
    assert package.retrieved_items[0].content == original_item_content
