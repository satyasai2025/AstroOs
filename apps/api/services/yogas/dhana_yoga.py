"""
AstroOS — Dhana Yoga (BPHS-DY-001, BPHS-DY-002)

Wealth combinations. Two representative major formulations implemented
for Phase 1 (not an exhaustive Dhana Yoga catalog — see Design Audit §3):

  BPHS-DY-001: Lords of the 2nd and 11th houses are associated
               (conjunct, mutual aspect, or one-way aspect).
  BPHS-DY-002: Lord of the 11th house is placed in a kendra or trikona
               from the lagna.

Introduces the house-lordship *placement* lookup (house_of_lord) as
shared infrastructure — the first yoga in Phase 1 needing it, reused by
every Raja Yoga after it (see Design Audit §5).
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_predicates import (
    KENDRA_HOUSES,
    TRIKONA_HOUSES,
    YogaContext,
    get_house,
    house_of_lord,
    is_associated,
)
from apps.api.services.yoga_registry import register_yoga


@register_yoga(
    yoga_id="BPHS-DY-001", name="Dhana Yoga (2nd-11th Lord Association)",
    category="Dhana Yoga", source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine", "GrahaEngine", "AspectEngine"),
)
def evaluate_dhana_2_11_association(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    house_2 = get_house(ctx, 2)
    house_11 = get_house(ctx, 11)
    lord_2, lord_11 = house_2.lord, house_11.lord
    trace.append(f"Step 1: HouseEngine.get_house_lord(2) → {lord_2}")
    trace.append(f"Step 2: HouseEngine.get_house_lord(11) → {lord_11}")

    if lord_2 == lord_11:
        # Same planet rules both houses — the "association" condition is
        # vacuous (a planet is trivially associated with itself), so this
        # yoga is reported not present via this specific mechanism rather
        # than fabricating a false positive.
        trace.append("Step 3: same planet rules both 2nd and 11th — not evaluable via this rule")
        missing.append("2nd and 11th lords are the same planet — this formulation does not apply")
        return YogaResult(
            yoga_id="BPHS-DY-001", name="Dhana Yoga (2nd-11th Lord Association)",
            category="Dhana Yoga", source_text="BPHS", rule_version="1.0",
            is_present=False, strength=None,
            involved_planets=(lord_2,), missing=tuple(missing), trace=tuple(trace),
        )

    associated = is_associated(ctx, lord_2, lord_11)
    trace.append(f"Step 3: is_associated({lord_2}, {lord_11}) → {associated}")

    if associated:
        satisfied.append(f"2nd lord ({lord_2}) and 11th lord ({lord_11}) are associated")
    else:
        missing.append(f"2nd lord ({lord_2}) and 11th lord ({lord_11}) are not associated")

    trace.append(f"Step 4: rule {'satisfied' if associated else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-DY-001", name="Dhana Yoga (2nd-11th Lord Association)",
        category="Dhana Yoga", source_text="BPHS", rule_version="1.0",
        is_present=associated, strength="full" if associated else None,
        involved_planets=(lord_2, lord_11),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-DY-002", name="Dhana Yoga (11th Lord in Kendra/Trikona)",
    category="Dhana Yoga", source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_dhana_11th_lord_kendra_trikona(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    house_11 = get_house(ctx, 11)
    lord_11 = house_11.lord
    trace.append(f"Step 1: HouseEngine.get_house_lord(11) → {lord_11}")

    placement = house_of_lord(ctx, 11)
    trace.append(f"Step 2: {lord_11}'s current placement → house {placement}")

    if placement is None:
        missing.append(f"{lord_11} not found in chart")
        return YogaResult(
            yoga_id="BPHS-DY-002", name="Dhana Yoga (11th Lord in Kendra/Trikona)",
            category="Dhana Yoga", source_text="BPHS", rule_version="1.0",
            is_present=False, strength=None, missing=tuple(missing), trace=tuple(trace),
        )

    in_kendra = placement in KENDRA_HOUSES
    in_trikona = placement in TRIKONA_HOUSES
    trace.append(f"Step 3: house {placement} kendra={in_kendra}, trikona={in_trikona}")

    is_present = in_kendra or in_trikona
    if is_present:
        location = "kendra" if in_kendra else "trikona"
        satisfied.append(f"11th lord ({lord_11}) is in a {location} house ({placement})")
    else:
        missing.append(f"11th lord ({lord_11}) is not in a kendra or trikona house (in house {placement})")

    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-DY-002", name="Dhana Yoga (11th Lord in Kendra/Trikona)",
        category="Dhana Yoga", source_text="BPHS", rule_version="1.0",
        is_present=is_present, strength="full" if is_present else None,
        involved_planets=(lord_11,), involved_houses=(placement,),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )
