"""
AstroOS — Research Query Service (Module 27)

Backs the Query Builder UI: filters research cases by AND-combined
conditions over the real canonical Fact vocabulary
(`apps/api/services/fact_builder.py`) — e.g.
`planet.saturn.retrograde=true`, `maraka.lord.saturn=true`,
`planet.rahu.house=1`. Reuses
`FeatureExtractionService._deserialize_facts`/`_latest_snapshot_entity`
rather than re-implementing facts_json parsing — this service only adds
the condition-matching layer on top of the same Fact list Pattern
Discovery already consumes.

One case can have multiple life events (each with its own snapshot); a
case matches a query if ANY of its events' latest snapshots satisfies
every condition (AND across conditions, OR across the case's events —
matches how a researcher would ask "does this person's chart show X",
not "does every single event of theirs show X").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.facts import Fact
from apps.api.models.research_case import LifeEventModel, ResearchCaseModel
from apps.api.services.feature_extraction import (
    FeatureExtractionService,
    _latest_snapshot_entity,
)

Operator = Literal["equals", "not_equals", "contains"]


@dataclass(frozen=True)
class QueryCondition:
    field: str
    operator: Operator
    value: str


def _matches(fact_value: object, operator: Operator, expected: str) -> bool:
    actual = str(fact_value).lower()
    expected_lower = expected.strip().lower()
    if operator == "equals":
        return actual == expected_lower
    if operator == "not_equals":
        return actual != expected_lower
    if operator == "contains":
        return expected_lower in actual
    return False


def _case_matches(facts: list[Fact], conditions: list[QueryCondition]) -> bool:
    by_key: dict[str, object] = {f.key: f.value for f in facts}
    for cond in conditions:
        if cond.field not in by_key:
            return False
        if not _matches(by_key[cond.field], cond.operator, cond.value):
            return False
    return True


class ResearchQueryService:
    """Scans every research case's real Fact data for AND-combined matches."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def query(
        self, conditions: list[QueryCondition]
    ) -> tuple[list[str], int]:
        """Returns (matching_research_case_ids, total_cases_scanned)."""
        if not conditions:
            return [], 0

        LatestSnapshot, rn = _latest_snapshot_entity()
        rows = (
            await self._session.execute(
                select(ResearchCaseModel.research_case_id, LatestSnapshot)
                .join(LifeEventModel, LatestSnapshot.life_event_id == LifeEventModel.id)
                .join(ResearchCaseModel, LifeEventModel.research_case_id == ResearchCaseModel.id)
                .where(ResearchCaseModel.deleted_at.is_(None))
                .where(rn == 1)
            )
        ).all()

        scanned_cases: set[str] = set()
        matched_cases: set[str] = set()
        for research_case_id, snapshot in rows:
            scanned_cases.add(research_case_id)
            if research_case_id in matched_cases:
                continue
            facts = FeatureExtractionService._deserialize_facts(snapshot)
            if facts is None:
                continue
            if _case_matches(facts, conditions):
                matched_cases.add(research_case_id)

        return list(matched_cases), len(scanned_cases)
