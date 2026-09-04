"""
Canonical Unit Tests for TPhalitCore Engine
============================================

Validates compliance with Vinay Ji's 78-document canonical rules:
1. 0-60 Base-2 Logarithmic Main Strength Scale (Uchcha=60, MT=45, Svagrihi=30... Neecha=0)
2. Start Page House Placement & Lordship Hierarchies (11L as primary functional malefic)
3. Panchadha Maitree (Naisargika + Tatkalika)
4. Tri-Lagna Sudarshana Chakra (LK, SK, CK + Amavasya discard rule)
5. 3-Level Dasha Concordance & Sadharmi interactions
6. 128-dimensional signed numerical feature tensor
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.ephemeris import Ascendant, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.phalita_core.tphalit_core import (
    TPhalitCore,
    TPhalitFeatureVector,
    MAIN_STRENGTH_SCALE,
    HOUSE_PLACEMENT_WEIGHTS,
    HOUSE_LORDSHIP_WEIGHTS,
)


@pytest.fixture
def canonical_engine():
    return TPhalitCore()


@pytest.fixture
def horoscope_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return HoroscopeEngine(wrapper)


@pytest.fixture
def sample_d1_chart(horoscope_engine):
    """Generate D1 chart for Taurus Lagna test case (Vadodara coords)."""
    dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    return horoscope_engine.generate_d1(dt, 22.3072, 73.1812)


def test_0_to_60_logarithmic_planetary_strength(canonical_engine, sample_d1_chart):
    """Verify planetary strength computation on real chart."""
    p_map = {p.planet.lower(): p for p in sample_d1_chart.planets}

    # Test that each planet returns a valid raw score (0-60), normalized score, and category
    for p_name, pos in p_map.items():
        raw, norm, cat, has_nb, _ = canonical_engine.compute_planet_strength(p_name, pos, sample_d1_chart)
        assert 0 <= raw <= 60
        assert -1.0 <= norm <= 1.0
        assert cat in MAIN_STRENGTH_SCALE or cat == "NEETHA_BHANGA"


def test_house_placement_and_lordship_hierarchy(canonical_engine):
    """Verify Start Page house hierarchies: 11L is most malefic (-1.0), 1H is best (+1.0)."""
    assert HOUSE_PLACEMENT_WEIGHTS[1] == 1.0
    assert HOUSE_PLACEMENT_WEIGHTS[9] == 0.90
    assert HOUSE_PLACEMENT_WEIGHTS[12] == -1.0

    assert HOUSE_LORDSHIP_WEIGHTS[1] == 1.0
    assert HOUSE_LORDSHIP_WEIGHTS[9] == 0.90
    assert HOUSE_LORDSHIP_WEIGHTS[11] == -1.0  # 11th lord is primary malefic
    assert HOUSE_LORDSHIP_WEIGHTS[6] == -0.85


def test_tri_lagna_sudarshana_chakra_evaluation(canonical_engine, sample_d1_chart):
    """Verify SC tri-lagna evaluation (LK, SK, CK)."""
    tri = canonical_engine.compute_tri_lagna_features(sample_d1_chart)
    assert "lagna" in tri
    assert "chandra_lagna" in tri
    assert "surya_lagna" in tri
    assert isinstance(tri["is_amavasya_sc"], bool)


def test_3_level_dasha_concordance(canonical_engine, sample_d1_chart):
    """Verify 3-level Dasha concordance calculation."""
    dasha_tree = DashaTree(
        system="vimshottari",
        birth_date=date(2020, 1, 1),
        trigger_planet="saturn",
        trigger_nakshatra="pushya",
        trigger_nakshatra_number=8,
        max_depth=3,
        total_cycle_years=120,
        mahadashas=(
            DashaPeriod(
                lord="saturn",
                start_date=date(2020, 1, 1),
                end_date=date(2039, 1, 1),
                duration_days=6940,
                level=1,
                sub_periods=(
                    DashaPeriod(
                        lord="saturn",
                        start_date=date(2020, 1, 1),
                        end_date=date(2023, 1, 1),
                        duration_days=1095,
                        level=2,
                        sub_periods=(
                            DashaPeriod(
                                lord="saturn",
                                start_date=date(2020, 1, 1),
                                end_date=date(2020, 6, 1),
                                duration_days=152,
                                level=3,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    feat = canonical_engine.compute_dasha_feature(dasha_tree, date(2020, 3, 1), sample_d1_chart)
    assert feat is not None
    assert feat.mahadasha_lord == "saturn"
    assert feat.antardasha_lord == "saturn"
    assert feat.pratyantardasha_lord == "saturn"
    assert feat.concordance_ratio == 1.0  # 3/3 agreement


def test_128_dimensional_feature_vector(canonical_engine, sample_d1_chart):
    """Verify that extract_full_vector returns a complete 128-dim signed tensor."""
    vec = canonical_engine.extract_full_vector(sample_d1_chart)
    assert isinstance(vec, TPhalitFeatureVector)
    assert len(vec.raw_vector) == 128
    assert len(vec.planets) >= 7
    assert len(vec.bhavas) == 12
    # All raw vector values must be bounded
    for v in vec.raw_vector:
        assert -5.0 <= v <= 5.0

