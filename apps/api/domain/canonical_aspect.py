"""
AstroOS — Canonical Drishti Domain Objects
==========================================
Source: Vinay Jha's Canonical Methodology (bhaavachalita.md, strength-of-a-house.md,
prediction-of-death.md, and Phalit.kkk A45_ShodashDrishti, frmDrishti).

Key Principles:
  1. Sphuta Drishti: Continuous 0 to 60 Virupa (Shashtiamsa) scale (100% = 60 virupas).
  2. Bhavesha Drishti: Lord's aspect on its own house protects it 100%;
     if aspect is 0, the baseline presence is 50% (30 virupas) per Jha's empirical law.
  3. Maitri Filter: An aspecting planet transfers its benefic qualities to friends,
     and transfers only malefic/rough traits to enemies (even if exalted).
  4. Sambandha Amplification: Conjunction or mutual reception with the house lord
     amplifies the aspect's potency.
  5. Divisional Drishti: Aspects evaluated in D-1, D-9, D-10, D-30, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DrishtiNature(str, Enum):
    BENEFIC_TRANSFER = "benefic_transfer"    # Friend receiving aspect -> benefic traits transferred
    MALEFIC_TRANSFER = "malefic_transfer"    # Enemy receiving aspect -> malefic/rough traits transferred
    NEUTRAL_TRANSFER = "neutral_transfer"    # Equal/neutral relation


@dataclass(frozen=True)
class DrishtiConfig:
    """Configurable options for Drishti calculations (Zero Hardcoding)."""
    enable_sphuta_continuous: bool = True          # 0..60 Virupas piecewise formula
    enable_bhavesha_50_percent_baseline: bool = True # Jha's 50% baseline when aspect is zero
    bhavesha_baseline_virupas: float = 30.0        # 50% of 60 virupas
    enable_maitri_filtering: bool = True           # Filter benefic vs malefic traits by Tatkalika/Panchadha Maitri
    enable_sambandha_amplification: bool = True    # Amplify aspect if aspecting planet is in sambandha with lord
    sambandha_amplification_factor: float = 1.5    # Multiplier (e.g. 1.5x or 2.0x)


@dataclass(frozen=True)
class SphutaDrishti:
    from_planet: str
    to_planet: str
    angle_deg: float
    virupas: float              # 0.0 to 60.0 Shashtiamsas
    percentage: float           # 0.0 to 100.0%
    aspect_type: str            # "universal_7th", "mars_special", "jupiter_special", "saturn_special", "partial"
    is_special: bool
    panchadha_relation: str     # "adhimitra", "mitra", "sama", "shatru", "adhishatru"
    transferred_nature: DrishtiNature
    is_sambandha_amplified: bool
    effective_virupas: float


@dataclass(frozen=True)
class BhaveshaDrishti:
    house_number: int
    rashi: str
    lord: str
    direct_aspect_virupas: float
    is_50_percent_baseline_active: bool
    effective_protection_virupas: float # min 30.0 if baseline active, up to 60.0
    trace: str


@dataclass(frozen=True)
class VargaDrishtiMatrix:
    varga_name: str             # "D1", "D9", "D10", "D30"
    sphuta_aspects: list[SphutaDrishti]
    total_benefic_virupas: float
    total_malefic_virupas: float