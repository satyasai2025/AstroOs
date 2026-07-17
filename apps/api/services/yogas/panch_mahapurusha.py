"""
AstroOS — Panch Mahapurusha Yoga (BPHS-PM-001 through 005)

Formed when Mars/Mercury/Jupiter/Venus/Saturn is in its own sign or
exalted, AND in a kendra (1st/4th/7th/10th) from the lagna.

Simplest yoga in the catalog — a single uniform rule applied to 5
planets, entirely satisfied by GrahaEngine.is_own_sign()/is_exalted()
plus KENDRA_HOUSES membership. Deliberately built first (see Design
Audit §5) to establish the evaluator/registry pattern with zero new
predicates required.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.yoga_predicates import KENDRA_HOUSES, YogaContext, get_planet
from apps.api.services.yoga_registry import register_yoga

_graha_engine = GrahaEngine()

# (yoga_id, name, planet)
_MAHAPURUSHA_YOGAS = [
    ("BPHS-PM-001", "Ruchaka Yoga", "mars"),
    ("BPHS-PM-002", "Bhadra Yoga", "mercury"),
    ("BPHS-PM-003", "Hamsa Yoga", "jupiter"),
    ("BPHS-PM-004", "Malavya Yoga", "venus"),
    ("BPHS-PM-005", "Sasa Yoga", "saturn"),
]


def _make_evaluator(yoga_id: str, name: str, planet: str):
    def evaluate(ctx: YogaContext) -> Optional[YogaResult]:
        trace: list[str] = []
        satisfied: list[str] = []
        missing: list[str] = []

        position = get_planet(ctx, planet)
        if position is None:
            missing.append(f"{planet} not found in chart")
            return YogaResult(
                yoga_id=yoga_id, name=name, category="Panch Mahapurusha",
                source_text="BPHS", rule_version="1.0", is_present=False,
                strength=None, missing=tuple(missing), trace=tuple(trace),
            )

        trace.append(f"Step 1: locate {planet} → house {position.house_number}, rashi {position.rashi}")

        is_own = _graha_engine.is_own_sign(planet, position.rashi)
        is_exalted = _graha_engine.is_exalted(planet, position.rashi)
        trace.append(f"Step 2: is_own_sign={is_own}, is_exalted={is_exalted}")

        if is_own:
            satisfied.append(f"{planet} in own sign ({position.rashi})")
        elif is_exalted:
            satisfied.append(f"{planet} exalted ({position.rashi})")
        else:
            missing.append(f"{planet} neither in own sign nor exalted (in {position.rashi})")

        is_kendra = position.house_number in KENDRA_HOUSES
        trace.append(f"Step 3: house {position.house_number} in kendra (1/4/7/10)? {is_kendra}")
        if is_kendra:
            satisfied.append(f"{planet} in kendra (house {position.house_number})")
        else:
            missing.append(f"{planet} not in kendra (in house {position.house_number})")

        is_present = (is_own or is_exalted) and is_kendra
        trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

        return YogaResult(
            yoga_id=yoga_id, name=name, category="Panch Mahapurusha",
            source_text="BPHS", rule_version="1.0", is_present=is_present,
            strength="full" if is_present else None,
            involved_planets=(planet,), involved_houses=(position.house_number,),
            satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        )
    return evaluate


for _yoga_id, _name, _planet in _MAHAPURUSHA_YOGAS:
    register_yoga(
        yoga_id=_yoga_id, name=_name, category="Panch Mahapurusha",
        source_text="BPHS", rule_version="1.0",
        requires=("D1", "HouseEngine", "GrahaEngine"),
    )(_make_evaluator(_yoga_id, _name, _planet))
