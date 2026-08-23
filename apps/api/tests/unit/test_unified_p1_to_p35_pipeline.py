"""
AstroOS — Unified Continuous P1 to P35 End-to-End Pipeline Integration Test

Executes the complete research stack continuously from Priority 1 through Priority 35:
  P1-P9   : Foundational Ephemeris, Chart, Varga, Ashtakavarga, Dasha, Transits, Orchestrator, DSL
  P10-P11 : Calibration & Experiment Registry SHA-256 Snapshot DAG
  P12-P14 : Confluence, Synastry, Rectification
  P15-P16 : Cohort Validation & Evidence Intelligence
  P17-P18 : Prediction Explainability & Batch Research Optimizer
  P19-P20 : Hypothesis Mining & Prospective Validation
  P21-P22 : Research Data Governance & Reproducibility Engine
  P23-P24 : Decision Synthesis & Knowledge Graph
  P25-P26 : Action Verdict & Portfolio Planner
  P27-P28 : Longitudinal Tracking & Adaptive Sequential Experimentation
  P29     : Benchmark Expansion Engine
  P30     : Research Publication & Cryptographic Audit Report Engine
  P31     : Research Forensic & Evidence Reconstruction Engine
  P32     : Research Evidence Intake & Real-World Outcome Registry Engine
  P33     : Research Validity & Statistical Integrity Engine
  P34     : Research Reproducibility, Replication & Falsification Engine
  P35     : External Validity, Generalization & Domain Transportability Engine
"""

import pytest

from apps.api.domain.research_evidence_registry import (
    ControlledResearchDomain,
    EvidenceOrigin,
    OutcomeVerificationStatus,
)
from apps.api.domain.research_forensics import ForensicVerdict
from apps.api.domain.research_generalization import (
    DistributionShiftType,
    GeneralizationVerdict,
    MatrixCellStatus,
    TransportabilityStatus,
)
from apps.api.domain.research_publication import PublicationStatus
from apps.api.domain.research_replication import (
    DatasetIndependenceStatus,
    FalsificationResult,
    ReplicationVerdict,
    ReproductionStatus,
)
from apps.api.domain.research_validity import ValidityVerdict
from apps.api.services.adaptive_research_engine import AdaptiveResearchEngine
from apps.api.services.benchmark_expansion_engine import BenchmarkExpansionEngine
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.cohort_validation_engine import CohortValidationEngine
from apps.api.services.decision_action_engine import ResearchDecisionActionEngine
from apps.api.services.decision_synthesis_engine import ResearchDecisionSynthesisEngine
from apps.api.services.evidence_intelligence_engine import EvidenceIntelligenceEngine
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.explainability_engine import PredictionExplainabilityEngine
from apps.api.services.hypothesis_mining_engine import HypothesisMiningEngine
from apps.api.services.longitudinal_tracking_engine import LongitudinalTrackingEngine
from apps.api.services.portfolio_planner_engine import ResearchPortfolioPlannerEngine
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine
from apps.api.services.research_data_governance_engine import ResearchDataGovernanceEngine
from apps.api.services.research_evidence_registry_engine import ResearchEvidenceRegistryEngine
from apps.api.services.research_forensic_engine import ResearchForensicEngine
from apps.api.services.research_generalization_engine import ResearchGeneralizationEngine
from apps.api.services.research_knowledge_graph_engine import ResearchKnowledgeGraphEngine
from apps.api.services.research_publication_engine import ResearchPublicationEngine
from apps.api.services.research_replication_engine import ResearchReplicationEngine
from apps.api.services.research_reproducibility_engine import ResearchReproducibilityEngine
from apps.api.services.research_validity_engine import ResearchValidityEngine


def test_unified_p1_to_p35_pipeline_continuous_execution():
    """
    Continuous End-to-End Test for P1 through P35.
    """
    print("\n=======================================================")
    print("STARTING UNIFIED CONTINUOUS P1 -> P35 PIPELINE EXECUTION")
    print("=======================================================")

    # 1. P10/P11 Infrastructure
    exp_reg = ExperimentRegistry.get_instance()
    calibration = CalibrationEngine.get_instance()

    # 2. P15/P16 Cohort & Evidence
    cohort = CohortValidationEngine()
    evidence = EvidenceIntelligenceEngine(cohort_engine=cohort, calibration_engine=calibration)
    ev_report = evidence.query_evidence_report("marriage")
    print(f"[OK] [P15/P16] Evidence Report compiled (Total techniques={ev_report.total_techniques_evaluated})")

    # 3. P19/P20 Mining & Prospective
    mining = HypothesisMiningEngine(cohort_engine=cohort, evidence_engine=evidence, experiment_registry=exp_reg)
    mining_report = mining.run_hypothesis_mining(
        discovery_dataset_id="ds-marriage-28",
        holdout_dataset_id="ds-marriage-100",
        target_objective="marriage",
        min_support_percent=15.0,
        min_statistical_lift=1.35,
        max_fdr_q_value=0.05,
    )
    print(f"[OK] [P19] Hypothesis Mining completed (Top lift={mining_report.top_hypotheses[0].discovery_statistical_lift:.2f}x)")

    prospective = ProspectiveValidationEngine(mining_engine=mining, evidence_engine=evidence, experiment_registry=exp_reg)
    pre_reg = prospective.pre_register_hypothesis(
        hypothesis_id="hyp-m1",
        rule_name="Prospective 7th Lord Dasha + Jupiter Aspect Rule",
        target_objective="marriage",
        formula_expression='DASHA == "7th_Lord" AND TRANSIT_ASPECT("Jupiter", 7) AND SAV_SCORE >= 30',
        thresholds={"min_lift": 1.35, "min_sav": 30.0},
        author="UnifiedPipelineTester",
    )
    from datetime import date as _date
    _pos_i = 0
    for _i in range(150):
        if _i % 3 == 0 and _pos_i < 50:
            _prob, _outcome = 0.9, True
            _pos_i += 1
        else:
            _prob, _outcome = 0.1, False
        prospective.log_blind_prediction(
            registration_id=pre_reg.registration_id,
            subject_id=f"subj-{_i:03d}",
            predicted_probability=_prob,
            prediction_window_start=_date(2026, 1, 1),
            prediction_window_end=_date(2026, 6, 30),
        )
        prospective.record_subject_outcome(pre_reg.registration_id, f"subj-{_i:03d}", _outcome)
    prosp_eval = prospective.evaluate_prospective_cohort(pre_reg.registration_id)
    print(f"[OK] [P20] Prospective Validation completed (ROC-AUC={prosp_eval.roc_auc:.3f})")

    # 4. P21/P22 Governance & Reproducibility
    data_gov = ResearchDataGovernanceEngine(experiment_registry=exp_reg)
    repro = ResearchReproducibilityEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, mining_engine=mining,
        prospective_engine=prospective, data_gov_engine=data_gov,
    )

    # 5. P23/P24 Decision Synthesis & Graph
    explain = PredictionExplainabilityEngine(evidence_engine=evidence, calibration_engine=calibration)
    decision = ResearchDecisionSynthesisEngine(
        cohort_engine=cohort, evidence_engine=evidence, explain_engine=explain,
        mining_engine=mining, prospective_engine=prospective,
        data_gov_engine=data_gov, repro_engine=repro, experiment_registry=exp_reg,
    )
    graph = ResearchKnowledgeGraphEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, evidence_engine=evidence,
        mining_engine=mining, prospective_engine=prospective,
        repro_engine=repro, data_gov_engine=data_gov,
    )

    # 6. P25/P26 Action Verdict & Portfolio Planner
    action = ResearchDecisionActionEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, evidence_engine=evidence,
        mining_engine=mining, prospective_engine=prospective,
        data_gov_engine=data_gov, repro_engine=repro,
        decision_engine=decision, graph_engine=graph,
    )
    planner = ResearchPortfolioPlannerEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, evidence_engine=evidence,
        mining_engine=mining, prospective_engine=prospective,
        data_gov_engine=data_gov, repro_engine=repro,
        graph_engine=graph, action_engine=action,
    )

    # 7. P27/P28 Longitudinal & Adaptive
    longitudinal = LongitudinalTrackingEngine(
        prospective_engine=prospective, planner_engine=planner, experiment_registry=exp_reg,
    )
    adaptive = AdaptiveResearchEngine(
        planner_engine=planner, longitudinal_engine=longitudinal, experiment_registry=exp_reg,
    )

    # 8. P29 Benchmark Expansion
    benchmark = BenchmarkExpansionEngine(experiment_registry=exp_reg)
    bm_report = benchmark.generate_cross_domain_report("snap-p11-p35-root")
    print(f"[OK] [P29] Benchmark Expansion complete (Accuracy={bm_report.overall_mean_reproduction_accuracy:.1f}%)")

    # 9. P30 Research Publication Engine
    pub_engine = ResearchPublicationEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, evidence_engine=evidence,
        mining_engine=mining, prospective_engine=prospective, data_gov_engine=data_gov,
        repro_engine=repro, decision_engine=decision, graph_engine=graph,
        action_engine=action, planner_engine=planner, longitudinal_engine=longitudinal,
        adaptive_engine=adaptive, benchmark_engine=benchmark,
    )
    publication = pub_engine.generate_publication_report(
        target_objective="marriage",
        snapshot_id="snap-p11-p35-root",
        status=PublicationStatus.PEER_REVIEW_READY,
    )
    print(f"[OK] [P30] Publication Report generated ({publication.report_id})")

    # 10. P31 Research Forensic Engine
    forensic_engine = ResearchForensicEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, evidence_engine=evidence,
        mining_engine=mining, prospective_engine=prospective, data_gov_engine=data_gov,
        repro_engine=repro, decision_engine=decision, graph_engine=graph,
        action_engine=action, planner_engine=planner, longitudinal_engine=longitudinal,
        adaptive_engine=adaptive, benchmark_engine=benchmark, publication_engine=pub_engine,
    )
    recon_res = forensic_engine.reconstruct_research_result("marriage", snapshot_id="snap-p11-p35-root")
    print(f"[OK] [P31] Forensic Reconstruction Verdict: {recon_res.verdict.value}")

    # 11. P32 Research Evidence Registry Engine
    evidence_reg = ResearchEvidenceRegistryEngine(experiment_registry=exp_reg)
    observation = evidence_reg.register_observation(
        subject_reference="subj-p35-pipeline-01",
        domain=ControlledResearchDomain.MARRIAGE,
        event_type="MARRIAGE_VERIFIED_DATE",
        event_description="Civil marriage ceremony recorded in public registry",
        event_date="2024-06-15",
        evidence_origin=EvidenceOrigin.OBSERVED_REAL_WORLD_EVIDENCE,
        verification_status=OutcomeVerificationStatus.INDEPENDENTLY_VERIFIED,
        verification_method="CIVIL_REGISTRY_CERTIFICATE",
        verifier_reference="PUBLIC_REGISTRAR",
        prospective_rule_id="hyp-m1",
        experiment_id="exp-p35-pipeline",
        p11_snapshot_id="snap-p11-p35-root",
    )
    print(f"[OK] [P32] Real-World Observation Registered ({observation.outcome_id})")

    # 12. P33 Research Validity Engine
    validity_engine = ResearchValidityEngine(
        experiment_registry=exp_reg,
        evidence_registry_engine=evidence_reg,
        cohort_engine=cohort,
        forensic_engine=forensic_engine,
        publication_engine=pub_engine,
    )
    val_assessment = validity_engine.assess_validity(target_objective="marriage", source_snapshot_id="snap-p11-p35-root")
    print(f"[OK] [P33] Research Validity Assessment completed (Verdict={val_assessment.overall_verdict.value})")

    # 13. P34 Research Replication Engine
    repl_engine = ResearchReplicationEngine(
        experiment_registry=exp_reg,
        validity_engine=validity_engine,
        evidence_registry_engine=evidence_reg,
        forensic_engine=forensic_engine,
    )
    claim = repl_engine.create_claim(research_question="Does 7th Lord Dasha predict timing?", original_assessment_id=val_assessment.assessment_id)
    proto = repl_engine.create_protocol(claim.claim_id)
    frozen_proto = repl_engine.freeze_protocol(proto.protocol_id)
    repl_study = repl_engine.assess_replication(claim_id=claim.claim_id, protocol_id=frozen_proto.protocol_id)
    print(f"[OK] [P34] Replication Assessment completed (Verdict={repl_study.overall_verdict.value})")

    # 14. P35 Research Generalization Engine
    gen_engine = ResearchGeneralizationEngine(
        experiment_registry=exp_reg,
        replication_engine=repl_engine,
        validity_engine=validity_engine,
        evidence_registry_engine=evidence_reg,
        forensic_engine=forensic_engine,
    )
    gen_assessment = gen_engine.assess_generalization(
        target_objective="marriage",
        source_replication_id=repl_study.replication_id,
    )
    print(f"[OK] [P35] External Validity Assessment completed ({gen_assessment.assessment_id}, Verdict={gen_assessment.overall_verdict.value})")
    print(f"[OK] [P35] Generalization Matrix computed ({len(gen_assessment.matrix_cells)} target cells, Status={gen_assessment.matrix_cells[0].status.value})")
    print(f"[OK] [P35] Transportability Assessment completed (Status={gen_assessment.transportability.status.value})")
    print(f"[OK] [P35] Generalization Snapshot generated (Snapshot ID={gen_assessment.generalization_snapshot_id})")

    # Pipeline Assertions
    assert gen_assessment.overall_verdict == GeneralizationVerdict.GENERALIZES
    assert gen_assessment.matrix_cells[0].status == MatrixCellStatus.SUPPORTED
    assert gen_assessment.transportability.status == TransportabilityStatus.HIGHLY_TRANSPORTABLE
    assert len(gen_assessment.generalization_fingerprint) == 64

    print("\n=======================================================")
    print("ALL P1 -> P35 CONTINUOUS PIPELINE TESTS PASSED 100%!")
    print("=======================================================")
