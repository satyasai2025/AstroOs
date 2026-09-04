"""
AstroOS — Event Category Tree Bulk Seed (Research Module)

One-time (idempotent) bulk-seed of the event_categories tree from a
pre-extracted ID->{name, docs} map (e.g. the research category
taxonomy), with an optional top-level rename map applied first.

Idempotent: reuses EventCategoryService.resolve_or_create_category_path,
which matches existing nodes by name — running this twice never creates
duplicates.

Usage:
    python -m apps.api.services.event_category_seed <category_id_map.json> [rename_map.json]
"""

from __future__ import annotations

import asyncio
import json
import sys

from apps.api.dependencies import _async_session_factory
from apps.api.services.event_category_service import EventCategoryService


async def seed_from_maps(
    category_id_map_path: str,
    rename_map_path: str | None = None,
) -> tuple[int, int]:
    """Returns (nodes_seen, nodes_created)."""
    with open(category_id_map_path, encoding="utf-8") as f:
        category_map: dict[str, dict] = json.load(f)

    rename: dict[str, str] = {}
    if rename_map_path:
        with open(rename_map_path, encoding="utf-8") as f:
            rename = json.load(f)

    seen = 0
    created = 0

    async with _async_session_factory() as session:
        service = EventCategoryService(session)
        skipped_no_name = 0
        for entry in category_map.values():
            raw_name = entry.get("name")
            if not raw_name:
                skipped_no_name += 1
                continue
            raw_path = [p.strip() for p in raw_name.split(" / ") if p.strip()]
            if not raw_path:
                skipped_no_name += 1
                continue
            # Apply the top-level rename (e.g. "Notable" -> "Fame & Renown")
            # only to the first segment — sub-levels are already the fuller
            # real category names in the source data.
            raw_path[0] = rename.get(raw_path[0], raw_path[0])

            node = await service.resolve_or_create_category_path(
                raw_path,
                source="import",
                source_doc_count=entry.get("docs"),
            )
            seen += 1
            # A freshly-created node has no siblings sharing its id yet on
            # this pass; we can't cheaply tell create-vs-reuse from here
            # without extra bookkeeping, so approximate via doc_count being
            # set (only true for a just-created leaf in this loop) — good
            # enough for a progress log, not used for correctness.
            if node.source_doc_count == entry.get("docs"):
                created += 1

        await session.commit()

    if skipped_no_name:
        print(f"Skipped {skipped_no_name} entr(y/ies) with no usable name.")

    return seen, created


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    category_map_path = sys.argv[1]
    rename_map_path = sys.argv[2] if len(sys.argv) > 2 else None

    seen, created = asyncio.run(seed_from_maps(category_map_path, rename_map_path))
    print(f"Seeded {seen} category entries ({created} newly created leaf nodes).")


if __name__ == "__main__":
    main()
