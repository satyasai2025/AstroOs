"""
AstroOS — TPhalitCore UDT Domain Models
=======================================
Implements the exact 6 User Defined Types (UDTs) specified by Vinay Jha
in Section 6 of 'Phalita MoE AI Model' (phalita-moe-ai-model.md):

  6.1 TPhalitContext       — Topic, temporal chart-level, and varga metadata
  6.2 TPhalitPlanet        — Signed numerical planetary state
  6.3 TPhalitBhava         — House score and occupant/lordship forces
  6.4 TPhalitAspect        — Continuous angular drishti forces
  6.5 TPhalitYoga          — Nonlinear yoga activations, cancellations & amplifications
  6.6 TPhalitFeatureVector — Hierarchical ML feature tensor with block totals
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional


class ChartLevelEnum(IntEnum):
    ANNUAL = 1      # Varsha Pravesha (360° solar cycle)
    MONTHLY = 2     # Maasa Pravesha (30° solar sign)
    VIDASHA = 3     # Pratyantara (2.5° solar sub-division)
    GOCHARA = 4     # Instantaneous transit moment


@dataclass(frozen=True)
class TPhalitContext:
    """
    Section 6.1: TPhalitContext
    Describes the topic, chart level, varga, and temporal weights for the calculation.
    """
    TopicID: int               # 1=Jataka, 2=Gold, 3=Rain, 4=Quake, 5=War/Political
    TimeJD: float              # Julian Day (UT)
    DateTimeText: str          # ISO formatted UTC string
    ChartLevel: int            # 1=Annual, 2=Monthly, 3=Vidasha, 4=Gochara
    VargaID: int               # 1=D1, 2=D2, 9=D9, 10=D10, 24=D24, 60=D60
    DegreePoint: float         # Current solar / reference degree in the cycle [0, 360)
    TemporalWeight: float      # Weight of this temporal level in total field
    VargaWeight: float         # Canonical Vimshopaka weight of this varga
    TargetHorizon: int         # Prediction horizon in days / degrees


@dataclass(frozen=True)
class TPhalitPlanet:
    """
    Section 6.2: TPhalitPlanet
    Signed numerical profile of a single Graha.
    """
    PlanetID: int              # 1=Sun, 2=Moon, 3=Mars, 4=Merc, 5=Jup, 6=Ven, 7=Sat, 8=Rahu, 9=Ketu
    PlanetName: str            # e.g. "Jupiter"
    NaturalNature: float       # Natural benefic (+1.0 Jup/Ven/Moon) vs malefic (-1.0 Sat/Mars/Rahu/Ketu)
    FunctionalNature: float    # Tri-Lagna Sudarshana Chakra functional score (+/-)
    HouseID: int               # Bhava placement (1 to 12)
    SignID: int                # Rashi placement (1 to 12)
    DignityRaw: float          # 1 to 9 (Neecha=1 to Exalted=9)
    DignityWeight: float       # BPHS Log-2 strength score (0 to 60)
    LordshipWeight: float      # Strength of houses ruled
    KarakaWeight: float        # Chara/Naisargika karaka weight
    AspectContribution: float  # Net aspect received from other grahas
    YogaContribution: float    # Amplifications / cancellations received from yogas
    FinalSignedEffect: float   # Net signed numerical effect [-1.0, +1.0]


@dataclass(frozen=True)
class TPhalitBhava:
    """
    Section 6.3: TPhalitBhava
    Signed numerical profile of a single house.
    """
    BhavaID: int               # 1 to 12
    SignID: int                # Primary Rashi of Bhava-Madhya (1 to 12)
    LordID: int                # PlanetID of the Bhava-Madhya lord
    OccupantCount: int         # Number of occupying grahas
    LordStrength: float        # S_eff of the lord (Main Strength * Varga Weight)
    OccupantEffect: float      # Net natural + functional nature of occupying planets
    AspectEffect: float        # Net aspect force cast on this house
    YogaEffect: float          # Yoga formations involving this house
    FinalBhavaScore: float     # Net signed house score [-1.0, +1.0]


@dataclass(frozen=True)
class TPhalitAspect:
    """
    Section 6.4: TPhalitAspect
    Angular drishti force between a planet and a target degree/point.
    """
    FromPlanet: int            # PlanetID of aspecting planet
    ToDegree: float            # Target sidereal degree [0, 360)
    AngularDistance: float     # Exact angular separation [0, 360)
    AspectType: int            # 7=Saptama(180°), 4=Chaturtha(90°), 8=Ashtama(210°), 5=Trikona(120°), 3=Tritiya(60°), 10=Dashama(270°)
    AspectStrength: float      # Virupas / normalized strength [0.0, 1.0] based on orb falloff
    SignedEffect: float        # AspectStrength * (NaturalNature + FunctionalNature)


@dataclass(frozen=True)
class TPhalitYoga:
    """
    Section 6.5: TPhalitYoga
    Nonlinear yoga activation, cancellation, or amplification.
    """
    YogaID: int                # Unique ID of the yoga
    YogaName: str              # e.g. "GajaKesari", "ViparitaRajaHarsha", "Neechabhanga"
    YogaClass: int             # 1=Raja, 2=Dhana, 3=Arishta, 4=Viparita, 5=Neechabhanga
    IsActive: bool             # True if formation conditions are satisfied
    RawStrength: float         # Base strength of the yoga
    SignedEffect: float        # Directional impact (+ for auspicious, - for arishta)
    CancelsFeatures: str       # Semicolon-separated feature IDs cancelled (e.g. "D1_Sat_Debilitation")
    SuppressesFeatures: str    # Feature IDs suppressed
    AmplifiesFeatures: str     # Feature IDs amplified (e.g. "D1_H10_Score;D1_Jup_Effect")
    FinalContribution: float   # Net contribution to feature vector


@dataclass(frozen=True)
class TPhalitFeatureVector:
    """
    Section 6.6: TPhalitFeatureVector
    Complete hierarchical feature vector for ML and deterministic inference.
    """
    AtomicFeatures: Dict[str, float]      # Flattened key-value pairs of all signed components
    BlockTotals: Dict[str, float]         # PlanetBlock, BhavaBlock, AspectBlock, YogaBlock, VargaBlock, TemporalBlock
    DeterministicScore: float             # Linear combination of block totals
    TargetValue: Optional[float]          # Ground truth event outcome (if historical)
    Metadata: TPhalitContext              # Contextual metadata
