"""
AstroOS — Arishta Yogas (BPHS-ARY-001 through 011)

Combinations classically read as indicating difficulty. Placed last in
Phase 2 (Design Audit §5) since it reuses both the houses-from-Moon
primitive (Chandra Yogas) and adjacency patterns established earlier in
this phase.

Phase 1 (v2.0.0):
  BPHS-ARY-001 Papakartari Yoga — the lagna hemmed between malefics in
               the houses immediately before (12th) and after (2nd) it
  BPHS-ARY-002 Malefics in 6th/8th/12th from Moon
  BPHS-ARY-003 Shakata Yoga — Moon in the 6th, 8th, or 12th from Jupiter

Phase 2 (v2.1.0 "Vistara"):
  BPHS-ARY-004 Papakartari Yoga (Moon) — Moon hemmed between malefics
  BPHS-ARY-005 Mars-Saturn Conjunction — Mars and Saturn conjunct (Graha Dosh)
  BPHS-ARY-006 Malefics in Kendras from Lagna — 3+ malefics in kendra
  BPHS-ARY-007 All Benefics in Dusthanas — every natural benefic in 6/8/12
  BPHS-ARY-008 Lagna Lord in Dusthana — lagna lord in 6th/8th/12th
  BPHS-ARY-009 Debilitated Planet in Kendra — any planet debilitated in kendra
  BPHS-ARY-010 Sun-Saturn Conjunction — Sun and Saturn conjunct
  BPHS-ARY-011 Rahu/Ketu in Kendras with Malefic Aspect

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
    CLASSICAL_SEVEN,
    KENDRA_HOUSES,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    TRIKONA_HOUSES,
    YogaContext,
    get_house,
    get_planet,
    houses_from,
    is_associated,
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


# ---------------------------------------------------------------------------
# Phase 2: Additional Arishta Yogas
# ---------------------------------------------------------------------------

@register_yoga(
    yoga_id="BPHS-ARY-004", name="Papakartari Yoga (Moon)", category="Arishta Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_papakartari_moon(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Moon hemmed between malefics in the 2nd and 12th from it.
    Classical inauspicious combination affecting emotional well-being
    and mental peace.
    """
    trace: list[str] = []
    moon = get_planet(ctx, "moon")
    if moon is None:
        return YogaResult(
            yoga_id="BPHS-ARY-004", name="Papakartari Yoga (Moon)", category="Arishta Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=("moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    twelfth = houses_from(moon.house_number, 12)
    second = houses_from(moon.house_number, 2)
    twelfth_occupants = planets_in_house(ctx, twelfth)
    second_occupants = planets_in_house(ctx, second)
    twelfth_malefics = [p for p in twelfth_occupants if is_natural_malefic(p)]
    second_malefics = [p for p in second_occupants if is_natural_malefic(p)]
    trace.append(f"Step 2: malefics in house {twelfth} (12th from Moon) → {twelfth_malefics}")
    trace.append(f"Step 3: malefics in house {second} (2nd from Moon) → {second_malefics}")

    is_present = len(twelfth_malefics) > 0 and len(second_malefics) > 0
    satisfied, missing = [], []
    counter_examples = []
    if twelfth_malefics:
        satisfied.append(f"Malefic(s) {twelfth_malefics} in 12th from Moon")
    else:
        missing.append("No malefic in 12th from Moon")
    if second_malefics:
        satisfied.append(f"Malefic(s) {second_malefics} in 2nd from Moon")
    else:
        missing.append("No malefic in 2nd from Moon")

    if is_present:
        counter_examples = [
            "If a benefic occupied 2nd or 12th from Moon, the Papakartari effect would be reduced",
            "Moon in a kendra from lagna can partially cancel this yoga",
        ]

    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-004", name="Papakartari Yoga (Moon)", category="Arishta Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(twelfth_malefics + second_malefics),
        involved_houses=(moon.house_number, twelfth, second),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-ARY-005", name="Mars-Saturn Conjunction (Graha Dosh)", category="Arishta Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_mars_saturn_conjunction(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Mars and Saturn conjunct — classical Graha Dosh indicating
    conflict, delays, and obstacles. One of the most widely recognized
    inauspicious combinations in Vedic astrology.
    """
    trace: list[str] = []
    mars = get_planet(ctx, "mars")
    saturn = get_planet(ctx, "saturn")
    if mars is None or saturn is None:
        return YogaResult(
            yoga_id="BPHS-ARY-005", name="Mars-Saturn Conjunction (Graha Dosh)", category="Arishta Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=("mars or saturn not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate mars → house {mars.house_number}")
    trace.append(f"Step 2: locate saturn → house {saturn.house_number}")

    conjunct = mars.house_number == saturn.house_number
    trace.append(f"Step 3: same house? {conjunct}")

    satisfied, missing = [], []
    counter_examples = []
    if conjunct:
        satisfied.append(f"Mars and Saturn conjunct in house {mars.house_number}")
        # Check if either is exalted
        if _graha_engine.is_exalted("mars", mars.rashi):
            satisfied.append("Mars is exalted — strengthens position despite conjunction")
        if _graha_engine.is_exalted("saturn", saturn.rashi):
            satisfied.append("Saturn is exalted — strengthens position despite conjunction")
        counter_examples = [
            "If Mars and Saturn were in different houses, this Graha Dosh would not form",
            "Mutual aspect (7th from each other) also creates tension but is classified separately",
        ]
    else:
        missing.append(f"Mars (house {mars.house_number}) and Saturn (house {saturn.house_number}) not conjunct")
        counter_examples = []

    is_present = conjunct
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-005", name="Mars-Saturn Conjunction (Graha Dosh)", category="Arishta Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=("mars", "saturn"),
        involved_houses=(mars.house_number,),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-ARY-006", name="Multiple Malefics in Kendras from Lagna", category="Arishta Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_malefics_in_kendras(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Three or more natural malefics in kendra houses from lagna.
    Concentrated malefic energy in angular houses creates obstacles
    and challenges.
    """
    trace: list[str] = []
    malefics_in_kendra = []
    for planet in CLASSICAL_SEVEN + ["rahu", "ketu"]:
        if planet not in NATURAL_MALEFICS:
            continue
        pos = get_planet(ctx, planet)
        if pos is not None and pos.house_number in KENDRA_HOUSES:
            malefics_in_kendra.append(planet)

    trace.append(f"Step 1: malefics in kendra → {malefics_in_kendra}")

    is_present = len(malefics_in_kendra) >= 3
    satisfied, missing = [], []
    counter_examples = []

    if is_present:
        satisfied.append(f"{len(malefics_in_kendra)} malefics in kendra: {malefics_in_kendra}")
        counter_examples = [
            "If fewer than 3 malefics were in kendra, this yoga would not form",
            "Benefics aspecting the kendra houses can mitigate the difficulty",
        ]
    else:
        missing.append(f"Only {len(malefics_in_kendra)} malefics in kendra (need 3+)")
        counter_examples = []

    trace.append(f"Step 2: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-006", name="Multiple Malefics in Kendras from Lagna", category="Arishta Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(malefics_in_kendra),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-ARY-007", name="All Benefics in Dusthanas", category="Arishta Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_benefics_in_dusthanas(ctx: YogaContext) -> Optional[YogaResult]:
    """
    All natural benefics placed in dusthana houses (6th, 8th, 12th).
    When benefics lose their ability to help by being in inauspicious
    houses, their positive influence is diminished.
    """
    trace: list[str] = []
    DUSTHANA_HOUSES = {6, 8, 12}
    benefics_in_dusthana = []
    benefics_outside = []

    for planet in CLASSICAL_SEVEN:
        if planet not in NATURAL_BENEFICS:
            continue
        pos = get_planet(ctx, planet)
        if pos is None:
            continue
        if pos.house_number in DUSTHANA_HOUSES:
            benefics_in_dusthana.append(planet)
        else:
            benefics_outside.append(planet)

    trace.append(f"Step 1: benefics in dusthana → {benefics_in_dusthana}")
    trace.append(f"Step 2: benefics outside dusthana → {benefics_outside}")

    is_present = len(benefics_outside) == 0 and len(benefics_in_dusthana) > 0
    satisfied, missing = [], []
    counter_examples = []

    if is_present:
        satisfied.append(f"All benefics ({benefics_in_dusthana}) in dusthana houses")
        counter_examples = [
            "If any benefic moved to a kendra/trikona house, this yoga would break",
            "A benefic in its own sign in dusthana can still provide some protection",
        ]
    else:
        if benefics_outside:
            missing.append(f"Benefics not in dusthana: {benefics_outside}")
        counter_examples = []

    trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-007", name="All Benefics in Dusthanas", category="Arishta Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(benefics_in_dusthana),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-ARY-008", name="Lagna Lord in Dusthana", category="Arishta Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_lagna_lord_in_dusthana(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Lagna lord placed in a dusthana house (6th, 8th, or 12th).
    The lagna lord represents the self/body — its placement in an
    inauspicious house indicates challenges to health, stability,
    and overall well-being.
    """
    trace: list[str] = []
    DUSTHANA_HOUSES = {6, 8, 12}
    lagna_lord = get_house(ctx, 1).lord
    trace.append(f"Step 1: lagna lord → {lagna_lord}")

    lord_pos = get_planet(ctx, lagna_lord)
    if lord_pos is None:
        return YogaResult(
            yoga_id="BPHS-ARY-008", name="Lagna Lord in Dusthana", category="Arishta Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=(f"{lagna_lord} not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 2: {lagna_lord} in house {lord_pos.house_number}")
    in_dusthana = lord_pos.house_number in DUSTHANA_HOUSES
    trace.append(f"Step 3: in dusthana? {in_dusthana}")

    satisfied, missing = [], []
    counter_examples = []

    if in_dusthana:
        satisfied.append(f"Lagna lord ({lagna_lord}) in dusthana (house {lord_pos.house_number})")
        # Check if debilitated
        if _graha_engine.is_debilitated(lagna_lord, lord_pos.rashi):
            satisfied.append(f"{lagna_lord} is also debilitated — intensifies affliction")
        counter_examples = [
            f"If {lagna_lord} moved to a kendra or trikona house, this yoga would not form",
            f"Exchange of signs between {lagna_lord} and the dusthana lord can provide relief",
        ]
    else:
        missing.append(f"Lagna lord ({lagna_lord}) not in dusthana (in house {lord_pos.house_number})")
        counter_examples = []

    is_present = in_dusthana
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-008", name="Lagna Lord in Dusthana", category="Arishta Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=(lagna_lord,),
        involved_houses=(lord_pos.house_number,),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-ARY-009", name="Debilitated Planet in Kendra", category="Arishta Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_debilitated_in_kendra(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Any planet debilitated in a kendra house. A debilitated planet
    in a kendra creates weakness in that planet's significations,
    and since kendra houses are angular (visible), the weakness
    becomes prominent.
    """
    trace: list[str] = []
    debilitated_in_kendra = []

    for planet in CLASSICAL_SEVEN:
        pos = get_planet(ctx, planet)
        if pos is None:
            continue
        if pos.house_number in KENDRA_HOUSES:
            is_deb = _graha_engine.is_debilitated(planet, pos.rashi)
            if is_deb:
                debilitated_in_kendra.append((planet, pos.house_number))
                trace.append(f"{planet} debilitated in kendra (house {pos.house_number}, sign {pos.rashi})")

    trace.append(f"Step 1: debilitated planets in kendra → {debilitated_in_kendra}")

    is_present = len(debilitated_in_kendra) > 0
    satisfied, missing = [], []
    counter_examples = []

    if is_present:
        for planet, house in debilitated_in_kendra:
            satisfied.append(f"{planet} debilitated in kendra (house {house})")
        counter_examples = [
            "If the debilitated planet had Neecha Bhanga (cancellation), the weakness would be reduced",
            "A different planet's debilitation in a kendra would create a separate instance of this yoga",
        ]
    else:
        missing.append("No planet is debilitated in a kendra house")
        counter_examples = []

    involved = tuple(p for p, _ in debilitated_in_kendra)
    involved_houses = tuple(h for _, h in debilitated_in_kendra)
    trace.append(f"Step 2: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-009", name="Debilitated Planet in Kendra", category="Arishta Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=involved,
        involved_houses=involved_houses,
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-ARY-010", name="Sun-Saturn Conjunction", category="Arishta Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_sun_saturn_conjunction(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Sun and Saturn conjunct — considered one of the most challenging
    planetary combinations. Saturn's darkness cools Sun's vitality,
    creating tension between authority (Sun) and restriction (Saturn).
    """
    trace: list[str] = []
    sun = get_planet(ctx, "sun")
    saturn = get_planet(ctx, "saturn")
    if sun is None or saturn is None:
        return YogaResult(
            yoga_id="BPHS-ARY-010", name="Sun-Saturn Conjunction", category="Arishta Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=("sun or saturn not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate sun → house {sun.house_number}")
    trace.append(f"Step 2: locate saturn → house {saturn.house_number}")

    conjunct = sun.house_number == saturn.house_number
    trace.append(f"Step 3: same house? {conjunct}")

    satisfied, missing = [], []
    counter_examples = []

    if conjunct:
        satisfied.append(f"Sun and Saturn conjunct in house {sun.house_number}")
        if _graha_engine.is_exalted("saturn", saturn.rashi):
            satisfied.append("Saturn is exalted — reduces the harshness of this combination")
        counter_examples = [
            "If Sun and Saturn were in different houses, this combination would not form",
            "Saturn retrograde in this conjunction can sometimes behave more favorably",
        ]
    else:
        missing.append(f"Sun (house {sun.house_number}) and Saturn (house {saturn.house_number}) not conjunct")
        counter_examples = []

    is_present = conjunct
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-010", name="Sun-Saturn Conjunction", category="Arishta Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=("sun", "saturn"),
        involved_houses=(sun.house_number,),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-ARY-011", name="Rahu/Ketu in Kendras with Malefic Aspect", category="Arishta Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine", "GrahaEngine", "AspectEngine"),
)
def evaluate_rahu_ketu_kendra_malefic(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Rahu or Ketu in a kendra house from lagna, additionally aspected
    by a natural malefic. Nodes in angular houses already create
    unconventional energy; malefic aspects intensify the difficulty.
    """
    trace: list[str] = []
    rahu = get_planet(ctx, "rahu")
    ketu = get_planet(ctx, "ketu")
    if rahu is None and ketu is None:
        return YogaResult(
            yoga_id="BPHS-ARY-011", name="Rahu/Ketu in Kendras with Malefic Aspect",
            category="Arishta Yoga", source_text="BPHS", rule_version="2.0",
            is_present=False, strength=None,
            missing=("neither rahu nor ketu found in chart",), trace=tuple(trace),
        )

    nodes_in_kendra = []
    for node_name, node_pos in [("rahu", rahu), ("ketu", ketu)]:
        if node_pos is not None and node_pos.house_number in KENDRA_HOUSES:
            # Check for malefic aspects on this node
            malefic_aspectors = []
            for malefic in ["sun", "mars", "saturn"]:
                if is_associated(ctx, malefic, node_name):
                    malefic_aspectors.append(malefic)
            if malefic_aspectors:
                nodes_in_kendra.append((node_name, node_pos.house_number, malefic_aspectors))
                trace.append(f"{node_name} in kendra (house {node_pos.house_number}) with malefic aspects from {malefic_aspectors}")

    trace.append(f"Step 1: nodes in kendra with malefic aspect → {nodes_in_kendra}")

    is_present = len(nodes_in_kendra) > 0
    satisfied, missing = [], []
    counter_examples = []

    if is_present:
        for node, house, aspectors in nodes_in_kendra:
            satisfied.append(f"{node} in kendra (house {house}) aspected by {aspectors}")
        counter_examples = [
            "If the node were not in a kendra, this specific combination would not form",
            "If no natural malefic aspected the node, the affliction would be reduced",
        ]
    else:
        # Check if nodes are in kendra but without malefic aspect
        nodes_in_kendra_no_aspect = []
        for node_name, node_pos in [("rahu", rahu), ("ketu", ketu)]:
            if node_pos is not None and node_pos.house_number in KENDRA_HOUSES:
                nodes_in_kendra_no_aspect.append(node_name)
        if nodes_in_kendra_no_aspect:
            missing.append(f"{nodes_in_kendra_no_aspect} in kendra but no malefic aspect")
        else:
            missing.append("No Rahu/Ketu in kendra houses")
        counter_examples = []

    involved_planets = tuple(n for n, _, _ in nodes_in_kendra) if nodes_in_kendra else ()
    involved_houses = tuple(h for _, h, _ in nodes_in_kendra) if nodes_in_kendra else ()
    trace.append(f"Step 2: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-ARY-011", name="Rahu/Ketu in Kendras with Malefic Aspect",
        category="Arishta Yoga", source_text="BPHS", rule_version="2.0",
        is_present=is_present, strength="full" if is_present else None,
        involved_planets=involved_planets,
        involved_houses=involved_houses,
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )
