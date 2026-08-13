"""
AstroOS — Shared Rashi Offset Helper

Computes the classical Vedic house number (1..12) of one rashi as counted
cyclically from another, treating the reference rashi itself as house 1.

Both TransitEngine's house-from-natal-Moon (Gochara) and
MarriageTimingEngine's house-from-Venus / house-from-7th-cusp aspect checks
reduce to this same modular-arithmetic formula — only the rashi-name
vocabulary (and how a name is turned into an index) differs between them, so
callers still resolve their own rashi -> index lookup and pass indices here.
"""

from __future__ import annotations


def house_offset(reference_index: int, target_index: int, total_signs: int = 12) -> int:
    """House number (1..total_signs) of `target_index`, counted cyclically
    from `reference_index` (reference itself = house 1)."""
    return ((target_index - reference_index) % total_signs) + 1
