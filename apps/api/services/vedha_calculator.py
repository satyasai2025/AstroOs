"""
AstroOS — Vedha Calculator (Module 11 Phase 2)

Determines whether a transiting planet's Gochara (transit) effect is
obstructed (Vedha) or, for an unfavorable house, relieved (Vipreet
Vedha) by another planet simultaneously transiting the paired house.
See packages/shared/transit_vedha_table.py for the full sourcing note.
"""

from __future__ import annotations

from typing import Optional

from packages.shared.transit_vedha_table import NO_VEDHA_EXCEPTION, VEDHA, VIPREET_VEDHA


class VedhaCalculator:
    """Stateless — needs only each planet's current house-from-natal-Moon."""

    def classify_house(self, planet: str, house: int) -> Optional[bool]:
        """
        True if `house` is one of `planet`'s classical good houses (per
        the Vedha table), False if a classical bad house (per the
        Vipreet Vedha table), None if this source states no rule for
        this planet/house combination at all.
        """
        if house in VEDHA.get(planet, {}):
            return True
        if house in VIPREET_VEDHA.get(planet, {}):
            return False
        return None

    def check(
        self, planet: str, house: int, all_houses_from_moon: dict[str, int]
    ) -> tuple[bool, bool, Optional[str]]:
        """
        Returns (has_vedha, has_vipreet_vedha, obstructing_or_relieving_planet).

        `all_houses_from_moon` must map every OTHER transiting planet
        (not `planet` itself) to its own current house-from-natal-Moon,
        for the same transit moment.
        """
        exception_planet = NO_VEDHA_EXCEPTION.get(planet)

        good_house_table = VEDHA.get(planet, {})
        if house in good_house_table:
            target_house = good_house_table[house]
            for other_planet, other_house in all_houses_from_moon.items():
                if other_planet == planet or other_planet == exception_planet:
                    continue
                if other_house == target_house:
                    return True, False, other_planet
            return False, False, None

        bad_house_table = VIPREET_VEDHA.get(planet, {})
        if house in bad_house_table:
            target_house = bad_house_table[house]
            for other_planet, other_house in all_houses_from_moon.items():
                if other_planet == planet or other_planet == exception_planet:
                    continue
                if other_house == target_house:
                    return False, True, other_planet
            return False, False, None

        return False, False, None
