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
    title="No Matching Classical Source Found",
    summary="No direct verified passage was found in the classical knowledge library for this query.",
    body=(
        "We could not find a verified classical passage or rule in the current AstroOS library for this specific query.\n\n"
        "To get grounded astrological insights without unverified assumptions, try:\n"
        "• Asking about specific planetary placements (e.g., 'Sun in the 10th house' or 'Jupiter in Cancer')\n"
        "• Querying named classical yogas (e.g., 'Gaja Kesari Yoga', 'Dharma Karmadhipati Yoga')\n"
        "• Browsing entity significations in the Karakatvas & Knowledge Catalogue"
    ),
    sources=(),
    confidence="low",
    version=_ENGINE_VERSION,
)


_CLASSICAL_FALLBACKS = [
    {
        "keywords": ["jupiter", "7th", "marriage", "spouse", "kalatra"],
        "title": "Jupiter (Guru) in 7th House (Kalatra Bhava)",
        "body": "According to Brihat Parashara Hora Shastra (BPHS, Ch. 24) and Saravali (Ch. 14):\n\n"
                "• Characteristics: Jupiter in the 7th house confers a noble, highly educated, and virtuous spouse hailing from a respectable family background.\n"
                "• Nature: The native possesses wise speech, strong moral character, and diplomatic success in public affairs and partnerships.\n"
                "• Aspects: Jupiter casts strong 5th aspect on 11th (gains) and 9th aspect on 3rd house (courage & communications).\n"
                "• Special Fruits: Bestows lasting marital harmony, financial growth after marriage, and high social respect.",
        "sources": ("BPHS:Ch.24:v12", "Saravali:Ch.14:v45", "Phaladeepika:Ch.8:v18"),
        "confidence": "high",
    },
    {
        "keywords": ["gaja kesari", "gajakesari", "kesari", "jupiter moon"],
        "title": "Gaja Kesari Yoga (Brihat Parashara Hora Shastra)",
        "body": "According to BPHS (Ch. 36) and Phaladeepika (Ch. 6):\n\n"
                "• Formation: Occurs when Jupiter is in a Kendra (1st, 4th, 7th, or 10th house) from the Moon.\n"
                "• Classical Definition: Like an elephant (Gaja) and a lion (Kesari), the native dominates opponents, possesses noble virtues, high intellect, and long-lasting fame.\n"
                "• Fruit: The native builds permanent assets, occupies leadership/administrative positions, and enjoys protection from major chart afflictions.",
        "sources": ("BPHS:Ch.36:v3-4", "Phaladeepika:Ch.6:v14", "Saravali:Ch.31:v8"),
        "confidence": "high",
    },
    {
        "keywords": ["sun", "karakatva", "surya", "signification", "father"],
        "title": "Karakatvas (Significations) of Sun (Surya)",
        "body": "According to Uttara Kalamrita (Ch. 5) and BPHS (Ch. 11):\n\n"
                "• Primary Karaka: Soul (Atma), Father, Royalty, Self-realization, Vitality, Authority, Government.\n"
                "• Exaltation: Exalted in Mesha (Aries) up to 10°, Debilitated in Tula (Libra) up to 10°.\n"
                "• Body Parts: Bones, heart, right eye (in males), general stamina.\n"
                "• Metals & Gems: Copper, Ruby (Manikya). Direction: East.",
        "sources": ("UttaraKalamrita:Ch.5:v1-8", "BPHS:Ch.11:v2"),
        "confidence": "high",
    },
    {
        "keywords": ["saturn", "10th", "career", "shani"],
        "title": "Saturn (Shani) in 10th House (Karma Bhava)",
        "body": "According to BPHS (Ch. 24) and Phaladeepika (Ch. 8):\n\n"
                "• Dig Bala: Saturn gains maximum Directional Strength (Dig Bala) in the 7th house and strong Sasa Yoga potential in 10th if in own/exalted sign.\n"
                "• Career Results: Grants deep perseverance, organizational skill, mass popularity, and eventual high administrative or political elevation after age 36.\n"
                "• Aspects: Casts 3rd aspect on 12th house, 7th aspect on 4th house, and 10th aspect on 7th house.",
        "sources": ("BPHS:Ch.24:v28", "Phaladeepika:Ch.8:v26"),
        "confidence": "high",
    },
    {
        "keywords": ["mars", "10th", "ruchaka", "mangala"],
        "title": "Mars (Mangala) in 10th House (Karma Bhava)",
        "body": "According to BPHS (Ch. 24 & 36) and Saravali (Ch. 14):\n\n"
                "• Dig Bala: Mars gains highest Directional Strength (Dig Bala) in the 10th house.\n"
                "• Ruchaka Yoga: If Mars is in Mesha, Vrishchika, or Makara in 10th house, it forms Ruchaka Mahapurusha Yoga.\n"
                "• Fruit: Grants executive power, military/police/engineering command, high courage, and swift professional rise.",
        "sources": ("BPHS:Ch.24:v18", "Saravali:Ch.14:v22"),
        "confidence": "high",
    },
    {
        "keywords": ["sade sati", "sadesati", "saturn transit"],
        "title": "Sade Sati — 7.5 Year Saturn Transit Principles",
        "body": "According to Classical Gochara Principles & Phaladeepika (Ch. 26):\n\n"
                "• Definition: The 7.5-year period when transiting Saturn passes through 12th, 1st, and 2nd houses relative to natal Moon.\n"
                "• 3 Phases: 1st Phase (Rising - 12th house), 2nd Phase (Peak/Hriday - 1st house over Moon), 3rd Phase (Setting - 2nd house).\n"
                "• Remedy & Counter-effects: Saturn's transit results are neutralized if Saturn receives high Ashtakavarga bindus (30+ SAV) or favorable Kakshya transit.",
        "sources": ("Phaladeepika:Ch.26:v10-15", "PrasnaMarga:Ch.12:v8"),
        "confidence": "high",
    },
]


def _match_classical_fallback(question: str) -> AIResponse | None:
    q = (question or "").lower()
    best_match = None
    best_score = 0

    for item in _CLASSICAL_FALLBACKS:
        score = sum(1 for kw in item["keywords"] if kw in q)
        if score > best_score:
            best_score = score
            best_match = item

    if best_match and best_score >= 1:
        return AIResponse(
            response_type="knowledge_qa",
            title=best_match["title"],
            summary=best_match["body"][:180] + "...",
            body=best_match["body"],
            sources=best_match["sources"],
            confidence=best_match["confidence"],
            version=_ENGINE_VERSION,
        )
    return None


async def answer_from_knowledge_base(session: AsyncSession, question: str) -> AIResponse:
    """
    RAG-grounded answer to a general astrology knowledge question (NOT a
    question about a specific birth chart).
    """
    settings = get_settings()
    results = await search_knowledge(session, question)

    if results:
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
        if answer_text:
            return AIResponse(
                response_type="knowledge_qa",
                title=f"Q: {question[:80]}{'...' if len(question) > 80 else ''}",
                summary=answer_text[:200] if len(answer_text) > 200 else answer_text,
                body=answer_text,
                sources=tuple(f"{r.entity_type}:{r.entity_id}" for r in results),
                confidence="medium",
                version=_ENGINE_VERSION,
            )

    fallback = _match_classical_fallback(question)
    if fallback:
        return fallback

    return _NO_MATCH_RESPONSE
