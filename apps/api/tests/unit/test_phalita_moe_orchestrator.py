"""
AstroOS — Unit Tests for Phalita Mixture of Experts (MoE) Orchestrator
"""

import pytest
from apps.api.services.intelligence import (
    LinkedSystemBuilder,
    DashaPeriod5Level,
)
from apps.api.services.phalita_core import (
    NatalStructuralExpert,
    DivisionalYogaExpert,
    TemporalDashaExpert,
    UpagrahaShadowExpert,
    ExpertRouter,
    ConflictResolutionEngine,
    PhalitaMoEOrchestrator,
)


@pytest.fixture
def sample_marriage_chart():
    # Mesha Lagna (0), Venus in Libra (6), Mandi in Scorpio (7)
    graha_pos = {
        "Sun": 0, "Moon": 3, "Mars": 0, "Mercury": 1,
        "Jupiter": 8, "Venus": 6, "Saturn": 10, "Rahu": 1, "Ketu": 7,
    }
    graph = LinkedSystemBuilder.build_graph(
        lagna_rashi_idx=0,
        graha_positions=graha_pos,
        gulika_rashi_idx=2,
        mandi_rashi_idx=6, # 7th house Mandi -> delay factor
    )
    dasha = DashaPeriod5Level(
        mahadasha="Venus",
        antardasha="Jupiter",
        pratyantardasha="Venus",
        sookshma="Venus",
        praana="Jupiter",
    )
    return graph, dasha


def test_expert_registry_evaluation(sample_marriage_chart):
    graph, dasha = sample_marriage_chart

    # 1. Structural Expert
    out_struct = NatalStructuralExpert.evaluate(graph, "marriage")
    assert out_struct.expert_name == "NatalStructuralExpert"
    assert 0.0 <= out_struct.expert_score <= 9.0

    # 2. Yoga Expert
    out_yoga = DivisionalYogaExpert.evaluate(graph, "marriage")
    assert out_yoga.expert_name == "DivisionalYogaExpert"
    assert 0.0 <= out_yoga.expert_score <= 9.0

    # 3. Temporal Dasha Expert
    out_temp = TemporalDashaExpert.evaluate(graph, dasha, "marriage")
    assert out_temp.expert_name == "TemporalDashaExpert"
    assert 0.0 <= out_temp.expert_score <= 9.0

    # 4. Upagraha Shadow Expert
    out_upa = UpagrahaShadowExpert.evaluate(graph, "marriage")
    assert out_upa.expert_name == "UpagrahaShadowExpert"
    assert 0.0 <= out_upa.expert_score <= 9.0


def test_expert_router_softmax_distribution():
    weights_marriage = ExpertRouter.route("marriage")
    assert round(weights_marriage.structural + weights_marriage.divisional + weights_marriage.temporal + weights_marriage.upagraha, 5) == 1.0
    # For marriage, Temporal and Upagraha should have significant weights
    assert weights_marriage.temporal > weights_marriage.divisional

    weights_career = ExpertRouter.route("career")
    assert round(weights_career.structural + weights_career.divisional + weights_career.temporal + weights_career.upagraha, 5) == 1.0
    # For career, Divisional/Yoga should have high weight
    assert weights_career.divisional > weights_career.upagraha


def test_conflict_resolution_engine(sample_marriage_chart):
    graph, dasha = sample_marriage_chart
    out_temp = TemporalDashaExpert.evaluate(graph, dasha, "marriage")
    out_upa = UpagrahaShadowExpert.evaluate(graph, "marriage")
    out_struct = NatalStructuralExpert.evaluate(graph, "marriage")
    out_div = DivisionalYogaExpert.evaluate(graph, "marriage")

    experts_map = {
        out_struct.expert_name: out_struct,
        out_div.expert_name: out_div,
        out_temp.expert_name: out_temp,
        out_upa.expert_name: out_upa,
    }

    res = ConflictResolutionEngine.resolve_conflicts(experts_map, fused_raw_score=7.0, domain="marriage")
    assert res.precedence_rule_applied != ""
    assert 0.0 <= res.adjusted_score <= 9.0


def test_phalita_moe_orchestrator_full_synthesis(sample_marriage_chart):
    graph, dasha = sample_marriage_chart

    verdict = PhalitaMoEOrchestrator.synthesize(graph, dasha, domain="marriage")
    assert verdict.domain == "marriage"
    assert 0.0 <= verdict.final_cognitive_score <= 9.0
    assert len(verdict.expert_breakdown) == 4
    assert len(verdict.gating_weights) == 4
    assert verdict.consensus_summary != ""
    assert verdict.actionable_recommendation != ""
    assert len(verdict.rule_traces) > 0


def test_phalita_moe_career_synthesis():
    # Mesha Lagna (0), Sun in Mesha (0), Mars in Makara (9) exalted in 10th
    graha_pos = {
        "Sun": 0, "Moon": 3, "Mars": 9, "Mercury": 0,
        "Jupiter": 11, "Venus": 6, "Saturn": 9, "Rahu": 1, "Ketu": 7,
    }
    graph = LinkedSystemBuilder.build_graph(
        lagna_rashi_idx=0,
        graha_positions=graha_pos,
        gulika_rashi_idx=9,  # 10th house Upachaya (+1.5 boost)
        mandi_rashi_idx=10,
    )
    dasha = DashaPeriod5Level(
        mahadasha="Mars",
        antardasha="Sun",
        pratyantardasha="Mars",
        sookshma="Sun",
        praana="Jupiter",
    )

    verdict = PhalitaMoEOrchestrator.synthesize(graph, dasha, domain="career")
    assert verdict.domain == "career"
    assert verdict.final_cognitive_score >= 6.0
    assert verdict.is_probable is True
