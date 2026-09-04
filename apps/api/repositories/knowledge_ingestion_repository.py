"""
AstroOS — Knowledge Ingestion Repository

Async SQLAlchemy repository for governed document and chunk persistence.

Provides:
  - upsert_document: idempotent document registration
  - upsert_chunk: idempotent chunk storage keyed on deterministic chunk_id
  - keyword_search: PostgreSQL full-text search with lifecycle/technique filters
  - get_chunks_by_filter: structured metadata-based faceted filtering
  - all_chunks_for_embedding_model: chunk retrieval for re-embedding jobs
"""

from __future__ import annotations

import uuid
from typing import List, Optional, Sequence

from sqlalchemy import and_, or_, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.knowledge_ingestion import IngestedChunk, IngestedDocument
from apps.api.models.knowledge_ingestion import IngestedChunkModel, IngestedDocumentModel


class KnowledgeIngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Document Operations ────────────────────────────────────────────────────

    async def upsert_document(self, doc: IngestedDocument) -> IngestedDocumentModel:
        """Insert or update document record keyed on (title, edition)."""
        values = {
            "id": doc.document_id,
            "source_id": doc.source_id,
            "book_id": None,  # caller can set via separate update if linking to BookModel
            "title": doc.title,
            "author": doc.author,
            "edition": doc.edition,
            "publication_year": doc.publication_year,
            "language": doc.language,
            "tradition": doc.tradition,
            "content_hash_sha256": doc.content_hash_sha256 or None,
            "status": doc.status.value,
            "doc_metadata": doc.metadata or None,
        }
        stmt = pg_insert(IngestedDocumentModel).values(**values)
        # Conflict on the PRIMARY KEY, not on (title, edition).
        #
        # Callers supply a deterministic document_id (e.g. the seed scripts use
        # uuid5 of the page slug), so `id` is the document's real identity and a
        # re-run collides there first. The (title, edition) unique constraint
        # cannot serve as the conflict target because `edition` is routinely
        # NULL, and PostgreSQL treats NULLs as DISTINCT in a UNIQUE constraint —
        # so that clause never fires for NULL-edition rows and the statement
        # fell through to a raw primary-key violation. This made the "idempotent
        # upsert" non-idempotent in practice: it only succeeded while the table
        # was empty.
        #
        # `title` is intentionally NOT in the update set: it is part of the
        # unique constraint, and rewriting it here could push an existing row
        # into collision with a different row.
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "source_id": stmt.excluded.source_id,
                "author": stmt.excluded.author,
                "edition": stmt.excluded.edition,
                "publication_year": stmt.excluded.publication_year,
                "language": stmt.excluded.language,
                "tradition": stmt.excluded.tradition,
                "content_hash_sha256": stmt.excluded.content_hash_sha256,
                "status": stmt.excluded.status,
                "doc_metadata": stmt.excluded.doc_metadata,
            },
        )
        await self._session.execute(stmt)
        result = await self._session.execute(
            select(IngestedDocumentModel).where(
                IngestedDocumentModel.id == doc.document_id
            )
        )
        return result.scalar_one()

    async def get_document_by_id(self, document_id: uuid.UUID) -> Optional[IngestedDocumentModel]:
        result = await self._session.execute(
            select(IngestedDocumentModel).where(
                IngestedDocumentModel.id == document_id,
                IngestedDocumentModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_documents(self, limit: int = 50, offset: int = 0) -> Sequence[IngestedDocumentModel]:
        result = await self._session.execute(
            select(IngestedDocumentModel)
            .where(IngestedDocumentModel.deleted_at.is_(None))
            .order_by(IngestedDocumentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    # ── Chunk Operations ───────────────────────────────────────────────────────

    async def upsert_chunk(self, chunk: IngestedChunk) -> IngestedChunkModel:
        """Insert or update chunk record keyed on deterministic chunk_id."""
        values = {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "source_id": chunk.source_id,
            "verse_id": chunk.verse_id,
            "chapter_section": chunk.chapter_section,
            "page_location": chunk.page_location,
            "passage_reference": chunk.passage_reference,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "content_hash_sha256": chunk.content_hash_sha256,
            "technique_framework": chunk.technique_framework.value,
            "lifecycle_state": chunk.lifecycle_state.value,
            "evidence_level": chunk.evidence_level.value,
            "evidence_family_id": chunk.evidence_family_id,
            "grahas": list(chunk.grahas) if chunk.grahas else None,
            "bhavas": list(chunk.bhavas) if chunk.bhavas else None,
            "rashis": list(chunk.rashis) if chunk.rashis else None,
            "nakshatras": list(chunk.nakshatras) if chunk.nakshatras else None,
            "yogas": list(chunk.yogas) if chunk.yogas else None,
            "event_types": list(chunk.event_types) if chunk.event_types else None,
            "is_ai_extracted": chunk.is_ai_extracted,
            "extraction_metadata": chunk.extraction_metadata or None,
            "embedding_model": chunk.embedding_model,
        }
        stmt = pg_insert(IngestedChunkModel).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_ingested_chunks_chunk_id",
            set_={
                "content": stmt.excluded.content,
                "content_hash_sha256": stmt.excluded.content_hash_sha256,
                "technique_framework": stmt.excluded.technique_framework,
                "lifecycle_state": stmt.excluded.lifecycle_state,
                "evidence_level": stmt.excluded.evidence_level,
                "evidence_family_id": stmt.excluded.evidence_family_id,
                "grahas": stmt.excluded.grahas,
                "bhavas": stmt.excluded.bhavas,
                "rashis": stmt.excluded.rashis,
                "nakshatras": stmt.excluded.nakshatras,
                "yogas": stmt.excluded.yogas,
                "event_types": stmt.excluded.event_types,
                "is_ai_extracted": stmt.excluded.is_ai_extracted,
                "extraction_metadata": stmt.excluded.extraction_metadata,
                "embedding_model": stmt.excluded.embedding_model,
                "verse_id": stmt.excluded.verse_id,
            },
        )
        await self._session.execute(stmt)
        result = await self._session.execute(
            select(IngestedChunkModel).where(
                IngestedChunkModel.chunk_id == chunk.chunk_id
            )
        )
        return result.scalar_one()

    async def get_chunk_by_chunk_id(self, chunk_id: str) -> Optional[IngestedChunkModel]:
        result = await self._session.execute(
            select(IngestedChunkModel).where(
                IngestedChunkModel.chunk_id == chunk_id,
                IngestedChunkModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def keyword_search(
        self,
        query_tokens: List[str],
        technique: Optional[str],
        lifecycle_states: List[str],
        include_unvalidated: bool,
        top_k: int,
    ) -> List[IngestedChunkModel]:
        """
        Keyword full-text search using PostgreSQL tsvector if available,
        with ILIKE fallback. Applies technique and lifecycle state filters.
        """
        conditions = [IngestedChunkModel.deleted_at.is_(None)]

        # Lifecycle filter
        if lifecycle_states:
            conditions.append(IngestedChunkModel.lifecycle_state.in_(lifecycle_states))

        # Technique filter
        if technique:
            conditions.append(IngestedChunkModel.technique_framework == technique)

        # Unvalidated filter
        if not include_unvalidated:
            conditions.append(IngestedChunkModel.evidence_level != "UNVALIDATED")

        # Keyword match: try tsvector first, fall back to ILIKE on content
        if query_tokens:
            tsquery_str = " & ".join(query_tokens)
            # Use search_vector if populated
            ts_condition = text(
                "search_vector @@ to_tsquery('english', :q)"
            ).bindparams(q=tsquery_str)
            # ILIKE fallback on content for any token
            ilike_conditions = [
                IngestedChunkModel.content.ilike(f"%{token}%")
                for token in query_tokens[:5]  # limit to first 5 tokens
            ]
            keyword_condition = or_(ts_condition, *ilike_conditions)
            conditions.append(keyword_condition)

        result = await self._session.execute(
            select(IngestedChunkModel)
            .where(and_(*conditions))
            .limit(top_k)
        )
        return list(result.scalars().all())

    async def get_chunks_by_filter(
        self,
        document_ids: Optional[List[uuid.UUID]] = None,
        source_ids: Optional[List[uuid.UUID]] = None,
        technique: Optional[str] = None,
        grahas: Optional[List[str]] = None,
        bhavas: Optional[List[int]] = None,
        lifecycle_states: Optional[List[str]] = None,
        include_unvalidated: bool = False,
        top_k: int = 50,
    ) -> List[IngestedChunkModel]:
        """Faceted metadata filter query using PostgreSQL ARRAY overlap operators."""
        conditions = [IngestedChunkModel.deleted_at.is_(None)]

        if document_ids:
            conditions.append(IngestedChunkModel.document_id.in_(document_ids))
        if source_ids:
            conditions.append(IngestedChunkModel.source_id.in_(source_ids))
        if technique:
            conditions.append(IngestedChunkModel.technique_framework == technique)
        if lifecycle_states:
            conditions.append(IngestedChunkModel.lifecycle_state.in_(lifecycle_states))
        if not include_unvalidated:
            conditions.append(IngestedChunkModel.evidence_level != "UNVALIDATED")
        if grahas:
            # PostgreSQL ARRAY overlap: grahas && ARRAY[...]
            conditions.append(
                IngestedChunkModel.grahas.overlap(grahas)  # type: ignore[attr-defined]
            )
        if bhavas:
            conditions.append(
                IngestedChunkModel.bhavas.overlap(bhavas)  # type: ignore[attr-defined]
            )

        result = await self._session.execute(
            select(IngestedChunkModel)
            .where(and_(*conditions))
            .limit(top_k)
        )
        return list(result.scalars().all())

    async def all_chunks_for_embedding_model(self, model_name: str) -> List[IngestedChunkModel]:
        """Return all chunks whose embedding was generated by the given model."""
        result = await self._session.execute(
            select(IngestedChunkModel).where(
                IngestedChunkModel.embedding_model == model_name,
                IngestedChunkModel.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
