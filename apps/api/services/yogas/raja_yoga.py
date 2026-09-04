"""
AstroOS — Kendra-Trikona Raja Yoga (BPHS-RY-001)

The central Raja Yoga formulation: the lord of a kendra house (1/4/7/10)
is associated (conjunct, mutual aspect, or one-way aspect) with the lord
of a trikona house (1/5/9).

House 1 is both a kendra and a trikona house — pairing it with itself is
excluded (trivial/vacuous), and any kendra/trikona pair whose lords
happen to be the same planet is also excluded for the same reason as
Dhana Yoga's 2nd-11th formulation. Builds directly on the house-lordship
placement lookup Dhana Yoga established (Design Audit §5).

All satisfying kendra/trikona lord pairs are reported, not just the
first found — a chart can have more than one.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_predicates import (
    KENDRA_HOUSES,
    TRIKONA_HOUSES,
    YogaContext,
    get_house,
    is_associated,
)
from apps.api.services.yoga_registry import register_yoga


@register_yoga(
    yoga_id="BPHS-RY-001", name="Kendra-Trikona Raja Yoga",
    category="Raja Yoga", source_text="BPHS", rule_version="1.0",
    requires=("D1", "HouseEngine", "AspectEngine"),
)
def evaluate_kendra_trikona_raja_yoga(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []
    involved_planets: set[str] = set()
    involved_houses: set[int] = set()

    checked_pairs: set[tuple[str, str]] = set()
    any_satisfied = False

    for kendra_house in sorted(KENDRA_HOUSES):
        for trikona_house in sorted(TRIKONA_HOUSES):
            if kendra_house == trikona_house:
                continue

            lord_kendra = get_house(ctx, kendra_house).lord
            lord_trikona = get_house(ctx, trikona_house).lord

            if lord_kendra == lord_trikona:
                continue  # same planet rules both — vacuous pairing

            pair_key = tuple(sorted((lord_kendra, lord_trikona)))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            trace.append(
                f"Checking kendra house {kendra_house} (lord {lord_kendra}) "
                f"vs trikona house {trikona_house} (lord {lord_trikona})"
            )
            associated = is_associated(ctx, lord_kendra, lord_trikona)
            trace.append(f"  is_associated({lord_kendra}, {lord_trikona}) → {associated}")

            if associated:
                any_satisfied = True
                satisfied.append(
                    f"Kendra lord {lord_kendra} (house {kendra_house}) associated with "
                    f"trikona lord {lord_trikona} (house {trikona_house})"
                )
                involved_planets.update({lord_kendra, lord_trikona})
                involved_houses.update({kendra_house, trikona_house})
            else:
                missing.append(
                    f"Kendra lord {lord_kendra} (house {kendra_house}) not associated with "
                    f"trikona lord {lord_trikona} (house {trikona_house})"
                )

    trace.append(f"Final: rule {'satisfied' if any_satisfied else 'not satisfied'} "
                  f"({len(satisfied)} of {len(checked_pairs)} pairs matched)")

    return YogaResult(
        yoga_id="BPHS-RY-001", name="Kendra-Trikona Raja Yoga",
        category="Raja Yoga", source_text="BPHS", rule_version="1.0",
        is_present=any_satisfied, strength="full" if any_satisfied else None,
        involved_planets=tuple(sorted(involved_planets)),
        involved_houses=tuple(sorted(involved_houses)),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
    )
