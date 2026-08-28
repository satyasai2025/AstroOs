"""
AstroOS — Medini & Financial Forecasting Engine (MediniEngine)
=============================================================

Canonical Shastric Implementation based on:
- Narapatijayacharya, Krishi Parashara & Yamaliya Swarodaya
- Vinay Jha (http://vedicastrology.wikidot.com/sapta-nadi-chakra, sensex-forecasting.md, sensex-vs-gold-comparison.md)

Core Modules:
1. Sapta-Nadi Chakra Weather & Precipitation Engine:
   - 7 Nadis: Chanda (Saturn), Vayu (Jupiter), Dahana (Mars), Saumya (Sun),
              Neera (Venus), Jala (Mercury), Amrita (Moon)
   - Planetary distribution across Water Nadis (Amrita, Jala, Neera) vs Fire/Wind Nadis
   - Rainfall probability & Intensity forecast (Torrential, Steady, Moderate, Scanty, Dry)
2. Financial & Commodity Market Sentiment Forecasting (Sensex & Gold):
   - Bullish / Bearish planetary velocity & ingress synthesis
   - Gold/Metals pressure from Sun/Mars/Jupiter
   - Equity Index (Sensex) sentiment from Mercury/Jupiter/Venus vs Saturn/Rahu pressure
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.services.ephemeris_wrapper import EphemerisWrapper

logger = logging.getLogger(__name__)

# 7 Nadis and their ruling planets & nature
_NADI_NAMES = ["CHANDA", "VAYU", "DAHANA", "SAUMYA", "NEERA", "JALA", "AMRITA"]
_NADI_RULERS = {
    "CHANDA": "SATURN",
    "VAYU": "JUPITER",
    "DAHANA": "MARS",
    "SAUMYA": "SUN",
    "NEERA": "VENUS",
    "JALA": "MERCURY",
    "AMRITA": "MOON",
}

# 28-Nakshatra SBC/Sapta-Nadi mapping (Krittika as 1)
# Krishi Parashara / Yamala Swarodaya 7-Nadi scheme:
_NAK_TO_NADI = {
    # Amrita (Water / Torrential)
    "ashlesha": "AMRITA", "magha": "AMRITA", "jyeshtha": "AMRITA", "mula": "AMRITA",
    # Jala (Water / Heavy rain)
    "pushya": "JALA", "purva_phalguni": "JALA", "anuradha": "JALA", "purva_ashadha": "JALA",
    # Neera (Water / Moderate rain)
    "punarvasu": "NEERA", "uttara_phalguni": "NEERA", "vishakha": "NEERA", "uttara_ashadha": "NEERA",
    # Saumya (Neutral / Clear skies)
    "ardra": "SAUMYA", "hasta": "SAUMYA", "swati": "SAUMYA", "abhijit": "SAUMYA",
    # Dahana (Fire / Heat)
    "mrigashira": "DAHANA", "chitra": "DAHANA", "dhanishta": "DAHANA", "shravana": "DAHANA",
    # Vayu (Wind / Storms)
    "rohini": "VAYU", "bharani": "VAYU", "shatabhisha": "VAYU", "purva_bhadrapada": "VAYU",
    # Chanda (Severe storms / Dry)
    "krittika": "CHANDA", "ashwini": "CHANDA", "revati": "CHANDA", "uttara_bhadrapada": "CHANDA",
}

_NAK_27_ORDER = [
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni", "uttara_phalguni",
    "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha",
    "purva_bhadrapada", "uttara_bhadrapada", "revati",
]


@dataclass(frozen=True)
class WeatherForecast:
    """Sapta-Nadi Chakra Weather and Precipitation Output."""
    target_date: date
    dominant_nadi: str
    rainfall_probability_pct: float
    rainfall_intensity: str              # "TORRENTIAL", "HEAVY_DOWNPOUR", "MODERATE_SHOWERS", "SCANTY", "DRY_CLEAR"
    temperature_trend: str               # "INTENSE_HEAT", "WARM", "MODERATE", "COOL", "CHILLY"
    active_water_planets: List[str]      # Planets residing in Neera, Jala, Amrita
    active_fire_planets: List[str]       # Planets residing in Dahana, Chanda


@dataclass(frozen=True)
class MarketForecast:
    """Financial Astrology Forecast for Equities (Sensex) & Commodities (Gold/Silver)."""
    target_date: date
    sensex_trend: str                    # "STRONGLY_BULLISH", "BULLISH_BIAS", "NEUTRAL_RANGEBOUND", "BEARISH_PRESSURE", "HIGH_VOLATILITY_CORRECTION"
    sensex_sentiment_score: float        # -1.0 (severe crash risk) to +1.0 (strong rally)
    gold_trend: str                      # "RISING_BULLISH", "STEADY_ACCUMULATION", "CONSOLIDATION", "BEARISH_CORRECTION"
    gold_sentiment_score: float          # -1.0 to +1.0
    key_drivers: List[str]
    caution_flag: bool                   # True if Mars-Saturn / Rahu combustion active


@dataclass(frozen=True)
class MediniForecastReport:
    """Complete Mundane & Financial Astrology Report."""
    target_date: date
    weather: WeatherForecast
    market: MarketForecast


class MediniEngine:
    """Computes Sapta-Nadi weather forecasts and financial market sentiment."""

    def __init__(self, ephemeris_path: str = "data/ephemeris"):
        self.wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)

    def _get_nakshatra_28(self, longitude: float) -> str:
        deg = longitude % 360.0
        if 276.6667 <= deg < 280.9056:
            return "abhijit"
        idx = int(deg // (360.0 / 27.0)) % 27
        return _NAK_27_ORDER[idx]

    def forecast_weather(self, target_date: date) -> WeatherForecast:
        """Calculates Sapta-Nadi Chakra rainfall & atmospheric conditions."""
        target_dt = datetime.combine(target_date, time(12, 0), tzinfo=timezone.utc)
        eph = self.wrapper.calculate(target_dt, 0.0, 0.0)

        nadi_occupancy: Dict[str, List[str]] = {n: [] for n in _NADI_NAMES}

        for p in eph.planet_positions:
            p_name = p.planet.upper()
            nak = self._get_nakshatra_28(p.sidereal_longitude)
            nadi = _NAK_TO_NADI.get(nak, "SAUMYA")
            nadi_occupancy[nadi].append(p_name)

        water_nadis = ["AMRITA", "JALA", "NEERA"]
        fire_nadis = ["DAHANA", "CHANDA"]

        water_planets = []
        for wn in water_nadis:
            water_planets.extend(nadi_occupancy[wn])

        fire_planets = []
        for fn in fire_nadis:
            fire_planets.extend(nadi_occupancy[fn])

        # Water score calculation
        water_score = 0.0
        for p in water_planets:
            if p in ["MOON", "VENUS", "MERCURY", "JUPITER"]:
                water_score += 0.25
            else:
                water_score += 0.10

        for p in fire_planets:
            if p in ["MARS", "SUN", "SATURN", "RAHU"]:
                water_score -= 0.20

        prob_pct = max(5.0, min(95.0, 40.0 + (water_score * 50.0)))

        if prob_pct >= 75.0:
            intensity = "TORRENTIAL" if "MOON" in water_planets or "VENUS" in water_planets else "HEAVY_DOWNPOUR"
        elif prob_pct >= 55.0:
            intensity = "MODERATE_SHOWERS"
        elif prob_pct >= 35.0:
            intensity = "SCANTY"
        else:
            intensity = "DRY_CLEAR"

        # Temperature
        if len(fire_planets) >= 3 and ("MARS" in fire_planets or "SUN" in fire_planets):
            temp = "INTENSE_HEAT"
        elif len(water_planets) >= 3:
            temp = "COOL"
        elif "SATURN" in nadi_occupancy["CHANDA"]:
            temp = "CHILLY"
        else:
            temp = "MODERATE"

        # Find most occupied Nadi
        dom_nadi = max(nadi_occupancy.keys(), key=lambda k: len(nadi_occupancy[k]))

        return WeatherForecast(
            target_date=target_date,
            dominant_nadi=dom_nadi,
            rainfall_probability_pct=round(prob_pct, 1),
            rainfall_intensity=intensity,
            temperature_trend=temp,
            active_water_planets=water_planets,
            active_fire_planets=fire_planets,
        )

    def forecast_market(self, target_date: date) -> MarketForecast:
        """Calculates equity (Sensex) and commodity (Gold) sentiment index."""
        target_dt = datetime.combine(target_date, time(12, 0), tzinfo=timezone.utc)
        eph = self.wrapper.calculate(target_dt, 0.0, 0.0)

        p_pos = {p.planet.lower(): p for p in eph.planet_positions}
        drivers = []
        sensex_score = 0.0
        gold_score = 0.0

        # Mercury (Commerce & Tech) & Jupiter (Expansion & Capital)
        merc = p_pos.get("mercury")
        jup = p_pos.get("jupiter")
        ven = p_pos.get("venus")
        sat = p_pos.get("saturn")
        mars = p_pos.get("mars")
        sun = p_pos.get("sun")

        if jup and not jup.is_retrograde:
            sensex_score += 0.25
            gold_score += 0.20
            drivers.append("Jupiter direct expansion")
        elif jup and jup.is_retrograde:
            sensex_score -= 0.15
            drivers.append("Jupiter retrograde cautious stance")

        if merc and not merc.is_retrograde:
            sensex_score += 0.20
        elif merc and merc.is_retrograde:
            sensex_score -= 0.25
            drivers.append("Mercury retrograde market churn")

        if ven:
            sensex_score += 0.15

        # Malefic pressure
        if sat and sat.is_retrograde:
            sensex_score -= 0.20
            gold_score += 0.25
            drivers.append("Saturn retrograde flight to gold safe-haven")

        if mars and sun:
            # Check Mars-Sun angular distance
            diff = abs(mars.sidereal_longitude - sun.sidereal_longitude) % 360.0
            if diff <= 15.0 or abs(diff - 180.0) <= 10.0:
                gold_score += 0.35
                sensex_score -= 0.20
                drivers.append("Sun-Mars combustion/opposition commodity spike")

        sensex_score = max(-1.0, min(1.0, sensex_score))
        gold_score = max(-1.0, min(1.0, gold_score))

        # Sensex Trend
        if sensex_score >= 0.40:
            s_trend = "STRONGLY_BULLISH"
        elif sensex_score >= 0.15:
            s_trend = "BULLISH_BIAS"
        elif sensex_score >= -0.15:
            s_trend = "NEUTRAL_RANGEBOUND"
        elif sensex_score >= -0.40:
            s_trend = "BEARISH_PRESSURE"
        else:
            s_trend = "HIGH_VOLATILITY_CORRECTION"

        # Gold Trend
        if gold_score >= 0.35:
            g_trend = "RISING_BULLISH"
        elif gold_score >= 0.10:
            g_trend = "STEADY_ACCUMULATION"
        elif gold_score >= -0.15:
            g_trend = "CONSOLIDATION"
        else:
            g_trend = "BEARISH_CORRECTION"

        caution = sensex_score <= -0.30 or (mars and sat and abs(mars.sidereal_longitude - sat.sidereal_longitude) <= 10.0)

        return MarketForecast(
            target_date=target_date,
            sensex_trend=s_trend,
            sensex_sentiment_score=round(sensex_score, 3),
            gold_trend=g_trend,
            gold_sentiment_score=round(gold_score, 3),
            key_drivers=drivers,
            caution_flag=bool(caution),
        )

    def generate_full_report(self, target_date: date) -> MediniForecastReport:
        """Generates unified Medini mundane and financial forecast."""
        weather = self.forecast_weather(target_date)
        market = self.forecast_market(target_date)
        return MediniForecastReport(target_date=target_date, weather=weather, market=market)
