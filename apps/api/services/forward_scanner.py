"""
Forward Event-Prediction Engine — Scanner Orchestrator (Phase 1)

ForwardScanner composes existing engines (PredictionOrchestrator, FactBuilder,
DashaEngine, TransitEngine, SignatureMatcher) to scan a natal chart for
marriage, job_change, and financial_gain event windows. It returns
ForwardScanResult / ForwardCandidate objects that carry timing windows,
scores, confidence, and honest uncertainty disclosures per RFC §1 and §8.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional, Sequence, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.dasha import DashaTree
from apps.api.domain.prediction_orchestration import (
    PARASHARI_STANDARD_PROFILE,
    ConsensusProfile,
    PredictionWindowCandidate,
)
from apps.api.services.forward_signatures import (
    EventSignatureDef,
    get_signature,
    list_signatures,
)
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
from apps.api.services.rule_engine import _OPERATORS, Condition


def _make_uncertainty_disclosure_global() -> str:
    return (
        "Phase 1 signatures derived from BPHS Ch.19 + classical Phaladeepika; "
        "not validated against a large labeled cohort. Treat as exploratory."
    )


#: Maps Phase-1 signature event_type -> the orchestrator/registry objective
#: vocabulary (which uses 'career', 'wealth', 'property_finance', ... rather
#: than the signature names). Without this mapping PredictEventWindows was
#: called with e.g. 'job_change' and the technique registry returned zero
#: techniques -> zero windows -> the forward scanner could never fire.
_EVENT_TYPE_TO_OBJECTIVE: dict[str, str] = {
    "marriage": "marriage",
    "job_change": "career",
    "financial_gain": "wealth",
    "relocation": "event_timing",
    "health": "event_timing",
    "progeny": "childbirth",
    "property": "property_finance",
}


def _objective_for(event_type: str) -> str:
    return _EVENT_TYPE_TO_OBJECTIVE.get(event_type, event_type)


def _make_uncertainty_disclosure_per_candidate() -> str:
    return (
        "Window bounded by Antardasha transition; peak_score is not a specific "
        "date. Manual verification recommended."
    )


@dataclass(frozen=True)
class ForwardCandidate:
    event_type: str
    signature_id: str
    timing_window_start: date
    timing_window_end: date
    peak_score: int
    confidence: float
    promise_status: str
    primary_drivers: Tuple[str, ...]
    supporting_factors: Tuple[str, ...]
    opposing_factors: Tuple[str, ...]
    classical_source: str
    evidence_fact_keys: Tuple[str, ...]
    uncertainty_disclosure: str


@dataclass(frozen=True)
class ForwardScanResult:
    chart_id: str
    target_start: date
    target_end: date
    event_types_evaluated: Tuple[str, ...]
    candidates: Tuple[ForwardCandidate, ...]
    total_slices_evaluated: int
    deterministic_signature: str
    uncertainty_disclosure: str
    scan_version: str = "forward_v1"


# ----------------------------------------------------------------------
# Private helpers
# ----------------------------------------------------------------------


_V1_SCORE_TO_CONFIDENCE: dict[int, float] = {
    0: 0.0, 10: 0.20, 20: 0.35, 30: 0.45, 40: 0.55, 50: 0.65,
    60: 0.72, 70: 0.78, 80: 0.83, 90: 0.88, 100: 0.92,
}


def _score_to_confidence(peak_score: int) -> float:
    s = max(0, min(100, peak_score))
    if s in _V1_SCORE_TO_CONFIDENCE:
        return _V1_SCORE_TO_CONFIDENCE[s]
    lower_keys = sorted(k for k in _V1_SCORE_TO_CONFIDENCE if k <= s)
    if not lower_keys:
        return 0.0
    k_low = lower_keys[-1]
    k_high = min(kk for kk in _V1_SCORE_TO_CONFIDENCE if kk > k_low)
    low_v = _V1_SCORE_TO_CONFIDENCE[k_low]
    high_v = _V1_SCORE_TO_CONFIDENCE[k_high]
    if k_high == k_low:
        return low_v
    return low_v + (high_v - low_v) * (s - k_low) / (k_high - k_low)


def _candidate_to_fact_dict(cand: PredictionWindowCandidate) -> dict[str, object]:
    fact_dict: dict[str, object] = {}
    for ev in cand.evidence_trace:
        if ev.startswith("["):
            close = ev.find("]")
            if close > 0:
                ev = ev[close + 1 :].lstrip()
        if "=" in ev:
            k, _, v = ev.partition("=")
            k = k.strip()
            v = v.strip()
            if v.lower() in ("true", "false"):
                fact_dict[k] = v.lower() == "true"
            else:
                try:
                    fact_dict[k] = float(v) if "." in v else int(v)
                except ValueError:
                    fact_dict[k] = v
    fact_dict["primary_drivers"] = cand.primary_drivers
    fact_dict["supporting_factors"] = cand.supporting_factors
    fact_dict["opposing_factors"] = cand.opposing_factors
    return fact_dict


def _evaluate_condition(cond: Condition, fact_dict: dict[str, object]) -> bool:
    if cond.fact_key not in fact_dict:
        return False
    value = fact_dict[cond.fact_key]
    if isinstance(value, (tuple, list)):
        op = _OPERATORS.get(cond.operator)
        if op is None:
            return False
        try:
            if op(cond.expected_value, value):
                return True
        except (TypeError, ValueError):
            pass
        return False
    op = _OPERATORS.get(cond.operator)
    if op is None:
        return False
    try:
        return bool(op(value, cond.expected_value))
    except (TypeError, ValueError):
        return False


def _match_signature_against_candidate(
    sig_def: EventSignatureDef, cand: PredictionWindowCandidate
) -> tuple[bool, tuple[str, ...]]:
    fact_dict = _candidate_to_fact_dict(cand)
    matched_keys: list[str] = []
    required_satisfied = True
    for cond in sig_def.required_conditions:
        if cond.fact_key not in fact_dict:
            # Evidence-absent != evidence-false. The orchestrator produced
            # this window only after its DASHA/PROMISE rules fired at/above
            # the activation threshold; a condition whose fact key simply
            # never appears in the evidence trace is UNKNOWN, not a veto.
            # Only an explicit conflicting value vetoes the window.
            continue
        if _evaluate_condition(cond, fact_dict):
            matched_keys.append(cond.fact_key)
        else:
            required_satisfied = False
            break
    if not required_satisfied:
        return False, tuple(matched_keys)
    return True, tuple(matched_keys)


def _build_forward_candidate(
    event_type: str,
    sig_def: EventSignatureDef,
    candidate: PredictionWindowCandidate,
    matched_keys: tuple[str, ...],
    confidence: float,
    promise_status: str,
    primary_drivers: tuple[str, ...],
    supporting_factors: tuple[str, ...],
    opposing_factors: tuple[str, ...],
) -> ForwardCandidate:
    return ForwardCandidate(
        event_type=event_type,
        signature_id=sig_def.signature_id,
        timing_window_start=candidate.start_date,
        timing_window_end=candidate.end_date,
        peak_score=candidate.peak_score,
        confidence=confidence,
        promise_status=promise_status,
        primary_drivers=primary_drivers,
        supporting_factors=supporting_factors,
        opposing_factors=opposing_factors,
        classical_source=sig_def.classical_source,
        evidence_fact_keys=matched_keys,
        uncertainty_disclosure=_make_uncertainty_disclosure_per_candidate(),
    )


class ForwardScanner:
    """Scan a natal chart for Phase 1 event types and return honest results.

    Composed of:
        - PredictionOrchestrator: handles window prediction, fact generation,
          and the macro/meso/micro zoom.
        - SignatureMatcher (via _match_signature_against_candidate): evaluates
          each orchestrator candidate against the Phase 1 EventSignatureDef
          conditions.

    The scanner itself does NOT call DashaEngine or TransitEngine directly.
    """

    def __init__(
        self,
        orchestrator: Optional[PredictionOrchestrator] = None,
        signatures: Optional[Sequence[EventSignatureDef]] = None,
    ):
        self._orchestrator = orchestrator or PredictionOrchestrator()
        self._signatures = list(signatures) if signatures else list(list_signatures())

    def scan(
        self,
        chart: D1Chart,
        dasha_tree: DashaTree,
        event_types: Optional[Sequence[str]] = None,
        target_start: Optional[date] = None,
        target_end: Optional[date] = None,
        profile: ConsensusProfile = PARASHARI_STANDARD_PROFILE,
    ) -> ForwardScanResult:
        if event_types is None:
            event_types = ["marriage", "job_change", "financial_gain", "relocation", "health", "progeny", "property"]
        if target_start is None:
            from datetime import datetime
            target_start = datetime.now().date()
        if target_end is None:
            target_end = date(target_start.year + 1, target_start.month, target_start.day)

        all_candidates: list[ForwardCandidate] = []
        event_types_evaluated: list[str] = []

        valid_events = {"marriage", "job_change", "financial_gain", "relocation", "health", "progeny", "property"}
        for event_type in event_types:
            if event_type not in valid_events:
                continue
            event_types_evaluated.append(event_type)

            orchestrator_windows = self._orchestrator.predict_event_windows(
                chart, dasha_tree, _objective_for(event_type),  # registry vocab
                target_start, target_end, profile,
            )

            try:
                sig_def = get_signature(event_type)
            except KeyError:
                sig_def = None

            cands = (
                orchestrator_windows.candidate_windows
                if hasattr(orchestrator_windows, "candidate_windows")
                else orchestrator_windows
            )
            for cand in cands:
                if sig_def is None:
                    continue
                matched, matched_keys = _match_signature_against_candidate(sig_def, cand)
                if not matched:
                    continue
                candidate = _build_forward_candidate(
                    event_type=event_type,
                    sig_def=sig_def,
                    candidate=cand,
                    matched_keys=matched_keys,
                    confidence=_score_to_confidence(cand.peak_score),
                    promise_status=cand.promise_status,
                    primary_drivers=cand.primary_drivers,
                    supporting_factors=cand.supporting_factors,
                    opposing_factors=cand.opposing_factors,
                )
                all_candidates.append(candidate)

        all_candidates.sort(key=lambda c: (-c.confidence, -c.peak_score))

        return ForwardScanResult(
            chart_id=getattr(chart, "chart_id", "default_chart"),
            target_start=target_start,
            target_end=target_end,
            event_types_evaluated=tuple(event_types_evaluated),
            candidates=tuple(all_candidates),
            total_slices_evaluated=len(all_candidates),
            deterministic_signature=self._deterministic_signature(tuple(all_candidates)),
            uncertainty_disclosure=_make_uncertainty_disclosure_global(),
        )

    @staticmethod
    def _deterministic_signature(candidates: tuple[ForwardCandidate, ...]) -> str:
        sorted_cands = sorted(candidates, key=lambda c: (c.event_type, c.signature_id, c.timing_window_start))
        parts: list[str] = []
        for c in sorted_cands:
            ev_str = ",".join(sorted(c.evidence_fact_keys))
            parts.append(
                f"{c.event_type}|{c.signature_id}|{c.timing_window_start}|"
                f"{c.timing_window_end}|{c.peak_score}|{c.confidence:.4f}|{ev_str}"
            )
        return "|".join(parts)


def quick_scan(
    chart: D1Chart,
    dasha_tree: DashaTree,
    event_types: Optional[Sequence[str]] = None,
    target_start: Optional[date] = None,
    target_end: Optional[date] = None,
) -> ForwardScanResult:
    scanner = ForwardScanner()
    return scanner.scan(
        chart=chart, dasha_tree=dasha_tree,
        event_types=event_types, target_start=target_start, target_end=target_end,
    )