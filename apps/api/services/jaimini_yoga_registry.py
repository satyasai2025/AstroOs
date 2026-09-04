"""
AstroOS — Jaimini Yoga Registry (Layer 6: Calculation Engine)

Central catalog of every registered Jaimini yoga rule. Individual rule
modules (apps/api/services/jaimini_yogas/*.py) register themselves here
via @register_jaimini_yoga at import time; JaiminiYogaEngine iterates
this registry rather than containing a hardcoded if/elif chain per rule
— identical structure to yoga_registry.py for Parashari yogas.
"""

from __future__ import annotations

from typing import Callable, Optional

from apps.api.domain.prediction_evidence import PredictionEvidence, PredictionRule
from apps.api.services._registry import Registry
from apps.api.services.jaimini_yoga_context import JaiminiYogaContext

JaiminiYogaEvaluator = Callable[[JaiminiYogaContext], PredictionEvidence]

_registry: Registry[str, tuple[PredictionRule, JaiminiYogaEvaluator]] = Registry(
    hash_line=lambda rule_id, entry: f"{rule_id}:{entry[0].rule_version}\n"
)


def register_jaimini_yoga(
    rule_id: str,
    name: str,
    sutra_reference: str,
    rule_version: str,
    requires: tuple[str, ...],
) -> Callable[[JaiminiYogaEvaluator], JaiminiYogaEvaluator]:
    """
    Decorator registering an evaluator function as a PredictionRule.

    Usage:
        @register_jaimini_yoga(
            rule_id="JAIMINI-RY-001", name="Atmakaraka-Amatyakaraka Raja Yoga",
            sutra_reference="Classical Jaimini karaka theory — Atmakaraka/"
                             "Amatyakaraka mutual Kendra or conjunction",
            rule_version="1.0", requires=("CharaKarakaResult", "RashiAspectResult"),
        )
        def evaluate_ak_amk_raja_yoga(ctx: JaiminiYogaContext) -> PredictionEvidence:
            ...
    """

    def decorator(evaluator: JaiminiYogaEvaluator) -> JaiminiYogaEvaluator:
        rule = PredictionRule(
            rule_id=rule_id,
            name=name,
            sutra_reference=sutra_reference,
            rule_version=rule_version,
            requires=requires,
        )
        _registry.register(
            rule_id, (rule, evaluator),
            duplicate_message=f"Duplicate rule_id registered: {rule_id!r}",
        )
        return evaluator

    return decorator


def all_jaimini_yogas() -> list[tuple[PredictionRule, JaiminiYogaEvaluator]]:
    """All registered (rule, evaluator) pairs, in registration order."""
    return _registry.all()


def get_jaimini_yoga(rule_id: str) -> Optional[tuple[PredictionRule, JaiminiYogaEvaluator]]:
    """Look up a registered (rule, evaluator) pair by id, or None if unknown."""
    return _registry.get(rule_id)


def clear_registry() -> None:
    """Test-only: clear all registrations. Not used by production code paths."""
    _registry.clear()
