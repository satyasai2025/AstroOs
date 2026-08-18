"""
AstroOS — Technique Resolver

Discovers, filters, and resolves TechniqueDefinitions for execution against
a chart or FactRegistry. Reads from the central technique_registry (in-code
fixtures) and coordinates with TechniqueRepository when loading persisted
techniques.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.technique import TechniqueDefinition
from apps.api.services.fact_registry import FactRegistry
from apps.api.services import technique_registry


class TechniqueResolver:
    """Resolves technique definitions based on explicit ID, objective, tradition,
    or fact availability."""

    def resolve_by_id(
        self, technique_id: str, version: int | None = None
    ) -> TechniqueDefinition | None:
        """Look up a technique by its stable slug and optional version."""
        return technique_registry.get_technique(technique_id, version)

    def resolve_by_objective(self, objective: str) -> list[TechniqueDefinition]:
        """Find all active techniques targeting a given astrological objective."""
        return technique_registry.techniques_by_objective(objective)

    def resolve_all(self) -> list[TechniqueDefinition]:
        """Return the latest version of every registered technique."""
        latest: dict[str, TechniqueDefinition] = {}
        for t in technique_registry.all_techniques():
            cur = latest.get(t.technique_id)
            if cur is None or t.version > cur.version:
                latest[t.technique_id] = t
        return list(latest.values())

    def resolve_applicable(
        self,
        facts: FactRegistry,
        objective: Optional[str] = None,
    ) -> list[TechniqueDefinition]:
        """Return techniques whose required inputs are satisfied by the given facts.
        If objective is provided, filters down to that objective."""
        candidates = (
            self.resolve_by_objective(objective)
            if objective
            else self.resolve_all()
        )
        applicable = []
        for t in candidates:
            if not t.required_inputs:
                applicable.append(t)
                continue
            # A technique is applicable if at least one required input is available
            has_available_input = any(facts.has_fact(req) for req in t.required_inputs)
            if has_available_input:
                applicable.append(t)
        return applicable