"""
AstroOS — Arishta Yogas (BPHS-ARY-001 through 003)

Combinations classically read as indicating difficulty. Placed last in
Phase 2 (Design Audit §5) since it reuses both the houses-from-Moon
primitive (Chandra Yogas) and adjacency patterns established earlier in
this phase.

  BPHS-ARY-001 Papakartari Yoga — the lagna hemmed between malefics in
               the houses immediately before (12th) and after (2nd) it
  BPHS-ARY-002 Malefics in 6th/8th/12th from Moon
  BPHS-ARY-003 Shakata Yoga — Moon in the 6th, 8th, or 12th from Jupiter

Product note (Design Audit §3): these are framed descriptively — which
classical condition is present — not predictively (what it supposedly
causes). Any predictive interpretation belongs in a later, clearly
labeled layer, not this engine's raw output.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.yoga_predicates import (
    KENDRA_HOUSES,
    YogaContext,
    get_planet,
    houses_from,
    is_natural_malefic,
    planets_in_house,
)
from apps.api.services.yoga_registry import register_yoga

_graha_engine = GrahaEngine()


@register_yoga(
    yoga_id="BPHS-ARY-001", name="Papakartari Yoga (Lagna)", category="Arishta Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_papakartari_lagna(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    lagna_house = 1
    twelfth = houses_from(lagna_house, 12)
    second = houses_from(lagna_house, 2)
    trace.append(f"Step 1: houses adjacent to lagna → 12th=house {twelfth}, 2nd=house {second}")

    twelfth_occupants = planets_in_house(ctx, twelfth)
    second_occupants = planets_in_house(ctx, second)
    twelfth_malefics = [p for p in twelfth_occupants if is_natural_malefic(p)]
    second_malefics = [p for p in second_occupants if is_natural_malefic(p)]
    trace.append(f"Step 2: malefics in house {twelfth} (12th) → {twelfth_malefics}")
    trace.append(f"Step 3: malefics in house {second} (2nd) → {second_malefics}")

    is_present = len(twelfth_malefics) > 0 and len(second_malefics) > 0
    satisfied, missing = [], []
    if twelfth_malefics:
        satisfied.append(f"Malefic(s) {twelfth_malefics} in 12th from lagna")
    else:
        missing.append("No malefic in 12th from lagna")
    if second_malefics:
        satisfied.append(f"Malefic(s) {second_malefics} in 2nd from lagna")
    else:
        missing.append("No malefic in 2nd from lagna")
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-001", name="Papakartari Yoga (Lagna)", category="Arishta Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(twelfth_malefics + second_malefics),
        involved_houses=(lagna_house, twelfth, second),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-ARY-002", name="Malefics in Dusthana from Moon", category="Arishta Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_malefics_from_moon(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    moon = get_planet(ctx, "moon")
    if moon is None:
        return YogaResult(
            yoga_id="BPHS-ARY-002", name="Malefics in Dusthana from Moon", category="Arishta Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    satisfied, missing = [], []
    involved_planets = ["moon"]
    involved_houses = [moon.house_number]
    any_present = False

    for offset in (6, 8, 12):
        target_house = houses_from(moon.house_number, offset)
        occupants = planets_in_house(ctx, target_house, exclude=("moon",))
        malefics_here = [p for p in occupants if is_natural_malefic(p)]
        trace.append(f"Step: {offset}th from moon (house {target_house}) malefics → {malefics_here}")
        involved_houses.append(target_house)
        if malefics_here:
            any_present = True
            satisfied.append(f"Malefic(s) {malefics_here} in {offset}th from Moon (house {target_house})")
            involved_planets.extend(malefics_here)
        else:
            missing.append(f"No malefic in {offset}th from Moon (house {target_house})")

    trace.append(f"Final: rule {'satisfied' if any_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-002", name="Malefics in Dusthana from Moon", category="Arishta Yoga",
        source_text="BPHS", rule_version="1.0", is_present=any_present,
        strength="full" if any_present else None,
        involved_planets=tuple(dict.fromkeys(involved_planets)),
        involved_houses=tuple(involved_houses),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-ARY-003", name="Shakata Yoga", category="Arishta Yoga",
    source_text="BPHS", rule_version="1.1",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_shakata_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    """
    rule_version 1.1 (was 1.0 in Phase 2): adds two commonly-cited
    classical cancellation conditions — Shakata is cancelled if Jupiter
    is in a kendra (1st/4th/7th/10th) from the lagna, OR if Jupiter is
    exalted in its own current sign. Same rationale for the version bump
    as Kemadruma Yoga: a genuine rule change, tracked explicitly rather
    than silently altering "1.0"'s behavior.

    Other classical cancellation conditions (e.g. Jupiter aspected by
    benefics) are still not implemented — one additional pair of
    exceptions, not the complete classical set.
    """
    trace: list[str] = []
    moon = get_planet(ctx, "moon")
    jupiter = get_planet(ctx, "jupiter")
    if moon is None or jupiter is None:
        return YogaResult(
            yoga_id="BPHS-ARY-003", name="Shakata Yoga", category="Arishta Yoga",
            source_text="BPHS", rule_version="1.1", is_present=False,
            strength=None, missing=("moon or jupiter not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate jupiter → house {jupiter.house_number}")
    trace.append(f"Step 2: locate moon → house {moon.house_number}")

    offsets_landing_on_moon = {
        offset for offset in range(1, 13)
        if houses_from(jupiter.house_number, offset) == moon.house_number
    }
    base_condition_met = bool(offsets_landing_on_moon & {6, 8, 12})
    trace.append(f"Step 3: moon's house relative to jupiter, offsets → {offsets_landing_on_moon}, "
                  f"matches {{6,8,12}}? {base_condition_met}")

    if not base_condition_met:
        return YogaResult(
            yoga_id="BPHS-ARY-003", name="Shakata Yoga", category="Arishta Yoga",
            source_text="BPHS", rule_version="1.1", is_present=False, strength=None,
            involved_planets=("moon", "jupiter"),
            involved_houses=(moon.house_number, jupiter.house_number),
            missing=("Moon is not in the 6th, 8th, or 12th from Jupiter",),
            trace=tuple(trace) + ("Step 4: base condition not met — cancellation check not applicable",),
        )

    satisfied = ["Moon is in the 6th, 8th, or 12th from Jupiter (base affliction condition met)"]
    missing = []
    trace.append("Step 4: base condition met — checking cancellation")

    jupiter_in_kendra = jupiter.house_number in KENDRA_HOUSES
    jupiter_exalted = _graha_engine.is_exalted("jupiter", jupiter.rashi)
    trace.append(f"Step 5: jupiter in kendra from lagna? {jupiter_in_kendra}")
    trace.append(f"Step 6: jupiter exalted? {jupiter_exalted}")

    is_cancelled = jupiter_in_kendra or jupiter_exalted
    is_present = base_condition_met and not is_cancelled

    if jupiter_in_kendra:
        satisfied.append("Cancelled: Jupiter is in a kendra house from lagna")
    if jupiter_exalted:
        satisfied.append("Cancelled: Jupiter is exalted")
    if is_cancelled:
        missing.append("Shakata does not manifest — cancelled by Jupiter's kendra placement or exaltation")

    trace.append(f"Step 7: final result — {'cancelled, not present' if is_cancelled else 'present, not cancelled'}")

    return YogaResult(
        yoga_id="BPHS-ARY-003", name="Shakata Yoga", category="Arishta Yoga",
        source_text="BPHS", rule_version="1.1", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=("moon", "jupiter"),
        involved_houses=(moon.house_number, jupiter.house_number),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )
