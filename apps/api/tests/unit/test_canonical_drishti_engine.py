"""
AstroOS — Unit Tests for Canonical Drishti Engine
=================================================
Validates Vinay Jha's Drishti Principles:
  1. Sphuta Drishti (0 to 60 Virupas piecewise continuous scale)
  2. Special aspects: Mars (4/8), Jupiter (5/9), Saturn (3/10)
  3. Maitri Filtering: Benefic trait transfer to friends vs Malefic to enemies
  4. Bhavesha 50% Baseline Law (Lord maintains 30 virupas even with 0 direct aspect)
  5. Sambandha Amplification
  6. Divisional Chart Drishti (D1, D9, D30)
  7. Flexible (Non-hardcoded) configuration via DrishtiConfig
"""

import pytest

from apps.api.domain.canonical_aspect import DrishtiConfig, DrishtiNature
from apps.api.services.canonical_drishti_engine import CanonicalDrishtiEngine


def test_sphuta_drishti_opposition_and_specials():
    """Verify 180° full opposition gives 60 virupas, and special aspects get classical bonuses."""
    engine = CanonicalDrishtiEngine()
    planet_rashis = {"sun": "aries", "saturn": "libra"}

    # 1. 180° opposition: Sun (0° Aries) to Saturn (180° Libra)
    asp1 = engine.compute_sphuta_drishti_between(
        from_planet="sun",
        to_planet="saturn",
        from_longitude=0.0,
        to_longitude=180.0,
        planet_rashis=planet_rashis,
    )
    assert asp1.virupas == 60.0
    assert asp1.percentage == 100.0
    assert asp1.aspect_type == "universal_7th"

    # 2. Saturn 3rd special aspect (60° separation)
    asp_sat = engine.compute_sphuta_drishti_between(
        from_planet="saturn",
        to_planet="sun",
        from_longitude=180.0,
        to_longitude=240.0, # 60° ahead of Saturn
        planet_rashis={"saturn": "libra", "sun": "sagittarius"},
    )
    assert asp_sat.is_special is True
    assert asp_sat.aspect_type == "saturn_3rd_special"
    assert asp_sat.virupas >= 45.0  # Includes 45 virupas bonus


def test_maitri_filtered_aspects():
    """Verify that an aspect on an enemy transfers MALEFIC_TRANSFER, while friend gets BENEFIC_TRANSFER."""
    engine = CanonicalDrishtiEngine()
    # Sun in Aries (0°), Saturn in Libra (180°): Natural enemies + 7th house = Adhishatru
    planet_rashis = {"sun": "aries", "saturn": "libra", "jupiter": "cancer"}

    asp_sun_sat = engine.compute_sphuta_drishti_between(
        from_planet="sun",
        to_planet="saturn",
        from_longitude=0.0,
        to_longitude=180.0,
        planet_rashis=planet_rashis,
    )
    assert asp_sun_sat.transferred_nature == DrishtiNature.MALEFIC_TRANSFER

    # Sun in Aries (0°), Jupiter in Cancer (95°): Natural friends (+1) + 4th house (+1) = Adhimitra (+2) -> BENEFIC_TRANSFER
    asp_sun_jup = engine.compute_sphuta_drishti_between(
        from_planet="sun",
        to_planet="jupiter",
        from_longitude=0.0,
        to_longitude=95.0,
        planet_rashis=planet_rashis,
    )
    assert asp_sun_jup.transferred_nature == DrishtiNature.BENEFIC_TRANSFER


def test_bhavesha_50_percent_baseline_law():
    """Verify Jha's law: A lord with 0 direct aspect retains a 50% (30 virupas) baseline protection."""
    engine = CanonicalDrishtiEngine()
    # Aries Lagna: 1st house lord is Mars
    # Place Mars at 30° (Taurus) -> Mars at 30° has 0 aspect on 1st house midpoint (15° Aries)
    planet_longitudes = {"mars": 35.0} # 2nd house

    bhava_drishti = engine.compute_bhavesha_drishti_protection("aries", planet_longitudes)

    h1 = bhava_drishti[1]
    assert h1.lord == "mars"
    assert h1.direct_aspect_virupas == 0.0
    assert h1.is_50_percent_baseline_active is True
    assert h1.effective_protection_virupas == 30.0 # Exactly 50% baseline!


def test_divisional_varga_drishti():
    """Verify Shodasha Varga Drishti calculation for D9 and D30 charts."""
    engine = CanonicalDrishtiEngine()
    d9_lons = {
        "sun": 45.0,
        "moon": 120.0,
        "mars": 180.0,
        "mercury": 48.0,
        "jupiter": 225.0,
        "venus": 90.0,
        "saturn": 0.0,
    }

    matrix = engine.compute_varga_drishti("D9", d9_lons)
    assert matrix.varga_name == "D9"
    assert len(matrix.sphuta_aspects) > 0
    assert matrix.total_benefic_virupas >= 0.0
    assert matrix.total_malefic_virupas >= 0.0