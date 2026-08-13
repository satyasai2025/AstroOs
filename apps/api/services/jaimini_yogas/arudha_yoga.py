"""
AstroOS — Jaimini Arudha Yoga: AL-A10 Kendra (JAIMINI-ARY-001)

Arudha Lagna (AL, the native's projected public image) and A10 (Arudha
of the 10th house, career/status) in mutual Kendra — a standard Arudha-
based status indicator: when the sign representing "how the world sees
you" and the sign representing "your career/standing" reinforce each
other angularly, public recognition and career prominence are indicated.

Source: standard Jaimini Arudha analysis (AL as the primary public-image
reference point; its Kendra relationship to A10 as a career-prominence
check) — widely taught in modern Jaimini Arudha courses.
"""

from __future__ import annotations

from apps.api.domain.prediction_evidence import (
    PredictionConfidence,
    PredictionEvidence,
    PredictionReason,
    PredictionRule,
)
from apps.api.services.jaimini_shared import is_kendra
from apps.api.services.jaimini_yoga_context import JaiminiYogaContext
from apps.api.services.jaimini_yoga_registry import register_jaimini_yoga

_RULE_ID = "JAIMINI-ARY-001"
_NAME = "Arudha Lagna - A10 Kendra Yoga"
_SUTRA = (
    "Standard Jaimini Arudha analysis — Arudha Lagna (AL) and A10 "
    "(Arudha of the 10th house) in mutual Kendra indicates public "
    "status/career prominence."
)
_VERSION = "1.0"
_REQUIRES = ("ArudhaResult",)


@register_jaimini_yoga(
    rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
)
def evaluate_al_a10_kendra_yoga(ctx: JaiminiYogaContext) -> PredictionEvidence:
    al = ctx.arudha.arudha_lagna
    a10 = ctx.arudha.by_house(10)

    is_matched = is_kendra(al.rashi, a10.rashi)
    reasons = (
        PredictionReason(
            description=f"Arudha Lagna ({al.rashi}) and A10 ({a10.rashi}) are in mutual Kendra.",
            matched_objects=("AL", "A10"),
            is_satisfied=is_matched,
        ),
    )
    confidence = PredictionConfidence(
        score=100 if is_matched else 0,
        satisfied_conditions=1 if is_matched else 0,
        total_conditions=1,
        basis="Single required condition: AL-A10 mutual Kendra.",
    )
    explanation = (
        f"AL ({al.rashi}) and A10 ({a10.rashi}) are in mutual Kendra — public status/career yoga present."
        if is_matched
        else f"AL ({al.rashi}) and A10 ({a10.rashi}) are not in mutual Kendra — yoga not present."
    )
    return PredictionEvidence(
        rule=PredictionRule(
            rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
        ),
        is_matched=is_matched,
        triggering_conditions=("al_a10_kendra",),
        reasons=reasons,
        confidence=confidence,
        explanation=explanation,
    )
