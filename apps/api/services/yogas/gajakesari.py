"""
AstroOS — Gajakesari Yoga (BPHS-OMY-001)

Jupiter in a kendra (1st/4th/7th/10th) counted from the Moon.

Deliberately built second in Phase 1 (see Design Audit §5): small and
contained, but introduces the houses-from-Moon primitive ahead of the
full Chandra Yoga category (Phase 2) needing it more heavily. Low risk
to get this primitive right early on a single simple yoga.

Core classical condition: Jupiter in kendra from Moon. Two additional
conditions affect strength (not presence) — Jupiter not debilitated and
not combust — reflecting the classical view that a "weak" Gajakesari
(technically present but with an afflicted Jupiter) is a lesser result
than a clean one.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.yoga_predicates import YogaContext, get_planet, is_in_kendra_from
from apps.api.services.yoga_registry import register_yoga

_graha_engine = GrahaEngine()


@register_yoga(
    yoga_id="BPHS-OMY-001", name="Gajakesari Yoga", category="Other Major Yoga",
    source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine", "GrahaEngine"),
)
def evaluate_gajakesari(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    jupiter = get_planet(ctx, "jupiter")
    moon = get_planet(ctx, "moon")
    if jupiter is None or moon is None:
        missing.append("jupiter or moon not found in chart")
        return YogaResult(
            yoga_id="BPHS-OMY-001", name="Gajakesari Yoga", category="Other Major Yoga",
            source_text="BPHS", rule_version="1.0", is_present=False,
            strength=None, missing=tuple(missing), trace=tuple(trace),
        )

    trace.append(f"Step 1: locate moon → house {moon.house_number}")
    trace.append(f"Step 2: locate jupiter → house {jupiter.house_number}")

    in_kendra = is_in_kendra_from(jupiter.house_number, moon.house_number)
    trace.append(f"Step 3: is jupiter's house a kendra from moon's house? {in_kendra}")

    if in_kendra:
        satisfied.append("Jupiter in Kendra from Moon")
    else:
        missing.append("Jupiter not in Kendra from Moon")

    is_present = in_kendra

    strength = None
    if is_present:
        not_debilitated = not _graha_engine.is_debilitated("jupiter", jupiter.rashi)
        not_combust = not jupiter.is_combust
        trace.append(f"Step 4: strength check — not_debilitated={not_debilitated}, not_combust={not_combust}")

        if not_debilitated:
            satisfied.append("Jupiter not debilitated")
        else:
            missing.append("Jupiter is debilitated (weakens the yoga)")

        if not_combust:
            satisfied.append("Jupiter not combust")
        else:
            missing.append("Jupiter is combust (weakens the yoga)")

        strength = "full" if (not_debilitated and not_combust) else "partial"
        trace.append(f"Step 5: rule satisfied, strength={strength}")

    return YogaResult(
        yoga_id="BPHS-OMY-001", name="Gajakesari Yoga", category="Other Major Yoga",
        source_text="BPHS", rule_version="1.0", is_present=is_present,
        strength=strength,
        involved_planets=("jupiter", "moon"),
        involved_houses=(jupiter.house_number, moon.house_number),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )
