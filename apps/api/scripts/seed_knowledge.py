"""
AstroOS — Knowledge Base Seed Script (Module 20, Phase B)

Manual, explicit, one-time-per-environment step that loads the curated
YAML knowledge catalogues (knowledge/sources/texts/, knowledge/catalogues/
grahas/, knowledge/catalogues/karakatvas/) into the `books` and
`karakatvas` database tables via knowledge_import_pipeline.load_yaml_catalogue.

This is NOT wired into app startup (apps/api/main.py does not import this
module) — you run it yourself, whenever you want the DB to pick up new or
changed catalogue content. It is idempotent: re-running it skips entries
that already exist (matched by title for books, and by
subject+graha+house_number for karakatvas), so it will never duplicate
rows.

Usage (from the repo root, with the same environment / .env the API
server uses — DATABASE_URL must be set):

    python -m apps.api.scripts.seed_knowledge

Exit code is non-zero on failure (missing knowledge/ directory, DB error,
etc.) so it is safe to use in a shell script and check $?.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Importing apps.api.dependencies builds the async SQLAlchemy engine and
# session factory from Settings().DATABASE_URL — the exact same
# construction the FastAPI app uses at request time (see
# apps/api/dependencies.py: _build_async_engine_args / _async_session_factory).
# Nothing here starts the FastAPI app or opens a network connection until
# a session is actually used below.
from apps.api.dependencies import _async_session_factory  # noqa: E402
from apps.api.repositories.knowledge_repository import KnowledgeRepository  # noqa: E402
from apps.api.services.knowledge_engine import KnowledgeEngine  # noqa: E402
from apps.api.services.knowledge_import_pipeline import load_yaml_catalogue  # noqa: E402

# apps/api/scripts/seed_knowledge.py -> apps/api/scripts -> apps/api -> apps -> <repo root>
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_KNOWLEDGE_ROOT = _REPO_ROOT / "knowledge"


async def _run() -> dict[str, int]:
    if not _KNOWLEDGE_ROOT.is_dir():
        print(
            f"ERROR: knowledge catalogue directory not found at {_KNOWLEDGE_ROOT}",
            file=sys.stderr,
        )
        sys.exit(1)

    async with _async_session_factory() as session:
        try:
            repo = KnowledgeRepository(session)
            engine = KnowledgeEngine(repo)
            counts = await load_yaml_catalogue(engine, catalogue_root=_KNOWLEDGE_ROOT)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return counts


def main() -> None:
    counts = asyncio.run(_run())
    print("Knowledge base seed complete:")
    print(f"  books created:              {counts['books']}")
    print(f"  karakatvas created:         {counts['karakatvas']}")
    print(f"  skipped (already present):  {counts['skipped']}")


if __name__ == "__main__":
    main()
