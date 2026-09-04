"""
Unit tests — Governed Knowledge Ingestion Pipeline

Tests:
- deterministic chunk ID generation
- content hashing
- provenance integrity validation
- broken provenance rejection
- lifecycle/evidence_level defaults (must be DOCUMENTED/UNVALIDATED)
- AI-extracted metadata flag
- document registration
- chunk ingestion
"""

from __future__ import annotations

import hashlib
import re
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.domain.knowledge_ingestion import (
    DocumentStatus,
    IngestedChunk,
    IngestedDocument,
)
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    ProvenanceIntegrityError,
    RuleLifecycleState,
    TechniqueFramework,
)
from apps.api.services.knowledge_ingestion_pipeline import GovernedIngestionPipeline


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_pipeline(stub_doc=None, stub_chunk=None):
    """Pipeline with mocked repository and no embedding client."""
    repo = MagicMock()
    repo.upsert_document = AsyncMock(return_value=stub_doc)
    repo.upsert_chunk = AsyncMock(return_value=stub_chunk)
    return GovernedIngestionPipeline(repository=repo, embedding_client_fn=None)


DOC_ID = uuid.uuid4()
SOURCE_ID = uuid.uuid4()


# ── Content Hash Tests ─────────────────────────────────────────────────────────

def test_compute_content_hash_deterministic():
    pipeline = make_pipeline()
    content = "When Jupiter is in the 10th house..."
    h1 = pipeline.compute_content_hash(content)
    h2 = pipeline.compute_content_hash(content)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_compute_content_hash_matches_sha256():
    pipeline = make_pipeline()
    content = "Sun in Aries gives vitality."
    expected = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
    assert pipeline.compute_content_hash(content) == expected


def test_compute_content_hash_different_content():
    pipeline = make_pipeline()
    h1 = pipeline.compute_content_hash("content A")
    h2 = pipeline.compute_content_hash("content B")
    assert h1 != h2


# ── Chunk ID Tests ─────────────────────────────────────────────────────────────

def test_build_chunk_id_deterministic():
    pipeline = make_pipeline()
    doc_id = uuid.UUID("12345678-1234-1234-1234-123456789abc")
    cid1 = pipeline.build_chunk_id(doc_id, "Chapter 24", "Page 142", 0)
    cid2 = pipeline.build_chunk_id(doc_id, "Chapter 24", "Page 142", 0)
    assert cid1 == cid2


def test_build_chunk_id_starts_with_chk():
    pipeline = make_pipeline()
    cid = pipeline.build_chunk_id(DOC_ID, "Ch. 1", "Sloka 1", 0)
    assert cid.startswith("CHK-")


def test_build_chunk_id_different_for_different_index():
    pipeline = make_pipeline()
    cid1 = pipeline.build_chunk_id(DOC_ID, "Chapter 35", "Sloka 3", 0)
    cid2 = pipeline.build_chunk_id(DOC_ID, "Chapter 35", "Sloka 3", 1)
    assert cid1 != cid2


def test_build_chunk_id_different_for_different_section():
    pipeline = make_pipeline()
    cid1 = pipeline.build_chunk_id(DOC_ID, "Chapter 1", "Page 10", 0)
    cid2 = pipeline.build_chunk_id(DOC_ID, "Chapter 2", "Page 10", 0)
    assert cid1 != cid2


# ── Provenance Integrity Tests ─────────────────────────────────────────────────

def test_ingest_chunk_rejects_empty_chapter_section():
    pipeline = make_pipeline()
    with pytest.raises(ProvenanceIntegrityError):
        import asyncio
        asyncio.run(pipeline.ingest_chunk(
            document_id=DOC_ID,
            source_id=SOURCE_ID,
            chapter_section="",        # INVALID
            page_location="Page 142",
            passage_reference="BPHS:Ch.24:v20",
            chunk_index=0,
            content="Jupiter in 10th house yields royal honors.",
            technique_framework=TechniqueFramework.PARASHARI,
        ))


def test_ingest_chunk_rejects_empty_content():
    pipeline = make_pipeline()
    with pytest.raises(ProvenanceIntegrityError):
        import asyncio
        asyncio.run(pipeline.ingest_chunk(
            document_id=DOC_ID,
            source_id=SOURCE_ID,
            chapter_section="Chapter 24",
            page_location="Page 142",
            passage_reference="BPHS:Ch.24:v20",
            chunk_index=0,
            content="   ",            # INVALID (whitespace only)
            technique_framework=TechniqueFramework.PARASHARI,
        ))


def test_ingest_chunk_rejects_empty_passage_reference():
    pipeline = make_pipeline()
    with pytest.raises(ProvenanceIntegrityError):
        import asyncio
        asyncio.run(pipeline.ingest_chunk(
            document_id=DOC_ID,
            source_id=SOURCE_ID,
            chapter_section="Chapter 24",
            page_location="Page 142",
            passage_reference="",      # INVALID
            chunk_index=0,
            content="Jupiter in 10th house yields royal honors.",
            technique_framework=TechniqueFramework.PARASHARI,
        ))


# ── Lifecycle & Evidence Level Defaults ───────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_chunk_defaults_to_documented_and_unvalidated():
    pipeline = make_pipeline()
    chunk = await pipeline.ingest_chunk(
        document_id=DOC_ID,
        source_id=SOURCE_ID,
        chapter_section="Chapter 24",
        page_location="Page 142",
        passage_reference="BPHS:Ch.24:v20",
        chunk_index=0,
        content="Jupiter in 10th house confers royal honors and high learning.",
        technique_framework=TechniqueFramework.PARASHARI,
    )
    assert chunk.lifecycle_state == RuleLifecycleState.DOCUMENTED
    assert chunk.evidence_level == EvidenceLevel.UNVALIDATED


@pytest.mark.asyncio
async def test_ingest_chunk_ai_extracted_flag():
    pipeline = make_pipeline()
    chunk = await pipeline.ingest_chunk(
        document_id=DOC_ID,
        source_id=SOURCE_ID,
        chapter_section="Chapter 35",
        page_location="Page 200",
        passage_reference="BPHS:Ch.35:v1",
        chunk_index=0,
        content="Jupiter in Kendra from Moon forms Gaja Kesari Yoga.",
        technique_framework=TechniqueFramework.PARASHARI,
        is_ai_extracted=True,
        extraction_metadata={"extractor": "gpt-4", "confidence": 0.9},
    )
    assert chunk.is_ai_extracted is True
    assert chunk.extraction_metadata["extractor"] == "gpt-4"


# ── Content Hash Integrity ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_chunk_stores_correct_hash():
    pipeline = make_pipeline()
    content = "Saturn in the 7th house delays marriage."
    chunk = await pipeline.ingest_chunk(
        document_id=DOC_ID,
        source_id=SOURCE_ID,
        chapter_section="Chapter 25",
        page_location="Page 155",
        passage_reference="BPHS:Ch.25:v5",
        chunk_index=0,
        content=content,
        technique_framework=TechniqueFramework.PARASHARI,
    )
    expected_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
    assert chunk.content_hash_sha256 == expected_hash


# ── Document Registration ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_document_returns_ingested_document():
    pipeline = make_pipeline()
    doc = await pipeline.register_document(
        title="Brihat Parashara Hora Shastra",
        author="Parashara",
        edition="Santhanam 1984",
        publication_year=1984,
        language="Sanskrit/English",
        tradition="Parashari",
        source_id=SOURCE_ID,
        book_id=None,
    )
    assert isinstance(doc, IngestedDocument)
    assert doc.title == "Brihat Parashara Hora Shastra"
    assert doc.tradition == "Parashari"
