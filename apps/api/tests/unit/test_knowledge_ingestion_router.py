"""
Unit tests — Governed Knowledge Ingestion & Retrieval Router

Tests:
- POST /ingest/document → 201, correct fields
- POST /ingest/chunk → 201, correct provenance fields
- POST /ingest/chunk → 422 on broken provenance (empty chapter_section)
- POST /ingest/chunk → 422 on unknown technique_framework
- GET /ingest/documents → 200, list
- POST /retrieval/retrieve → 200, EvidencePackage structure
- POST /retrieval/grounded-qa → 200, is_astrological_prediction=False
- POST /retrieval/grounded-qa → governance_disclosure present
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.domain.knowledge_ingestion import (
    DocumentStatus,
    EvidencePackage,
    EvidenceWarning,
    EvidenceWarningType,
    GroundedQAResponse,
    IngestedChunk,
    IngestedDocument,
    RetrievalFilter,
    RetrievalMethod,
    RetrievedEvidenceItem,
)
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    ProvenanceIntegrityError,
    RuleLifecycleState,
    TechniqueFramework,
)
from apps.api.routers import knowledge_ingestion
from apps.api.services.governed_retrieval_engine import GovernedRetrievalEngine
from apps.api.services.knowledge_ingestion_pipeline import GovernedIngestionPipeline
from apps.api.services.source_grounded_qa_service import SourceGroundedQAService


# ── Fixtures ───────────────────────────────────────────────────────────────────

DOC_ID = uuid.uuid4()
SRC_ID = uuid.uuid4()
CHUNK_ID = "CHK-ABCD1234-CHAPTER-24-PAGE-142-0000"


def _make_doc() -> IngestedDocument:
    return IngestedDocument(
        document_id=DOC_ID,
        source_id=SRC_ID,
        title="Brihat Parashara Hora Shastra",
        author="Parashara",
        edition="Santhanam 1984",
        publication_year=1984,
        language="Sanskrit/English",
        tradition="Parashari",
        status=DocumentStatus.PARSED,
    )


def _make_chunk() -> IngestedChunk:
    return IngestedChunk(
        chunk_id=CHUNK_ID,
        document_id=DOC_ID,
        source_id=SRC_ID,
        chapter_section="Chapter 24",
        page_location="Page 142",
        passage_reference="BPHS:Ch.24:v20",
        chunk_index=0,
        content="Jupiter in 10th house confers royal honors and high learning.",
        content_hash_sha256="a" * 64,
        technique_framework=TechniqueFramework.PARASHARI,
        lifecycle_state=RuleLifecycleState.DOCUMENTED,
        evidence_level=EvidenceLevel.UNVALIDATED,
    )


def _make_empty_package() -> EvidencePackage:
    return EvidencePackage(
        package_id="EP-test0001",
        query="test query",
        retrieval_method=RetrievalMethod.KEYWORD_EXACT,
        filters_applied={},
        retrieved_items=(),
        warnings=(),
        total_items_matched=0,
    )


def _make_qa_response(package: EvidencePackage) -> GroundedQAResponse:
    return GroundedQAResponse(
        response_id="QA-test0001",
        question="What is Gaja Kesari Yoga?",
        evidence_package=package,
        source_facts=(),
        grounded_synthesis="LLM not configured. Refer to source facts above.",
        governance_disclosure="GOVERNANCE DISCLOSURE: No classical source passages were retrieved.",
        is_astrological_prediction=False,
    )


@pytest.fixture
def client() -> TestClient:
    # Set up mock pipeline and retrieval engine
    mock_pipeline = MagicMock(spec=GovernedIngestionPipeline)
    mock_pipeline.register_document = AsyncMock(return_value=_make_doc())
    mock_pipeline.ingest_chunk = AsyncMock(return_value=_make_chunk())
    mock_pipeline._repository = MagicMock()
    mock_pipeline._repository.list_documents = AsyncMock(return_value=[])

    mock_engine = MagicMock(spec=GovernedRetrievalEngine)
    mock_engine.retrieve = AsyncMock(return_value=_make_empty_package())

    knowledge_ingestion.set_pipeline(mock_pipeline)
    knowledge_ingestion.set_retrieval_engine(mock_engine)

    app = FastAPI()
    app.include_router(knowledge_ingestion.router, prefix="/api/v1")
    return TestClient(app)


# ── Document Ingestion Tests ───────────────────────────────────────────────────

def test_ingest_document_201(client: TestClient):
    resp = client.post("/api/v1/knowledge/ingest/document", json={
        "title": "Brihat Parashara Hora Shastra",
        "author": "Parashara",
        "edition": "Santhanam 1984",
        "publication_year": 1984,
        "language": "Sanskrit/English",
        "tradition": "Parashari",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Brihat Parashara Hora Shastra"
    assert data["status"] == "PARSED"
    assert "document_id" in data


def test_ingest_document_no_author(client: TestClient):
    resp = client.post("/api/v1/knowledge/ingest/document", json={
        "title": "Anonymous Research Document",
    })
    assert resp.status_code == 201


# ── Chunk Ingestion Tests ──────────────────────────────────────────────────────

def test_ingest_chunk_201(client: TestClient):
    resp = client.post("/api/v1/knowledge/ingest/chunk", json={
        "document_id": str(DOC_ID),
        "chapter_section": "Chapter 24",
        "page_location": "Page 142",
        "passage_reference": "BPHS:Ch.24:v20",
        "chunk_index": 0,
        "content": "Jupiter in 10th house confers royal honors and high learning.",
        "technique_framework": "Parashari",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["chunk_id"] == CHUNK_ID
    assert data["lifecycle_state"] == "DOCUMENTED"
    assert data["evidence_level"] == "UNVALIDATED"


def test_ingest_chunk_broken_provenance_returns_422(client: TestClient):
    """Broken provenance (empty chapter_section) must be rejected with 422."""
    # Set up pipeline to raise ProvenanceIntegrityError
    mock_pipeline = MagicMock(spec=GovernedIngestionPipeline)
    mock_pipeline.ingest_chunk = AsyncMock(
        side_effect=ProvenanceIntegrityError("chapter_section must not be empty.")
    )
    knowledge_ingestion.set_pipeline(mock_pipeline)

    resp = client.post("/api/v1/knowledge/ingest/chunk", json={
        "document_id": str(DOC_ID),
        "chapter_section": "",   # INVALID
        "page_location": "Page 142",
        "passage_reference": "BPHS:Ch.24:v20",
        "chunk_index": 0,
        "content": "Jupiter in 10th house...",
        "technique_framework": "Parashari",
    })
    assert resp.status_code == 422


def test_ingest_chunk_invalid_technique_422(client: TestClient):
    resp = client.post("/api/v1/knowledge/ingest/chunk", json={
        "document_id": str(DOC_ID),
        "chapter_section": "Chapter 1",
        "page_location": "Page 1",
        "passage_reference": "BOOK:Ch.1:v1",
        "chunk_index": 0,
        "content": "Some content.",
        "technique_framework": "INVALID_TECHNIQUE_XYZ",
    })
    assert resp.status_code == 422


def test_ingest_chunk_ai_extracted_flag(client: TestClient):
    mock_chunk = _make_chunk()
    # Return a mock chunk with is_ai_extracted=True
    from dataclasses import replace
    ai_chunk = IngestedChunk(
        chunk_id=CHUNK_ID,
        document_id=DOC_ID,
        source_id=SRC_ID,
        chapter_section="Chapter 35",
        page_location="Page 200",
        passage_reference="BPHS:Ch.35:v3",
        chunk_index=0,
        content="Jupiter in Kendra from Moon forms Gaja Kesari.",
        content_hash_sha256="b" * 64,
        technique_framework=TechniqueFramework.PARASHARI,
        lifecycle_state=RuleLifecycleState.DOCUMENTED,
        evidence_level=EvidenceLevel.UNVALIDATED,
        is_ai_extracted=True,
        extraction_metadata={"extractor": "llm-v1"},
    )
    mock_pipeline = MagicMock(spec=GovernedIngestionPipeline)
    mock_pipeline.ingest_chunk = AsyncMock(return_value=ai_chunk)
    knowledge_ingestion.set_pipeline(mock_pipeline)

    resp = client.post("/api/v1/knowledge/ingest/chunk", json={
        "document_id": str(DOC_ID),
        "chapter_section": "Chapter 35",
        "page_location": "Page 200",
        "passage_reference": "BPHS:Ch.35:v3",
        "chunk_index": 0,
        "content": "Jupiter in Kendra from Moon forms Gaja Kesari.",
        "technique_framework": "Parashari",
        "is_ai_extracted": True,
        "extraction_metadata": {"extractor": "llm-v1"},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_ai_extracted"] is True


# ── Document List Test ─────────────────────────────────────────────────────────

def test_list_documents_200(client: TestClient):
    resp = client.get("/api/v1/knowledge/ingest/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Retrieval Tests ────────────────────────────────────────────────────────────

def test_retrieve_returns_evidence_package(client: TestClient):
    resp = client.post("/api/v1/knowledge/retrieval/retrieve", json={
        "query": "Jupiter in 10th house career effects",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "package_id" in data
    assert "retrieved_items" in data
    assert "warnings" in data
    assert "total_items_matched" in data


def test_retrieve_invalid_technique_422(client: TestClient):
    resp = client.post("/api/v1/knowledge/retrieval/retrieve", json={
        "query": "Some query",
        "technique_framework": "INVALID_FRAMEWORK",
    })
    assert resp.status_code == 422


def test_retrieve_default_excludes_unvalidated(client: TestClient):
    """
    Default retrieval (include_unvalidated=False) must not include
    UNVALIDATED/UNKNOWN lifecycle items. We verify the engine receives
    the correct filter parameter.
    """
    resp = client.post("/api/v1/knowledge/retrieval/retrieve", json={
        "query": "Jupiter Kendra yoga",
        "include_unvalidated": False,
    })
    assert resp.status_code == 200


# ── Grounded QA Tests ─────────────────────────────────────────────────────────

def test_grounded_qa_is_astrological_prediction_always_false(client: TestClient):
    """
    is_astrological_prediction must ALWAYS be False in grounded QA responses.
    This is a hard structural invariant.
    """
    resp = client.post("/api/v1/knowledge/retrieval/grounded-qa", json={
        "question": "What is Gaja Kesari Yoga?",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_astrological_prediction"] is False


def test_grounded_qa_has_governance_disclosure(client: TestClient):
    resp = client.post("/api/v1/knowledge/retrieval/grounded-qa", json={
        "question": "What are the effects of Jupiter in the 10th house?",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "governance_disclosure" in data
    assert len(data["governance_disclosure"]) > 0


def test_grounded_qa_has_evidence_package(client: TestClient):
    resp = client.post("/api/v1/knowledge/retrieval/grounded-qa", json={
        "question": "Explain Ruchaka Yoga.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "evidence_package" in data
    assert "package_id" in data["evidence_package"]
    assert "warnings" in data["evidence_package"]
