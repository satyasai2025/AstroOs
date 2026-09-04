"""
AstroOS — Shared Degree Math Helpers

Two primitives independently reimplemented across services/*.py:

- normalize_degrees(): plain [0, 360) wraparound. Python's `%` on floats
  already returns a non-negative result for a positive divisor, so a single
  `% 360.0` is sufficient — no separate negative-input guard is needed.
- shorter_arc_distance(): the shorter-arc angular separation (0-180°)
  between two ecliptic longitudes, used by every Shadbala "closeness to an
  angle" component (Dig/Paksha/Uchcha/Yuddha Bala) and by transit pattern
  detection (planetary returns, aspect orbs).
"""

from __future__ import annotations


def normalize_degrees(deg: float) -> float:
    """Normalise any degree value to [0, 360)."""
    return deg % 360.0


def shorter_arc_distance(a: float, b: float) -> float:
    """Shorter-arc angular distance (0-180°) between two ecliptic longitudes."""
    diff = abs(a - b) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff
