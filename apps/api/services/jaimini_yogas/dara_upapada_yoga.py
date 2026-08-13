"""
AstroOS — Jaimini Marriage Yoga: Darakaraka-Upapada Lagna Relationship (JAIMINI-DUY-001)

Darakaraka (DK, spouse significator) and Upapada Lagna (UL, the
classical marriage significator point) in the same sign or in mutual
Kendra — a standard, widely-taught baseline check for a stable,
favorably-supported marriage indication.

Source: standard Jaimini marriage analysis (DK and UL read together as
the two primary marriage significators; their harmonious angular
relationship as a supportive baseline) — see e.g. Sanjay Rath's Jaimini
marriage-analysis teachings.
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

_RULE_ID = "JAIMINI-DUY-001"
_NAME = "Darakaraka-Upapada Lagna Relationship"
_SUTRA = (
    "Standard Jaimini marriage analysis — Darakaraka (DK) and Upapada "
    "Lagna (UL) conjunct or in mutual Kendra indicates a favorably "
    "supported marriage."
)
_VERSION = "1.0"
_REQUIRES = ("CharaKarakaResult", "ArudhaResult")


@register_jaimini_yoga(
    rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
)
def evaluate_dara_upapada_yoga(ctx: JaiminiYogaContext) -> PredictionEvidence:
    dk = ctx.chara_karaka.darakaraka
    ul = ctx.arudha.upapada_lagna

    conjunct = dk.rashi == ul.rashi
    kendra = is_kendra(dk.rashi, ul.rashi)
    is_matched = conjunct or kendra

    reasons = (
        PredictionReason(
            description=f"Darakaraka ({dk.planet}, {dk.rashi}) and Upapada Lagna ({ul.rashi}) "
            "are conjunct (same sign).",
            matched_objects=(dk.planet, "UL"),
            is_satisfied=conjunct,
        ),
        PredictionReason(
            description=f"Darakaraka ({dk.rashi}) and Upapada Lagna ({ul.rashi}) are in mutual Kendra.",
            matched_objects=(dk.planet, "UL"),
            is_satisfied=kendra,
        ),
    )
    satisfied = sum(1 for r in reasons if r.is_satisfied)
    confidence = PredictionConfidence(
        score=round(100 * satisfied / len(reasons)),
        satisfied_conditions=satisfied,
        total_conditions=len(reasons),
        basis=f"{satisfied} of {len(reasons)} supporting conditions satisfied (either alone is sufficient).",
    )
    explanation = (
        f"DK ({dk.planet}, {dk.rashi}) and UL ({ul.rashi}) are conjunct or in mutual Kendra — "
        "favorable marriage indication."
        if is_matched
        else f"DK ({dk.planet}, {dk.rashi}) and UL ({ul.rashi}) share neither conjunction nor "
        "Kendra — no supportive indication from this rule."
    )
    return PredictionEvidence(
        rule=PredictionRule(
            rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
        ),
        is_matched=is_matched,
        triggering_conditions=("dk_ul_conjunct", "dk_ul_kendra"),
        reasons=reasons,
        confidence=confidence,
        explanation=explanation,
    )
