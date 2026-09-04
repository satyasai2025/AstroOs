"""
AstroOS — Solar Yogas (BPHS-OMY-002 through 005)

Sun-relative combinations — the same 2nd/12th-from-reference structure
as Sunapha/Anapha/Durudhara (Chandra Yogas), but counted from the Sun
instead of the Moon. Reuses houses_from()/planets_in_house() directly,
no new predicates needed.

  BPHS-OMY-002 Vosi Yoga        — planet(s) (excl. Moon) in the 2nd from Sun
  BPHS-OMY-003 Vasi Yoga        — planet(s) (excl. Moon) in the 12th from Sun
  BPHS-OMY-004 Ubhayachari Yoga — planets in BOTH the 2nd and 12th from Sun
  BPHS-OMY-005 Budhaditya Yoga  — Sun and Mercury conjunct
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_predicates import (
    YogaContext,
    get_planet,
    houses_from,
    is_conjunct,
    planets_in_house,
)
from apps.api.services.yoga_registry import register_yoga


def _sun_or_none(ctx: YogaContext):
    return get_planet(ctx, "sun")


@register_yoga(
    yoga_id="BPHS-OMY-002", name="Vosi Yoga", category="Other Major Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_vosi(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    sun = _sun_or_none(ctx)
    if sun is None:
        return YogaResult(
            yoga_id="BPHS-OMY-002", name="Vosi Yoga", category="Other Major Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("sun not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate sun → house {sun.house_number}")
    second_house = houses_from(sun.house_number, 2)
    trace.append(f"Step 2: 2nd from sun → house {second_house}")

    occupants = planets_in_house(ctx, second_house, exclude=("sun", "moon"))
    trace.append(f"Step 3: planets in house {second_house} (excl. sun/moon) → {occupants}")

    is_present = len(occupants) > 0
    satisfied = (f"Planet(s) {occupants} in 2nd from Sun",) if is_present else ()
    missing = () if is_present else ("No planet (other than Moon) in 2nd from Sun",)
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-OMY-002", name="Vosi Yoga", category="Other Major Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(["sun"] + occupants),
        involved_houses=(sun.house_number, second_house),
        satisfied=satisfied, missing=missing, trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-OMY-003", name="Vasi Yoga", category="Other Major Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_vasi(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    sun = _sun_or_none(ctx)
    if sun is None:
        return YogaResult(
            yoga_id="BPHS-OMY-003", name="Vasi Yoga", category="Other Major Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("sun not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate sun → house {sun.house_number}")
    twelfth_house = houses_from(sun.house_number, 12)
    trace.append(f"Step 2: 12th from sun → house {twelfth_house}")

    occupants = planets_in_house(ctx, twelfth_house, exclude=("sun", "moon"))
    trace.append(f"Step 3: planets in house {twelfth_house} (excl. sun/moon) → {occupants}")

    is_present = len(occupants) > 0
    satisfied = (f"Planet(s) {occupants} in 12th from Sun",) if is_present else ()
    missing = () if is_present else ("No planet (other than Moon) in 12th from Sun",)
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-OMY-003", name="Vasi Yoga", category="Other Major Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(["sun"] + occupants),
        involved_houses=(sun.house_number, twelfth_house),
        satisfied=satisfied, missing=missing, trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-OMY-004", name="Ubhayachari Yoga", category="Other Major Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_ubhayachari(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    sun = _sun_or_none(ctx)
    if sun is None:
        return YogaResult(
            yoga_id="BPHS-OMY-004", name="Ubhayachari Yoga", category="Other Major Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("sun not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate sun → house {sun.house_number}")
    second_house = houses_from(sun.house_number, 2)
    twelfth_house = houses_from(sun.house_number, 12)
    second_occupants = planets_in_house(ctx, second_house, exclude=("sun", "moon"))
    twelfth_occupants = planets_in_house(ctx, twelfth_house, exclude=("sun", "moon"))
    trace.append(f"Step 2: 2nd from sun (house {second_house}) occupants → {second_occupants}")
    trace.append(f"Step 3: 12th from sun (house {twelfth_house}) occupants → {twelfth_occupants}")

    is_present = len(second_occupants) > 0 and len(twelfth_occupants) > 0
    satisfied, missing = [], []
    if second_occupants:
        satisfied.append(f"Planet(s) {second_occupants} in 2nd from Sun")
    else:
        missing.append("No planet (other than Moon) in 2nd from Sun")
    if twelfth_occupants:
        satisfied.append(f"Planet(s) {twelfth_occupants} in 12th from Sun")
    else:
        missing.append("No planet (other than Moon) in 12th from Sun")
    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-OMY-004", name="Ubhayachari Yoga", category="Other Major Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(["sun"] + second_occupants + twelfth_occupants),
        involved_houses=(sun.house_number, second_house, twelfth_house),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )


@register_yoga(
    yoga_id="BPHS-OMY-005", name="Budhaditya Yoga", category="Other Major Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
def evaluate_budhaditya(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    sun = get_planet(ctx, "sun")
    mercury = get_planet(ctx, "mercury")
    if sun is None or mercury is None:
        return YogaResult(
            yoga_id="BPHS-OMY-005", name="Budhaditya Yoga", category="Other Major Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=("sun or mercury not found in chart",), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate sun → house {sun.house_number}")
    trace.append(f"Step 2: locate mercury → house {mercury.house_number}")
    conjunct = is_conjunct(ctx, "sun", "mercury")
    trace.append(f"Step 3: is_conjunct(sun, mercury) → {conjunct}")

    satisfied = ("Sun and Mercury are conjunct",) if conjunct else ()
    missing = () if conjunct else ("Sun and Mercury are not conjunct",)
    trace.append(f"Step 4: rule {'satisfied' if conjunct else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-OMY-005", name="Budhaditya Yoga", category="Other Major Yoga",
        source_text="BPHS", rule_version="1.0", is_present=conjunct,
        strength="full" if conjunct else None,
        involved_planets=("sun", "mercury"), involved_houses=(sun.house_number,),
        satisfied=satisfied, missing=missing, trace=tuple(trace),
    )
