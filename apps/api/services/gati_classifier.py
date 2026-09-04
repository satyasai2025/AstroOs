"""
AstroOS — Ashta Gati (Eight Planetary Speed States) Classifier

Classical Jyotish describes a graha's daily motion as one of eight
"Gati" (speed) states, derived from how its current speed compares to
its own mean daily motion: Vakra (retrograde), Manda/Mandatara (slower
than mean), Sama (near mean), Chara/Atichara (faster than mean), with
Vikala for near-stationary motion.

**Explicitly a simplified approximation, not verified classical
fidelity** — same honesty-over-precision judgment call already made in
shadbala/chesta_bala.py, which this module reuses mean-speed constants
from. True classical Gati (and its 8-way subdivision, including
Anuvakra/Kutila) is defined from the Sighra Kendra (heliocentric
anomaly) and from acceleration between consecutive days, neither of
which this codebase computes from a single instantaneous position.
Anuvakra and Kutila specifically require comparing motion across two
moments (just-turned-retrograde vs. just-turned-direct) and so are not
distinguishable from one instant — treat this as a reasonable stand-in
using only speed_deg_per_day and is_retrograde, not classical-text-exact.

Rahu/Ketu are excluded from the retrograde check: lunar nodes move
backward by definition (not a notable state for them the way it is for
the five classical grahas), so their Gati is read from speed magnitude
alone, against their own steady mean nodal rate.
"""

from __future__ import annotations

# Approximate mean geocentric daily motion, degrees/day (magnitude).
# Commonly-cited reference figures — mars/mercury/jupiter/venus/saturn
# match shadbala/chesta_bala.py's _APPROX_MEAN_SPEED exactly; sun/moon/
# rahu/ketu are added here since Gati (unlike Chesta Bala) classically
# applies to all 9 grahas, not just the 5 non-luminaries.
_APPROX_MEAN_SPEED: dict[str, float] = {
    "sun": 0.9856,
    "moon": 13.176,
    "mars": 0.524,
    "mercury": 1.383,
    "jupiter": 0.083,
    "venus": 1.2,
    "saturn": 0.034,
    "rahu": 0.0529,
    "ketu": 0.0529,
}

_STATIONARY_THRESHOLD = 0.01  # deg/day — below this, treated as stationary

_NODES = {"rahu", "ketu"}


def classify_gati(planet: str, speed_deg_per_day: float, is_retrograde: bool) -> str:
    """
    Returns one of: "vakra", "vikala", "mandatara", "manda", "sama",
    "chara", "atichara" — lowercase, matching the app's other enum-style
    string fields (e.g. dignity).
    """
    mean_speed = _APPROX_MEAN_SPEED.get(planet)
    if mean_speed is None or mean_speed <= 0:
        return "sama"

    abs_speed = abs(speed_deg_per_day)

    if abs_speed < _STATIONARY_THRESHOLD:
        return "vikala"

    if planet not in _NODES and is_retrograde:
        return "vakra"

    ratio = abs_speed / mean_speed
    if ratio < 0.25:
        return "mandatara"
    if ratio < 0.75:
        return "manda"
    if ratio < 1.25:
        return "sama"
    if ratio < 1.75:
        return "chara"
    return "atichara"
