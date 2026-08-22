"""
Unit tests for StatisticalSweepEngine (Module 17, Phase 2)
"""

import math
import pytest

from apps.api.domain.statistical_sweep import (
    AstrologicalExposureRule,
    ContingencyTable2x2,
    HypothesisCategory,
    HypothesisDefinition,
    ScientificVerdict,
)
from apps.api.services.statistical_sweep_engine import (
    StatisticalSweepEngine,
    benjamini_hochberg_fdr,
    chi_square_test_2x2,
    compute_odds_ratio_and_ci,
    compute_relative_risk_and_ci,
    fisher_exact_test_2x2,
)


class TestStatisticalSweepEngine:
    def test_fisher_exact_test_2x2_known_values(self):
        # Classic tea tasting example / standard contingency
        # a=3, b=1, c=1, d=3 (total=8)
        p_val = fisher_exact_test_2x2(3, 1, 1, 3)
        assert 0.0 < p_val <= 1.0
        assert p_val == pytest.approx(0.48571, rel=1e-2)

        # Extreme table (perfect correlation)
        # a=10, b=0, c=0, d=10
        p_extreme = fisher_exact_test_2x2(10, 0, 0, 10)
        assert p_extreme < 0.001

        # Null table
        # a=5, b=5, c=5, d=5
        p_null = fisher_exact_test_2x2(5, 5, 5, 5)
        assert p_null == pytest.approx(1.0, rel=1e-2)

    def test_chi_square_test_2x2(self):
        # Moderate table: a=20, b=5, c=8, d=22 (N=55)
        stat, p_val = chi_square_test_2x2(20, 5, 8, 22, use_yates=True)
        assert stat > 0.0
        assert 0.0 <= p_val <= 1.0
        # Highly skewed table should have p < 0.05
        assert p_val < 0.01

        # Empty table edge case
        stat_zero, p_zero = chi_square_test_2x2(0, 0, 0, 0)
        assert stat_zero == 0.0
        assert p_zero == 1.0

    def test_odds_ratio_and_ci_with_zero_cell(self):
        # Non-zero table
        or_val, ci_low, ci_high = compute_odds_ratio_and_ci(20, 5, 8, 22)
        assert or_val == pytest.approx(11.0, rel=1e-1)
        assert ci_low < or_val < ci_high
        assert ci_low > 1.0

        # Zero-cell table (Haldane-Anscombe correction triggers)
        or_zero, low_z, high_z = compute_odds_ratio_and_ci(10, 0, 2, 15)
        assert or_zero > 1.0
        assert low_z < or_zero < high_z

    def test_relative_risk_and_ci(self):
        rr_val, rr_low, rr_high = compute_relative_risk_and_ci(20, 10, 5, 25)
        assert rr_val > 1.0
        assert rr_low < rr_val < rr_high

    def test_benjamini_hochberg_fdr(self):
        p_values = [0.001, 0.01, 0.04, 0.20, 0.80]
        q_values = benjamini_hochberg_fdr(p_values)
        assert len(q_values) == len(p_values)
        # Monotonicity check
        for i in range(len(q_values) - 1):
            assert q_values[i] <= q_values[i + 1]
        # First p-value should be adjusted: 0.001 * 5 / 1 = 0.005
        assert q_values[0] == pytest.approx(0.005, rel=1e-2)

    def test_standard_hypotheses_catalogue(self):
        engine = StatisticalSweepEngine()
        hypotheses = engine.get_standard_hypotheses()
        assert len(hypotheses) >= 5
        categories = {h.category for h in hypotheses}
        assert HypothesisCategory.MARRIAGE in categories
        assert HypothesisCategory.CAREER in categories
        assert HypothesisCategory.HEALTH in categories
        assert HypothesisCategory.LONGEVITY in categories
        for h in hypotheses:
            assert h.id.startswith("HYP-")
            assert len(h.title) > 0
            assert h.exposure_rule.rule_type != ""

    def test_contingency_table_builder_and_evaluation(self):
        engine = StatisticalSweepEngine()
        hyp = engine.get_standard_hypotheses()[0]  # HYP-MARRIAGE-01 (Venus in Kendra/Trikona)

        # Synthetic cohort
        cohort = [
            # Exposed Case (Venus in 7th, married before 30)
            {"planets": [{"planet": "Venus", "house_number": 7}], "outcomes": {"marriage_before_30": True}},
            {"planets": [{"planet": "Venus", "house_number": 1}], "outcomes": {"marriage_before_30": True}},
            {"planets": [{"planet": "Venus", "house_number": 4}], "outcomes": {"marriage_before_30": True}},
            {"planets": [{"planet": "Venus", "house_number": 9}], "outcomes": {"marriage_before_30": True}},
            {"planets": [{"planet": "Venus", "house_number": 11}], "outcomes": {"marriage_before_30": True}},
            # Exposed Control (Venus in 7th, married after 30)
            {"planets": [{"planet": "Venus", "house_number": 7}], "outcomes": {"marriage_before_30": False}},
            # Unexposed Case (Venus in 6th, married before 30)
            {"planets": [{"planet": "Venus", "house_number": 6}], "outcomes": {"marriage_before_30": True}},
            # Unexposed Control (Venus in 8th/12th, married after 30)
            {"planets": [{"planet": "Venus", "house_number": 8}], "outcomes": {"marriage_before_30": False}},
            {"planets": [{"planet": "Venus", "house_number": 12}], "outcomes": {"marriage_before_30": False}},
            {"planets": [{"planet": "Venus", "house_number": 6}], "outcomes": {"marriage_before_30": False}},
        ]

        table = engine.build_contingency_table(cohort, hyp)
        assert table.total_n == 10
        assert table.a_exposed_cases == 5
        assert table.b_exposed_controls == 1
        assert table.c_unexposed_cases == 1
        assert table.d_unexposed_controls == 3

        result = engine.evaluate_hypothesis(hyp, table, total_hypotheses_in_sweep=1)
        assert result.sample_size_n == 10
        assert result.odds_ratio > 1.0
        assert len(result.audit_trace) > 0
        assert result.has_small_sample_warning is True
        # With N=10, p > 0.05 so verdict is NULL_INSUFFICIENT_EVIDENCE
        assert result.verdict == ScientificVerdict.NULL_INSUFFICIENT_EVIDENCE

        # Test larger cohort table (e.g. scaled up by 10x)
        large_table = ContingencyTable2x2(a_exposed_cases=50, b_exposed_controls=10, c_unexposed_cases=10, d_unexposed_controls=30)
        large_result = engine.evaluate_hypothesis(hyp, large_table, total_hypotheses_in_sweep=1)
        assert large_result.fisher_exact_p_value < 0.001
        assert large_result.verdict == ScientificVerdict.CONFIRMED_SIGNIFICANT

    def test_multi_hypothesis_sweep_execution(self):
        engine = StatisticalSweepEngine()
        cohort = [
            {
                "planets": [
                    {"planet": "Venus", "house_number": 7},
                    {"planet": "Sun", "house_number": 10},
                    {"planet": "Jupiter", "house_number": 2},
                ],
                "outcomes": {
                    "marriage_before_30": True,
                    "executive_leadership": True,
                    "top_quartile_wealth": True,
                },
            },
            {
                "planets": [
                    {"planet": "Venus", "house_number": 8},
                    {"planet": "Sun", "house_number": 6},
                    {"planet": "Jupiter", "house_number": 8},
                ],
                "outcomes": {
                    "marriage_before_30": False,
                    "executive_leadership": False,
                    "top_quartile_wealth": False,
                },
            },
        ]

        report = engine.run_multi_hypothesis_sweep("Cohort_Test_2026", cohort)
        assert report.total_cohort_size == 2
        assert report.hypotheses_tested_count == len(engine.get_standard_hypotheses())
        assert len(report.results) == report.hypotheses_tested_count
        assert report.bonferroni_alpha < 0.05

    def test_cohort_pipeline_orchestration_full_flow(self):
        from apps.api.services.statistical_sweep_engine import CohortPipelineOrchestrator

        orchestrator = CohortPipelineOrchestrator()
        raw_records = [
            {
                "event_id": "EVT-001",
                "subject_id": "SUB-001",
                "birth_datetime_utc": "1990-05-15T09:00:00+00:00",
                "birth_latitude": 19.0760,
                "birth_longitude": 72.8777,
                "birth_confidence": "AA",
                "actual_date": "2018-05-15",
                "event_type": "marriage",
                "event_date_confidence": "exact_date",
                "event_verification": "official_document",
            },
            {
                "event_id": "EVT-002",
                "subject_id": "SUB-002",
                "birth_datetime_utc": "1985-08-20T14:30:00+00:00",
                "birth_latitude": 28.6139,
                "birth_longitude": 77.2090,
                "birth_confidence": "A",
                "actual_date": "2010-06-20",
                "event_type": "promotion",
                "event_date_confidence": "exact_date",
                "event_verification": "official_document",
            },
            {
                # Duplicate record (to verify QC duplicate detection)
                "event_id": "EVT-001-DUP",
                "subject_id": "SUB-001",
                "birth_datetime_utc": "1990-05-15T09:00:00+00:00",
                "birth_latitude": 19.0760,
                "birth_longitude": 72.8777,
                "birth_confidence": "AA",
                "actual_date": "2018-05-15",
                "event_type": "marriage",
                "event_date_confidence": "exact_date",
                "event_verification": "official_document",
            },
            {
                # Invalid coordinates record (to verify QC rejection)
                "event_id": "EVT-003-INVALID",
                "subject_id": "SUB-003",
                "birth_datetime_utc": "1992-01-01T00:00:00+00:00",
                "birth_latitude": 199.0,  # Invalid lat
                "birth_longitude": 72.0,
                "birth_confidence": "AA",
                "actual_date": "2020-01-01",
                "event_type": "marriage",
                "event_date_confidence": "exact_date",
                "event_verification": "official_document",
            },
        ]

        result = orchestrator.run_pipeline(
            cohort_tag="Validation_Cohort_Pipeline",
            raw_records=raw_records,
            min_rodden_rating="B",
        )

        # Stage 1: Ingestion summary
        assert result.stage_1_ingestion.total_received == 4
        assert result.stage_1_ingestion.total_accepted == 2
        assert result.stage_1_ingestion.total_rejected == 2
        assert result.stage_1_ingestion.duplicates_count >= 1
        assert len(result.stage_1_ingestion.provenance_hash_sha256) == 64

        # Stage 2: Validation summary
        assert result.stage_2_validation.accepted_events_count == 2
        assert result.stage_2_validation.rejected_events_count == 2
        assert "INVALID_COORDINATES" in result.stage_2_validation.rejections_by_code
        assert "HARD_DUPLICATE_COLLISION" in result.stage_2_validation.rejections_by_code

        # Stage 3: Batch chart generation
        assert result.stage_3_batch_charts.generated_charts_count == 2
        assert result.stage_3_batch_charts.calculation_time_ms > 0

        # Stage 4: Feature extraction
        assert result.stage_4_feature_extraction.subjects_profiled_count == 2
        assert "planets_count" in result.stage_4_feature_extraction.sample_features

        # Stage 5 & 6: Hypothesis sweep report
        assert result.stage_5_hypothesis_sweep.hypotheses_tested_count >= 5
        assert len(result.sweep_report.results) >= 5

    def test_benchmark_cohorts_and_expanded_hypotheses(self):
        engine = StatisticalSweepEngine()
        benchmarks = engine.get_benchmark_cohorts()
        assert len(benchmarks) >= 4

        gauquelin = next((b for b in benchmarks if b["cohort_id"] == "GAUQUELIN_ATHLETES_BENCHMARK"), None)
        assert gauquelin is not None
        assert gauquelin["sample_size"] == 100
        assert len(gauquelin["records"]) == 100

        # Test sweep on benchmark cohort
        standards = engine.get_standard_hypotheses()
        assert len(standards) >= 8

        sweep_report = engine.run_multi_hypothesis_sweep(
            cohort_tag=gauquelin["title"],
            cohort_records=gauquelin["records"],
            hypotheses=standards,
            nominal_alpha=0.05,
        )
        assert sweep_report.total_cohort_size == 100
        assert sweep_report.hypotheses_tested_count >= 8
        assert len(sweep_report.results) >= 8
        assert sweep_report.bonferroni_alpha < 0.01

        # Check Mars Digbala hypothesis
        mars_hyp = next((r for r in sweep_report.results if r.hypothesis.id == "HYP-CAREER-02"), None)
        assert mars_hyp is not None
        assert mars_hyp.sample_size_n == 100
        assert mars_hyp.contingency_table.total_n == 100
        assert mars_hyp.odds_ratio > 1.0  # Demonstrates positive association in sports cohort

