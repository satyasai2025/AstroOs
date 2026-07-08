"""
AstroOS — Shared Constants

Immutable reference values used across the platform.
These are Vedic astrology domain constants — not configuration values.
Configuration belongs in apps/api/config.py.

All values sourced from classical texts (BPHS, Jataka Parijata, Sarvartha Chintamani).
"""

from typing import Final

# ── Zodiac ────────────────────────────────────────────────────────────────────

TOTAL_RASHIS: Final[int] = 12
DEGREES_PER_RASHI: Final[float] = 30.0
TOTAL_DEGREES: Final[float] = 360.0

# ── Nakshatras ────────────────────────────────────────────────────────────────

TOTAL_NAKSHATRAS: Final[int] = 27
DEGREES_PER_NAKSHATRA: Final[float] = 360.0 / 27  # 13°20'
PADAS_PER_NAKSHATRA: Final[int] = 4
TOTAL_PADAS: Final[int] = TOTAL_NAKSHATRAS * PADAS_PER_NAKSHATRA  # 108

# ── Dashas ────────────────────────────────────────────────────────────────────

# Vimshottari dasha cycle — 120 year total
VIMSHOTTARI_TOTAL_YEARS: Final[int] = 120

# Dasha periods in years (ordered by nakshatra lord sequence)
VIMSHOTTARI_DASHA_YEARS: Final[dict[str, int]] = {
    "ketu":    7,
    "venus":   20,
    "sun":     6,
    "moon":    10,
    "mars":    7,
    "rahu":    18,
    "jupiter": 16,
    "saturn":  19,
    "mercury": 17,
}

# ── Planetary dignities ───────────────────────────────────────────────────────

# Exaltation degrees (rashi name → peak degree within rashi)
EXALTATION_DEGREES: Final[dict[str, tuple[str, float]]] = {
    "sun":     ("aries", 10.0),
    "moon":    ("taurus", 3.0),
    "mars":    ("capricorn", 28.0),
    "mercury": ("virgo", 15.0),
    "jupiter": ("cancer", 5.0),
    "venus":   ("pisces", 27.0),
    "saturn":  ("libra", 20.0),
    "rahu":    ("gemini", 20.0),   # Traditional; varies by school
    "ketu":    ("sagittarius", 20.0),
}

# Debilitation is exactly 180° from exaltation
DEBILITATION_RASHIS: Final[dict[str, str]] = {
    "sun":     "libra",
    "moon":    "scorpio",
    "mars":    "cancer",
    "mercury": "pisces",
    "jupiter": "capricorn",
    "venus":   "virgo",
    "saturn":  "aries",
    "rahu":    "sagittarius",
    "ketu":    "gemini",
}

# Moolatrikona rashis
MOOLATRIKONA_RASHIS: Final[dict[str, str]] = {
    "sun":     "leo",
    "moon":    "taurus",
    "mars":    "aries",
    "mercury": "virgo",
    "jupiter": "sagittarius",
    "venus":   "libra",
    "saturn":  "aquarius",
}

# Own signs (swakshetra)
OWN_SIGNS: Final[dict[str, list[str]]] = {
    "sun":     ["leo"],
    "moon":    ["cancer"],
    "mars":    ["aries", "scorpio"],
    "mercury": ["gemini", "virgo"],
    "jupiter": ["sagittarius", "pisces"],
    "venus":   ["taurus", "libra"],
    "saturn":  ["capricorn", "aquarius"],
}

# ── Swiss Ephemeris planet IDs ────────────────────────────────────────────────
# These are the swe_calc_ut() planet identifiers — do not change.
SWEPH_PLANET_IDS: Final[dict[str, int]] = {
    "sun":     0,
    "moon":    1,
    "mars":    4,
    "mercury": 2,
    "jupiter": 5,
    "venus":   3,
    "saturn":  6,
    "rahu":    11,  # True node
    "ketu":    -1,  # Derived as Rahu + 180°
}

# ── Time ──────────────────────────────────────────────────────────────────────

JULIAN_DAY_J2000: Final[float] = 2451545.0  # J2000.0 epoch
SECONDS_PER_DAY: Final[float] = 86400.0
