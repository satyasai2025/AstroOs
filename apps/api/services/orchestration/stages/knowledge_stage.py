"""
AstroOS — Knowledge Stage

Best-effort keyword correlation, not a semantic citation engine —
searches the Knowledge base by each present yoga's name and dedupes
results. Module 20 (Knowledge) has no yoga-to-citation mapping today;
this is the same "explicit, pragmatic gap, not silent" pattern used
elsewhere (see routers/ai.py's docstring).
"""

from __future__ import annotations

import uuid

from apps.api.domain.knowledge import KnowledgeSearchQuery, KnowledgeSearchResult
from apps.api.services.orchestration.stage import PipelineContext


class KnowledgeStage:
    name = "knowledge"

    def __init__(self, *, knowledge_engine) -> None:
        self._knowledge_engine = knowledge_engine

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        seen: set[tuple[str, uuid.UUID]] = set()
        citations: list[KnowledgeSearchResult] = []
        for yoga in ctx.yoga_results:
            if not yoga.is_present:
                continue
            results = await self._knowledge_engine.search(
                KnowledgeSearchQuery(text=yoga.name, limit=3)
            )
            for r in results:
                key = (r.entity_type, r.entity_id)
                if key not in seen:
                    seen.add(key)
                    citations.append(r)
        ctx.knowledge_citations = citations
        return ctx
