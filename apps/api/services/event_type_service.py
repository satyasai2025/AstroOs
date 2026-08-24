"""
AstroOS — Event Type Tree Service (Research Module)

Resolves an "A / B / C"-style event-type path to a leaf EventTypeModel,
creating any missing node along the way — direct mirror of
event_category_service.py's EventCategoryService, minus Vedic tagging
(not applicable to event types).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.event_type import EventTypeModel


@dataclass(frozen=True)
class EventTypeTreeNode:
    """Read-shape for the nested tree response — decoupled from the ORM row."""
    id: str
    name: str
    level: int
    path: str
    source: str
    children: list["EventTypeTreeNode"] = field(default_factory=list)


class EventTypeService:
    """Stateless-ish service wrapping the event_types adjacency-list tree."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def resolve_or_create_event_type_path(
        self,
        path_parts: Sequence[str],
        *,
        source: str = "import",
    ) -> EventTypeModel:
        """
        Given ["Relationship", "Marriage", "Love marriage"], walk/create
        each level under its correct parent and return the leaf node.
        Case-insensitive name matching. Raises ValueError on an empty path.
        """
        cleaned = [p.strip() for p in path_parts if p and p.strip()]
        if not cleaned:
            raise ValueError("event_type_path must contain at least one non-empty segment")

        parent_id: Optional[uuid.UUID] = None
        node: Optional[EventTypeModel] = None
        path_so_far: list[str] = []

        for level, name in enumerate(cleaned):
            path_so_far.append(name)
            stmt = select(EventTypeModel).where(
                EventTypeModel.parent_id == parent_id,
                EventTypeModel.level == level,
            )
            result = await self._session.execute(stmt)
            candidates = result.scalars().all()
            match = next((c for c in candidates if c.name.lower() == name.lower()), None)

            if match is None:
                match = EventTypeModel(
                    name=name,
                    parent_id=parent_id,
                    level=level,
                    path=" / ".join(path_so_far),
                    source=source,
                )
                self._session.add(match)
                await self._session.flush()  # need match.id as the next level's parent_id

            node = match
            parent_id = match.id

        assert node is not None  # cleaned is non-empty, loop always assigns node
        return node

    async def get_tree(self) -> list[EventTypeTreeNode]:
        """Full tree, nested. Loaded flat then assembled in Python."""
        stmt = select(EventTypeModel).order_by(
            EventTypeModel.level, EventTypeModel.sort_order, EventTypeModel.name,
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        by_id: dict[uuid.UUID, EventTypeTreeNode] = {}
        children_of: dict[Optional[uuid.UUID], list[EventTypeTreeNode]] = {}

        for row in rows:
            node = EventTypeTreeNode(
                id=str(row.id), name=row.name, level=row.level, path=row.path,
                source=row.source,
            )
            by_id[row.id] = node
            children_of.setdefault(row.parent_id, []).append(node)

        for row in rows:
            node = by_id[row.id]
            node.children.extend(children_of.get(row.id, []))

        return children_of.get(None, [])

    async def update_node(
        self,
        event_type_id: uuid.UUID,
        *,
        description: Optional[str] = None,
    ) -> Optional[EventTypeModel]:
        """Researcher-curation step: attach/update a description on an
        existing (usually auto-created) node. Returns None if not found."""
        node = await self._session.get(EventTypeModel, event_type_id)
        if node is None:
            return None
        if description is not None:
            node.description = description
        node.source = "manual"
        await self._session.flush()
        return node
