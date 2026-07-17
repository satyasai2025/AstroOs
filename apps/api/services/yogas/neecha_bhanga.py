"""
AstroOS — Neecha Bhanga Raja Yoga (BPHS-NBRY-001 through 009)

Cancellation of a planet's debilitation under specific conditions, which
itself is classically read as producing a Raja Yoga. Built last in Phase
1 (Design Audit §5) — the most complex item in the phase, benefiting from
every primitive already built and tested (dignity, house-lordship
placement, kendra-from-lagna, kendra-from-Moon via houses_from).

BPHS lists roughly 4-5 independent, alternative sufficient conditions for
cancellation. This implements three commonly-cited ones — any ONE being
true cancels the debilitation. This is NOT an exhaustive enumeration of
every classical cancellation clause; additional conditions are a Phase 3
refinement, tracked explicitly rather than silently assumed complete.

Implemented conditions (any one sufficient):
  (a) The dispositor of the debilitation sign is itself in a kendra from
      the lagna or from the Moon.
  (b) The planet that would be exalted in the debilitation sign is
      itself in a kendra from the lagna, OR is conjunct/aspecting the
      debilitated planet.
  (c) The dispositor of the debilitated planet is itself exalted (in its
      own current sign).
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.yoga_predicates import (
    KENDRA_HOUSES,
    YogaContext,
    dispositor_of,
    exalted_in_sign,
    get_planet,
    is_associated,
    is_in_kendra_from,
)
from apps.api.services.yoga_registry import register_yoga

_graha_engine = GrahaEngine()

# All 9 grahas have a defined debilitation sign in DEBILITATION_RASHIS.
# Rahu/Ketu debilitation is more contested across traditions than the 7
# classical grahas' — included for completeness since the shared
# constants table already defines it, not as a claim of universal
# agreement across all classical sources.
_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

_ID_PREFIX = "BPHS-NBRY-"


def _make_evaluator(yoga_id: str, planet: str):
    name = f"Neecha Bhanga Raja Yoga ({planet.capitalize()})"

    def evaluate(ctx: YogaContext) -> Optional[YogaResult]:
        trace: list[str] = []
        satisfied: list[str] = []
        missing: list[str] = []

        position = get_planet(ctx, planet)
        moon = get_planet(ctx, "moon")
        if position is None or moon is None:
            missing.append(f"{planet} or moon not found in chart")
            return YogaResult(
                yoga_id=yoga_id, name=name, category="Neecha Bhanga Raja Yoga",
                source_text="BPHS", rule_version="1.0", is_present=False,
                strength=None, missing=tuple(missing), trace=tuple(trace),
            )

        is_debilitated = _graha_engine.is_debilitated(planet, position.rashi)
        trace.append(f"Step 1: is {planet} debilitated? {is_debilitated} (rashi={position.rashi})")

        if not is_debilitated:
            missing.append(f"{planet} is not debilitated")
            return YogaResult(
                yoga_id=yoga_id, name=name, category="Neecha Bhanga Raja Yoga",
                source_text="BPHS", rule_version="1.0", is_present=False,
                strength=None, involved_planets=(planet,), missing=tuple(missing),
                trace=tuple(trace),
            )

        debilitation_rashi = position.rashi
        dispositor = dispositor_of(debilitation_rashi)
        dispositor_position = get_planet(ctx, dispositor)
        trace.append(f"Step 2: dispositor of {debilitation_rashi} → {dispositor}")

        # (a) dispositor in kendra from lagna or Moon
        cond_a = False
        if dispositor_position is not None:
            in_kendra_lagna = dispositor_position.house_number in KENDRA_HOUSES
            in_kendra_moon = is_in_kendra_from(dispositor_position.house_number, moon.house_number)
            cond_a = in_kendra_lagna or in_kendra_moon
            trace.append(
                f"Step 3: (a) dispositor {dispositor} in kendra from lagna={in_kendra_lagna}, "
                f"from moon={in_kendra_moon} → {cond_a}"
            )
            if cond_a:
                satisfied.append(f"(a) Dispositor {dispositor} is in a kendra house")
            else:
                missing.append(f"(a) Dispositor {dispositor} is not in a kendra house")
        else:
            trace.append(f"Step 3: (a) dispositor {dispositor} not found in chart → condition not evaluable")
            missing.append(f"(a) Dispositor {dispositor} not found in chart")

        # (b) the sign's exaltation-lord is in kendra from lagna, or conjunct/aspecting the debilitated planet
        cond_b = False
        exalt_lord = exalted_in_sign(debilitation_rashi)
        if exalt_lord is not None:
            exalt_lord_position = get_planet(ctx, exalt_lord)
            if exalt_lord_position is not None:
                exalt_in_kendra = exalt_lord_position.house_number in KENDRA_HOUSES
                exalt_associated = is_associated(ctx, exalt_lord, planet)
                cond_b = exalt_in_kendra or exalt_associated
                trace.append(
                    f"Step 4: (b) exaltation-lord {exalt_lord} in kendra={exalt_in_kendra}, "
                    f"associated with {planet}={exalt_associated} → {cond_b}"
                )
                if cond_b:
                    satisfied.append(f"(b) Exaltation-lord {exalt_lord} in kendra or associated with {planet}")
                else:
                    missing.append(f"(b) Exaltation-lord {exalt_lord} neither in kendra nor associated with {planet}")
            else:
                trace.append(f"Step 4: (b) exaltation-lord {exalt_lord} not found in chart → condition not evaluable")
                missing.append(f"(b) Exaltation-lord {exalt_lord} not found in chart")
        else:
            trace.append(f"Step 4: (b) no planet exalts in {debilitation_rashi} → condition not applicable")
            missing.append(f"(b) No planet exalts in {debilitation_rashi}")

        # (c) dispositor of the debilitated planet is itself exalted
        cond_c = False
        if dispositor_position is not None:
            cond_c = _graha_engine.is_exalted(dispositor, dispositor_position.rashi)
            trace.append(f"Step 5: (c) dispositor {dispositor} exalted in own position? {cond_c}")
            if cond_c:
                satisfied.append(f"(c) Dispositor {dispositor} is itself exalted")
            else:
                missing.append(f"(c) Dispositor {dispositor} is not exalted")
        else:
            trace.append(f"Step 5: (c) dispositor {dispositor} not found in chart → condition not evaluable")
            missing.append(f"(c) Dispositor {dispositor} not found in chart")

        cancelled = cond_a or cond_b or cond_c
        trace.append(f"Step 6: cancellation {'achieved' if cancelled else 'not achieved'} "
                      f"(a={cond_a}, b={cond_b}, c={cond_c})")

        return YogaResult(
            yoga_id=yoga_id, name=name, category="Neecha Bhanga Raja Yoga",
            source_text="BPHS", rule_version="1.0", is_present=cancelled,
            strength="cancelled" if cancelled else None,
            involved_planets=(planet, dispositor),
            involved_houses=(position.house_number,),
            satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        )
    return evaluate


for _i, _planet in enumerate(_PLANETS, start=1):
    _yoga_id = f"{_ID_PREFIX}{_i:03d}"
    register_yoga(
        yoga_id=_yoga_id, name=f"Neecha Bhanga Raja Yoga ({_planet.capitalize()})",
        category="Neecha Bhanga Raja Yoga", source_text="BPHS", rule_version="1.0",
        requires=("D1", "HouseEngine", "GrahaEngine", "AspectEngine"),
    )(_make_evaluator(_yoga_id, _planet))
