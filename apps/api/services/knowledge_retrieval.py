"""
AstroOS — Knowledge Retrieval (Phase IV, IV.3.1 — RAG)

The "smart search" step of Retrieval-Augmented Generation: given a
question, find the most relevant passages already stored in AstroOS's
knowledge base (apps/api/services/embedding_client.py turns both the
question and every stored passage into embedding vectors; this module
finds which stored vectors are closest to the question's).

Deliberately brute-force (compare against every stored embedding, no
approximate-nearest-neighbor index) — AstroOS's knowledge base is a
few thousand verses/rules at most, well within what plain Python/NumPy
handles in milliseconds. An ANN index (e.g. pgvector, FAISS) would be
the right upgrade if the knowledge base ever grows to the point this
becomes measurably slow — not needed at this scale, and not worth the
extra infrastructure dependency until it is.

Everything here degrades gracefully: no local embedding server running,
no stored embeddings yet, or an empty query all return an empty result
list rather than raising — grounded_qa's caller then just falls back to
the plain template answer, per AI_BACKEND's existing fallback contract.
"""

from __future__ import annotations

import math

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.domain.ai import AIResponse
from apps.api.domain.knowledge import KnowledgeSearchResult
from apps.api.repositories.knowledge_embedding_repository import KnowledgeEmbeddingRepository
from apps.api.services.embedding_client import embed_text
from apps.api.services.local_llm_client import enrich_narration


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """1.0 = identical meaning, 0.0 = unrelated, -1.0 = opposite —
    the standard measure of how close two embedding vectors are."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


async def search_knowledge(
    session: AsyncSession,
    query: str,
    top_k: int | None = None,
) -> list[KnowledgeSearchResult]:
    """
    Find the `top_k` knowledge-base passages most relevant to `query`,
    ranked by embedding similarity (highest first).

    Returns an empty list — never raises — if the local embedding
    server is unreachable, the query embeds to nothing useful, or no
    passages have been embedded yet (see scripts/backfill_embeddings.py).
    """
    settings = get_settings()
    top_k = top_k or settings.KNOWLEDGE_RETRIEVAL_TOP_K

    query_vector = embed_text(
        base_url=settings.LOCAL_LLM_BASE_URL,
        model=settings.EMBEDDING_MODEL,
        timeout_seconds=settings.LOCAL_LLM_TIMEOUT_SECONDS,
        text=query,
    )
    if query_vector is None:
        return []

    repo = KnowledgeEmbeddingRepository(session)
    stored = await repo.all_for_model(settings.EMBEDDING_MODEL)
    if not stored:
        return []

    scored = [
        (row, _cosine_similarity(query_vector, row.embedding))
        for row in stored
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    return [
        KnowledgeSearchResult(
            entity_type=row.source_type,
            entity_id=row.source_id,
            title=row.source_type.capitalize(),
            snippet=row.embedded_text[:280],
            relevance=round(relevance, 4),
        )
        for row, relevance in scored[:top_k]
        if relevance > 0.0
    ]


_ENGINE_VERSION = "1.0"

_NO_MATCH_RESPONSE = AIResponse(
    response_type="knowledge_qa",
    title="No Matching Source Found",
    summary="No relevant passage was found in the knowledge base for this question.",
    body=(
        "This could mean: the question isn't covered by what's been "
        "imported yet (see scripts/seed_knowledge.py and "
        "scripts/backfill_embeddings.py), or the local embedding server "
        "isn't running (see docs/rag-knowledge-search.md), or "
        "AI_BACKEND isn't set to \"local_llm\"."
    ),
    sources=(),
    confidence="low",
    version=_ENGINE_VERSION,
)


async def answer_from_knowledge_base(session: AsyncSession, question: str) -> AIResponse:
    """
    RAG-grounded answer to a general astrology knowledge question (NOT a
    question about a specific birth chart — see QAResponder in
    ai_engine.py for that).

    Unlike AIEngine._maybe_enrich()'s "enrich if possible, else fall back
    to template" contract, there is no template equivalent to fall back
    to here — this is a new capability, not an enhancement of an
    existing deterministic one. So if no relevant passages are found (or
    the local model server is unreachable), this returns an explicit
    "no match" response rather than ever letting the model answer
    ungrounded — answering without a real source is exactly what RAG
    exists to prevent.
    """
    settings = get_settings()
    results = await search_knowledge(session, question)
    if not results:
        return _NO_MATCH_RESPONSE

    grounding_text = "\n\n".join(
        f"[{r.entity_type} {r.entity_id}] {r.snippet}" for r in results
    )
    answer_text = enrich_narration(
        base_url=settings.LOCAL_LLM_BASE_URL,
        model=settings.LOCAL_LLM_MODEL,
        timeout_seconds=settings.LOCAL_LLM_TIMEOUT_SECONDS,
        grounding_text=grounding_text,
        instruction=(
            f"Answer this question using ONLY the source facts below: {question}"
        ),
    )
    if answer_text is None:
        return _NO_MATCH_RESPONSE

    return AIResponse(
        response_type="knowledge_qa",
        title=f"Q: {question[:80]}{'...' if len(question) > 80 else ''}",
        summary=answer_text[:200] if len(answer_text) > 200 else answer_text,
        body=answer_text,
        sources=tuple(f"{r.entity_type}:{r.entity_id}" for r in results),
        confidence="medium",
        version=_ENGINE_VERSION,
    )
