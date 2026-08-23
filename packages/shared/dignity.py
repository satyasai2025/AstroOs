"""
AstroOS — Shared Dignity Computation

Extracted from apps/api/services/ephemeris_wrapper.py's previously-private
`_compute_dignity()` (Module 9 Phase 2 prerequisite work for Sthana Bala).
That function was always pure (planet, rashi, rashi_degree) -> dignity,
with zero dependency on chart context — it just lived in the wrong place
to be reused, duplicating GrahaEngine's separate, less-complete
is_exalted()/is_own_sign()/etc. boolean checks.

Lives in packages/shared/ (not apps/api/domain/ or a service module) so
both EphemerisWrapper (Module 2) and GrahaEngine (Module 5) can import it
without creating a backwards dependency — Module 2 must not depend on
Module 5. Returns a plain string (matching DignityType's enum values)
rather than DignityType itself, since DignityType lives in
apps/api/domain/ephemeris.py and packages/shared/ must not depend on
apps/ either; callers wrap the string into DignityType themselves.

This is also now the prerequisite for Saptavargaja Bala (Shadbala,
Sthana Bala's cross-varga sub-component): the same pure function works
for a divisional chart's varga_rashi/varga_rashi_degree exactly as it
does for a D1 chart's rashi/rashi_degree — no varga-specific logic
needed, since dignity is defined purely by (planet, sign, degree)
regardless of which chart that sign came from.
"""

from __future__ import annotations

from typing import Optional

from packages.shared.constants import (
    DEBILITATION_RASHIS,
    EXALTATION_DEGREES,
    MOOLATRIKONA_RASHIS,
    OWN_SIGNS,
)

_RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

# Degree ranges within which Moolatrikona applies (outside these ranges,
# the planet's own-sign placement in that same rashi still applies via
# OWN_SIGNS, just not at Moolatrikona strength). Standard BPHS convention
# — verified exact match against PyJHora's moola_trikona_range_of_planets
# (jhora/const.py) for all 7 classical grahas.
MOOLATRIKONA_RANGES: dict[str, tuple[float, float]] = {
    "sun":     (0.0, 20.0),     # Leo 0-20°
    "moon":    (3.0, 30.0),     # Taurus 3-30°
    "mars":    (0.0, 12.0),     # Aries 0-12°
    "mercury": (15.0, 20.0),    # Virgo 15-20°
    "jupiter": (0.0, 10.0),     # Sagittarius 0-10°
    "venus":   (0.0, 15.0),     # Libra 0-15°
    "saturn":  (0.0, 20.0),     # Aquarius 0-20°
}

# Alternate Moolatrikona convention (user-supplied research, not the
# standard BPHS/PyJHora ranges above — an explicitly opt-in alternate
# tradition, never the default). Differs from MOOLATRIKONA_RANGES in
# exactly two entries: Moon's Taurus range ends at 20° instead of 30°,
# and Venus's Libra range ends at 12° instead of 15° (mirroring Mars's
# 12° Aries boundary in the opposite sign). Every other planet/rashi
# matches the standard convention exactly.
MOOLATRIKONA_RANGES_ALT_RESEARCH: dict[str, tuple[float, float]] = {
    **MOOLATRIKONA_RANGES,
    "moon":  (3.0, 20.0),
    "venus": (0.0, 12.0),
}

MoolatrikonaConvention = str  # "classical" (default) or "alt_research"

# Simplified natural friend/enemy relationships (Naisargika Maitri).
FRIENDS: dict[str, list[str]] = {
    "sun":     ["moon", "mars", "jupiter"],
    "moon":    ["sun", "mercury"],
    "mars":    ["sun", "moon", "jupiter"],
    "mercury": ["sun", "venus"],
    "jupiter": ["sun", "moon", "mars"],
    "venus":   ["mercury", "saturn"],
    "saturn":  ["mercury", "venus"],
}
ENEMIES: dict[str, list[str]] = {
    "sun":     ["venus", "saturn"],
    "moon":    ["rahu", "ketu"],
    "mars":    ["mercury"],
    "mercury": ["moon"],
    "jupiter": ["mercury", "venus"],
    "venus":   ["sun", "moon"],
    "saturn":  ["sun", "moon", "mars"],
}


def compute_dignity_value(
    planet: str,
    rashi: str,
    rashi_degree: float,
    moolatrikona_convention: MoolatrikonaConvention = "classical",
) -> Optional[str]:
    """
    Compute classical Vedic dignity for a planet in a sign, at a given
    degree within that sign. Works identically for a D1 chart's own
    rashi/rashi_degree or a divisional chart's varga_rashi/
    varga_rashi_degree — dignity is defined purely by (planet, sign,
    degree), not by which chart that placement came from.

    Order of precedence: exalted -> debilitated -> moolatrikona -> own
    -> friendly -> enemy -> neutral.

    moolatrikona_convention: "classical" (default, matches PyJHora/BPHS
    exactly) or "alt_research" (an explicitly opt-in alternate Moon/Venus
    Moolatrikona boundary set — see MOOLATRIKONA_RANGES_ALT_RESEARCH's
    docstring). Never changes the default behavior of existing callers.

    Returns a plain string matching DignityType's enum values (e.g.
    "exalted"), or None for Rahu/Ketu (dignity not classically assigned
    in this schema) — callers wrap the string into DignityType
    themselves, since DignityType is not importable from this module
    (see module docstring on the packages/apps dependency direction).
    """
    if planet in ("rahu", "ketu"):
        return None

    active_moolatrikona_ranges = (
        MOOLATRIKONA_RANGES_ALT_RESEARCH if moolatrikona_convention == "alt_research"
        else MOOLATRIKONA_RANGES
    )

    if planet in EXALTATION_DEGREES:
        ex_rashi, _ = EXALTATION_DEGREES[planet]
        if rashi == ex_rashi:
            return "exalted"

    if planet in DEBILITATION_RASHIS:
        if rashi == DEBILITATION_RASHIS[planet]:
            return "debilitated"

    if planet in MOOLATRIKONA_RASHIS:
        if rashi == MOOLATRIKONA_RASHIS[planet]:
            start, end = active_moolatrikona_ranges.get(planet, (0.0, 30.0))
            if start <= rashi_degree < end:
                return "moolatrikona"

    if planet in OWN_SIGNS:
        if rashi in OWN_SIGNS[planet]:
            return "own"

    rashi_lord = None
    for r in _RASHI_LIST:
        if r == rashi:
            for graha_name, signs in OWN_SIGNS.items():
                if rashi in signs:
                    rashi_lord = graha_name
                    break
            break

    if rashi_lord:
        if rashi_lord in FRIENDS.get(planet, []):
            return "friendly"
        if rashi_lord in ENEMIES.get(planet, []):
            return "enemy"

    return "neutral"
