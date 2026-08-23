"""
AstroOS — Sphuta Drishti Engine (Layer 6: Calculation Engine)

Stateless calculation service computing exact degree-based aspect strength
(Sphuta Drishti) in Virupas (0 to 60, where 60 Virupas = 1 Rupa = 100% aspect
strength) based on BPHS Chapter 28 piecewise equations.

Sphuta Drishti is the subtle degree-sensitive form of Graha Drishti calculated
from forward zodiacal angular distance D:
    D = (target_longitude - source_longitude) mod 360°  (0° <= D < 360°)

This service is purely mathematical and deterministic. It contains no database
queries, API routing, AI prompt logic, or astrological predictions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from apps.api.domain.ephemeris import SiderealPosition


@dataclass(frozen=True)
class SphutaDrishtiResult:
    """
    Result of a Sphuta Drishti calculation between a source longitude
    and a target longitude.
    """
    source_longitude: float
    target_longitude: float
    angular_distance: float  # D in degrees, 0 <= D < 360
    virupa_strength: float   # S in Virupas, 0.0 <= S <= 60.0
    percentage: float        # (virupa_strength / 60.0) * 100.0


def calculate_forward_distance(source_longitude: float, target_longitude: float) -> float:
    """
    Calculate the forward zodiacal angular distance D from source to target.
    D = (target - source) mod 360, where 0 <= D < 360.
    """
    d = (target_longitude - source_longitude) % 360.0
    return d if d >= 0.0 else d + 360.0


class SphutaDrishtiEngine:
    """
    Stateless calculation engine for degree-based aspect strength (Sphuta Drishti)
    in Virupas (0 to 60) per Brihat Parashara Hora Shastra (BPHS) Chapter 28.
    """

    def compute(
        self, from_planet: str, source_longitude: float, target_longitude: float
    ) -> SphutaDrishtiResult:
        """
        Compute Sphuta Drishti from a given planet at source_longitude toward
        target_longitude (another planet, house cusp, Lagna, or special point).
        """
        if not (0.0 <= source_longitude < 360.0):
            source_longitude = source_longitude % 360.0
            if source_longitude < 0:
                source_longitude += 360.0

        if not (0.0 <= target_longitude < 360.0):
            target_longitude = target_longitude % 360.0
            if target_longitude < 0:
                target_longitude += 360.0

        d = calculate_forward_distance(source_longitude, target_longitude)
        planet_key = from_planet.strip().lower()

        if planet_key == "saturn":
            virupa = self._compute_saturn(d)
        elif planet_key == "mars":
            virupa = self._compute_mars(d)
        elif planet_key == "jupiter":
            virupa = self._compute_jupiter(d)
        else:
            # Sun, Moon, Mercury, Venus, Rahu, Ketu, or generic points
            virupa = self._compute_general(d)

        # Defensive invariant: clamp virupa between 0.0 and 60.0
        virupa_clamped = max(0.0, min(60.0, virupa))
        percentage = round((virupa_clamped / 60.0) * 100.0, 4)

        return SphutaDrishtiResult(
            source_longitude=round(source_longitude, 4),
            target_longitude=round(target_longitude, 4),
            angular_distance=round(d, 4),
            virupa_strength=round(virupa_clamped, 4),
            percentage=percentage,
        )

    def _compute_general(self, d: float) -> float:
        """
        Sphuta Drishti formula for Sun, Moon, Mercury, and Venus.
        Valid for angular distance D (0 <= D < 360). Zero aspect for D <= 30 or D >= 300.
        """
        if d <= 30.0 or d >= 300.0:
            return 0.0
        if 30.0 < d <= 60.0:
            return (d / 2.0) - 15.0
        if 60.0 < d <= 90.0:
            return d - 45.0
        if 90.0 < d <= 120.0:
            return 90.0 - (d / 2.0)
        if 120.0 < d <= 150.0:
            return 150.0 - d
        if 150.0 < d <= 180.0:
            return (2.0 * d) - 300.0
        if 180.0 < d < 300.0:
            return 150.0 - (d / 2.0)
        return 0.0

    def _compute_saturn(self, d: float) -> float:
        """
        Saturn-specific Sphuta Drishti piecewise linear formula (BPHS Ch. 28).
        Saturn has special peak 4-Pada (60 Virupa) aspects on 3rd (60°) and 10th (270°).

        BUGFIX NOTE: the 60°<D<=90° and 90°<D<=120° segments used to be two
        separate lines (120-D, then 90-D/2) that disagreed at the shared
        boundary D=90 (30 Virupas vs 45 Virupas -- a discontinuous jump).
        No independent standalone-capped-at-60 Sputa Drishti source exists in
        PyJHora (only the un-normalized Shadbala-internal aggregation in
        strength.py's __drik_bala_calc_1, which is a different quantity per
        drik_bala.py's own docstring), so this was fixed by hand-deriving the
        single line that actually passes through the confirmed peak
        (D=60 -> 60 Virupas, from the neighbouring 30<D<=60 segment) and the
        confirmed 90<D<=120 segment's own value at D=120 (30 Virupas,
        matching the following 120<D<=150 segment). Both former segments
        collapse into one continuous line: 90 - D/2.
        """
        if d <= 30.0 or d >= 300.0:
            return 0.0
        if 30.0 < d <= 60.0:
            return (2.0 * d) - 60.0
        if 60.0 < d <= 120.0:
            return 90.0 - (d / 2.0)
        if 120.0 < d <= 150.0:
            return 150.0 - d
        if 150.0 < d <= 180.0:
            return (2.0 * d) - 300.0
        if 180.0 < d <= 240.0:
            return 150.0 - (d / 2.0)
        if 240.0 < d <= 270.0:
            return d - 210.0
        if 270.0 < d < 300.0:
            return 600.0 - (2.0 * d)
        return 0.0

    def _compute_mars(self, d: float) -> float:
        """
        Mars-specific Sphuta Drishti piecewise linear formula (BPHS Ch. 28).
        Mars has special peak 4-Pada (60 Virupa) aspects on 4th (90°) and 8th (210°).

        PROVENANCE NOTE / SOURCE RESOLUTION:
        The text source gives for 240° < D < 300°: `S = (150° - D/2`.
        BPHS Ch. 28 authoritative text gives S = 150° - D/2 for the interval from 180° to 300°
        (except in 210°..240° where S = 270° - D applies for the 8th aspect slope).
        Therefore, for 240° < D < 300°, S = 150° - D/2 evaluates continuously from
        30 Virupas at 240° down to 0 Virupas at 300°.

        BUGFIX NOTE: the old 180°<D<=210° segment (150-D/2) fell to 45 Virupas
        at D=210, but the following 210°<D<=240° segment (270-D) started at
        60 Virupas at D=210 -- a 15-Virupa discontinuity right at the 8th-house
        peak this function's own docstring claims (60 Virupas at D=210). No
        independent standalone-capped Sputa Drishti formula exists in PyJHora
        to arbitrate this (checked jhora/horoscope/chart/strength.py -- the
        only aspect-strength code there is the un-normalized Shadbala-internal
        __drik_bala_calc_1/_drik_bala, a different quantity per drik_bala.py's
        own docstring). Since both D=180 (7th, general peak) and D=210 (8th,
        Mars special peak) must independently equal 60 Virupas, the correct
        continuous fix is a flat plateau of 60 Virupas across 180°<D<=210°
        (mirroring the already-continuous 90°<D<=150° valley-and-recovery
        shape between the 4th-house peak at D=90 and the 7th-house peak at
        D=180 that was already present and already continuous).
        """
        if d <= 30.0 or d >= 300.0:
            return 0.0
        if 30.0 < d <= 60.0:
            return (d / 2.0) - 15.0
        if 60.0 < d <= 90.0:
            return (1.5 * d) - 75.0
        if 90.0 < d <= 150.0:
            return 150.0 - d
        if 150.0 < d <= 180.0:
            return (2.0 * d) - 300.0
        if 180.0 < d <= 210.0:
            return 60.0
        if 210.0 < d <= 240.0:
            return 270.0 - d
        if 240.0 < d < 300.0:
            return 150.0 - (d / 2.0)
        return 0.0

    def _compute_jupiter(self, d: float) -> float:
        """
        Jupiter-specific Sphuta Drishti piecewise linear formula (BPHS Ch. 28).
        Jupiter has special peak 4-Pada (60 Virupa) aspects on 5th (120°) and 9th (240°).

        PROVENANCE NOTE / SOURCE RESOLUTION:
        The text source lists an overlapping clause `180° < D < 300°: S = 150° - D/2` after
        `240° < D < 270°: S = 300° - D`.
        In classical BPHS Ch. 28, S = 150° - D/2 is the general background equation for D in 180°..300°,
        which is overridden by Jupiter's 9th house peak aspect.

        BUGFIX NOTE: the old segments here had two independently-verifiable
        bugs, found by hand-checking continuity at every shared boundary (no
        independent standalone-capped Sputa Drishti source exists in PyJHora
        to arbitrate the zone placement itself -- see sphuta_drishti_engine
        module docstring / drik_bala.py cross-check -- so only self-consistency
        bugs, not zone choice, were corrected):
          1. Old 120°<D<=150° segment (180-D) gave 30 Virupas at D=150, but the
             following 150°<D<=180° segment (2D-300) gives 0 at D=150+ --
             a discontinuity. Fixed by replacing 180-D with 300-2D, which
             still starts at the confirmed peak of 60 at D=120 (matching the
             preceding 90°<D<=120° segment D/2) and now correctly falls to 0
             at D=150 (matching the following segment).
          2. Old 210°<D<=240° segment (D-150) evaluated to 90 Virupas at
             D=240 -- outside the valid [0,60] range and contradicting this
             function's own docstring claim of "60 Virupas at 240°" (a plain
             arithmetic error in the original formula, not just a boundary
             mismatch). Fixed with 0.5*D-60, which is 45 at D=210 (matching
             the preceding 180°<D<=210° segment 150-D/2) and exactly 60 at
             D=240 as the docstring requires. The following 240°<D<=270°
             segment (300-D) was likewise refit to 420-1.5*D so it starts at
             60 at D=240 and still lands on the shared 150-D/2 background
             curve's value of 15 Virupas at D=270.
        """
        if d <= 30.0 or d >= 300.0:
            return 0.0
        if 30.0 < d <= 60.0:
            return (d / 2.0) - 15.0
        if 60.0 < d <= 90.0:
            return d - 45.0
        if 90.0 < d <= 120.0:
            return d / 2.0
        if 120.0 < d <= 150.0:
            return 300.0 - (2.0 * d)
        if 150.0 < d <= 180.0:
            return (2.0 * d) - 300.0
        if 180.0 < d <= 210.0:
            return 150.0 - (d / 2.0)
        if 210.0 < d <= 240.0:
            return (0.5 * d) - 60.0
        if 240.0 < d <= 270.0:
            return 420.0 - (1.5 * d)
        if 270.0 < d < 300.0:
            return 150.0 - (d / 2.0)
        return 0.0
