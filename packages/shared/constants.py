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
DEGREES_PER_PADA: Final[float] = DEGREES_PER_NAKSHATRA / 4  # 3°20'
TOTAL_PADAS: Final[int] = TOTAL_NAKSHATRAS * PADAS_PER_NAKSHATRA  # 108


# ── Vimshottari Dasha ─────────────────────────────────────────────────────────
#
# Source: BPHS (Brihat Parashara Hora Shastra), Chapter 46.
# 120-year cycle. Nakshatra lord is determined by (nakshatra_index % 9).

VIMSHOTTARI_TOTAL_YEARS: Final[int] = 120

# Canonical lord sequence (ketu is index 0 → nakshatra 1 Ashwini, nakshatra 10 Magha, etc.)
VIMSHOTTARI_SEQUENCE: Final[list[str]] = [
    "ketu", "venus", "sun", "moon", "mars",
    "rahu", "jupiter", "saturn", "mercury",
]

# Period in years for each Vimshottari lord
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

# Nakshatra (0-indexed 0=Ashwini … 26=Revati) → Vimshottari starting lord
# Formula: VIMSHOTTARI_SEQUENCE[nakshatra_index % 9]
VIMSHOTTARI_NAKSHATRA_LORDS: Final[list[str]] = (
    VIMSHOTTARI_SEQUENCE * 3  # 9 × 3 = 27 nakshatras
)

# ── Yogini Dasha ──────────────────────────────────────────────────────────────
#
# 36-year cycle. 8 Yogini lords; nakshatra_index % 8 gives starting yogini.
# Source: BPHS Chapter 47.

YOGINI_TOTAL_YEARS: Final[int] = 36

YOGINI_SEQUENCE: Final[list[str]] = [
    "mangala", "pingala", "dhanya", "bhramari",
    "bhadrika", "ulka", "siddha", "sankata",
]

# Yogini name → ruling Graha
YOGINI_GRAHA: Final[dict[str, str]] = {
    "mangala":  "moon",
    "pingala":  "sun",
    "dhanya":   "jupiter",
    "bhramari": "mars",
    "bhadrika": "mercury",
    "ulka":     "saturn",
    "siddha":   "venus",
    "sankata":  "rahu",
}

# Yogini name → period in years (1 through 8)
YOGINI_DASHA_YEARS: Final[dict[str, int]] = {
    "mangala":  1,
    "pingala":  2,
    "dhanya":   3,
    "bhramari": 4,
    "bhadrika": 5,
    "ulka":     6,
    "siddha":   7,
    "sankata":  8,
}

# Nakshatra (0-indexed) → Yogini sequence index: YOGINI_SEQUENCE[nakshatra_index % 8]
YOGINI_NAKSHATRA_LORDS: Final[list[str]] = (
    YOGINI_SEQUENCE * 4  # 8 × 3 = 24; pad with first 3 → 27
)[:27]

# ── Ashtottari Dasha ──────────────────────────────────────────────────────────
#
# 108-year cycle. 8 lords. Applied when Rahu occupies a Kendra or Trikona from
# Lagna (or in some traditions, used only for day births with specific conditions).
# Nakshatra assignment: each lord governs 3–4 consecutive nakshatras.
# Source: BPHS Chapter 46.

ASHTOTTARI_TOTAL_YEARS: Final[int] = 108

# Lord sequence for sub-period calculation
ASHTOTTARI_SEQUENCE: Final[list[str]] = [
    "sun", "moon", "mars", "mercury",
    "saturn", "jupiter", "rahu", "venus",
]

ASHTOTTARI_DASHA_YEARS: Final[dict[str, int]] = {
    "sun":     6,
    "moon":    15,
    "mars":    8,
    "mercury": 17,
    "saturn":  10,
    "jupiter": 19,
    "rahu":    12,
    "venus":   21,
}

# Nakshatra (0-indexed, 0=Ashwini) → Ashtottari starting lord.
# Each of 8 lords governs either 3 or 4 consecutive nakshatras (27 total).
# Order follows the Parashari assignment.
ASHTOTTARI_NAKSHATRA_LORDS: Final[list[str]] = [
    "venus",    # 0  Ashwini
    "sun",      # 1  Bharani
    "sun",      # 2  Krittika
    "moon",     # 3  Rohini
    "moon",     # 4  Mrigashira
    "mars",     # 5  Ardra
    "mars",     # 6  Punarvasu
    "mercury",  # 7  Pushya
    "mercury",  # 8  Ashlesha
    "saturn",   # 9  Magha
    "saturn",   # 10 Purva Phalguni
    "jupiter",  # 11 Uttara Phalguni
    "jupiter",  # 12 Hasta
    "rahu",     # 13 Chitra
    "rahu",     # 14 Swati
    "venus",    # 15 Vishakha
    "venus",    # 16 Anuradha
    "sun",      # 17 Jyeshtha
    "sun",      # 18 Mula
    "moon",     # 19 Purva Ashadha
    "moon",     # 20 Uttara Ashadha
    "mars",     # 21 Shravana
    "mars",     # 22 Dhanishtha
    "mercury",  # 23 Shatabhisha
    "mercury",  # 24 Purva Bhadrapada
    "saturn",   # 25 Uttara Bhadrapada
    "jupiter",  # 26 Revati
]

# ── Kalachakra Dasha ──────────────────────────────────────────────────────────
#
# Sign-based dasha using Moon's D9 (Navamsha) position as the starting sign.
# Savya (odd D1 signs) progresses forward; Apasavya (even) progresses backward.
# Source: BPHS Chapter 47.

KALACHAKRA_TOTAL_YEARS: Final[int] = 100  # Canonical total for one complete cycle

# Period in years for each sign in Kalachakra
KALACHAKRA_SIGN_YEARS: Final[dict[str, int]] = {
    "aries":       7,
    "taurus":      9,
    "gemini":      9,
    "cancer":      16,
    "leo":         7,
    "virgo":       9,
    "libra":       9,
    "scorpio":     7,
    "sagittarius": 9,
    "capricorn":   4,
    "aquarius":    4,
    "pisces":      10,
}
# Sum: 7+9+9+16+7+9+9+7+9+4+4+10 = 100 ✓

# Forward (Savya) progression through all 12 signs
KALACHAKRA_SAVYA_SIGNS: Final[list[str]] = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

# Backward (Apasavya) progression through all 12 signs
KALACHAKRA_APASAVYA_SIGNS: Final[list[str]] = list(reversed(KALACHAKRA_SAVYA_SIGNS))

# ── Planetary dignities ───────────────────────────────────────────────────────

# Exaltation degrees (planet → (rashi, degree within rashi))
EXALTATION_DEGREES: Final[dict[str, tuple[str, float]]] = {
    "sun":     ("aries", 10.0),
    "moon":    ("taurus", 3.0),
    "mars":    ("capricorn", 28.0),
    "mercury": ("virgo", 15.0),
    "jupiter": ("cancer", 5.0),
    "venus":   ("pisces", 27.0),
    "saturn":  ("libra", 20.0),
    "rahu":    ("gemini", 20.0),
    "ketu":    ("sagittarius", 20.0),
}

# Debilitation rashis (exactly 180° from exaltation)
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

# Sign lords (natural ruler of each sign)
SIGN_LORDS: Final[dict[str, str]] = {
    "aries":       "mars",
    "taurus":      "venus",
    "gemini":      "mercury",
    "cancer":      "moon",
    "leo":         "sun",
    "virgo":       "mercury",
    "libra":       "venus",
    "scorpio":     "mars",
    "sagittarius": "jupiter",
    "capricorn":   "saturn",
    "aquarius":    "saturn",
    "pisces":      "jupiter",
}

# Jaimini alternate lords (used in Chara and Narayana dasha)
# Scorpio: Ketu (alternate for Mars); Aquarius: Rahu (alternate for Saturn)
JAIMINI_ALT_LORDS: Final[dict[str, str]] = {
    "scorpio":  "ketu",
    "aquarius": "rahu",
}

# ── Swiss Ephemeris planet IDs ────────────────────────────────────────────────

SWEPH_PLANET_IDS: Final[dict[str, int]] = {
    "sun":     0,
    "moon":    1,
    "mars":    4,
    "mercury": 2,
    "jupiter": 5,
    "venus":   3,
    "saturn":  6,
    "rahu":    10,  # see SWEPH_NODE_IDS — default (mean) node; overridden per-wrapper
    "ketu":    -1,  # Derived as Rahu + 180°
}

# Lunar node variants. Classical Vedic practice — and both Jagannatha Hora and
# AstroSage, verified against a reference chart — use the MEAN node; the true
# (osculating) node can differ from it by up to ~1.8°, enough to shift Rahu/Ketu
# into a different nakshatra and therefore change Vimshottari dasha balance.
# Exposed as a choice (Settings.NODE_TYPE) rather than hardcoded, since some
# schools and most Western software prefer the true node.
SWEPH_NODE_IDS: Final[dict[str, int]] = {
    "mean": 10,  # swe.MEAN_NODE
    "true": 11,  # swe.TRUE_NODE
}
DEFAULT_NODE_TYPE: Final[str] = "mean"

# ── Time ──────────────────────────────────────────────────────────────────────

JULIAN_DAY_J2000: Final[float] = 2451545.0
SECONDS_PER_DAY: Final[float] = 86400.0
DAYS_PER_JULIAN_YEAR: Final[float] = 365.25
