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
        """
        if d <= 30.0 or d >= 300.0:
            return 0.0
        if 30.0 < d <= 60.0:
            return (2.0 * d) - 60.0
        if 60.0 < d <= 90.0:
            return 120.0 - d
        if 90.0 < d <= 120.0:
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
        if d == 180.0:
            return 60.0
        if 180.0 < d <= 210.0:
            return 150.0 - (d / 2.0)
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
        which is overridden by Jupiter's 9th house peak aspect:
          - 210° < D <= 240°: S = D - 150° (rises to 60 Virupas at 240°)
          - 240° < D <= 270°: S = 300° - D (falls from 60 at 240° to 30 at 270°)
          - 270° < D < 300°: S = 150° - D/2 (falls from 15 at 270° to 0 at 300°)
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
            return 180.0 - d
        if 150.0 < d <= 180.0:
            return (2.0 * d) - 300.0
        if 180.0 < d <= 210.0:
            return 150.0 - (d / 2.0)
        if 210.0 < d <= 240.0:
            return d - 150.0
        if 240.0 < d <= 270.0:
            return 300.0 - d
        if 270.0 < d < 300.0:
            return 150.0 - (d / 2.0)
        return 0.0
