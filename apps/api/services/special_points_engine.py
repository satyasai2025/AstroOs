"""
AstroOS — Special Sensitive Points Engine

Implements:
1. Bhrigu Bindu (Destiny point: forward midpoint from Rahu to Moon along the zodiac)
2. Yogi Point & Yogi Planet (Nakshatra lord of Sun + Moon + 93°20')
3. Sahayogi Planet (Sign lord of Yogi point)
4. Avayogi Point & Avayogi Planet (Point offset by 186°40', 6th Nakshatra from Yogi)
"""

from __future__ import annotations

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.special_points import (
    BhriguBinduResult,
    SpecialPointsSnapshot,
    YogiPointsResult,
)
from apps.api.services.ephemeris_wrapper import (
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from packages.shared.constants import SIGN_LORDS
from packages.shared.rashi_offset import house_offset

_YOGI_CONSTANT_DEG = 93.0 + 20.0 / 60.0    # 93° 20' (3 signs 3° 20')
_AVAYOGI_CONSTANT_DEG = 186.0 + 40.0 / 60.0  # 186° 40' (14 nakshatra spans)


class SpecialPointsEngine:
    """Computes Bhrigu Bindu, Yogi, Sahayogi, and Avayogi for any D1Chart."""

    def compute_bhrigu_bindu(self, chart: D1Chart) -> BhriguBinduResult:
        moon_pos = next((p for p in chart.planets if p.planet.lower() == "moon"), None)
        rahu_pos = next((p for p in chart.planets if p.planet.lower() == "rahu"), None)

        if not moon_pos or not rahu_pos:
            raise ValueError("Chart must contain Moon and Rahu positions for Bhrigu Bindu calculation.")

        moon_lon = moon_pos.sidereal_longitude
        rahu_lon = rahu_pos.sidereal_longitude

        # Forward span from Rahu to Moon
        span = (moon_lon - rahu_lon) % 360.0
        bb_lon = (rahu_lon + span / 2.0) % 360.0

        rashi, deg = longitude_to_rashi(bb_lon)
        nak = longitude_to_nakshatra(bb_lon)
        sign_lord = SIGN_LORDS.get(rashi.lower(), "")

        asc_rashi_idx = int(chart.ascendant.sidereal_longitude // 30.0)
        bb_rashi_idx = int(bb_lon // 30.0)
        house_num = house_offset(asc_rashi_idx, bb_rashi_idx)

        return BhriguBinduResult(
            sidereal_longitude=round(bb_lon, 6),
            rashi=rashi,
            rashi_degree=round(deg, 4),
            nakshatra=nak.nakshatra,
            pada=nak.pada,
            nakshatra_lord=nak.lord,
            sign_lord=sign_lord,
            house_number=house_num,
        )

    def compute_yogi_points(self, chart: D1Chart) -> YogiPointsResult:
        sun_pos = next((p for p in chart.planets if p.planet.lower() == "sun"), None)
        moon_pos = next((p for p in chart.planets if p.planet.lower() == "moon"), None)

        if not sun_pos or not moon_pos:
            raise ValueError("Chart must contain Sun and Moon positions for Yogi Point calculation.")

        sun_lon = sun_pos.sidereal_longitude
        moon_lon = moon_pos.sidereal_longitude

        # Yogi Point = (Sun + Moon + 93°20') mod 360
        yogi_lon = (sun_lon + moon_lon + _YOGI_CONSTANT_DEG) % 360.0
        yogi_rashi, yogi_deg = longitude_to_rashi(yogi_lon)
        yogi_nak = longitude_to_nakshatra(yogi_lon)

        yogi_planet = yogi_nak.lord
        sahayogi_planet = SIGN_LORDS.get(yogi_rashi.lower(), "")

        # Avayogi Point = (Yogi Point + 186°40') mod 360
        avayogi_lon = (yogi_lon + _AVAYOGI_CONSTANT_DEG) % 360.0
        avayogi_rashi, avayogi_deg = longitude_to_rashi(avayogi_lon)
        avayogi_nak = longitude_to_nakshatra(avayogi_lon)
        avayogi_planet = avayogi_nak.lord

        return YogiPointsResult(
            yogi_point_longitude=round(yogi_lon, 6),
            yogi_point_rashi=yogi_rashi,
            yogi_point_rashi_degree=round(yogi_deg, 4),
            yogi_point_nakshatra=yogi_nak.nakshatra,
            yogi_point_pada=yogi_nak.pada,
            yogi_planet=yogi_planet,
            sahayogi_planet=sahayogi_planet,
            avayogi_point_longitude=round(avayogi_lon, 6),
            avayogi_point_rashi=avayogi_rashi,
            avayogi_point_rashi_degree=round(avayogi_deg, 4),
            avayogi_point_nakshatra=avayogi_nak.nakshatra,
            avayogi_point_pada=avayogi_nak.pada,
            avayogi_planet=avayogi_planet,
        )

    def compute_all(self, chart: D1Chart) -> SpecialPointsSnapshot:
        bb = self.compute_bhrigu_bindu(chart)
        yogi = self.compute_yogi_points(chart)
        return SpecialPointsSnapshot(
            bhrigu_bindu=bb,
            yogi_points=yogi,
        )
