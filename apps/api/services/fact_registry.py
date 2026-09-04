"""
AstroOS — Fact Registry (Module 13)

Storage + direct lookup only, same minimal-access discipline as
OntologyRegistry (Module 12) — no querying, no inference. RuleEngine
reads facts from here and nowhere else.
"""

from __future__ import annotations

from typing import Any

from apps.api.domain.facts import Fact


class FactRegistry:
    """Stores Facts, keyed by their dotted-path key. One value per key."""

    def __init__(self) -> None:
        self._facts: dict[str, Fact] = {}

    def add_fact(self, fact: Fact) -> None:
        self._facts[fact.key] = fact

    def get_fact(self, key: str) -> Fact | None:
        return self._facts.get(key)

    def get_value(self, key: str, default: Any = None) -> Any:
        fact = self._facts.get(key)
        return fact.value if fact is not None else default

    def has_fact(self, key: str) -> bool:
        return key in self._facts

    def all_facts(self) -> list[Fact]:
        return list(self._facts.values())

    def fact_count(self) -> int:
        return len(self._facts)
