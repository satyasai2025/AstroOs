"""
AstroOS — Sanyasa Yoga (BPHS-SY-001, BPHS-SY-002)

Combinations classically indicating renunciation. Per the Design Audit
§3, this needs no new primitives beyond what Phase 1/2 already built —
placed in Phase 3 for scope reasons (a smaller, less-requested category),
not technical difficulty.

  BPHS-SY-001: 4 or more of the 7 classical grahas conjunct in one house.
  BPHS-SY-002: The lagna lord placed in the 12th house AND either
               debilitated or conjunct a natural malefic (weak/afflicted
               placement away from the body/self significations of the
               1st house).
"""

from __future__ import annotations

from collections import Counter
from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.yoga_predicates import (
    CLASSICAL_SEVEN,
    YogaContext,
    get_house,
    get_planet,
    house_of_lord,
    is_conjunct,
    is_natural_malefic,
)
from apps.api.services.yoga_registry import register_yoga

_graha_engine = GrahaEngine()


@register_yoga(
    yoga_id="BPHS-SY-001", name="Sanyasa Yoga (4+ Grahas Conjunct)", category="Sanyasa Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_sanyasa_conjunction(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    houses_present: dict[str, int] = {}
    for planet in CLASSICAL_SEVEN:
        position = get_planet(ctx, planet)
        if position is not None:
            houses_present[planet] = position.house_number

    trace.append(f"Step 1: houses for present classical grahas → {houses_present}")

    house_counts = Counter(houses_present.values())
    if not house_counts:
        return YogaResult(
            yoga_id="BPHS-SY-001", name="Sanyasa Yoga (4+ Grahas Conjunct)",
            category="Sanyasa Yoga", source_text="BPHS", rule_version="1.0",
            is_present=False, strength=None,
            missing=("no classical grahas found in chart",), trace=tuple(trace),
        )

    busiest_house, count = house_counts.most_common(1)[0]
    trace.append(f"Step 2: busiest house → {busiest_house} with {count} grahas")

    is_present = count >= 4
    involved = [p for p, h in houses_present.items() if h == busiest_house]

    satisfied = (f"{count} grahas ({involved}) conjunct in house {busiest_house}",) if is_present else ()
    missing = () if is_present else (f"No house has 4+ grahas conjunct (busiest: house {busiest_house} with {count})",)
    trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-SY-001", name="Sanyasa Yoga (4+ Grahas Conjunct)",
        category="Sanyasa Yoga", source_text="BPHS", rule_version="1.0",
        is_present=is_present, strength="full" if is_present else None,
        involved_planets=tuple(involved), involved_houses=(busiest_house,),
        satisfied=satisfied, missing=missing, trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-SY-002", name="Sanyasa Yoga (Lagna Lord Afflicted in 12th)",
    category="Sanyasa Yoga", source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_sanyasa_lagna_lord(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    lagna_lord = get_house(ctx, 1).lord
    trace.append(f"Step 1: lagna lord → {lagna_lord}")

    placement = house_of_lord(ctx, 1)
    trace.append(f"Step 2: {lagna_lord}'s placement → house {placement}")

    if placement is None:
        return YogaResult(
            yoga_id="BPHS-SY-002", name="Sanyasa Yoga (Lagna Lord Afflicted in 12th)",
            category="Sanyasa Yoga", source_text="BPHS", rule_version="1.0",
            is_present=False, strength=None,
            missing=(f"{lagna_lord} not found in chart",), trace=tuple(trace),
        )

    in_12th = placement == 12
    trace.append(f"Step 3: is {lagna_lord} in the 12th house? {in_12th}")
    if not in_12th:
        return YogaResult(
            yoga_id="BPHS-SY-002", name="Sanyasa Yoga (Lagna Lord Afflicted in 12th)",
            category="Sanyasa Yoga", source_text="BPHS", rule_version="1.0",
            is_present=False, strength=None,
            involved_planets=(lagna_lord,), involved_houses=(placement,),
            missing=(f"{lagna_lord} is not in the 12th house (in house {placement})",),
            trace=tuple(trace),
        )

    lord_position = get_planet(ctx, lagna_lord)
    is_debilitated = _graha_engine.is_debilitated(lagna_lord, lord_position.rashi)
    conjunct_malefic = [
        p for p in CLASSICAL_SEVEN + ["rahu", "ketu"]
        if p != lagna_lord and is_natural_malefic(p) and is_conjunct(ctx, lagna_lord, p)
    ]
    trace.append(f"Step 4: is_debilitated={is_debilitated}, conjunct malefics={conjunct_malefic}")

    is_afflicted = is_debilitated or bool(conjunct_malefic)
    satisfied, missing = [], []
    if is_debilitated:
        satisfied.append(f"{lagna_lord} is debilitated in the 12th house")
    if conjunct_malefic:
        satisfied.append(f"{lagna_lord} is conjunct malefic(s) {conjunct_malefic} in the 12th house")
    if not is_afflicted:
        missing.append(f"{lagna_lord} is in the 12th house but neither debilitated nor conjunct a malefic")

    trace.append(f"Step 5: rule {'satisfied' if is_afflicted else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-SY-002", name="Sanyasa Yoga (Lagna Lord Afflicted in 12th)",
        category="Sanyasa Yoga", source_text="BPHS", rule_version="1.0",
        is_present=is_afflicted, strength="full" if is_afflicted else None,
        involved_planets=tuple([lagna_lord] + conjunct_malefic),
        involved_houses=(12,),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )
