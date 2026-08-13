"""
AstroOS — Knowledge Embedding Repository (Phase IV, IV.3.1 — RAG retrieval)

Persistence for KnowledgeEmbeddingModel rows. Not versioned like the rest
of apps/api/repositories/knowledge_repository.py — an embedding is a
derived artifact of its source text, not a classical-source fact, so it's
simply upserted (replaced in place) when re-embedded rather than
soft-append versioned.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.astrology import KnowledgeEmbeddingModel


class KnowledgeEmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        source_type: str,
        source_id: uuid.UUID,
        embedded_text: str,
        embedding: list[float],
        model_name: str,
    ) -> None:
        """Insert, or replace in place if this (source, model) pair
        already has an embedding — re-embedding the same source with the
        same model is idempotent, not append-only."""
        stmt = pg_insert(KnowledgeEmbeddingModel).values(
            source_type=source_type,
            source_id=source_id,
            embedded_text=embedded_text,
            embedding=embedding,
            model_name=model_name,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_knowledge_embeddings_source_model",
            set_={
                "embedded_text": stmt.excluded.embedded_text,
                "embedding": stmt.excluded.embedding,
            },
        )
        await self._session.execute(stmt)

    async def all_for_model(self, model_name: str) -> Sequence[KnowledgeEmbeddingModel]:
        """Every stored embedding produced by `model_name` — embeddings
        from different models are not comparable, so callers must never
        mix vectors across model_name values in one similarity search."""
        result = await self._session.execute(
            select(KnowledgeEmbeddingModel).where(
                KnowledgeEmbeddingModel.model_name == model_name,
                KnowledgeEmbeddingModel.deleted_at.is_(None),
            )
        )
        return result.scalars().all()

    async def delete_for_source(self, *, source_type: str, source_id: uuid.UUID) -> None:
        """Remove all embeddings for one source row (any model) — used
        when a source is superseded/deleted so stale vectors don't
        surface in future searches."""
        await self._session.execute(
            delete(KnowledgeEmbeddingModel).where(
                KnowledgeEmbeddingModel.source_type == source_type,
                KnowledgeEmbeddingModel.source_id == source_id,
            )
        )
