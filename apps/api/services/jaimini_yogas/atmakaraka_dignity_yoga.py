"""
AstroOS — Jaimini Atmakaraka Dignity Yoga (JAIMINI-AKD-001)

Atmakaraka (AK) exalted, in Moolatrikona, or in its own sign is
considered highly favorable for the native's core life purpose and
self-actualization; AK debilitated is considered a genuine affliction to
the same. One of the most universally-cited Atmakaraka principles —
distinct from the AK-Amatyakaraka Raja Yoga (JAIMINI-RY-001), which
concerns AK's relationship to another karaka rather than AK's own
dignity.

Reads dignity directly off the D1Chart's SiderealPosition for the
Atmakaraka's planet (packages.shared.dignity's existing classification —
no dignity logic is recomputed here).

Source: standard Jaimini/Parashari-combined Atmakaraka analysis
(Atmakaraka dignity as a soul-purpose strength indicator) — widely
taught wherever Chara Karaka itself is taught.
"""

from __future__ import annotations

from apps.api.domain.prediction_evidence import (
    PredictionConfidence,
    PredictionEvidence,
    PredictionReason,
    PredictionRule,
)
from apps.api.services.jaimini_yoga_context import JaiminiYogaContext
from apps.api.services.jaimini_yoga_registry import register_jaimini_yoga

_RULE_ID = "JAIMINI-AKD-001"
_NAME = "Atmakaraka Dignity Yoga"
_SUTRA = (
    "Standard Atmakaraka analysis — Atmakaraka exalted, in Moolatrikona, "
    "or in its own sign strengthens the native's core life purpose; "
    "Atmakaraka debilitated afflicts it."
)
_VERSION = "1.0"
_REQUIRES = ("CharaKarakaResult", "D1Chart")
_FAVORABLE_DIGNITIES = frozenset({"exalted", "moolatrikona", "own"})


@register_jaimini_yoga(
    rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
)
def evaluate_atmakaraka_dignity_yoga(ctx: JaiminiYogaContext) -> PredictionEvidence:
    ak = ctx.chara_karaka.atmakaraka
    rule = PredictionRule(
        rule_id=_RULE_ID, name=_NAME, sutra_reference=_SUTRA, rule_version=_VERSION, requires=_REQUIRES
    )

    ak_positions = [p for p in ctx.d1_chart.planets if p.planet == ak.planet]
    if not ak_positions:
        reason = PredictionReason(
            description=f"No D1 position data found for Atmakaraka {ak.planet!r}.",
            matched_objects=(ak.planet,),
            is_satisfied=False,
        )
        return PredictionEvidence(
            rule=rule,
            is_matched=False,
            triggering_conditions=("ak_dignity_lookup",),
            reasons=(reason,),
            confidence=PredictionConfidence(
                score=0, satisfied_conditions=0, total_conditions=1, basis="Atmakaraka position unavailable."
            ),
            explanation=f"Could not evaluate Atmakaraka dignity — no D1 position for {ak.planet}.",
        )

    raw_dignity = ak_positions[0].dignity
    # SiderealPosition.dignity is a DignityType (str, Enum) or None — extract
    # the plain string value for display; DignityType inherits Enum's
    # verbose __str__ ("DignityType.EXALTED"), not str's, so an f-string
    # would otherwise render that instead of "exalted".
    dignity = getattr(raw_dignity, "value", raw_dignity) or "neutral"
    is_favorable = dignity in _FAVORABLE_DIGNITIES
    is_debilitated = dignity == "debilitated"
    is_matched = is_favorable  # the yoga itself is the FAVORABLE case; debilitation is reported as a separate flag

    reasons = (
        PredictionReason(
            description=f"Atmakaraka ({ak.planet}) dignity is {dignity} "
            f"({'favorable' if is_favorable else 'not favorable'}).",
            matched_objects=(ak.planet,),
            is_satisfied=is_favorable,
        ),
        PredictionReason(
            description=f"Atmakaraka ({ak.planet}) is debilitated (affliction to soul purpose).",
            matched_objects=(ak.planet,),
            is_satisfied=is_debilitated,
        ),
    )
    satisfied = sum(1 for r in reasons if r.is_satisfied)
    confidence = PredictionConfidence(
        score=round(100 * satisfied / len(reasons)),
        satisfied_conditions=satisfied,
        total_conditions=len(reasons),
        basis=f"Dignity classification: {dignity}.",
    )
    explanation = (
        f"Atmakaraka ({ak.planet}) is {dignity} — favorable for the native's core life purpose."
        if is_matched
        else f"Atmakaraka ({ak.planet}) is debilitated — affliction to the native's core life purpose."
        if is_debilitated
        else f"Atmakaraka ({ak.planet}) has neutral dignity ({dignity}) — no strong "
        "indication from this rule."
    )
    return PredictionEvidence(
        rule=rule,
        is_matched=is_matched,
        triggering_conditions=("ak_favorable_dignity", "ak_debilitated"),
        reasons=reasons,
        confidence=confidence,
        explanation=explanation,
    )
