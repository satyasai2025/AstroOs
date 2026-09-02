"""
AstroOS — End-to-End Shastric Reasoning Pipeline
=================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md
Master orchestrator executing:
Canonical Facts -> Technique Resolver -> Rule Engine -> Evidence -> Calibrated Prediction -> AI Explanation
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.intelligence.cognitive_reasoner import DashaPeriod5Level
from apps.api.services.intelligence.linked_system import LinkedChartGraph, LinkedSystemBuilder
from apps.api.services.phalita_core.canonical_facts_generator import (
    CanonicalFacts,
    CanonicalFactsGenerator,
)
from apps.api.services.phalita_core.evidence_aggregator import (
    DomainEvidencePackage,
    EvidenceAggregator,
)
from apps.api.services.phalita_core.phalita_moe_orchestrator import (
    PhalitaMoEConsultationVerdict,
    PhalitaMoEOrchestrator,
)
from apps.api.services.phalita_core.prediction_calibrator import (
    CalibratedPredictionVerdict,
    PredictionCalibrator,
)
from apps.api.services.phalita_core.shastric_explanation_narrator import (
    ShastricExplanationNarrator,
    ShastricGroundedExplanation,
)
from apps.api.services.phalita_core.shastric_rule_engine import (
    RuleEngineEvaluationResult,
    ShastricRuleEngine,
)
from apps.api.services.phalita_core.technique_resolver import (
    ResolvedTechniquePlan,
    TechniqueResolver,
)
from apps.api.services.upagraha_engine import UpagrahaEngine


@dataclass(frozen=True)
class ShastricPipelineExecutionResult:
    domain: str
    target_date_iso: str
    canonical_facts: CanonicalFacts
    resolved_technique_plan: ResolvedTechniquePlan
    rule_evaluation_result: RuleEngineEvaluationResult
    evidence_package: DomainEvidencePackage
    calibrated_prediction_verdict: CalibratedPredictionVerdict
    grounded_explanation: ShastricGroundedExplanation


class ShastricReasoningPipeline:
    """
    Master pipeline executing the full 6-stage Shastric reasoning architecture.
    """

    def __init__(self, ephem_wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = ephem_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._facts_gen = CanonicalFactsGenerator(self._wrapper)
        self._upagraha_engine = UpagrahaEngine(self._wrapper)

    def execute_pipeline(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        domain: str = "career",
        target_date: Optional[date] = None,
        ayanamsa: str = "lahiri",
    ) -> ShastricPipelineExecutionResult:
        """
        Executes complete end-to-end pipeline.
        """
        if birth_datetime.tzinfo is None:
            birth_datetime = birth_datetime.replace(tzinfo=timezone.utc)

        t_date = target_date or birth_datetime.date()
        dom_clean = domain.lower()

        # Stage 1: Calculation-Only Canonical Facts
        facts = self._facts_gen.generate_facts(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            target_date=t_date,
            ayanamsa=ayanamsa,
        )

        # Stage 2: Technique Resolution
        plan = TechniqueResolver.resolve_domain_plan(dom_clean)

        # Stage 3: Declarative Rule Engine
        rule_res = ShastricRuleEngine.evaluate_rules(facts, dom_clean)

        # Stage 4: Evidence Aggregation
        evidence = EvidenceAggregator.aggregate_evidence(facts, rule_res)

        # Build Linked Graph & Dasha for MoE Orchestration
        graha_pos = {p.planet.capitalize(): p.rashi_index for p in facts.planets}
        upagraha_rep = self._upagraha_engine.compute_upagrahas(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )
        graph = LinkedSystemBuilder.from_canonical_report(
            lagna_rashi_idx=facts.ascendant_rashi_idx,
            graha_positions=graha_pos,
            upagraha_report=upagraha_rep,
        )
        active_dasha_5l = DashaPeriod5Level.from_canonical_path(
            md_lord=facts.active_d1_dasha.get("MD", "Sun"),
            ad_lord=facts.active_d1_dasha.get("AD", "Sun"),
            pd_lord=facts.active_d1_dasha.get("PD", "Sun"),
            sookshma_lord=facts.active_d1_dasha.get("Sookshma", "Sun"),
            praana_lord=facts.active_d1_dasha.get("Praana", "Sun"),
        )
        moe_verdict = PhalitaMoEOrchestrator.synthesize(
            graph=graph,
            dasha=active_dasha_5l,
            domain=dom_clean,
        )

        # Stage 5: Calibrated Prediction Engine
        pred_verdict = PredictionCalibrator.calibrate_prediction(evidence, moe_verdict)

        # Stage 6: Grounded AI Explanation Narrator
        explanation = ShastricExplanationNarrator.generate_explanation(facts, evidence, pred_verdict)

        return ShastricPipelineExecutionResult(
            domain=dom_clean,
            target_date_iso=t_date.isoformat(),
            canonical_facts=facts,
            resolved_technique_plan=plan,
            rule_evaluation_result=rule_res,
            evidence_package=evidence,
            calibrated_prediction_verdict=pred_verdict,
            grounded_explanation=explanation,
        )
