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

_REGISTRY: dict[str, YogaDefinition] = {}


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
        if yoga_id in _REGISTRY:
            raise ValueError(f"Duplicate yoga_id registered: {yoga_id!r}")
        _REGISTRY[yoga_id] = YogaDefinition(
            yoga_id=yoga_id,
            name=name,
            category=category,
            source_text=source_text,
            rule_version=rule_version,
            requires=requires,
            evaluator=evaluator,
        )
        return evaluator
    return decorator


def all_yogas() -> list[YogaDefinition]:
    """All registered yoga definitions, in registration order."""
    return list(_REGISTRY.values())


def get_yoga(yoga_id: str) -> Optional[YogaDefinition]:
    """Look up a registered yoga definition by its id, or None if unknown."""
    return _REGISTRY.get(yoga_id)


def clear_registry() -> None:
    """Test-only: clear all registrations. Not used by production code paths."""
    _REGISTRY.clear()
