"""
AstroOS — Jaimini Yoga Engine (Layer 6: Calculation Engine)

Stateless service evaluating every registered Jaimini yoga rule against
a JaiminiYogaContext. No Swiss Ephemeris or database dependency —
operates purely on already-computed Jaimini engine outputs (Chara
Karaka, Arudha, Rashi Aspect, optionally Karakamsa).

Deliberately narrow initial scope — five rules, one per approved
category:
  1. JAIMINI-RY-001  — Raja Yoga: Atmakaraka/Amatyakaraka mutual Kendra.
  2. JAIMINI-ARY-001 — Arudha-based: Arudha Lagna / A10 mutual Kendra.
  3. JAIMINI-KY-001  — Karakamsa-based: benefic in Kendra from Karakamsa.
  4. JAIMINI-DUY-001 — Darakaraka/Upapada Lagna relationship (marriage).
  5. JAIMINI-AKD-001 — Atmakaraka dignity (own-sign/exalted vs. debilitated).

Explicitly excludes: generic Parashari yogas (already covered by
YogaEngine — this engine never duplicates that logic), experimental or
inferred combinations, and anything without a citable source. See each
rule module in apps/api/services/jaimini_yogas/ for its own reference.

Every registered rule is evaluated and returned, matched or not — same
"how close did this chart come" rationale as YogaEngine.evaluate_all().
"""

from __future__ import annotations

from apps.api.domain.prediction_evidence import PredictionEvidence
from apps.api.services.jaimini_yoga_context import JaiminiYogaContext
from apps.api.services.jaimini_yoga_registry import all_jaimini_yogas, get_jaimini_yoga

# Importing this triggers every rule module's @register_jaimini_yoga decorators.
from apps.api.services import jaimini_yogas as _jaimini_yogas  # noqa: F401


class JaiminiYogaEngine:
    """Stateless service evaluating all registered Jaimini yoga rules
    against a chart's already-computed Jaimini engine outputs."""

    def evaluate_all(self, ctx: JaiminiYogaContext) -> list[PredictionEvidence]:
        """Evaluate every registered rule. Returns one PredictionEvidence
        per registered rule (matched or not) — never filters."""
        return [evaluator(ctx) for _, evaluator in all_jaimini_yogas()]

    def evaluate_one(self, ctx: JaiminiYogaContext, rule_id: str) -> PredictionEvidence:
        """Evaluate a single rule by its stable id, for targeted debugging/research."""
        entry = get_jaimini_yoga(rule_id)
        if entry is None:
            raise KeyError(f"No Jaimini yoga rule registered with id {rule_id!r}")
        _, evaluator = entry
        return evaluator(ctx)
