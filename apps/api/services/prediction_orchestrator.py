"""
AstroOS — Prediction Orchestration Engine

Orchestrates multi-technique evaluation across adaptive temporal slices:
  1. Uses AdaptiveTemporalScanner to generate hierarchical event intervals
  2. Uses FactBuilder to produce point-in-time canonical facts for each slice
  3. Uses TechniqueResolver & TechniqueEngine to evaluate rules
  4. Synthesizes deterministic prediction score and candidate windows

STRICT CONTRACT: Does NOT calculate astrological rules directly; delegates 100%
of rule evaluation to TechniqueEngine.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Optional

from apps.api.domain.dasha import DashaTree
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.prediction_orchestration import (
    ConsensusProfile,
    PARASHARI_STANDARD_PROFILE,
    PredictionSynthesisResult,
    PredictionWindowCandidate,
    PromiseStatus,
    SliceEvaluation,
    TemporalResolution,
    TimeSlice,
)
from apps.api.domain.technique import TriggerStatus
from apps.api.services.adaptive_temporal_scanner import AdaptiveTemporalScanner
from apps.api.services.fact_builder import FactBuilder
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.technique_resolver import TechniqueResolver


class PredictionOrchestrator:
    """Deterministic event prediction orchestrator."""

    def __init__(
        self,
        scanner: Optional[AdaptiveTemporalScanner] = None,
        fact_builder: Optional[FactBuilder] = None,
        resolver: Optional[TechniqueResolver] = None,
        engine: Optional[TechniqueEngine] = None,
    ) -> None:
        self._scanner = scanner or AdaptiveTemporalScanner()
        self._fact_builder = fact_builder or FactBuilder()
        self._resolver = resolver or TechniqueResolver()
        self._engine = engine or TechniqueEngine()

    def predict_event_windows(
        self,
        chart: D1Chart,
        dasha_tree: Optional[DashaTree],
        objective: str,
        target_start: date,
        target_end: date,
        profile: ConsensusProfile = PARASHARI_STANDARD_PROFILE,
        enable_micro_zoom: bool = True,
    ) -> PredictionSynthesisResult:
        """
        Synthesizes deterministic candidate prediction windows for a given life
        event objective over the target date range.
        """
        # 1. Resolve applicable techniques for this objective
        techniques = self._resolver.resolve_by_objective(objective)
        if not techniques:
            # Fallback to all applicable techniques
            sample_facts = self._fact_builder.build_facts(chart)
            techniques = self._resolver.resolve_applicable(sample_facts, objective=objective)

        # 2. Generate Macro Slices
        macro_slices = self._scanner.generate_macro_slices(dasha_tree, target_start, target_end)
        all_evaluations: list[SliceEvaluation] = []

        macro_count = len(macro_slices)
        refined_count = 0

        for m_slice in macro_slices:
            m_eval = self._evaluate_slice(chart, dasha_tree, m_slice, techniques, profile)
            all_evaluations.append(m_eval)

            # 3. Adaptive Zoom: If macro slice crosses activation threshold, refine to meso
            if m_eval.deterministic_score >= profile.minimum_activation_threshold and enable_micro_zoom:
                meso_slices = self._scanner.refine_to_meso_slices(m_slice)
                refined_count += len(meso_slices)

                for meso in meso_slices:
                    meso_eval = self._evaluate_slice(chart, dasha_tree, meso, techniques, profile)
                    all_evaluations.append(meso_eval)

        # 4. Cluster active slices into Prediction Window Candidates
        candidates = self._cluster_into_candidates(objective, all_evaluations, profile)

        # 5. Compute Deterministic Signature
        sig_input = f"{objective}:{target_start}:{target_end}:{profile.profile_id}:{len(candidates)}"
        for c in candidates:
            sig_input += f"|{c.start_date}:{c.end_date}:{c.peak_score}"
        deterministic_hash = hashlib.sha256(sig_input.encode()).hexdigest()[:16]

        summary = (
            f"Prediction synthesis for '{objective}' evaluated {len(all_evaluations)} temporal slices "
            f"({macro_count} macro, {refined_count} refined). Identified {len(candidates)} candidate window(s) "
            f"under profile '{profile.name}'."
        )

        return PredictionSynthesisResult(
            event_type=objective,
            target_start_date=target_start,
            target_end_date=target_end,
            consensus_profile_used=profile,
            candidate_windows=tuple(candidates),
            total_slices_evaluated=len(all_evaluations),
            macro_slices_count=macro_count,
            refined_slices_count=refined_count,
            deterministic_signature=deterministic_hash,
            summary=summary,
        )

    def _evaluate_slice(
        self,
        chart: D1Chart,
        dasha_tree: Optional[DashaTree],
        slice_obj: TimeSlice,
        techniques: list,
        profile: ConsensusProfile,
    ) -> SliceEvaluation:
        """Evaluates all candidate techniques on a point-in-time fact registry."""
        facts = self._fact_builder.build_facts(
            chart=chart,
            transit_datetime_utc=slice_obj.midpoint_datetime_utc,
            dasha_tree=dasha_tree,
        )

        primary_triggers: list[str] = []
        supporting_factors: list[str] = []
        contradicting_factors: list[str] = []
        evidence_trace: list[str] = []
        technique_scores: dict[str, int] = {}

        natal_promise_score = 100
        dasha_score = 0
        transit_score = 0
        has_promise_rule = False

        for tech in techniques:
            res = self._engine.execute(tech, facts)
            technique_scores[tech.technique_id] = res.confidence

            for trigger in res.triggers:
                if trigger.status == TriggerStatus.TRIGGERED:
                    if trigger.role.value == "primary":
                        primary_triggers.append(f"[{tech.technique_id}] {trigger.rule_id}: {trigger.rule_name}")
                        if "PROMISE" in trigger.rule_id or "promise" in trigger.rule_name.lower():
                            has_promise_rule = True
                            natal_promise_score = 100
                        elif "DASH" in trigger.rule_id or "dasha" in trigger.rule_name.lower():
                            dasha_score = max(dasha_score, 100)
                        else:
                            transit_score = max(transit_score, 100)
                    elif trigger.role.value == "supporting":
                        supporting_factors.append(f"[{tech.technique_id}] {trigger.rule_id}: {trigger.rule_name}")
                    elif trigger.role.value in ("contradicting", "cancellation"):
                        contradicting_factors.append(f"[{tech.technique_id}] {trigger.rule_id}: {trigger.rule_name}")

            for ev in res.evidence:
                evidence_trace.append(f"[{tech.technique_id}] {ev}")

        # Check if natal promise was checked but failed
        for tech in techniques:
            for ref in tech.rule_refs:
                if "PROMISE" in ref.rule_id or "promise" in ref.rule_id.lower():
                    # If this promise rule was evaluated but NOT in primary_triggers
                    if not any(ref.rule_id in trig for trig in primary_triggers):
                        natal_promise_score = 0
                        has_promise_rule = True

        promise_status = (
            PromiseStatus.ESTABLISHED
            if natal_promise_score > 0
            else PromiseStatus.ABSENT
            if has_promise_rule
            else PromiseStatus.ESTABLISHED
        )

        # Multi-factor score synthesis
        raw_score = (
            profile.natal_promise_weight * natal_promise_score
            + profile.dasha_weight * dasha_score
            + profile.transit_weight * transit_score
        )

        # Conflict penalty
        if contradicting_factors:
            raw_score -= len(contradicting_factors) * (5.0 * profile.conflict_penalty_multiplier)

        final_score = int(max(0, min(100, round(raw_score))))

        # If Natal Promise is ABSENT, strictly cap score below activation threshold
        if promise_status == PromiseStatus.ABSENT:
            final_score = min(final_score, 30)

        return SliceEvaluation(
            slice=slice_obj,
            deterministic_score=final_score,
            promise_status=promise_status,
            dasha_active=dasha_score > 0,
            gochara_active=transit_score > 0,
            primary_triggers=tuple(primary_triggers),
            supporting_factors=tuple(supporting_factors),
            contradicting_factors=tuple(contradicting_factors),
            evidence_trace=tuple(evidence_trace),
            technique_scores=technique_scores,
        )

    def _cluster_into_candidates(
        self,
        event_type: str,
        evaluations: list[SliceEvaluation],
        profile: ConsensusProfile,
    ) -> list[PredictionWindowCandidate]:
        """Groups contiguous slices exceeding the minimum threshold into candidate windows."""
        # Filter slices that meet or exceed threshold
        active_evals = [e for e in evaluations if e.deterministic_score >= profile.minimum_activation_threshold]
        if not active_evals:
            return []

        # Sort by start date
        active_evals.sort(key=lambda e: e.slice.start_date)

        clusters: list[list[SliceEvaluation]] = []
        cur_cluster: list[SliceEvaluation] = [active_evals[0]]

        for ev in active_evals[1:]:
            prev = cur_cluster[-1]
            # If contiguous or overlapping
            if ev.slice.start_date <= prev.slice.end_date:
                cur_cluster.append(ev)
            else:
                clusters.append(cur_cluster)
                cur_cluster = [ev]
        if cur_cluster:
            clusters.append(cur_cluster)

        candidates: list[PredictionWindowCandidate] = []

        for group in clusters:
            start_date = min(e.slice.start_date for e in group)
            end_date = max(e.slice.end_date for e in group)

            # Find peak slice
            peak_eval = max(group, key=lambda e: e.deterministic_score)
            peak_date = peak_eval.slice.start_date

            all_drivers: set[str] = set()
            all_supp: set[str] = set()
            all_opp: set[str] = set()
            all_ev: set[str] = set()

            for e in group:
                all_drivers.update(e.primary_triggers)
                all_supp.update(e.supporting_factors)
                all_opp.update(e.contradicting_factors)
                all_ev.update(e.evidence_trace)

            c_hash = hashlib.sha256(f"{event_type}:{start_date}:{end_date}:{peak_eval.deterministic_score}".encode()).hexdigest()[:12]

            candidates.append(
                PredictionWindowCandidate(
                    event_type=event_type,
                    start_date=start_date,
                    end_date=end_date,
                    peak_date=peak_date,
                    peak_score=peak_eval.deterministic_score,
                    promise_status=peak_eval.promise_status,
                    primary_drivers=tuple(sorted(all_drivers)),
                    supporting_factors=tuple(sorted(all_supp)),
                    opposing_factors=tuple(sorted(all_opp)),
                    evidence_trace=tuple(sorted(all_ev)),
                    resolution_level=peak_eval.slice.resolution,
                    deterministic_hash=c_hash,
                )
            )

        # Sort candidate windows by peak score descending
        candidates.sort(key=lambda c: c.peak_score, reverse=True)
        return candidates