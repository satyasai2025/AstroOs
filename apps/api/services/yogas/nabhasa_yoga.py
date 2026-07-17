"""
AstroOS — Nabhasa Yogas, Ashraya sub-category (BPHS-NY-001 through 003)

Architecturally distinct from every other yoga in the catalog (Design
Audit §3/§4): these examine the aggregate distribution of ALL planets
across sign modalities at once, not a relationship between 2-3 named
planets/houses.

  BPHS-NY-001 Rajju Yoga  — all 7 classical grahas in movable signs
  BPHS-NY-002 Musala Yoga — all 7 classical grahas in fixed signs
  BPHS-NY-003 Nala Yoga   — all 7 classical grahas in dual signs

Scope note: Nabhasa Yogas number roughly 32 across four sub-categories
(Ashraya, Dala, Akriti, Sankhya) in BPHS. Only the 3 Ashraya Yogas are
implemented here — they are simple, unambiguous, and consistently
defined across sources. The Dala/Akriti/Sankhya sub-categories have more
cross-text variation in exact naming and thresholds; implementing them
correctly needs verification against a primary source rather than
recall, consistent with how nakshatra deity/shakti data was deliberately
left unpopulated during reference table seeding (Module 6.5) rather than
asserted from unverified memory. Deferred to a follow-up pass.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_predicates import (
    CLASSICAL_SEVEN,
    DUAL_SIGNS,
    FIXED_SIGNS,
    MOVABLE_SIGNS,
    YogaContext,
    get_planet,
)
from apps.api.services.yoga_registry import register_yoga


def _make_ashraya_evaluator(yoga_id: str, name: str, sign_set: frozenset, modality_label: str):
    def evaluate(ctx: YogaContext) -> Optional[YogaResult]:
        trace: list[str] = []
        satisfied: list[str] = []
        missing: list[str] = []

        rashis_by_planet: dict[str, str] = {}
        for planet in CLASSICAL_SEVEN:
            position = get_planet(ctx, planet)
            if position is None:
                missing.append(f"{planet} not found in chart")
                trace.append(f"{planet} not found in chart — cannot evaluate")
                return YogaResult(
                    yoga_id=yoga_id, name=name, category="Nabhasa Yoga",
                    source_text="BPHS", rule_version="1.0", is_present=False,
                    strength=None, missing=tuple(missing), trace=tuple(trace),
                )
            rashis_by_planet[planet] = position.rashi

        trace.append(f"Step 1: rashis for all 7 classical grahas → {rashis_by_planet}")

        outside_modality = {p: r for p, r in rashis_by_planet.items() if r not in sign_set}
        trace.append(
            f"Step 2: grahas NOT in a {modality_label} sign → "
            f"{outside_modality if outside_modality else 'none'}"
        )

        is_present = len(outside_modality) == 0
        if is_present:
            satisfied.append(f"All 7 classical grahas are in {modality_label} signs")
        else:
            for planet, rashi in outside_modality.items():
                missing.append(f"{planet} is in {rashi}, not a {modality_label} sign")

        trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

        return YogaResult(
            yoga_id=yoga_id, name=name, category="Nabhasa Yoga",
            source_text="BPHS", rule_version="1.0", is_present=is_present,
            strength="full" if is_present else None,
            involved_planets=tuple(CLASSICAL_SEVEN),
            satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        )
    return evaluate


register_yoga(
    yoga_id="BPHS-NY-001", name="Rajju Yoga", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="1.0", requires=("D1", "GrahaEngine"),
)(_make_ashraya_evaluator("BPHS-NY-001", "Rajju Yoga", frozenset(MOVABLE_SIGNS), "movable"))

register_yoga(
    yoga_id="BPHS-NY-002", name="Musala Yoga", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="1.0", requires=("D1", "GrahaEngine"),
)(_make_ashraya_evaluator("BPHS-NY-002", "Musala Yoga", frozenset(FIXED_SIGNS), "fixed"))

register_yoga(
    yoga_id="BPHS-NY-003", name="Nala Yoga", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="1.0", requires=("D1", "GrahaEngine"),
)(_make_ashraya_evaluator("BPHS-NY-003", "Nala Yoga", frozenset(DUAL_SIGNS), "dual"))
