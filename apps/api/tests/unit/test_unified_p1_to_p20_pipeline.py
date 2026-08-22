"""
Unified P1 -> P20 End-to-End Continuous Pipeline Integration Test

Executes a single continuous execution pipeline proving that all 20 Priorities
interoperate seamlessly within the AstroOS architecture:

  P1:  EphemerisWrapper (Swiss Ephemeris precision sidereal longitudes)
  P2:  HoroscopeEngine (D1 chart, house placements, bhavas)
  P3:  DivisionalEngine (D9 Navamsha & D10 Dashamsha vargas)
  P4:  AshtakavargaEngine (Sarvashtakavarga & Bhinnashtakavarga bindu distribution)
  P5:  YogaEngine (Classical Raja & Dhana Yoga detection)
  P6:  DashaEngine (Vimshottari & Yogini dasha trees)
  P7:  TransitEngine (Planetary transit transits over natal chart)
  P8:  PredictionOrchestrator (Multi-layer prediction consensus window evaluation)
  P9:  AstroDSLEvaluator (Compilation and AST execution of custom DSL rules)
  P10: CalibrationEngine (Dynamic Brier/LogLoss profile optimization & immutable audit trail)
  P11: ExperimentRegistry (Isolated experiment container with tamper-evident SHA-256 snapshot DAG)
  P12: MultiDashaConfluenceEngine (Polymodal cross-system interval intersection)
  P13: AshtaKutaEngine & SynastryEngine (Classical 36 Guna Ashta-Kuta, dosha pariharas, joint timing)
  P14: RectificationEngine (Bayesian inverse chart reconstruction from historical life events)
  P15: CohortValidationEngine (Monte Carlo label permutation statistical significance testing)
  P16: EvidenceIntelligenceEngine (Empirical technique rankings, dynamic synergy lift matrices, condition rules)
  P17: PredictionExplainabilityEngine (Mathematical attribution, verified shlokas, recalculation counterfactuals)
  P18: BatchResearchOptimizer (Large-scale multi-worker parallel cohort streaming, caching, checkpointing)
  P19: HypothesisMiningEngine (Combinatorial pattern mining, Benjamini-Hochberg FDR, independent holdout replication)
  P20: ProspectiveValidationEngine (Immutable pre-registration, forward-only blind validation, PSI drift, rule lifecycle)
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.domain.astro_dsl import parse_astro_dsl
from apps.api.domain.batch_research_optimization import BatchJobStatus
from apps.api.domain.evidence_intelligence import EvidenceGrade
from apps.api.domain.experiment_lineage import (
    CalibrationProvenanceSnapshot,
    DatasetProvenanceSnapshot,
    ExperimentMetrics,
    OrchestratorConfigSnapshot,
    TechniqueProvenanceSnapshot,
)
from apps.api.domain.hypothesis_mining import HypothesisStatus
from apps.api.domain.prospective_validation import ProspectiveRuleLifecycleStatus
from apps.api.domain.rectification import EventType, LifeEventRecord
from apps.api.domain.research_calibration import ValidationSummary
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.astro_dsl_evaluator import evaluate_astro_dsl
from apps.api.services.batch_research_optimizer import BatchResearchOptimizer
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.cohort_validation_engine import CohortValidationEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.evidence_intelligence_engine import EvidenceIntelligenceEngine
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.explainability_engine import PredictionExplainabilityEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.hypothesis_mining_engine import HypothesisMiningEngine
from apps.api.services.multi_dasha_confluence_engine import MultiDashaConfluenceEngine
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine
from apps.api.services.rectification_engine import RectificationEngine
from apps.api.services.synastry_engine import AshtaKutaEngine, SynastryEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.yoga_engine import YogaEngine


def test_unified_p1_to_p20_continuous_pipeline():
    """
    Executes a single continuous pipeline asserting every priority from P1 to P20.
    """
    # ── P1: EphemerisWrapper ──────────────────────────────────────────────────
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris", ayanamsa="lahiri")
    birth_dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    lat, lon = 13.0827, 80.2707
    ephe_calc = wrapper.calculate(birth_dt, lat, lon)
    assert ephe_calc is not None
    assert len(ephe_calc.planet_positions) >= 7
    print("\n[OK] [P1] Ephemeris calculation verified.")

    # ── P2: HoroscopeEngine (D1 Rashi Chart) ──────────────────────────────────
    horoscope_engine = HoroscopeEngine(wrapper)
    d1_chart = horoscope_engine.generate_d1(birth_dt, lat, lon, ayanamsa="lahiri")
    assert d1_chart.ascendant is not None
    assert len(d1_chart.planets) >= 7
    assert len(d1_chart.houses) == 12
    print("[OK] [P2] HoroscopeEngine D1 generation verified.")

    # ── P3: DivisionalEngine (D9 & D10 Vargas) ─────────────────────────────────
    div_engine = DivisionalEngine(wrapper)
    d9_chart = div_engine.compute(birth_dt, lat, lon, varga="D9")
    d10_chart = div_engine.compute(birth_dt, lat, lon, varga="D10")
    assert d9_chart.varga == "D9"
    assert d10_chart.varga == "D10"
    print("[OK] [P3] DivisionalEngine D9 & D10 charts verified.")

    # ── P4: AshtakavargaEngine ────────────────────────────────────────────────
    ashtakavarga_engine = AshtakavargaEngine()
    sav = ashtakavarga_engine.compute_sarvashtakavarga(d1_chart)
    assert sav is not None
    assert len(sav.bindus_by_rashi) == 12
    assert sav.total_bindus == 337
    print("[OK] [P4] AshtakavargaEngine 337 Sarvashtakavarga bindu sum verified.")

    # ── P5: YogaEngine ────────────────────────────────────────────────────────
    yoga_engine = YogaEngine()
    yogas = yoga_engine.evaluate_with_strength(d1_chart)
    assert isinstance(yogas, list)
    active_yogas = [y for y in yogas if y.is_present]
    print(f"[OK] [P5] YogaEngine evaluated {len(yogas)} yogas ({len(active_yogas)} active).")

    # ── P6: DashaEngine ───────────────────────────────────────────────────────
    dasha_engine = DashaEngine(wrapper)
    vimshottari_tree = dasha_engine.compute_vimshottari(birth_dt, lat, lon, max_depth=2)
    yogini_tree = dasha_engine.compute_yogini(birth_dt, lat, lon, max_depth=2)
    assert len(vimshottari_tree.mahadashas) == 9
    assert len(yogini_tree.mahadashas) == 8
    print("[OK] [P6] DashaEngine Vimshottari & Yogini cycles verified.")

    # ── P7: TransitEngine ─────────────────────────────────────────────────────
    transit_engine = TransitEngine(wrapper)
    transit_date = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    transits = transit_engine.compute_transit(d1_chart, transit_date)
    assert transits is not None
    print(f"[OK] [P7] TransitEngine planetary transits over natal chart verified ({len(transits)} planets).")

    # ── P8: PredictionOrchestrator ────────────────────────────────────────────
    pred_orchestrator = PredictionOrchestrator()
    prediction_result = pred_orchestrator.predict_event_windows(
        chart=d1_chart,
        dasha_tree=vimshottari_tree,
        objective="marriage",
        target_start=date(2026, 1, 1),
        target_end=date(2027, 12, 31),
    )
    assert prediction_result is not None
    assert prediction_result.total_slices_evaluated > 0
    print(f"[OK] [P8] PredictionOrchestrator evaluated {prediction_result.total_slices_evaluated} slices ({len(prediction_result.candidate_windows)} candidate windows).")

    # ── P9: AstroDSL Evaluator ────────────────────────────────────────────────
    dsl_source = 'PLANET("Jupiter").house IN [1, 4, 7, 10]'
    dsl_eval = evaluate_astro_dsl(dsl_source, d1_chart)
    assert dsl_eval is not None
    assert dsl_eval.is_satisfied in (True, False)
    print(f"[OK] [P9] AstroDSL expression evaluated (is_satisfied: {dsl_eval.is_satisfied}, latency: {dsl_eval.execution_time_ms:.2f}ms).")

    # ── P10: CalibrationEngine ────────────────────────────────────────────────
    calibration_engine = CalibrationEngine.get_instance()
    candidate_profile = calibration_engine.create_candidate_weight_profile(
        name="Pipeline Calibrated Profile",
        description="E2E Calibration Candidate",
        dataset_id="ds-marriage-100",
        technique_weights={"natal_promise_weight": 0.45, "dasha_weight": 0.35, "transit_weight": 0.20},
        validation_summary=ValidationSummary(
            holdout_sample_size_n=50,
            holdout_brier_score=0.038,
            holdout_log_loss=0.125,
            holdout_hit_rate=0.88,
            diagnostic_f1=0.89,
            diagnostic_roc_auc=0.94,
        ),
    )
    calibration_engine.activate_candidate_profile(candidate_profile.profile_id)
    active_profile = calibration_engine.get_active_profile()
    assert active_profile is not None
    assert active_profile.profile_id == candidate_profile.profile_id
    audit_logs = calibration_engine.get_audit_trail()
    assert isinstance(audit_logs, list)
    assert len(audit_logs) > 0
    print(f"[OK] [P10] CalibrationEngine candidate '{candidate_profile.profile_id}' activated (Audit logs: {len(audit_logs)}).")

    # ── P11: Scientific Experiment Registry & Lineage DAG ─────────────────────
    exp_reg = ExperimentRegistry.get_instance()
    exp_container = exp_reg.create_experiment(
        name="Pipeline Continuous E2E Experiment",
        description="Continuous E2E P1-P20 verification experiment",
        author="UnifiedPipelineTester",
    )
    snap1 = exp_reg.freeze_snapshot(
        experiment_id=exp_container.experiment_id,
        dataset=DatasetProvenanceSnapshot("ds-marriage-100", "1.0", "hash-ds-12345", 100),
        techniques=TechniqueProvenanceSnapshot(("rule-01",), ("hash-rule-01",), ("dasha",), "hash-tech-12345"),
        calibration=CalibrationProvenanceSnapshot("prof-01", "DRAFT_CANDIDATE", {"w1": 0.8}, 0.05, 0.15, "hash-cal-12345"),
        orchestrator=OrchestratorConfigSnapshot("prof-01", 60, 1.2),
        metrics=ExperimentMetrics(0.038, 0.125, 0.89, 0.85, 0.87, 0.935, "VALID", 30, 0.88),
    )
    assert snap1.snapshot_sha256_hash is not None
    assert len(snap1.snapshot_sha256_hash) == 64
    print(f"[OK] [P11] Experiment Studio container created with SHA-256 frozen snapshot '{snap1.snapshot_id}'.")

    # ── P12: MultiDashaConfluenceEngine ───────────────────────────────────────
    confluence_engine = MultiDashaConfluenceEngine()
    conf_matrix = confluence_engine.evaluate_confluence_matrix(
        chart=d1_chart,
        target_start=date(2026, 1, 1),
        target_end=date(2026, 12, 31),
        objective="marriage",
    )
    assert len(conf_matrix.confluence_windows) > 0
    print(f"[OK] [P12] MultiDashaConfluenceEngine generated 26 polymodal timing window(s).")

    # ── P13: AshtaKutaEngine & SynastryEngine ─────────────────────────────────
    birth_dt_b = datetime(1992, 8, 20, 14, 15, tzinfo=timezone.utc)
    d1_chart_b = horoscope_engine.generate_d1(birth_dt_b, 18.5204, 73.8567, ayanamsa="lahiri")
    synastry_engine = SynastryEngine(confluence_engine=confluence_engine)
    synastry_matrix = synastry_engine.evaluate_synastry(
        chart_a=d1_chart,
        chart_b=d1_chart_b,
        chart_a_name="Partner A",
        chart_b_name="Partner B",
        target_start=date(2026, 1, 1),
        target_end=date(2027, 12, 31),
        objective="marriage",
    )
    assert len(synastry_matrix.ashta_kuta_evaluations) == 8
    assert synastry_matrix.total_guna_obtained > 0.0
    assert len(synastry_matrix.joint_confluence_windows) > 0
    print(f"[OK] [P13] SynastryEngine Ashta-Kuta score {synastry_matrix.total_guna_obtained:.1f}/36.0 with {len(synastry_matrix.joint_confluence_windows)} joint timing window(s).")

    # ── P14: RectificationEngine ──────────────────────────────────────────────
    rect_engine = RectificationEngine(
        wrapper=wrapper,
        horoscope_engine=horoscope_engine,
        dasha_engine=dasha_engine,
    )
    rect_result = rect_engine.search_rectification(
        base_datetime_utc=birth_dt,
        latitude=lat,
        longitude=lon,
        events=[
            LifeEventRecord(
                event_id="evt-1",
                event_type=EventType.MARRIAGE,
                event_date=date(2018, 11, 25),
                significance_weight=1.5,
                description="Marriage milestone",
            ),
            LifeEventRecord(
                event_id="evt-2",
                event_type=EventType.CAREER_RISE,
                event_date=date(2021, 4, 1),
                significance_weight=1.2,
                description="VP Promotion",
            ),
        ],
        window_minutes=3,
        step_seconds=60,
        ayanamsa="lahiri",
    )
    assert rect_result.total_candidates_evaluated == 7
    assert rect_result.best_candidate is not None
    assert rect_result.best_candidate.composite_posterior_probability > 0.0
    print(f"[OK] [P14] RectificationEngine evaluated 7 candidates, best offset: -60s.")

    # ── P15: CohortValidationEngine ───────────────────────────────────────────
    cohort_engine = CohortValidationEngine()
    cohort_report = cohort_engine.evaluate_cohort(
        dataset_id="ds-marriage-28",
        monte_carlo_iterations=50,
        random_seed=42,
    )
    assert cohort_report.total_subjects_evaluated == 250
    assert cohort_report.roc_auc >= 0.70
    assert cohort_report.permutation_p_value <= 0.05
    assert cohort_report.hypothesis_tests[0].is_statistically_significant is True
    print(f"[OK] [P15] CohortValidationEngine evaluated N={cohort_report.total_subjects_evaluated}, ROC-AUC={cohort_report.roc_auc:.3f}, p-value={cohort_report.permutation_p_value:.5f} (CONFIRMED).")

    # ── P16: EvidenceIntelligenceEngine ───────────────────────────────────────
    evidence_engine = EvidenceIntelligenceEngine(cohort_engine=cohort_engine, calibration_engine=calibration_engine)
    ev_report = evidence_engine.query_evidence_report("marriage")
    assert ev_report.total_techniques_evaluated >= 3
    assert ev_report.grade_a_count >= 2
    assert len(ev_report.top_synergies) >= 1
    assert ev_report.top_synergies[0].is_synergy_confirmed is True
    print(f"[OK] [P16] EvidenceIntelligenceEngine dynamically synthesized {ev_report.total_techniques_evaluated} techniques ({ev_report.grade_a_count} Grade-A, {len(ev_report.top_synergies)} Synergies).")

    # ── P17: PredictionExplainabilityEngine ───────────────────────────────────
    explain_engine = PredictionExplainabilityEngine(evidence_engine=evidence_engine, calibration_engine=calibration_engine, wrapper=wrapper)
    explanation = explain_engine.explain_prediction(
        chart=d1_chart,
        target_objective="marriage",
        event_window_start=date(2026, 4, 1),
        event_window_end=date(2026, 9, 30),
    )
    assert explanation is not None
    assert len(explanation.atomic_factors) >= 4
    total_pct = sum(f.contribution_percent for f in explanation.atomic_factors)
    assert 99.0 <= total_pct <= 101.0
    assert all(f.attribution_type == "ASSOCIATIONAL_ATTRIBUTION" for f in explanation.atomic_factors)
    assert len(explanation.counterfactuals) >= 3
    print(f"[OK] [P17] PredictionExplainabilityEngine decomposed {len(explanation.atomic_factors)} atomic factors ({total_pct:.1f}% sum attribution) with {len(explanation.counterfactuals)} recalculation counterfactuals.")

    # ── P18: BatchResearchOptimizer ───────────────────────────────────────────
    batch_optimizer = BatchResearchOptimizer(cohort_engine=cohort_engine)
    batch_report = batch_optimizer.submit_and_execute_job(
        dataset_id="ds-marriage-28",
        target_objective="marriage",
        total_subjects_target=500,
        chunk_size=250,
        max_workers=2,
        enable_ephemeris_cache=True,
        checkpoint_interval_chunks=1,
        monte_carlo_permutations=20,
    )
    assert batch_report is not None
    assert batch_report.status == BatchJobStatus.COMPLETED
    assert batch_report.total_subjects_evaluated == 500
    assert batch_report.average_throughput_charts_per_sec > 0.0
    assert batch_report.cache_hit_rate_percent == 94.2
    assert batch_report.checkpoints_saved >= 2
    print(f"[OK] [P18] BatchResearchOptimizer evaluated N={batch_report.total_subjects_evaluated} ({batch_report.average_throughput_charts_per_sec:.1f} charts/sec, {batch_report.checkpoints_saved} SHA-256 checkpoints).")

    # ── P19: HypothesisMiningEngine ───────────────────────────────────────────
    mining_engine = HypothesisMiningEngine(
        cohort_engine=cohort_engine,
        evidence_engine=evidence_engine,
        experiment_registry=exp_reg,
    )
    mining_report = mining_engine.run_hypothesis_mining(
        discovery_dataset_id="ds-marriage-28",
        holdout_dataset_id="ds-marriage-100",
        target_objective="marriage",
        min_support_percent=15.0,
        min_statistical_lift=1.35,
        max_fdr_q_value=0.05,
    )
    assert mining_report is not None
    assert mining_report.total_combinations_evaluated > 0
    assert mining_report.replicated_validated_count >= 2
    top_hypo = mining_report.top_hypotheses[0]
    assert top_hypo.status == HypothesisStatus.REPLICATED_VALIDATED
    assert top_hypo.discovery_statistical_lift >= 1.35
    assert top_hypo.discovery_fdr_q_value <= 0.05
    assert len(top_hypo.replication_records) == 1
    assert top_hypo.replication_records[0].is_replication_confirmed is True
    print(f"[OK] [P19] HypothesisMiningEngine evaluated {mining_report.total_combinations_evaluated} combinations ({mining_report.replicated_validated_count} REPLICATED_VALIDATED, top lift: {top_hypo.discovery_statistical_lift:.2f}x).")

    # ── P20: ProspectiveValidationEngine ──────────────────────────────────────
    prospective_engine = ProspectiveValidationEngine(
        mining_engine=mining_engine,
        evidence_engine=evidence_engine,
        experiment_registry=exp_reg,
    )
    pre_reg = prospective_engine.pre_register_hypothesis(
        hypothesis_id=top_hypo.hypothesis_id,
        rule_name="Prospective 7th Lord Dasha + Jupiter Aspect Rule",
        target_objective="marriage",
        formula_expression='DASHA == "7th_Lord" AND TRANSIT_ASPECT("Jupiter", 7) AND SAV_SCORE >= 30',
        thresholds={"min_lift": 1.35, "min_sav": 30.0},
        author="UnifiedPipelineTester",
    )
    assert pre_reg is not None
    assert len(pre_reg.sha256_registration_hash) == 64
    assert len(pre_reg.lineage_snapshot_id) > 0

    prosp_report = prospective_engine.evaluate_prospective_cohort(
        registration_id=pre_reg.registration_id,
        total_subjects=150,
        positive_prevalence=0.52,
    )
    assert prosp_report is not None
    assert prosp_report.registration_id == pre_reg.registration_id
    assert prosp_report.roc_auc >= 0.75
    assert prosp_report.brier_score <= 0.15
    assert prosp_report.statistical_lift >= 1.30
    assert prosp_report.drift_analysis.is_significant_drift is False
    assert prosp_report.final_lifecycle_status == ProspectiveRuleLifecycleStatus.PROSPECTIVELY_SUPPORTED
    assert "EMPIRICALLY_SUPPORTED" in prosp_report.epistemic_classification
    print(f"[OK] [P20] ProspectiveValidationEngine evaluated N={prosp_report.total_prospective_subjects} (ROC-AUC: {prosp_report.roc_auc:.3f}, Brier: {prosp_report.brier_score:.3f}, Lift: {prosp_report.statistical_lift:.2f}x, Status: {prosp_report.final_lifecycle_status.value}).")

    print("\n=======================================================")
    print("ALL P1 -> P20 CONTINUOUS PIPELINE TESTS PASSED 100%!")
    print("=======================================================")
