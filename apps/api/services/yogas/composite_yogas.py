"""
AstroOS — Composite Yogas (BPHS-COMP-001 through 007)

Multi-planet/house combinations that produce classical yogas by bringing
together conditions across multiple houses and planetary dignities.

  BPHS-COMP-001 Lakshmi Yoga   — 9th lord in own/exalted sign + Venus in kendra
  BPHS-COMP-002 Saraswati Yoga — Jupiter, Venus, Mercury all in kendra from lagna
  BPHS-COMP-003 Harsha Yoga    — 6th lord in 6th house
  BPHS-COMP-004 Sarala Yoga    — 8th lord in 8th house
  BPHS-COMP-005 Vimala Yoga    — 12th lord in 12th house
  BPHS-COMP-006 Dridha Yoga    — 6th, 8th, and 12th lords all in own houses
  BPHS-COMP-007 Guru-Mangala Yoga — Jupiter aspecting Mars

These yogas combine house-lordship, dignity, and positional factors —
the hallmark of composite yoga detection. Each evaluator checks multiple
conditions simultaneously, reporting which sub-conditions are satisfied
and which are not.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.yoga_predicates import (
    KENDRA_HOUSES,
    YogaContext,
    get_house,
    get_planet,
    is_associated,
)
from apps.api.services.yoga_registry import register_yoga

_graha_engine = GrahaEngine()


@register_yoga(
    yoga_id="BPHS-COMP-001", name="Lakshmi Yoga", category="Composite Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_lakshmi_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    """
    The 9th house lord in its own sign or exalted, AND Venus in a kendra
    from lagna. A classical wealth and prosperity combination — the 9th
    lord represents fortune/bhagya, and Venus represents luxury/comfort.

    Counter-examples:
      - If 9th lord is debilitated, the yoga weakens significantly
      - If Venus is debilitated or in dusthana, the prosperity element weakens
    """
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    house_9 = get_house(ctx, 9)
    lord_9 = house_9.lord
    trace.append(f"Step 1: 9th house lord → {lord_9}")

    lord_9_pos = get_planet(ctx, lord_9)
    if lord_9_pos is None:
        missing.append(f"{lord_9} not found in chart")
        return YogaResult(
            yoga_id="BPHS-COMP-001", name="Lakshmi Yoga", category="Composite Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=tuple(missing), trace=tuple(trace),
        )

    # Condition 1: 9th lord in own sign or exalted
    lord_9_own = _graha_engine.is_own_sign(lord_9, lord_9_pos.rashi)
    lord_9_exalted = _graha_engine.is_exalted(lord_9, lord_9_pos.rashi)
    cond1 = lord_9_own or lord_9_exalted
    trace.append(f"Step 2: {lord_9} own sign={lord_9_own}, exalted={lord_9_exalted} → cond1={cond1}")

    if cond1:
        satisfied.append(f"9th lord {lord_9} {'exalted' if lord_9_exalted else 'in own sign'} ({lord_9_pos.rashi})")
    else:
        missing.append(f"9th lord {lord_9} neither exalted nor in own sign (in {lord_9_pos.rashi})")

    # Condition 2: Venus in kendra from lagna
    venus = get_planet(ctx, "venus")
    if venus is None:
        missing.append("Venus not found in chart")
        cond2 = False
    else:
        cond2 = venus.house_number in KENDRA_HOUSES
        trace.append(f"Step 3: Venus in house {venus.house_number}, kendra? {cond2}")
        if cond2:
            satisfied.append(f"Venus in kendra (house {venus.house_number})")
        else:
            missing.append(f"Venus not in kendra (in house {venus.house_number})")

    is_present = cond1 and cond2
    counter_examples = []
    if is_present:
        counter_examples = [
            f"If {lord_9} were debilitated, the fortune element would weaken",
            "If Venus were debilitated or in a dusthana, the prosperity element would weaken",
        ]

    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'} (cond1={cond1}, cond2={cond2})")

    return YogaResult(
        yoga_id="BPHS-COMP-001", name="Lakshmi Yoga", category="Composite Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=(lord_9, "venus"),
        involved_houses=(lord_9_pos.house_number, venus.house_number if venus else 0),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-COMP-002", name="Saraswati Yoga", category="Composite Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_saraswati_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Jupiter, Venus, and Mercury all in kendra houses from lagna.
    The three planets of wisdom, beauty, and intellect combined in
    angular houses — classical indicator of learning, arts, and eloquence.
    """
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    planets_to_check = ["jupiter", "venus", "mercury"]
    in_kendra = []
    not_in_kendra = []

    for planet in planets_to_check:
        pos = get_planet(ctx, planet)
        if pos is None:
            missing.append(f"{planet} not found in chart")
            not_in_kendra.append(planet)
            continue
        if pos.house_number in KENDRA_HOUSES:
            in_kendra.append(planet)
            satisfied.append(f"{planet} in kendra (house {pos.house_number})")
        else:
            not_in_kendra.append(planet)
            missing.append(f"{planet} not in kendra (in house {pos.house_number})")

    trace.append(f"Step 1: in kendra → {in_kendra}, not in kendra → {not_in_kendra}")

    is_present = len(in_kendra) == 3
    counter_examples = []
    if is_present:
        counter_examples = [
            "If any of Jupiter/Venus/Mercury moved to a non-kendra house, Saraswati Yoga would break",
            "If any of these three were debilitated, the yoga would be weakened",
        ]

    trace.append(f"Step 2: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-COMP-002", name="Saraswati Yoga", category="Composite Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(in_kendra),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


def _make_tri_lord_yoga_evaluator(
    yoga_id: str, name: str, house_number: int
):
    """
    Factory for yogas where a specific house's lord sits in that same house.
    Harsha (6th lord in 6th), Sarala (8th lord in 8th), Vimala (12th lord in 12th).
    """
    def evaluate(ctx: YogaContext) -> Optional[YogaResult]:
        trace: list[str] = []
        satisfied: list[str] = []
        missing: list[str] = []

        house = get_house(ctx, house_number)
        lord = house.lord
        trace.append(f"Step 1: house {house_number} lord → {lord}")

        lord_pos = get_planet(ctx, lord)
        if lord_pos is None:
            missing.append(f"{lord} not found in chart")
            return YogaResult(
                yoga_id=yoga_id, name=name, category="Composite Yoga",
                source_text="BPHS", rule_version="2.0", is_present=False,
                strength=None, missing=tuple(missing), trace=tuple(trace),
            )

        in_own_house = lord_pos.house_number == house_number
        trace.append(f"Step 2: {lord} in house {lord_pos.house_number}, own house ({house_number})? {in_own_house}")

        if in_own_house:
            satisfied.append(f"House {house_number} lord ({lord}) placed in house {house_number}")
        else:
            missing.append(f"House {house_number} lord ({lord}) not in house {house_number} (in house {lord_pos.house_number})")

        counter_examples = []
        if in_own_house:
            counter_examples = [
                f"If {lord} moved to a different house, this yoga would break",
                f"If {lord} were debilitated, the yoga would be weakened even in its own house",
            ]

        trace.append(f"Step 3: rule {'satisfied' if in_own_house else 'not satisfied'}")

        return YogaResult(
            yoga_id=yoga_id, name=name, category="Composite Yoga",
            source_text="BPHS", rule_version="2.0", is_present=in_own_house,
            strength="full" if in_own_house else None,
            involved_planets=(lord,),
            involved_houses=(house_number,),
            satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
            counter_examples=tuple(counter_examples),
        )
    return evaluate


# BPHS-COMP-003: Harsha Yoga — 6th lord in 6th house
register_yoga(
    yoga_id="BPHS-COMP-003", name="Harsha Yoga", category="Composite Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)(_make_tri_lord_yoga_evaluator("BPHS-COMP-003", "Harsha Yoga", 6))

# BPHS-COMP-004: Sarala Yoga — 8th lord in 8th house
register_yoga(
    yoga_id="BPHS-COMP-004", name="Sarala Yoga", category="Composite Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)(_make_tri_lord_yoga_evaluator("BPHS-COMP-004", "Sarala Yoga", 8))

# BPHS-COMP-005: Vimala Yoga — 12th lord in 12th house
register_yoga(
    yoga_id="BPHS-COMP-005", name="Vimala Yoga", category="Composite Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)(_make_tri_lord_yoga_evaluator("BPHS-COMP-005", "Vimala Yoga", 12))


@register_yoga(
    yoga_id="BPHS-COMP-006", name="Dridha Yoga", category="Composite Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_dridha_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    """
    6th, 8th, and 12th lords ALL placed in their respective houses
    (6th lord in 6th, 8th lord in 8th, 12th lord in 12th). A rare
    combination of all three dusthana lords being in their own houses,
    classically indicating strong protection from enemies, obstacles,
    and losses.
    """
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    dusthana_status: dict[int, tuple[str, bool]] = {}
    all_in_own = True

    for house_num in (6, 8, 12):
        house = get_house(ctx, house_num)
        lord = house.lord
        lord_pos = get_planet(ctx, lord)
        if lord_pos is None:
            missing.append(f"{lord} (house {house_num} lord) not found in chart")
            all_in_own = False
            continue

        in_own = lord_pos.house_number == house_num
        dusthana_status[house_num] = (lord, in_own)
        trace.append(f"House {house_num}: lord {lord} in house {lord_pos.house_number}, own? {in_own}")

        if in_own:
            satisfied.append(f"House {house_num} lord ({lord}) in house {house_num}")
        else:
            missing.append(f"House {house_num} lord ({lord}) not in house {house_num} (in {lord_pos.house_number})")
            all_in_own = False

    trace.append(f"Step 1: all in own houses? {all_in_own}")

    counter_examples = []
    if all_in_own:
        counter_examples = [
            "If any of the three dusthana lords moved to a different house, Dridha Yoga would break",
            "If any dusthana lord were debilitated, the yoga would be weakened",
        ]

    trace.append(f"Step 2: rule {'satisfied' if all_in_own else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-COMP-006", name="Dridha Yoga", category="Composite Yoga",
        source_text="BPHS", rule_version="2.0", is_present=all_in_own,
        strength="full" if all_in_own else None,
        involved_planets=tuple(lord for lord, _ in dusthana_status.values() if lord is not None),
        involved_houses=(6, 8, 12),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


@register_yoga(
    yoga_id="BPHS-COMP-007", name="Guru-Mangala Yoga", category="Composite Yoga",
    source_text="BPHS", rule_version="2.0",
    requires=("D1", "HouseEngine", "AspectEngine"),
)
def evaluate_guru_mangala_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    """
    Jupiter (Guru) and Mars (Mangala) associated — conjunct, mutual
    aspect, or one-way aspect. Classical combination for righteous
    action, courage guided by wisdom, and dharmic energy.

    Note: this is different from Chandra-Mangala Yoga (BPHS-CY-006)
    which involves Moon-Mars. Guru-Mangala is Jupiter-Mars.
    """
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    jupiter = get_planet(ctx, "jupiter")
    mars = get_planet(ctx, "mars")
    if jupiter is None or mars is None:
        missing.append("jupiter or mars not found in chart")
        return YogaResult(
            yoga_id="BPHS-COMP-007", name="Guru-Mangala Yoga", category="Composite Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=tuple(missing), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate jupiter → house {jupiter.house_number}")
    trace.append(f"Step 2: locate mars → house {mars.house_number}")

    associated = is_associated(ctx, "jupiter", "mars")
    trace.append(f"Step 3: is_associated(jupiter, mars) → {associated}")

    if associated:
        satisfied.append("Jupiter and Mars are associated (conjunct or aspecting)")
    else:
        missing.append("Jupiter and Mars are not associated")

    counter_examples = []
    if associated:
        counter_examples = [
            "If Jupiter and Mars were in different houses with no aspect, this yoga would not form",
            "If either Jupiter or Mars were debilitated, the yoga would be weakened",
        ]

    trace.append(f"Step 4: rule {'satisfied' if associated else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-COMP-007", name="Guru-Mangala Yoga", category="Composite Yoga",
        source_text="BPHS", rule_version="2.0", is_present=associated,
        strength="full" if associated else None,
        involved_planets=("jupiter", "mars"),
        involved_houses=(jupiter.house_number, mars.house_number),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )
