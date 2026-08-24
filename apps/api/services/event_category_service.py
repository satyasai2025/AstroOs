"""
AstroOS — Event Category Tree Service (Research Module)

Resolves an "A / B / C"-style category path to a leaf EventCategoryModel,
creating any missing node along the way (open vocabulary — see
apps/api/models/event_category.py's module docstring for why this is
deliberately unlike the closed EventType enum). Matching is by exact
name (case-insensitive) at each level under the correct parent, so
importing the same path twice never creates duplicates.

Also provides the nested-tree read used by GET /event-categories and the
Vedic-metadata tagging update used by PATCH /event-categories/{id}.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.models.event_category import EventCategoryModel


@dataclass(frozen=True)
class CategoryTreeNode:
    """Read-shape for the nested tree response — decoupled from the ORM row."""
    id: str
    name: str
    level: int
    path: str
    house_number: Optional[int]
    karaka_planet: Optional[str]
    source: str
    source_doc_count: Optional[int]
    children: list["CategoryTreeNode"] = field(default_factory=list)


class EventCategoryService:
    """Stateless-ish service wrapping the event_categories adjacency-list tree."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def resolve_or_create_category_path(
        self,
        path_parts: Sequence[str],
        *,
        source: str = "import",
        source_doc_count: Optional[int] = None,
    ) -> EventCategoryModel:
        """
        Given ["Notable", "Famous", "Royal family"], walk/create each
        level under its correct parent and return the leaf node.
        Case-insensitive name matching so "notable" and "Notable" resolve
        to the same node. Raises ValueError on an empty path.
        """
        cleaned = [p.strip() for p in path_parts if p and p.strip()]
        if not cleaned:
            raise ValueError("category_path must contain at least one non-empty segment")

        parent_id: Optional[uuid.UUID] = None
        node: Optional[EventCategoryModel] = None
        path_so_far: list[str] = []

        for level, name in enumerate(cleaned):
            path_so_far.append(name)
            stmt = select(EventCategoryModel).where(
                EventCategoryModel.parent_id == parent_id,
                EventCategoryModel.level == level,
            )
            result = await self._session.execute(stmt)
            candidates = result.scalars().all()
            match = next((c for c in candidates if c.name.lower() == name.lower()), None)

            if match is None:
                match = EventCategoryModel(
                    name=name,
                    parent_id=parent_id,
                    level=level,
                    path=" / ".join(path_so_far),
                    source=source,
                    source_doc_count=source_doc_count if level == len(cleaned) - 1 else None,
                )
                self._session.add(match)
                await self._session.flush()  # need match.id as the next level's parent_id

            node = match
            parent_id = match.id

        assert node is not None  # cleaned is non-empty, loop always assigns node
        return node

    async def get_tree(self) -> list[CategoryTreeNode]:
        """Full tree, nested. Loaded flat then assembled in Python (simplest
        correct approach at this depth; revisit with a recursive CTE if the
        real dataset's node count ever makes this the bottleneck)."""
        stmt = select(EventCategoryModel).order_by(
            EventCategoryModel.level, EventCategoryModel.sort_order, EventCategoryModel.name,
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        by_id: dict[uuid.UUID, CategoryTreeNode] = {}
        children_of: dict[Optional[uuid.UUID], list[CategoryTreeNode]] = {}

        for row in rows:
            node = CategoryTreeNode(
                id=str(row.id), name=row.name, level=row.level, path=row.path,
                house_number=row.house_number, karaka_planet=row.karaka_planet,
                source=row.source, source_doc_count=row.source_doc_count,
            )
            by_id[row.id] = node
            children_of.setdefault(row.parent_id, []).append(node)

        for row in rows:
            node = by_id[row.id]
            node.children.extend(children_of.get(row.id, []))

        return children_of.get(None, [])

    async def update_tags(
        self,
        category_id: uuid.UUID,
        *,
        house_number: Optional[int] = None,
        karaka_planet: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[EventCategoryModel]:
        """Researcher-curation step: attach/update Vedic metadata on an
        existing (usually auto-created) node. Returns None if not found."""
        node = await self._session.get(EventCategoryModel, category_id)
        if node is None:
            return None
        if house_number is not None:
            node.house_number = house_number
        if karaka_planet is not None:
            node.karaka_planet = karaka_planet
        if description is not None:
            node.description = description
        node.source = "manual"
        await self._session.flush()
        return node
