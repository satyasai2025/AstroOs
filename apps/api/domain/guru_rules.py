"""
AstroOS — Guru Research Layer Domain Models

Data models representing custom research rules, degree zones,
and planetary evaluation results for proprietary/teacher research paradigms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class GuruZoneType(str, Enum):
    EXALTATION = "exaltation"
    DEBILITATION = "debilitation"
    MOOLATRIKONA = "moolatrikona"
    OWN_SIGN = "own_sign"
    FRIENDLY = "friendly"
    ENEMY = "enemy"
    NEUTRAL = "neutral"
    SPECIAL = "special"


@dataclass(frozen=True)
class GuruZoneRule:
    """
    Represents a specific degree slice rule within a zodiac sign.
    """
    start_deg: float
    end_deg: float
    zone_type: GuruZoneType
    ruling_planet: str
    description: str
    strength_weight: float = 1.0
    custom_tags: List[str] = field(default_factory=list)


@dataclass
class GuruSignPartition:
    """
    Represents all custom degree partitions for a given rashi.
    """
    rashi: str
    rules: List[GuruZoneRule] = field(default_factory=list)
    custom_notes: Optional[str] = None


@dataclass
class PlanetGuruEvaluation:
    """
    Evaluation output for a single planet under the Guru Research Layer.
    """
    planet: str
    rashi: str
    degree_in_rashi: float
    classical_dignity: Optional[str]
    guru_zone_name: str
    guru_zone_type: GuruZoneType
    guru_zone_lord: str
    guru_zone_range: str
    is_ruler_match: bool  # True if the planet in the zone is the zone's ruling planet
    is_dignity_agreement: bool  # True if classical dignity matches guru zone dignity
    notes: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GuruChartEvaluation:
    """
    Complete chart evaluation report under the Guru Research Layer.
    """
    evaluations: List[PlanetGuruEvaluation]
    agreements_count: int
    deviations_count: int
    summary_insights: List[str] = field(default_factory=list)
