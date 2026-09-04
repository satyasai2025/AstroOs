"""
AstroOS — Special Sensitive Points Domain Models

1. Bhrigu Bindu (Destiny point: exact midpoint of Moon and Rahu).
2. Yogi, Sahayogi & Avayogi Points and Ruling Planets.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BhriguBinduResult:
    """Midpoint of Moon and Rahu (Destiny / Karmic Point)."""
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str
    sign_lord: str
    house_number: int


@dataclass(frozen=True)
class YogiPointsResult:
    """Yogi, Sahayogi (Duplicate Yogi), and Avayogi (Obstruction) Points."""
    yogi_point_longitude: float
    yogi_point_rashi: str
    yogi_point_rashi_degree: float
    yogi_point_nakshatra: str
    yogi_point_pada: int
    yogi_planet: str  # Nakshatra lord of Yogi Point
    sahayogi_planet: str  # Rashi lord of Yogi Point

    avayogi_point_longitude: float
    avayogi_point_rashi: str
    avayogi_point_rashi_degree: float
    avayogi_point_nakshatra: str
    avayogi_point_pada: int
    avayogi_planet: str  # Nakshatra lord of Avayogi Point


@dataclass(frozen=True)
class SpecialPointsSnapshot:
    """Complete snapshot of Special Points for a chart."""
    bhrigu_bindu: BhriguBinduResult
    yogi_points: YogiPointsResult
    rule_version: str = "1.0"
