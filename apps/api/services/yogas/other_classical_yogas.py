"""
AstroOS — Other Classical Yogas (BPHS-OMY-006, BPHS-OMY-007)

  BPHS-OMY-006 Amala Yoga    — a natural benefic in the 10th house from
                               the lagna OR from the Moon
  BPHS-OMY-007 Kalasarpa Yoga — all 7 classical grahas confined entirely
                               to one hemisphere of the Rahu-Ketu axis
                               (i.e. none straddle both sides)

Kalasarpa Yoga is the one Phase 3 addition with the same "aggregate,
whole-chart" shape as the Nabhasa Ashraya Yogas (Design Audit §4) — it
checks all 7 classical grahas' positions relative to the Rahu-Ketu axis
at once, not a pairwise relationship.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_predicates import (
    CLASSICAL_SEVEN,
    YogaContext,
    get_planet,
    houses_from,
    is_natural_benefic,
    planets_in_house,
)
from apps.api.services.yoga_registry import register_yoga


@register_yoga(
    yoga_id="BPHS-OMY-006", name="Amala Yoga", category="Other Major Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_amala_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []
    involved_planets: list[str] = []
    involved_houses: list[int] = []

    tenth_from_lagna = houses_from(1, 10)
    lagna_benefics = [p for p in planets_in_house(ctx, tenth_from_lagna) if is_natural_benefic(p)]
    trace.append(f"Step 1: 10th from lagna (house {tenth_from_lagna}) benefics → {lagna_benefics}")
    if lagna_benefics:
        satisfied.append(f"Benefic(s) {lagna_benefics} in 10th from lagna")
        involved_planets.extend(lagna_benefics)
        involved_houses.append(tenth_from_lagna)
    else:
        missing.append(f"No benefic in 10th from lagna (house {tenth_from_lagna})")

    moon = get_planet(ctx, "moon")
    moon_benefics: list[str] = []
    if moon is not None:
        tenth_from_moon = houses_from(moon.house_number, 10)
        moon_benefics = [p for p in planets_in_house(ctx, tenth_from_moon, exclude=("moon",))
                          if is_natural_benefic(p)]
        trace.append(f"Step 2: 10th from moon (house {tenth_from_moon}) benefics → {moon_benefics}")
        if moon_benefics:
            satisfied.append(f"Benefic(s) {moon_benefics} in 10th from Moon")
            involved_planets.extend(moon_benefics)
            involved_houses.append(tenth_from_moon)
        else:
            missing.append(f"No benefic in 10th from Moon (house {tenth_from_moon})")
    else:
        trace.append("Step 2: moon not found in chart — skipping 10th-from-Moon check")
        missing.append("moon not found in chart — 10th-from-Moon check skipped")

    is_present = bool(lagna_benefics) or bool(moon_benefics)
    trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-OMY-006", name="Amala Yoga", category="Other Major Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(dict.fromkeys(involved_planets)),
        involved_houses=tuple(involved_houses),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-OMY-007", name="Kalasarpa Yoga", category="Other Major Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1",),
)
def evaluate_kalasarpa_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    rahu = get_planet(ctx, "rahu")
    ketu = get_planet(ctx, "ketu")
    if rahu is None or ketu is None:
        return YogaResult(
            yoga_id="BPHS-OMY-007", name="Kalasarpa Yoga", category="Other Major Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("rahu or ketu not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate rahu → house {rahu.house_number}")
    trace.append(f"Step 2: locate ketu → house {ketu.house_number}")

    # Rahu and Ketu are always exactly opposite (7th from each other).
    # Hemisphere A: houses at offsets 1-6 from Rahu (i.e. Rahu's house
    # through the house just before Ketu's).
    # Hemisphere B: houses at offsets 1-6 from Ketu (the other half).
    hemisphere_a = {houses_from(rahu.house_number, offset) for offset in range(1, 7)}
    hemisphere_b = {houses_from(ketu.house_number, offset) for offset in range(1, 7)}
    trace.append(f"Step 3: hemisphere A (Rahu side) houses → {sorted(hemisphere_a)}")
    trace.append(f"Step 4: hemisphere B (Ketu side) houses → {sorted(hemisphere_b)}")

    planet_houses = {}
    for planet in CLASSICAL_SEVEN:
        position = get_planet(ctx, planet)
        if position is not None:
            planet_houses[planet] = position.house_number
    trace.append(f"Step 5: classical graha houses → {planet_houses}")

    all_in_a = all(h in hemisphere_a for h in planet_houses.values())
    all_in_b = all(h in hemisphere_b for h in planet_houses.values())
    is_present = bool(planet_houses) and (all_in_a or all_in_b)
    trace.append(f"Step 6: all in hemisphere A? {all_in_a}, all in hemisphere B? {all_in_b}")

    satisfied, missing = [], []
    if is_present:
        side = "Rahu" if all_in_a else "Ketu"
        satisfied.append(f"All 7 classical grahas confined to the {side}-side hemisphere of the Rahu-Ketu axis")
    else:
        straddling = [p for p, h in planet_houses.items() if h not in hemisphere_a and h not in hemisphere_b]
        missing.append("Classical grahas are not all confined to one hemisphere of the Rahu-Ketu axis")
        if straddling:
            missing.append(f"Unexpected: {straddling} fall in neither computed hemisphere (check input)")

    trace.append(f"Step 7: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-OMY-007", name="Kalasarpa Yoga", category="Other Major Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(["rahu", "ketu"] + list(planet_houses.keys())),
        involved_houses=(rahu.house_number, ketu.house_number),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )
