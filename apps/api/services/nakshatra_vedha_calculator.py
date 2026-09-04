"""
AstroOS — Nakshatra Vedha Calculator (Sarvatobhadra Chakra)

Distinct from packages/shared/transit_vedha_table.py's Rashi/Gochara
Vedha (house-pair based, checked from natal Moon): this is nakshatra-
based, checked purely from planet-to-planet nakshatra geometry on the
Sarvatobhadra Chakra (SBC) grid — see packages/shared/sarvatobhadra_grid.py
for the grid derivation and sourcing.

Per Saravali (https://saravali.github.io/astrology/sbc_vedhas.html): a
planet in direct motion casts its Vedha ray Forward (clockwise
diagonal); a retrograde planet casts it Backward (counter-clockwise
diagonal); a stationary planet casts it Opposite (straight across). This
module only distinguishes direct vs retrograde (the two states this
codebase already computes via is_retrograde) — true "stationary" would
need a near-zero-speed threshold this app doesn't classify anywhere
else, so it's not modeled here; a direct-but-near-stationary planet is
treated as direct (Forward), which is a known simplification, not a
fabricated third state.

Unlike Rashi Vedha, Saravali does not describe Nakshatra Vedha as
inherently good-house/bad-house — it's presented as a general
obstruction relationship between nakshatras. So this reports a plain
Active/Clear obstruction, not a favorable/unfavorable judgment.
"""

from __future__ import annotations

from typing import Optional

from packages.shared.sarvatobhadra_grid import (
    SBC_BORDER,
    backward_vedha_target,
    forward_vedha_target,
)


def is_sbc_nakshatra(nakshatra: str) -> bool:
    """True if `nakshatra` (standard 27-system token, or "abhijit") has a
    position on the SBC border grid."""
    return nakshatra in SBC_BORDER


class NakshatraVedhaCalculator:
    """Stateless — needs each planet's current (28-system) nakshatra and
    motion state, plus every other planet's current (28-system)
    nakshatra for the same transit moment."""

    def target_nakshatra(self, nakshatra: str, is_retrograde: bool) -> tuple[str, str]:
        """Returns (target_nakshatra, vedha_type) — "forward" for direct
        motion, "backward" for retrograde."""
        if is_retrograde:
            return backward_vedha_target(nakshatra), "backward"
        return forward_vedha_target(nakshatra), "forward"

    def check(
        self,
        planet: str,
        nakshatra: str,
        is_retrograde: bool,
        all_nakshatras: dict[str, str],
    ) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Returns (has_vedha, obstructing_planet, vedha_type, target_nakshatra).

        `all_nakshatras` must map every OTHER transiting planet (not
        `planet` itself) to its own current (28-system) nakshatra, for
        the same transit moment.
        """
        target, vedha_type = self.target_nakshatra(nakshatra, is_retrograde)
        for other_planet, other_nakshatra in all_nakshatras.items():
            if other_planet == planet:
                continue
            if other_nakshatra == target:
                return True, other_planet, vedha_type, target
        return False, None, vedha_type, target
