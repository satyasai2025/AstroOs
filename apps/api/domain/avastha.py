"""
AstroOS — Avastha (Planetary State) Domain Objects

Classical planetary states (BPHS Ch. 45):
1. Baladi Avastha (5-fold, degree-based)
2. Deeptadi Avastha (8-fold, dignity-based)
3. Jagradadi Avastha (3-fold, consciousness/alertness based)
4. Sayanadi Avastha (12-fold, activity-based)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AvasthaResult:
    """All 4 computed Avasthas for one planet."""
    planet: str
    baladi_avastha: str
    baladi_trace: tuple[str, ...]
    deeptadi_avastha: str
    deeptadi_trace: tuple[str, ...]
    jagradadi_avastha: Optional[str] = None
    jagradadi_trace: Optional[tuple[str, ...]] = None
    sayanadi_avastha: Optional[str] = None
    sayanadi_trace: Optional[tuple[str, ...]] = None

