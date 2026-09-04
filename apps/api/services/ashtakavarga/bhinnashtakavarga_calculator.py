"""
AstroOS — Bhinnashtakavarga Calculator (Module 10)

Computes one target graha's individual Ashtakavarga: for each of the 8
contributors (7 grahas + Lagna), mark the rashis their bindu table
assigns (counted cyclically from the contributor's own rashi), then sum
across all 8 contributors per rashi.
"""

from __future__ import annotations

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult
from packages.shared.ashtakavarga_bindu_table import BINDU_TABLE, CONTRIBUTORS, TARGET_PLANETS
from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]

_RULE_VERSION = "1.0"


def _rashi_at_offset(reference_rashi: str, offset: int) -> str:
    """
    The rashi that is `offset` positions from `reference_rashi`,
    cyclically (offset=1 is the reference rashi itself, matching the
    same 1-indexed convention used by houses_from() in yoga_predicates.py).
    """
    reference_index = _RASHI_LIST.index(reference_rashi)
    target_index = (reference_index + offset - 1) % 12
    return _RASHI_LIST[target_index]


class BhinnashtakavargaCalculator:
    """
    Stateless — needs only each contributor's rashi (7 planets' rashis +
    the lagna's rashi).
    """

    def calculate(
        self, target_planet: str, contributor_rashis: dict[str, str]
    ) -> BhinnashtakavargaResult:
        """
        `contributor_rashis` must have an entry for every name in
        CONTRIBUTORS ("sun".."saturn", "lagna") mapping to that
        contributor's current rashi.
        """
        if target_planet not in TARGET_PLANETS:
            raise ValueError(
                f"Bhinnashtakavarga is only computed for the 7 classical grahas, got {target_planet!r}"
            )

        missing = [c for c in CONTRIBUTORS if c not in contributor_rashis]
        if missing:
            raise ValueError(f"Missing rashi for contributor(s): {missing}")

        bindus_by_rashi = [0] * 12
        target_table = BINDU_TABLE[target_planet]

        for contributor, offsets in target_table.items():
            contributor_rashi = contributor_rashis[contributor]
            for offset in offsets:
                marked_rashi = _rashi_at_offset(contributor_rashi, offset)
                bindus_by_rashi[_RASHI_LIST.index(marked_rashi)] += 1

        return BhinnashtakavargaResult(
            target_planet=target_planet,
            bindus_by_rashi=tuple(bindus_by_rashi),
            total_bindus=sum(bindus_by_rashi),
            rule_version=_RULE_VERSION,
        )

    def calculate_all(
        self, contributor_rashis: dict[str, str]
    ) -> list[BhinnashtakavargaResult]:
        return [self.calculate(planet, contributor_rashis) for planet in TARGET_PLANETS]
