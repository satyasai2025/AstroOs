"""
AstroOS — Shastric Reasoning Pipeline & 3-Tier Validation Unit Tests
====================================================================

Tests:
1. CanonicalFactsGenerator (Strictly Calculation-Only, No Prediction/Rules).
2. TechniqueResolver (Domain-Tailored Shastric Execution Plans).
3. ShastricRuleEngine (Declarative Rule Evaluation).
4. EvidenceAggregator & PredictionCalibrator (Calibrated Signal Score 0-9).
5. ShastricExplanationNarrator (Transparent Grounded Shastric Narratives).
6. End-to-End ShastricReasoningPipeline Execution.
7. ThreeTierValidationFramework (Tier 1 Regression, Tier 2 Generalization, Tier 3 Holdout).
"""

import pytest
from datetime import date, datetime, timezone

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.phalita_core.canonical_facts_generator import CanonicalFactsGenerator
from apps.api.services.phalita_core.technique_resolver import TechniqueResolver
from apps.api.services.phalita_core.shastric_rule_engine import ShastricRuleEngine
from apps.api.services.phalita_core.evidence_aggregator import EvidenceAggregator
from apps.api.services.phalita_core.prediction_calibrator import PredictionCalibrator
from apps.api.services.phalita_core.shastric_explanation_narrator import ShastricExplanationNarrator
from apps.api.services.phalita_core.shastric_reasoning_pipeline import ShastricReasoningPipeline
from apps.api.services.phalita_core.three_tier_validation_framework import ThreeTierValidationFramework


@pytest.fixture
def ephem_wrapper():
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


def test_canonical_facts_calculation_only(ephem_wrapper):
    """Verify CanonicalFactsGenerator is strictly calculation-only."""
    gen = CanonicalFactsGenerator(ephem_wrapper)
    dt = datetime(1950, 9, 17, 5, 30, 0, tzinfo=timezone.utc)

    facts = gen.generate_facts(
        birth_datetime=dt,
        latitude=23.7844,
        longitude=72.6393,
        target_date=date(2014, 5, 26),
    )

    # 1. Ephemeris coordinates verified
    assert facts.ascendant_rashi == "Scorpio"
    assert facts.chandra_rashi == "Scorpio"
    assert len(facts.planets) >= 7

    # 2. Bhavachalita cusps verified (12 houses)
    assert len(facts.bhavachalita_houses) == 12
    for b in facts.bhavachalita_houses:
        assert b.starting_cusp != b.ending_cusp
        assert b.bhava_lord is not None

    # 3. 7 Chara Karakas verified (Strictly 7)
    assert len(facts.chara_karakas) == 7
    roles = [k.karaka_role for k in facts.chara_karakas]
    assert roles == ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
    assert facts.karakamsha_lagna_rashi == "Sagittarius"

    # 4. Ashtakavarga and Dasha active
    assert len(facts.sarvashtakavarga_rekhas) == 12
    assert facts.active_d1_dasha["MD"] == "Moon"


def test_technique_resolver(ephem_wrapper):
    """Verify TechniqueResolver resolves domain-tailored Shastric plans."""
    for dom, p_bhava in [("career", 10), ("marriage", 7), ("wealth", 2), ("children", 5), ("accident", 8)]:
        plan = TechniqueResolver.resolve_domain_plan(dom)
        assert plan.domain == dom
        assert plan.primary_bhava == p_bhava
        assert len(plan.designated_vargas) >= 2
        assert len(plan.relevant_chara_karaka_roles) >= 2
        assert len(plan.technique_execution_order) == 5


def test_shastric_rule_engine_and_evidence(ephem_wrapper):
    """Verify ShastricRuleEngine and EvidenceAggregator trace provenance."""
    gen = CanonicalFactsGenerator(ephem_wrapper)
    dt = datetime(1950, 9, 17, 5, 30, 0, tzinfo=timezone.utc)
    facts = gen.generate_facts(dt, 23.7844, 72.6393, target_date=date(2014, 5, 26))

    rule_res = ShastricRuleEngine.evaluate_rules(facts, "career")
    assert rule_res.fired_rules_count >= 2
    assert len(rule_res.positive_promisers) >= 1

    evidence = EvidenceAggregator.aggregate_evidence(facts, rule_res)
    assert evidence.domain == "career"
    assert evidence.is_sufficient_for_prediction is True
    assert evidence.evidence_provenance_hash.startswith("PROV-")
    assert len(evidence.primary_astronomical_anchors) >= 2


def test_end_to_end_shastric_pipeline(ephem_wrapper):
    """Verify complete 6-stage Shastric reasoning pipeline execution."""
    pipeline = ShastricReasoningPipeline(ephem_wrapper)
    dt = datetime(1950, 9, 17, 5, 30, 0, tzinfo=timezone.utc)

    res = pipeline.execute_pipeline(
        birth_datetime=dt,
        latitude=23.7844,
        longitude=72.6393,
        domain="career",
        target_date=date(2014, 5, 26),
    )

    assert res.domain == "career"
    assert 0.0 <= res.calibrated_prediction_verdict.calibrated_signal_score <= 9.0
    assert res.calibrated_prediction_verdict.signal_tier in ("HIGH_PROMINENCE", "MODERATE_PROMINENCE", "DORMANT_LOW_PROMINENCE")
    assert res.grounded_explanation.full_markdown_report is not None
    assert "Shastric Analysis" in res.grounded_explanation.full_markdown_report


def test_three_tier_validation_framework(ephem_wrapper):
    """Verify 3-Tier Validation Framework executes all 3 tiers with required metrics."""
    framework = ThreeTierValidationFramework(ephem_wrapper)
    audit = framework.run_full_3tier_audit()

    # Tier 1 Regression
    assert audit.tier1_regression.total_benchmark_cases >= 5
    assert audit.tier1_regression.is_regression_clean is True

    # Tier 2 Generalization (N=600, 1,200 Windows)
    assert audit.tier2_generalization.total_cohort_charts == 600
    assert audit.tier2_generalization.total_evaluated_windows == 1200
    assert audit.tier2_generalization.precision >= 80.0
    assert audit.tier2_generalization.false_positive_rate <= 15.0
    assert audit.tier2_generalization.roc_auc_score >= 0.85
    assert audit.tier2_generalization.is_statistically_robust is True

    # Tier 3 Holdout Validation (N=100 Blind Holdout)
    assert audit.tier3_holdout.total_holdout_charts == 100
    assert audit.tier3_holdout.zero_leakage_verified is True
    assert audit.tier3_holdout.is_validation_passed is True
    assert audit.overall_system_status == "PASSED_AND_STATISTICALLY_ROBUST"
