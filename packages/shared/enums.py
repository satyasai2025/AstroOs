"""
AstroOS — Shared Enumerations

All Vedic astrology reference enumerations live here.
These are the canonical values used across the API, domain models,
ephemeris calculations, and frontend type generation.

Module 1 provides the structural scaffolding.
Vedic astrology enum values will be expanded in their respective modules
(Rashi Module, Nakshatra Module, Graha Module, etc.).
"""

from enum import Enum


class Rashi(str, Enum):
    """Twelve zodiac signs (rashis). Names are Sanskrit; values are English slugs."""
    MESHA = "aries"
    VRISHABHA = "taurus"
    MITHUNA = "gemini"
    KARKA = "cancer"
    SIMHA = "leo"
    KANYA = "virgo"
    TULA = "libra"
    VRISCHIKA = "scorpio"
    DHANU = "sagittarius"
    MAKARA = "capricorn"
    KUMBHA = "aquarius"
    MEENA = "pisces"


class Graha(str, Enum):
    """Navagraha — the nine planets in Vedic astrology."""
    SURYA = "sun"
    CHANDRA = "moon"
    MANGALA = "mars"
    BUDHA = "mercury"
    GURU = "jupiter"
    SHUKRA = "venus"
    SHANI = "saturn"
    RAHU = "rahu"
    KETU = "ketu"


class Nakshatra(str, Enum):
    """Twenty-seven lunar mansions."""
    ASHWINI = "ashwini"
    BHARANI = "bharani"
    KRITTIKA = "krittika"
    ROHINI = "rohini"
    MRIGASHIRA = "mrigashira"
    ARDRA = "ardra"
    PUNARVASU = "punarvasu"
    PUSHYA = "pushya"
    ASHLESHA = "ashlesha"
    MAGHA = "magha"
    PURVA_PHALGUNI = "purva_phalguni"
    UTTARA_PHALGUNI = "uttara_phalguni"
    HASTA = "hasta"
    CHITRA = "chitra"
    SWATI = "swati"
    VISHAKHA = "vishakha"
    ANURADHA = "anuradha"
    JYESHTHA = "jyeshtha"
    MULA = "mula"
    PURVA_ASHADHA = "purva_ashadha"
    UTTARA_ASHADHA = "uttara_ashadha"
    SHRAVANA = "shravana"
    DHANISHTHA = "dhanishtha"
    SHATABHISHA = "shatabhisha"
    PURVA_BHADRAPADA = "purva_bhadrapada"
    UTTARA_BHADRAPADA = "uttara_bhadrapada"
    REVATI = "revati"


class Bhava(str, Enum):
    """Twelve houses (bhavas)."""
    FIRST = "1"
    SECOND = "2"
    THIRD = "3"
    FOURTH = "4"
    FIFTH = "5"
    SIXTH = "6"
    SEVENTH = "7"
    EIGHTH = "8"
    NINTH = "9"
    TENTH = "10"
    ELEVENTH = "11"
    TWELFTH = "12"


class AyanamsaSystem(str, Enum):
    """Supported ayanamsa systems for sidereal calculations."""
    LAHIRI = "lahiri"           # Chitrapaksha — most common in India
    KRISHNAMURTI = "kp"        # KP system
    RAMAN = "raman"            # B.V. Raman's ayanamsa
    YUKTESHWAR = "yukteshwar"  # Sri Yukteshwar's ayanamsa
    FAGAN_BRADLEY = "fagan_bradley"  # Western sidereal
    TRUE_CHITRA = "true_chitra"      # True Chitrapaksha
    TRUE_PUSHYA = "true_pushya"      # True Pushya paksha (used by P.V.R. Narasimha Rao)
    LAHIRI_JHA_ANCHORED = "lahiri_jha_anchored"  # Spica 180:00:03 at Ujjain, 22-Mar-285 AD Noon (Vinay Jha Kundalee Drik mode)


class VargaMethod(str, Enum):
    """
    Divisional chart calculation method:
    - POPULAR: Modern commercial standard (JHora / Parashara's Light default).
               Only D30 has reversed order in even signs.
    - ARSHA_PARASHARI: Vinay Jha's Kundalee switch @10944 based on original Sanskrit BPHS.
                       Reversed progression in even signs for D2, D7, D9, D10, D16, D20, D24, D27, D30, D60.
    """
    POPULAR = "popular"
    ARSHA_PARASHARI = "arsha_parashari"


class ChartType(str, Enum):
    """Supported divisional chart types (vargas)."""
    RASHI = "D1"          # Birth chart
    HORA = "D2"           # Wealth
    DREKKANA = "D3"       # Siblings
    CHATURTHAMSHA = "D4"  # Property / Fortune
    SAPTAMSHA = "D7"      # Children
    NAVAMSHA = "D9"       # Marriage / Dharma — most important varga
    DASHAMSHA = "D10"     # Career
    DWADASHAMSHA = "D12"  # Parents
    SHODASHAMSHA = "D16"  # Vehicles
    VIMSHAMSHA = "D20"    # Spirituality
    CHATURVIMSHAMSHA = "D24"  # Education
    SAPTAVIMSHAMSHA = "D27"   # Strength / Nakshatras
    TRIMSHAMSHA = "D30"       # Evils / Misfortunes
    KHAVEDAMSHA = "D40"       # Auspicious / Inauspicious effects
    AKSHAVEDAMSHA = "D45"     # General indications
    SHASHTIAMSHA = "D60"      # Past karma — most subtle
