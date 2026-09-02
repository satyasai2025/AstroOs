"""
AstroOS — Phase 2: 12-Bhava Life Domains & Siddhantic Fusion Test Suite
========================================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md
Tests:
1. 12-Bhava Domain Registry Integrity (Houses 1-12, Karakas, Designated Vargas).
2. Divisional Vimshottari Dasha Engine (D9, D10, D7, D4, D30).
3. Main Strength x Vimshopaka Final Varga Fusion & Neecha Bhanga.
4. Bhavottama (Kimshukadi) Detection.
5. Transit (Gochara) & Ashtakavarga Rekha Trigger Engine.
6. Multi-Domain Cognitive MoE Orchestration across all 12 life areas.
"""

import pytest
from datetime import date, datetime, timezone

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.intelligence.linked_system import LinkedSystemBuilder
from apps.api.services.intelligence.cognitive_reasoner import DashaPeriod5Level
from apps.api.services.divisional_vimshottari_engine import DivisionalVimshottariEngine
from apps.api.services.phalita_core.domain_significators import (
    DOMAIN_SIGNIFICATOR_REGISTRY,
    get_domain_config,
    get_all_domains,
)
from apps.api.services.phalita_core.varga_strength_fusion import (
    VargaStrengthFusionEngine,
    PlanetVargaStrengthDetail,
)
from apps.api.services.phalita_core.bhavottama_engine import BhavottamaEngine
from apps.api.services.phalita_core.transit_trigger_engine import TransitTriggerEngine
from apps.api.services.phalita_core.phalita_moe_orchestrator import PhalitaMoEOrchestrator


@pytest.fixture
def ephem_wrapper():
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


@pytest.fixture
def sample_chart(ephem_wrapper):
    dt = datetime(1985, 5, 15, 14, 30, 0, tzinfo=timezone.utc)
    engine = HoroscopeEngine(ephem_wrapper)
    return engine.generate_d1(dt, 28.6139, 77.2090)


@pytest.fixture
def sample_graph(sample_chart):
    graha_positions = {p.planet.capitalize(): int(p.sidereal_longitude / 30.0) % 12 for p in sample_chart.planets}
    lagna_idx = int(sample_chart.ascendant.sidereal_longitude / 30.0) % 12
    return LinkedSystemBuilder.build_graph(
        lagna_rashi_idx=lagna_idx,
        graha_positions=graha_positions,
        gulika_rashi_idx=(lagna_idx + 6) % 12,
        mandi_rashi_idx=(lagna_idx + 7) % 12,
    )



def test_12_bhava_domain_registry():
    """Verify all 12 domains exist and match their classical Bhava foundations."""
    domains = get_all_domains()
    assert len(domains) == 12

    expected_houses = {
        "health": 1,
        "wealth": 2,
        "siblings": 3,
        "property": 4,
        "children": 5,
        "legal": 6,
        "marriage": 7,
        "accident": 8,
        "father": 9,
        "career": 10,
        "gains": 11,
        "foreign": 12,
    }

    for dom, expected_h in expected_houses.items():
        cfg = get_domain_config(dom)
        assert cfg.primary_house == expected_h, f"Domain {dom} should map to house {expected_h}"
        assert len(cfg.supporting_houses) >= 1
        assert len(cfg.naisargika_karakas) >= 1
        assert cfg.designated_varga in (1, 2, 3, 4, 7, 9, 10, 12, 30)


def test_divisional_vimshottari_computation(ephem_wrapper):
    """Verify independent Vimshottari calculations for D9, D10, D7, D4, and D30."""
    engine = DivisionalVimshottariEngine(ephem_wrapper)
    dt = datetime(1985, 5, 15, 14, 30, 0, tzinfo=timezone.utc)

    for varga in (9, 10, 7, 4, 30):
        tree = engine.compute_divisional_vimshottari(
            birth_datetime=dt,
            latitude=28.6139,
            longitude=77.2090,
            varga_number=varga,
            max_depth=3,
        )
        assert tree is not None
        assert tree.system == f"Vimshottari_D{varga}"
        assert len(tree.mahadashas) >= 9


        # Active lords at target date
        active_lords = engine.get_active_lords_at_date(tree, date(2023, 6, 1), varga_number=varga)
        assert active_lords.mahadasha_lord.lower() in ("sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu", "venus")
        assert active_lords.antardasha_lord.lower() in ("sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu", "venus")



def test_varga_strength_fusion_and_neecha_bhanga():
    """Verify Log-Base-2 Main Strength x Vimshopaka Weight and Neecha Bhanga."""
    # Sun exalted in Aries (Rashi 0) -> Main Strength = 9
    detail_sun = VargaStrengthFusionEngine.evaluate_planet_varga_strength(
        planet="sun",
        varga_number=1,
        sign_index=0,
    )
    assert detail_sun.dignity_score == 9
    assert detail_sun.final_varga_strength == 9 * 3.0  # D1 Vimshopaka weight = 3.0

    # Moon in Scorpio (Rashi 7) -> Debilitated (Score 1)
    detail_moon_deb = VargaStrengthFusionEngine.evaluate_planet_varga_strength(
        planet="moon",
        varga_number=1,
        sign_index=7,
    )
    assert detail_moon_deb.dignity_score == 1
    assert not detail_moon_deb.is_debilitation_cancelled

    # Moon in Scorpio conjunct Mars (sign lord) -> Debilitation cancelled to Neutral (Score 4)
    detail_moon_nb = VargaStrengthFusionEngine.evaluate_planet_varga_strength(
        planet="moon",
        varga_number=1,
        sign_index=7,
        sign_occupants=("moon", "mars"),
    )
    assert detail_moon_nb.dignity_score == 4
    assert detail_moon_nb.is_debilitation_cancelled


def test_bhavottama_detection():
    """Verify Bhavottama (same house across divisionals) and yoga amplification."""
    # Planet in H10 in D1, H10 in D9, and H10 in D10 (Exalted in D1 sign 0)
    status_tri = BhavottamaEngine.evaluate_planet(
        planet="Sun",
        d1_house=10,
        d9_house=10,
        d10_house=10,
        d1_sign_idx=0,
    )
    assert status_tri.is_tri_bhavottama
    assert status_tri.amplification_factor == 2.0  # Kimshuka Yoga exalted multiplier

    # Planet in different houses
    status_diff = BhavottamaEngine.evaluate_planet(
        planet="Moon",
        d1_house=4,
        d9_house=8,
        d10_house=12,
        d1_sign_idx=3,
    )
    assert not status_diff.is_tri_bhavottama
    assert not status_diff.is_d1_d9_bhavottama
    assert status_diff.amplification_factor == 1.0


def test_transit_gochara_trigger(ephem_wrapper):
    """Verify Gochara trigger with Ashtakavarga rekha support."""
    engine = TransitTriggerEngine(ephem_wrapper)
    target_d = date(2026, 3, 15)

    # Natal Lagna = Aries (0), evaluating Career (H10 -> Capricorn 9)
    sav_test_matrix = {9: 34} # High SAV in Capricorn
    res = engine.evaluate_transit_trigger(
        natal_lagna_rashi_idx=0,
        domain="career",
        primary_house=10,
        target_date=target_d,
        sav_matrix=sav_test_matrix,
    )
    assert res.domain == "career"
    assert res.sav_score == 34
    assert res.is_sav_benefic


def test_12_domain_moe_synthesis(sample_graph):
    """Verify multi-expert synthesis across all 12 canonical life domains."""
    dasha = DashaPeriod5Level.from_canonical_path(
        md_lord="Jupiter",
        ad_lord="Sun",
        pd_lord="Mars",
        sookshma_lord="Venus",
        praana_lord="Mercury",
    )

    domains = get_all_domains()
    for dom in domains:
        verdict = PhalitaMoEOrchestrator.synthesize(sample_graph, dasha, domain=dom)
        assert verdict.domain == dom
        assert 0.0 <= verdict.final_cognitive_score <= 9.0
        assert isinstance(verdict.is_probable, bool)
        assert len(verdict.expert_breakdown) == 4
        assert "TemporalDashaExpert" in verdict.expert_breakdown
        assert len(verdict.gating_weights) == 4
        assert len(verdict.rule_traces) >= 2
