"""
AstroOS — Shri Surya Siddhanta (SSS) Classical Calculation Engine
Classical Reference: Surya Siddhanta (Madhyamadhikara & Spashtadhikara), Dr. Lakshmana Jha Model.
Computes traditional Mean (Madhyama) and True (Sphuta) planetary longitudes and traditional Sunrise/Ishtakala.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone

# SSS Revolution Constants per Mahayuga (4,320,000 solar years)
SSS_YUGADIMA_DAYS = 1577917828.0  # Civil days in a Mahayuga (Surya Siddhanta)
SSS_REVOLUTIONS = {
    "sun": 4320000.0,
    "moon": 57753336.0,
    "mars": 2296832.0,
    "mercury": 17937060.0,
    "jupiter": 364220.0,
    "venus": 7022376.0,
    "saturn": 146568.0,
    "rahu": -232238.0, # Retrograde node
}

# Mandoccha (Apogee) degrees in Surya Siddhanta
SSS_MANDOCCHA = {
    "sun": 77.2833,
    "mars": 130.0333,
    "mercury": 220.4500,
    "jupiter": 171.3000,
    "venus": 79.8333,
    "saturn": 236.6167,
}

# Manda Paridhi (Epicycle circumference in degrees)
SSS_MANDA_PARIDHI = {
    "sun": 14.0,
    "moon": 32.0,
    "mars": 70.0,
    "mercury": 29.0,
    "jupiter": 33.0,
    "venus": 11.0,
    "saturn": 49.0,
}

class SuryaSiddhantaEngine:
    """
    Classical Surya Siddhanta mathematical calculation engine.
    """

    @staticmethod
    def ahargana_from_kaliyuga(dt: datetime) -> float:
        """Calculate Kali Ahargana (elapsed days since Kaliyuga start: 18 Feb 3102 BC)."""
        # Julian Day for Kaliyuga epoch = 588465.5 JD
        # Standard Unix/Gregorian date to JD
        y, m, d = dt.year, dt.month, dt.day
        hour_fraction = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0
        
        if m <= 2:
            y -= 1
            m += 12
        a = math.floor(y / 100)
        b = 2 - a + math.floor(a / 4)
        jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5 + hour_fraction
        
        kali_epoch_jd = 588465.5
        ahargana = jd - kali_epoch_jd
        return ahargana

    def calculate_madhyama_graha(self, ahargana: float, planet: str) -> float:
        """Mean sidereal longitude according to Surya Siddhanta Mahayuga cycles."""
        revs = SSS_REVOLUTIONS.get(planet, 4320000.0)
        mean_revs = (ahargana * revs) / SSS_YUGADIMA_DAYS
        deg = (mean_revs % 1.0) * 360.0
        if deg < 0:
            deg += 360.0
        return deg

    def calculate_sphuta_surya(self, ahargana: float) -> tuple[float, float]:
        """Compute True Sun (Sphuta Surya) and Mandaphala (Equation of Center)."""
        mean_sun = self.calculate_madhyama_graha(ahargana, "sun")
        mando = SSS_MANDOCCHA["sun"]
        kendra = (mean_sun - mando) % 360.0
        
        # Manda Phala = (Manda Paridhi / 360) * sin(Kendra) * (180 / pi)
        mandaphala_deg = (SSS_MANDA_PARIDHI["sun"] / 360.0) * math.sin(math.radians(kendra)) * (180.0 / math.pi)
        true_sun = (mean_sun - mandaphala_deg) % 360.0
        return true_sun, mandaphala_deg

    def calculate_suryodaya_traditional(self, lat_deg: float, sun_lon_deg: float) -> dict[str, float]:
        """
        Compute traditional Charakhanda, Dinamana, and Sunrise time using Surya Siddhanta spherical trigonometry.
        """
        # Sun Declination (Kranti): sin(delta) = sin(sun_lon) * sin(24 deg)
        kranti_rad = math.asin(math.sin(math.radians(sun_lon_deg)) * math.sin(math.radians(24.0)))
        kranti_deg = math.degrees(kranti_rad)
        
        # Chara (Ascensional difference) = tan(lat) * tan(kranti)
        sin_chara = math.tan(math.radians(lat_deg)) * math.tan(kranti_rad)
        sin_chara = max(-1.0, min(1.0, sin_chara))
        chara_deg = math.degrees(math.asin(sin_chara))
        
        # Dinamana (Length of daylight) in Ghatis (1 Ghati = 24 mins, 60 Ghatis = 24h)
        # Dinamana = 30 + (chara_deg / 6) Ghatis
        day_ghatis = 30.0 + (chara_deg / 6.0)
        night_ghatis = 60.0 - day_ghatis
        
        # Local Sunrise in Ghatis from midnight = (30 - day_ghatis / 2)
        sunrise_ghatis = (60.0 - day_ghatis) / 2.0
        sunrise_hours = (sunrise_ghatis * 24.0) / 60.0
        
        return {
            "kranti_deg": round(kranti_deg, 4),
            "chara_deg": round(chara_deg, 4),
            "dinamana_ghatis": round(day_ghatis, 2),
            "ratrimana_ghatis": round(night_ghatis, 2),
            "traditional_sunrise_hours": round(sunrise_hours, 4),
        }
