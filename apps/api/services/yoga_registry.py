"""
AstroOS — Yoga Registry (Module 8)

Central catalog of every registered yoga. Individual yoga modules
(apps/api/services/yogas/*.py) register themselves here via
@register_yoga at import time; YogaEngine iterates this registry rather
than containing a hardcoded if/elif chain per yoga.
"""

from __future__ import annotations

from typing import Callable, Optional

from apps.api.domain.yoga import YogaDefinition, YogaResult
from apps.api.services._registry import Registry

_registry: Registry[str, YogaDefinition] = Registry(
    hash_line=lambda yoga_id, definition: f"{yoga_id}:{definition.rule_version}\n"
)


def register_yoga(
    yoga_id: str,
    name: str,
    category: str,
    source_text: str,
    rule_version: str,
    requires: tuple[str, ...],
) -> Callable:
    """
    Decorator registering an evaluator function as a YogaDefinition.

    Usage:
        @register_yoga(
            yoga_id="BPHS-PM-001", name="Ruchaka Yoga",
            category="Panch Mahapurusha", source_text="BPHS",
            rule_version="1.0", requires=("D1", "HouseEngine", "GrahaEngine"),
        )
        def evaluate_ruchaka(ctx: YogaContext) -> Optional[YogaResult]:
            ...
    """
    def decorator(evaluator: Callable[..., Optional[YogaResult]]) -> Callable:
        definition = YogaDefinition(
            yoga_id=yoga_id,
            name=name,
            category=category,
            source_text=source_text,
            rule_version=rule_version,
            requires=requires,
            evaluator=evaluator,
        )
        _registry.register(
            yoga_id, definition,
            duplicate_message=f"Duplicate yoga_id registered: {yoga_id!r}",
        )
        return evaluator
    return decorator


def all_yogas() -> list[YogaDefinition]:
    """All registered yoga definitions, in registration order."""
    return _registry.all()


def get_yoga(yoga_id: str) -> Optional[YogaDefinition]:
    """Look up a registered yoga definition by its id, or None if unknown."""
    return _registry.get(yoga_id)


def clear_registry() -> None:
    """Test-only: clear all registrations. Not used by production code paths."""
    _registry.clear()
