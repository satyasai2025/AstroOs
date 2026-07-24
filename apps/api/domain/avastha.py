"""
AstroOS — Avastha (Planetary State) Domain Objects

Classical planetary states (BPHS Ch. 6, "Avastha Adhyaya" and later
texts). Two of the several classical Avastha systems are implemented
here — see avastha_engine.py's module docstring for exactly why only
these two, and why Jagradadi (Shayanadi-derived) Avastha is
deliberately NOT implemented rather than approximated.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AvasthaResult:
    """Both computed Avasthas for one planet."""
    planet: str
    baladi_avastha: str
    baladi_trace: tuple[str, ...]
    deeptadi_avastha: str
    deeptadi_trace: tuple[str, ...]
