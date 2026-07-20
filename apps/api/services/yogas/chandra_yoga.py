"""
AstroOS — Chandra Yogas (BPHS-CY-001 through 008)

Moon-relative house combinations. Built first in Phase 2 (Design Audit
§5) since Gajakesari (Phase 1) already proved out the houses_from()
primitive on a simple case — every yoga here extends that directly
rather than introducing new infrastructure.

Phase 1 (v2.0.0):
  BPHS-CY-001 Sunapha   — any planet (excl. Sun) in the 2nd from Moon
  BPHS-CY-002 Anapha    — any planet (excl. Sun) in the 12th from Moon
  BPHS-CY-003 Durudhara — planets in BOTH the 2nd and 12th from Moon
  BPHS-CY-004 Kemadruma — no planets in 2nd/12th from Moon AND none
                          conjunct Moon (inauspicious; classical
                          cancellation exceptions, e.g. Moon in kendra
                          from lagna, are a Phase 3 refinement, not
                          implemented here — this is the base condition
                          only, reported honestly as such)
  BPHS-CY-005 Adhi Yoga — natural benefics in the 6th, 7th, and 8th
                          houses from Moon (full if all three occupied,
                          partial if 1-2 are)
  BPHS-CY-006 Chandra-Mangala Yoga — Moon and Mars associated

Phase 2 (v2.1.0 "Vistara"):
  BPHS-CY-007 Amavasya Yoga — Sun conjunct Moon (New Moon; within ~12 degrees)
  BPHS-CY-008 Vyatipata Yoga — Moon and Sun in mutual dusthana (8th from each other)
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_predicates import (
    KENDRA_HOUSES,
    NATURAL_MALEFICS,
    YogaContext,
    get_planet,
    houses_from,
    is_associated,
    is_natural_benefic,
    planets_in_house,
)
from apps.api.services.yoga_registry import register_yoga


def _moon_or_none(ctx: YogaContext):
    return get_planet(ctx, "moon")


@register_yoga(
    yoga_id="BPHS-CY-001", name="Sunapha Yoga", category="Chandra Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_sunapha(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    moon = _moon_or_none(ctx)
    if moon is None:
        return YogaResult(
            yoga_id="BPHS-CY-001", name="Sunapha Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    second_house = houses_from(moon.house_number, 2)
    trace.append(f"Step 2: 2nd from moon → house {second_house}")

    occupants = planets_in_house(ctx, second_house, exclude=("sun", "moon"))
    trace.append(f"Step 3: planets in house {second_house} (excl. sun/moon) → {occupants}")

    is_present = len(occupants) > 0
    satisfied = (f"Planet(s) {occupants} in 2nd from Moon",) if is_present else ()
    missing = () if is_present else ("No planet (other than Sun) in 2nd from Moon",)
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-CY-001", name="Sunapha Yoga", category="Chandra Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(["moon"] + occupants),
        involved_houses=(moon.house_number, second_house),
        satisfied=satisfied, missing=missing, trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-CY-002", name="Anapha Yoga", category="Chandra Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_anapha(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    moon = _moon_or_none(ctx)
    if moon is None:
        return YogaResult(
            yoga_id="BPHS-CY-002", name="Anapha Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    twelfth_house = houses_from(moon.house_number, 12)
    trace.append(f"Step 2: 12th from moon → house {twelfth_house}")

    occupants = planets_in_house(ctx, twelfth_house, exclude=("sun", "moon"))
    trace.append(f"Step 3: planets in house {twelfth_house} (excl. sun/moon) → {occupants}")

    is_present = len(occupants) > 0
    satisfied = (f"Planet(s) {occupants} in 12th from Moon",) if is_present else ()
    missing = () if is_present else ("No planet (other than Sun) in 12th from Moon",)
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-CY-002", name="Anapha Yoga", category="Chandra Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(["moon"] + occupants),
        involved_houses=(moon.house_number, twelfth_house),
        satisfied=satisfied, missing=missing, trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-CY-003", name="Durudhara Yoga", category="Chandra Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_durudhara(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    moon = _moon_or_none(ctx)
    if moon is None:
        return YogaResult(
            yoga_id="BPHS-CY-003", name="Durudhara Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    second_house = houses_from(moon.house_number, 2)
    twelfth_house = houses_from(moon.house_number, 12)
    second_occupants = planets_in_house(ctx, second_house, exclude=("sun", "moon"))
    twelfth_occupants = planets_in_house(ctx, twelfth_house, exclude=("sun", "moon"))
    trace.append(f"Step 2: 2nd from moon (house {second_house}) occupants → {second_occupants}")
    trace.append(f"Step 3: 12th from moon (house {twelfth_house}) occupants → {twelfth_occupants}")

    is_present = len(second_occupants) > 0 and len(twelfth_occupants) > 0
    satisfied, missing = [], []
    if second_occupants:
        satisfied.append(f"Planet(s) {second_occupants} in 2nd from Moon")
    else:
        missing.append("No planet (other than Sun) in 2nd from Moon")
    if twelfth_occupants:
        satisfied.append(f"Planet(s) {twelfth_occupants} in 12th from Moon")
    else:
        missing.append("No planet (other than Sun) in 12th from Moon")
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-CY-003", name="Durudhara Yoga", category="Chandra Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(["moon"] + second_occupants + twelfth_occupants),
        involved_houses=(moon.house_number, second_house, twelfth_house),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-CY-004", name="Kemadruma Yoga", category="Chandra Yoga",
    source_text="BPHS", rule_version="1.1",
    requires=("D1", "HouseEngine"),
)
def evaluate_kemadruma(ctx: YogaContext) -> Optional[YogaResult]:
    """
    rule_version 1.1 (was 1.0 in Phase 2): adds the most commonly-cited
    classical cancellation exception — Kemadruma is cancelled if the
    Moon itself is placed in a kendra (1st/4th/7th/10th) from the lagna.
    This is a genuine rule change, not a bugfix, which is exactly why the
    version was bumped rather than silently changed under "1.0" — any
    research comparing charts evaluated under 1.0 vs 1.1 will see
    different is_present values for charts where this specific
    cancellation applies, and the version field makes that visible
    rather than silently inconsistent.

    Other classical cancellation conditions (e.g. Moon aspected by
    specific benefics, Moon conjunct certain combinations) are still NOT
    implemented — this is one additional exception, not the complete
    classical set. Remains an explicit, tracked deferral.
    """
    trace: list[str] = []
    moon = _moon_or_none(ctx)
    if moon is None:
        return YogaResult(
            yoga_id="BPHS-CY-004", name="Kemadruma Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="1.1", is_present=False,
            strength=None, missing=("moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    second_house = houses_from(moon.house_number, 2)
    twelfth_house = houses_from(moon.house_number, 12)
    second_occupants = planets_in_house(ctx, second_house, exclude=("sun", "moon"))
    twelfth_occupants = planets_in_house(ctx, twelfth_house, exclude=("sun", "moon"))
    conjunct = planets_in_house(ctx, moon.house_number, exclude=("moon",))
    trace.append(f"Step 2: 2nd from moon occupants → {second_occupants}")
    trace.append(f"Step 3: 12th from moon occupants → {twelfth_occupants}")
    trace.append(f"Step 4: planets conjunct moon → {conjunct}")

    base_condition_met = not second_occupants and not twelfth_occupants and not conjunct
    satisfied, missing = [], []

    if not base_condition_met:
        if second_occupants:
            missing.append(f"Planet(s) {second_occupants} present in 2nd from Moon (blocks Kemadruma)")
        if twelfth_occupants:
            missing.append(f"Planet(s) {twelfth_occupants} present in 12th from Moon (blocks Kemadruma)")
        if conjunct:
            missing.append(f"Planet(s) {conjunct} conjunct Moon (blocks Kemadruma)")
        trace.append("Step 5: base condition not met — cancellation check not applicable")

        return YogaResult(
            yoga_id="BPHS-CY-004", name="Kemadruma Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="1.1", is_present=False, strength=None,
            involved_planets=("moon",), involved_houses=(moon.house_number,),
            satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        )

    satisfied.append("No planets in 2nd/12th from Moon or conjunct Moon (base affliction condition met)")
    trace.append("Step 5: base condition met — checking cancellation")

    moon_in_kendra_from_lagna = moon.house_number in KENDRA_HOUSES
    trace.append(f"Step 6: is Moon in kendra from lagna? {moon_in_kendra_from_lagna}")

    is_cancelled = moon_in_kendra_from_lagna
    is_present = base_condition_met and not is_cancelled

    if is_cancelled:
        satisfied.append("Cancelled: Moon is in a kendra house from lagna")
        missing.append("Kemadruma does not manifest — cancelled by Moon's kendra placement")
    trace.append(f"Step 7: final result — {'cancelled, not present' if is_cancelled else 'present, not cancelled'}")

    return YogaResult(
        yoga_id="BPHS-CY-004", name="Kemadruma Yoga", category="Chandra Yoga",
        source_text="BPHS", rule_version="1.1", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=("moon",), involved_houses=(moon.house_number,),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-CY-005", name="Adhi Yoga", category="Chandra Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_adhi_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    moon = _moon_or_none(ctx)
    if moon is None:
        return YogaResult(
            yoga_id="BPHS-CY-005", name="Adhi Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    houses_checked = {}
    satisfied, missing = [], []
    involved_planets = ["moon"]

    for offset in (6, 7, 8):
        target_house = houses_from(moon.house_number, offset)
        occupants = planets_in_house(ctx, target_house, exclude=("moon",))
        benefics_here = [p for p in occupants if is_natural_benefic(p)]
        houses_checked[offset] = (target_house, benefics_here)
        trace.append(
            f"Step {offset - 4}: {offset}th from moon (house {target_house}) "
            f"benefic occupants → {benefics_here}"
        )
        if benefics_here:
            satisfied.append(f"Benefic(s) {benefics_here} in {offset}th from Moon (house {target_house})")
            involved_planets.extend(benefics_here)
        else:
            missing.append(f"No benefic in {offset}th from Moon (house {target_house})")

    houses_with_benefics = sum(1 for _, (_, b) in houses_checked.items() if b)
    is_present = houses_with_benefics > 0
    strength = None
    if is_present:
        strength = "full" if houses_with_benefics == 3 else "partial"
    trace.append(f"Step 5: {houses_with_benefics}/3 houses have a benefic → strength={strength}")

    return YogaResult(
        yoga_id="BPHS-CY-005", name="Adhi Yoga", category="Chandra Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength=strength,
        involved_planets=tuple(dict.fromkeys(involved_planets)),
        involved_houses=(moon.house_number,) + tuple(h for h, _ in houses_checked.values()),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-CY-006", name="Chandra-Mangala Yoga", category="Chandra Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine", "AspectEngine"),
)
def evaluate_chandra_mangala(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    moon = get_planet(ctx, "moon")
    mars = get_planet(ctx, "mars")
    if moon is None or mars is None:
        return YogaResult(
            yoga_id="BPHS-CY-006", name="Chandra-Mangala Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("moon or mars not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    trace.append(f"Step 2: locate mars → house {mars.house_number}")
    associated = is_associated(ctx, "moon", "mars")
    trace.append(f"Step 3: is_associated(moon, mars) → {associated}")

    satisfied = ("Moon and Mars are associated (conjunct or aspecting)",) if associated else ()
    missing = () if associated else ("Moon and Mars are not associated",)
    trace.append(f"Step 4: rule {'satisfied' if associated else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-CY-006", name="Chandra-Mangala Yoga", category="Chandra Yoga",
        source_text="BPHS", rule_version="1.0", is_present=associated,
        strength="full" if associated else None,
        involved_planets=("moon", "mars"),
        involved_houses=(moon.house_number, mars.house_number),
        satisfied=satisfied, missing=missing, trace=tuple(trace),
    )


# ---------------------------------------------------------------------------
# Phase 2: Additional Chandra Yogas
# ---------------------------------------------------------------------------

@register_yoga(
    yoga_id="BPHS-CY-007", name="Amavasya Yoga", category="Chandra Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_amavasya(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Sun conjunct Moon (New Moon). Classically within ~12 degrees orb.
    This is the condition that produces Amavasya (no-moon / new moon) —
    when the Sun and Moon are conjunct in the same sign, the Moon is
    not visible (being near the same longitude as the Sun).

    Counter-examples (weakening conditions):
      - If Sun and Moon are in different signs, no Amavasya yoga
      - If Moon is waxing (Shukla Paksha), this condition is weaker
      - Moon combust (within ~6 degrees of Sun) intensifies the effect
    """
    trace: list[str] = []
    sun = get_planet(ctx, "sun")
    moon = get_planet(ctx, "moon")
    if sun is None or moon is None:
        return YogaResult(
            yoga_id="BPHS-CY-007", name="Amavasya Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=("sun or moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate sun → house {sun.house_number}, rashi {sun.rashi}")
    trace.append(f"Step 2: locate moon → house {moon.house_number}, rashi {moon.rashi}")

    same_sign = sun.rashi == moon.rashi
    same_house = sun.house_number == moon.house_number
    trace.append(f"Step 3: same sign? {same_sign}, same house? {same_house}")

    is_present = same_sign  # Amavasya requires same sign (conjunct in longitude)
    satisfied, missing = [], []
    counter_examples = []

    if is_present:
        satisfied.append(f"Sun and Moon conjunct in {sun.rashi} (same sign)")
        if moon.is_combust:
            satisfied.append("Moon is combust — intensifies Amavasya effect")
        counter_examples = [
            "If Moon moved to a different sign from Sun, Amavasya yoga would not form",
            "If Moon were waxing (Shukla Paksha) — not applicable here since same-sign Moon is always Amavasya",
        ]
    else:
        missing.append(f"Sun ({sun.rashi}) and Moon ({moon.rashi}) not in same sign")
        counter_examples = []

    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-CY-007", name="Amavasya Yoga", category="Chandra Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=("sun", "moon"),
        involved_houses=(sun.house_number, moon.house_number),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-CY-008", name="Vyatipata Yoga", category="Chandra Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_vyatipata(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Moon and Sun in mutual dusthana — Moon in the 8th from Sun (or
    equivalently, Sun in the 8th from Moon). This is an inauspicious
    Chandra Yoga indicating obstacles and difficulties.

    Note: some classical texts define Vyatipata more precisely using
    specific nakshatra positions. This implementation uses the commonly-cited
    house-based formulation (8th from Sun).

    Counter-examples:
      - If Moon is not in 8th from Sun, this yoga does not form
      - Jupiter aspect on Moon can mitigate the difficulty
      - Moon in kendra from lagna provides some protection
    """
    trace: list[str] = []
    sun = get_planet(ctx, "sun")
    moon = get_planet(ctx, "moon")
    if sun is None or moon is None:
        return YogaResult(
            yoga_id="BPHS-CY-008", name="Vyatipata Yoga", category="Chandra Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=("sun or moon not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate sun → house {sun.house_number}")
    trace.append(f"Step 2: locate moon → house {moon.house_number}")

    # Check if Moon is in 8th from Sun
    moon_from_sun = houses_from(sun.house_number, 8)
    is_moon_8th = moon.house_number == moon_from_sun
    trace.append(f"Step 3: 8th from sun = house {moon_from_sun}, moon at house {moon.house_number} → match? {is_moon_8th}")

    satisfied, missing = [], []
    counter_examples = []

    if is_moon_8th:
        satisfied.append(f"Moon is in the 8th house from Sun (house {moon_from_sun})")
        # Check mitigating factors
        moon_in_kendra = moon.house_number in KENDRA_HOUSES
        if moon_in_kendra:
            satisfied.append("Moon in kendra from lagna — provides some mitigation")
        counter_examples = [
            "If Moon moved to any house other than the 8th from Sun, this yoga would not form",
            "Jupiter aspecting Moon can mitigate the difficulties indicated by this yoga",
        ]
    else:
        missing.append(f"Moon is not in the 8th from Sun (at house {moon_from_sun})")
        counter_examples = []

    is_present = is_moon_8th
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-CY-008", name="Vyatipata Yoga", category="Chandra Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=("moon", "sun"),
        involved_houses=(moon.house_number, sun.house_number),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )
