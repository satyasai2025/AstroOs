"""
AstroOS — Jaimini Raja Yoga: Atmakaraka-Amatyakaraka Kendra (JAIMINI-RY-001)

Atmakaraka (AK, soul significator) and Amatyakaraka (AmK, career/
minister significator) in mutual Kendra (1st/4th/7th/10th from each
other, by D1 rashi placement) — one of the most widely-cited Jaimini
Raja Yogas: the two most personally significant karakas in a supportive
angular relationship indicates the native's core self-purpose and
professional/mentor role reinforce each other. A same-sign conjunction
is inherently a Kendra (1st from itself), so needs no separate clause.

Source: classical Jaimini karaka theory, universally taught alongside
Chara Karaka itself (the AK/AmK relationship as the primary Jaimini
Raja Yoga check) — see e.g. Sanjay Rath's Jaimini commentaries and
standard Jaimini course curricula.
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

_RULE_ID = "JAIMINI-RY-001"
_NAME = "Atmakaraka-Amatyakaraka Raja Yoga"
_SUTRA = (
    "Classical Jaimini karaka theory — Atmakaraka and Amatyakaraka in "
    "mutual Kendra (or conjunction) form a Raja Yoga."
)
_VERSION = "1.0"
_REQUIRES = ("CharaKarakaResult", "RashiAspectResult")


@register_jaimini_yoga(
    rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
)
def evaluate_ak_amk_raja_yoga(ctx: JaiminiYogaContext) -> PredictionEvidence:
    ak = ctx.chara_karaka.atmakaraka
    amk = ctx.chara_karaka.by_name("Amatyakaraka")

    kendra_relationship = is_kendra(ak.rashi, amk.rashi)
    aspect_supports = ctx.rashi_aspect.does_aspect(ak.rashi, amk.rashi) or ctx.rashi_aspect.does_aspect(
        amk.rashi, ak.rashi
    )

    reasons = (
        PredictionReason(
            description=(
                f"Atmakaraka ({ak.planet}, in {ak.rashi}) and Amatyakaraka "
                f"({amk.planet}, in {amk.rashi}) are in mutual Kendra."
            ),
            matched_objects=(ak.planet, amk.planet),
            is_satisfied=kendra_relationship,
        ),
        PredictionReason(
            description="Atmakaraka's and Amatyakaraka's signs cast a Rashi Drishti on each "
            "other (corroborating evidence, not required for the yoga itself).",
            matched_objects=(ak.rashi, amk.rashi),
            is_satisfied=aspect_supports,
        ),
    )

    is_matched = kendra_relationship  # the aspect check is corroborating only, not required
    satisfied_count = sum(1 for r in reasons if r.is_satisfied)
    confidence = PredictionConfidence(
        score=round(100 * satisfied_count / len(reasons)),
        satisfied_conditions=satisfied_count,
        total_conditions=len(reasons),
        basis=f"{satisfied_count} of {len(reasons)} supporting conditions satisfied.",
    )
    explanation = (
        f"{ak.planet.title()} (AK) and {amk.planet.title()} (AmK) are in mutual Kendra — Raja Yoga present."
        if is_matched
        else f"{ak.planet.title()} (AK) and {amk.planet.title()} (AmK) are not in mutual Kendra — "
        "Raja Yoga not present."
    )

    return PredictionEvidence(
        rule=PredictionRule(
            rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
        ),
        is_matched=is_matched,
        triggering_conditions=("ak_amk_kendra", "ak_amk_rashi_aspect"),
        reasons=reasons,
        confidence=confidence,
        explanation=explanation,
    )
