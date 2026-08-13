"""
AstroOS — Jaimini Karakamsa Yoga: Benefic in Kendra from Karakamsa (JAIMINI-KY-001)

A natural benefic occupying a Kendra house (1st/4th/7th/10th, counted
from Karakamsa treated as a Lagna — see karakamsa_engine.py's
relative_houses) indicates fame, recognition, and prosperity connected
to the native's core soul purpose — one of the most commonly cited
Karakamsa-based yogas, since Karakamsa's houses are read exactly like a
second Lagna for this purpose.

Requires a D9 chart (via JaiminiYogaContext.karakamsa) — if unavailable,
this rule reports itself as not-matched with an explicit reason, rather
than crashing the whole evaluation run over one missing optional input.

Source: standard Jaimini Karakamsa analysis (benefic Kendra from
Karakamsa as a status/recognition indicator) — widely taught alongside
Karakamsa itself.
"""

from __future__ import annotations

from apps.api.domain.prediction_evidence import (
    PredictionConfidence,
    PredictionEvidence,
    PredictionReason,
    PredictionRule,
)
from apps.api.services.jaimini_shared import is_benefic
from apps.api.services.jaimini_yoga_context import JaiminiYogaContext
from apps.api.services.jaimini_yoga_registry import register_jaimini_yoga

_RULE_ID = "JAIMINI-KY-001"
_NAME = "Karakamsa Benefic Kendra Yoga"
_SUTRA = (
    "Standard Jaimini Karakamsa analysis — a natural benefic in Kendra "
    "(1st/4th/7th/10th) from Karakamsa indicates fame/recognition tied "
    "to the soul's core purpose."
)
_VERSION = "1.0"
_REQUIRES = ("KarakamsaResult",)
_KENDRA_HOUSES = (1, 4, 7, 10)


@register_jaimini_yoga(
    rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
)
def evaluate_karakamsa_benefic_kendra_yoga(ctx: JaiminiYogaContext) -> PredictionEvidence:
    rule = PredictionRule(
        rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
    )

    if ctx.karakamsa is None:
        reason = PredictionReason(
            description="No D9 (Navamsa) chart was supplied — Karakamsa could not be computed.",
            matched_objects=(),
            is_satisfied=False,
        )
        return PredictionEvidence(
            rule=rule,
            is_matched=False,
            triggering_conditions=("karakamsa_available",),
            reasons=(reason,),
            confidence=PredictionConfidence(
                score=0, satisfied_conditions=0, total_conditions=1, basis="D9 chart unavailable."
            ),
            explanation="Karakamsa data unavailable for this evaluation (no D9 chart supplied).",
        )

    benefic_kendra_houses = [
        h
        for h in ctx.karakamsa.relative_houses
        if h.house_number in _KENDRA_HOUSES and any(is_benefic(p, ctx.d1_chart) for p in h.planets)
    ]
    is_matched = len(benefic_kendra_houses) > 0

    reasons = tuple(
        PredictionReason(
            description=f"House {h.house_number} from Karakamsa ({h.rashi}) holds benefic(s): {h.planets}.",
            matched_objects=h.planets,
            is_satisfied=True,
        )
        for h in benefic_kendra_houses
    ) or (
        PredictionReason(
            description="No natural benefic occupies a Kendra house from Karakamsa.",
            matched_objects=(),
            is_satisfied=False,
        ),
    )

    total = len(reasons)
    satisfied = sum(1 for r in reasons if r.is_satisfied)
    confidence = PredictionConfidence(
        score=round(100 * satisfied / total),
        satisfied_conditions=satisfied,
        total_conditions=total,
        basis=f"{satisfied} of {total} Kendra houses from Karakamsa hold a benefic.",
    )
    explanation = (
        f"{len(benefic_kendra_houses)} Kendra house(s) from Karakamsa "
        f"({ctx.karakamsa.karakamsa_rashi}) hold a natural benefic — yoga present."
        if is_matched
        else f"No Kendra house from Karakamsa ({ctx.karakamsa.karakamsa_rashi}) holds a "
        "natural benefic — yoga not present."
    )
    return PredictionEvidence(
        rule=rule,
        is_matched=is_matched,
        triggering_conditions=("benefic_in_kendra_from_karakamsa",),
        reasons=reasons,
        confidence=confidence,
        explanation=explanation,
    )
