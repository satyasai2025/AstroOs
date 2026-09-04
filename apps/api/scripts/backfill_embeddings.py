"""
AstroOS — Knowledge Embedding Backfill Script (Phase IV, IV.3.1 — RAG)

Manual, explicit, re-runnable step that embeds every verse and rule
currently in the `verses`/`rules` tables into `knowledge_embeddings`, so
grounded_qa() (services/ai_engine.py) has something to retrieve. Requires
a local embedding server (e.g. `ollama pull nomic-embed-text && ollama
serve`) reachable at Settings.LOCAL_LLM_BASE_URL — see
docs/rag-knowledge-search.md for the full setup.

NOT wired into app startup, same convention as scripts/seed_knowledge.py
— run it yourself, whenever the knowledge base changes (after
seed_knowledge.py, or after adding/editing rules). Idempotent: re-running
re-embeds and upserts every row rather than duplicating (skip-if-unchanged
is not attempted — re-embedding is cheap and this avoids a second "did
the text change" comparison to get wrong).

Usage (repo root, DATABASE_URL and a local embedding server both set up):

    python -m apps.api.scripts.backfill_embeddings

Exit code is non-zero if the embedding server was unreachable for every
row (nothing got embedded) — zero if at least one row succeeded, so a
partially-available server doesn't look like total failure.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from apps.api.config import get_settings
from apps.api.dependencies import _async_session_factory  # noqa: E402
from apps.api.models.astrology import RuleModel, VerseModel
from apps.api.repositories.knowledge_embedding_repository import KnowledgeEmbeddingRepository
from apps.api.services.embedding_client import embed_text


async def _embed_verses(session, repo, settings) -> tuple[int, int]:
    result = await session.execute(
        select(VerseModel).where(VerseModel.deleted_at.is_(None))
    )
    verses = result.scalars().all()

    succeeded = 0
    for verse in verses:
        text = verse.translation or verse.original_text
        if not text:
            continue
        vector = embed_text(
            base_url=settings.LOCAL_LLM_BASE_URL,
            model=settings.EMBEDDING_MODEL,
            timeout_seconds=settings.LOCAL_LLM_TIMEOUT_SECONDS,
            text=text,
        )
        if vector is None:
            continue
        await repo.upsert(
            source_type="verse", source_id=verse.id,
            embedded_text=text, embedding=vector,
            model_name=settings.EMBEDDING_MODEL,
        )
        succeeded += 1
    return succeeded, len(verses)


async def _embed_rules(session, repo, settings) -> tuple[int, int]:
    result = await session.execute(
        select(RuleModel).where(RuleModel.deleted_at.is_(None))
    )
    rules = result.scalars().all()

    succeeded = 0
    for rule in rules:
        text = f"{rule.title}: {rule.interpretation}"
        vector = embed_text(
            base_url=settings.LOCAL_LLM_BASE_URL,
            model=settings.EMBEDDING_MODEL,
            timeout_seconds=settings.LOCAL_LLM_TIMEOUT_SECONDS,
            text=text,
        )
        if vector is None:
            continue
        await repo.upsert(
            source_type="rule", source_id=rule.id,
            embedded_text=text, embedding=vector,
            model_name=settings.EMBEDDING_MODEL,
        )
        succeeded += 1
    return succeeded, len(rules)


async def _run() -> dict[str, tuple[int, int]]:
    settings = get_settings()
    async with _async_session_factory() as session:
        repo = KnowledgeEmbeddingRepository(session)
        verse_ok, verse_total = await _embed_verses(session, repo, settings)
        rule_ok, rule_total = await _embed_rules(session, repo, settings)
        await session.commit()
    return {"verses": (verse_ok, verse_total), "rules": (rule_ok, rule_total)}


def main() -> None:
    results = asyncio.run(_run())
    total_ok = sum(ok for ok, _ in results.values())
    total_rows = sum(total for _, total in results.values())

    print("Knowledge embedding backfill:")
    for kind, (ok, total) in results.items():
        print(f"  {kind}: {ok}/{total} embedded")
    print(f"  total: {total_ok}/{total_rows} embedded")

    if total_rows > 0 and total_ok == 0:
        print(
            "\nERROR: nothing was embedded — is the local embedding server "
            "running and reachable at LOCAL_LLM_BASE_URL? "
            "See docs/rag-knowledge-search.md."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
