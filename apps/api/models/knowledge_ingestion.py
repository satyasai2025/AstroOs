"""
AstroOS — Knowledge Ingestion ORM Models

Provides two tables for the governed ingestion layer:
  - ingested_documents: registered source documents entering the pipeline
  - ingested_chunks:    text chunks with immutable hierarchical provenance

Reuses:
  - AstroBase (uuid pk, created_at, updated_at, deleted_at)
  - Existing ARRAY(String/Integer), JSON, TSVECTOR from PostgreSQL dialect
  - BookModel and VerseModel are referenced via optional FK, not duplicated.

Does NOT duplicate BookModel, VerseModel, RuleModel, or KnowledgeEmbeddingModel.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import (
    Boolean, Index, Integer, String, Text, UniqueConstraint, text
)
from sqlalchemy.dialects.postgresql import ARRAY, JSON, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class IngestedDocumentModel(AstroBase):
    """
    A document entering the governed ingestion pipeline.

    May correspond to an existing BookModel (via book_id FK) or be a new
    research/raw document without a canonical book record. These cases are
    kept explicitly separate: linking book_id does not merge the two systems.
    """
    __tablename__ = "ingested_documents"
    __table_args__ = (
        UniqueConstraint("title", "edition", name="uq_ingested_documents_title_edition"),
    )

    # Optional link to the existing canonical BookModel — does NOT replace it.
    book_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        # Intentional: no FK constraint to avoid migration coupling with astrology.py
        nullable=True,
        index=True,
        comment="Optional reference to books.id — links without duplicating the canonical book record.",
    )

    # Stable external source identifier (e.g. the KnowledgeSource ID from reliability framework)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    edition: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, server_default="Sanskrit/English")
    tradition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_hash_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="RAW_UPLOADED",
        comment="DocumentStatus enum value: RAW_UPLOADED, PARSED, CHUNKED, INDEXED, ARCHIVED"
    )
    doc_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="Arbitrary bibliographic metadata. Named doc_metadata to avoid SQLAlchemy reserved name collision."
    )


class IngestedChunkModel(AstroBase):
    """
    An immutable text chunk with complete, deterministic provenance chain.

    chunk_id is a human-readable deterministic string (e.g. CHK-BPHS-CH24-V20)
    distinct from the UUID primary key (id from AstroBase).

    Optional verse_id links to the existing canonical VerseModel without
    duplicating it. Embeddings for chunks are stored in the existing
    KnowledgeEmbeddingModel (source_type='ingested_chunk', source_id=chunk.id).
    """
    __tablename__ = "ingested_chunks"
    __table_args__ = (
        UniqueConstraint("chunk_id", name="uq_ingested_chunks_chunk_id"),
        Index("ix_ingested_chunks_technique_lifecycle",
              "technique_framework", "lifecycle_state"),
        Index("ix_ingested_chunks_evidence_level", "evidence_level"),
        # GIN indexes for array and full-text search columns
        Index("ix_ingested_chunks_grahas_gin",
              "grahas", postgresql_using="gin"),
        Index("ix_ingested_chunks_bhavas_gin",
              "bhavas", postgresql_using="gin"),
        Index("ix_ingested_chunks_search_vector_gin",
              "search_vector", postgresql_using="gin"),
    )

    # Deterministic human-readable chunk identifier
    chunk_id: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True,
        comment="Deterministic string ID: CHK-{doc_prefix}-{section_slug}-{page_slug}-{index:04d}"
    )

    # Provenance FKs
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # Intentional soft reference — no FK CASCADE to keep layers decoupled
        nullable=False, index=True,
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    # Optional link to canonical VerseModel — does NOT duplicate verse data
    verse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="Optional FK to verses.id — links existing canonical verse without replacing it."
    )

    # Provenance chain fields
    chapter_section: Mapped[str] = mapped_column(String(500), nullable=False)
    page_location: Mapped[str] = mapped_column(String(200), nullable=False)
    passage_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    # Technique and governance
    technique_framework: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Parashari",
        comment="TechniqueFramework enum value: Parashari, Jaimini, KP System, etc."
    )
    lifecycle_state: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="DOCUMENTED",
        comment="RuleLifecycleState: UNKNOWN, DOCUMENTED, REVIEWED, VALIDATED, CANONICAL"
    )
    evidence_level: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="UNVALIDATED",
        comment="EvidenceLevel: HIGH, MODERATE, LOW, UNVALIDATED, CONTRADICTED, INSUFFICIENT_DATA"
    )
    evidence_family_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Astrological metadata tags (stored as arrays for GIN-indexed filter queries)
    grahas: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(50)), nullable=True)
    bhavas: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    rashis: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(50)), nullable=True)
    nakshatras: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)
    yogas: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(200)), nullable=True)
    event_types: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)

    # AI extraction provenance
    is_ai_extracted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"),
        comment="True if metadata was suggested by AI — must not be treated as authoritative fact."
    )
    extraction_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="Metadata about extraction: model used, confidence, extractor version."
    )

    # Embedding tracking
    embedding_model: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="Name of embedding model used to embed this chunk (stored in knowledge_embeddings table)."
    )

    # Full-text search vector — populated by DB trigger or backfill job
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR, nullable=True,
        comment="PostgreSQL tsvector for full-text search. Updated by trigger or backfill."
    )
