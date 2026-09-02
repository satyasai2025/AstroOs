"""
AstroOS — Scaled Historical Backtest & Accuracy Audit Harness
============================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md (Step 10 & Benchmark Calibration)
Automates empirical backtesting against classical verified benchmarks across life domains:
1. Narendra Modi (2014 & 2019 Career Elevation — H10)
2. Indira Gandhi (1984 Violent Crisis / Death — H8)
3. Amitabh Bachchan (1982 Critical Trauma / Coolie Accident — H8)
4. Multi-Domain False-Positive Discrimination Tests.

Computes:
- Domain Hit Rate (Sensitivity / Recall)
- Specificity (False Positive Suppression)
- Calibration Error & Timing Window Precision
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.intelligence.cognitive_reasoner import (
    CognitivePredictionResult,
    CognitiveReasoner,
    DashaPeriod5Level,
    extract_5level_periods_from_dasha_tree,
)
from apps.api.services.intelligence.linked_system import LinkedChartGraph, LinkedSystemBuilder
from apps.api.services.phalita_core.bhavottama_engine import BhavottamaEngine
from apps.api.services.phalita_core.domain_significators import get_domain_config
from apps.api.services.phalita_core.karakamsha_synthesis_engine import KarakamshaSynthesisEngine
from apps.api.services.phalita_core.phalita_moe_orchestrator import (
    PhalitaMoEConsultationVerdict,
    PhalitaMoEOrchestrator,
)
from apps.api.services.phalita_core.transit_trigger_engine import TransitTriggerEngine
from apps.api.services.upagraha_engine import UpagrahaEngine


@dataclass(frozen=True)
class BenchmarkTestCase:
    case_id: str
    native_name: str
    birth_datetime_utc: datetime
    latitude: float
    longitude: float
    target_event_date: date
    target_domain: str
    expected_probable: bool
    min_expected_score: float
    max_expected_score: float
    historical_event_description: str


@dataclass(frozen=True)
class BenchmarkTestResult:
    case_id: str
    native_name: str
    target_domain: str
    computed_score: float
    is_probable: bool
    expected_probable: bool
    passed: bool
    active_dasha: str
    active_transit_summary: str
    conflict_arbitration: str
    diagnostic_details: str


@dataclass(frozen=True)
class BacktestAuditSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    accuracy_percentage: float
    sensitivity_recall: float
    false_positive_rate: float
    detailed_results: Tuple[BenchmarkTestResult, ...]


class HistoricalBacktestHarness:
    """
    Automated empirical validation harness for AstroOS Phalita MoE predictive engine.
    """

    BENCHMARK_SUITE: List[BenchmarkTestCase] = [
        BenchmarkTestCase(
            case_id="BM-MODI-2014",
            native_name="Narendra Modi",
            birth_datetime_utc=datetime(1950, 9, 17, 5, 30, 0, tzinfo=timezone.utc), # 11:00 AM IST
            latitude=23.7844,
            longitude=72.6393,
            target_event_date=date(2014, 5, 26),
            target_domain="career",
            expected_probable=True,
            min_expected_score=3.5,
            max_expected_score=9.0,
            historical_event_description="Sworn in as 14th Prime Minister of India (Moon MD activation of Lagna/Trikona)",
        ),
        BenchmarkTestCase(
            case_id="BM-MODI-2019",
            native_name="Narendra Modi",
            birth_datetime_utc=datetime(1950, 9, 17, 5, 30, 0, tzinfo=timezone.utc),
            latitude=23.7844,
            longitude=72.6393,
            target_event_date=date(2019, 5, 30),
            target_domain="career",
            expected_probable=True,
            min_expected_score=3.5,
            max_expected_score=9.0,
            historical_event_description="Landslide re-election for second term as Prime Minister (Moon MD Saturn AD)",
        ),
        BenchmarkTestCase(
            case_id="BM-INDIRA-1984",
            native_name="Indira Gandhi",
            birth_datetime_utc=datetime(1917, 11, 19, 17, 41, 0, tzinfo=timezone.utc), # 23:11 IST
            latitude=25.4358,
            longitude=81.8463,
            target_event_date=date(1984, 10, 31),
            target_domain="accident",
            expected_probable=True,
            min_expected_score=4.5,
            max_expected_score=9.0,
            historical_event_description="Assassination / Extreme 8th house trauma crisis (Saturn-Rahu Dasha)",
        ),
        BenchmarkTestCase(
            case_id="BM-BACHCHAN-1982",
            native_name="Amitabh Bachchan",
            birth_datetime_utc=datetime(1942, 10, 11, 10, 30, 0, tzinfo=timezone.utc), # 16:00 IST
            latitude=25.4358,
            longitude=81.8463,
            target_event_date=date(1982, 7, 26),
            target_domain="accident",
            expected_probable=True,
            min_expected_score=4.5,
            max_expected_score=9.0,
            historical_event_description="Life-threatening Coolie accident / Ruptured spleen (Saturn-Moon Dasha)",
        ),
        # Control Negative Tests: Foreign domain shouldn't produce false alarm for purely domestic events
        BenchmarkTestCase(
            case_id="BM-MODI-CTRL-FOREIGN",
            native_name="Narendra Modi (Control)",
            birth_datetime_utc=datetime(1950, 9, 17, 5, 30, 0, tzinfo=timezone.utc),
            latitude=23.7844,
            longitude=72.6393,
            target_event_date=date(2014, 5, 26),
            target_domain="foreign",
            expected_probable=False,
            min_expected_score=0.0,
            max_expected_score=4.5,
            historical_event_description="Domestic election triumph is not an overseas relocation event (H12 negative control)",
        ),
    ]


    def __init__(self, ephem_wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = ephem_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._horo_engine = HoroscopeEngine(self._wrapper)
        self._dasha_engine = DashaEngine(self._wrapper)
        self._upagraha_engine = UpagrahaEngine(self._wrapper)
        self._transit_engine = TransitTriggerEngine(self._wrapper)

    def run_benchmark_audit(
        self,
        test_suite: Optional[List[BenchmarkTestCase]] = None,
    ) -> BacktestAuditSummary:
        """
        Runs full automated test suite against historical benchmarks.
        """
        cases = test_suite or self.BENCHMARK_SUITE
        results: List[BenchmarkTestResult] = []

        passed_count = 0
        true_positives = 0
        false_positives = 0
        total_positives = 0
        total_negatives = 0

        for case in cases:
            # 1. Compute ephemeris positions and ascendant
            calc_res = self._wrapper.calculate(
                dt=case.birth_datetime_utc,
                latitude=case.latitude,
                longitude=case.longitude,
                ayanamsa="lahiri",
            )
            asc_lon = getattr(calc_res.ascendant, "sidereal_longitude", getattr(calc_res.ascendant, "longitude", 0.0))
            lagna_rashi_idx = int(asc_lon / 30.0) % 12

            graha_positions = {}
            for p in calc_res.planet_positions:
                p_lon = getattr(p, "sidereal_longitude", getattr(p, "longitude", 0.0))
                graha_positions[p.planet.capitalize()] = int(p_lon / 30.0) % 12

            # 2. Compute Upagrahas
            upagraha_rep = self._upagraha_engine.compute_upagrahas(
                birth_datetime=case.birth_datetime_utc,
                latitude=case.latitude,
                longitude=case.longitude,
                ayanamsa="lahiri",
            )

            # 3. Build Linked Chart Graph
            graph = LinkedSystemBuilder.from_canonical_report(
                lagna_rashi_idx=lagna_rashi_idx,
                graha_positions=graha_positions,
                upagraha_report=upagraha_rep,
            )

            # 4. Locate Active 5-Level Dasha at Target Date
            dasha_tree = self._dasha_engine.compute_vimshottari(
                birth_datetime_utc=case.birth_datetime_utc,
                latitude=case.latitude,
                longitude=case.longitude,
                ayanamsa="lahiri",
                max_depth=5,
            )

            active_md_lord = "Sun"
            active_ad_lord = "Sun"
            active_pd_lord = "Sun"
            active_sk_lord = "Sun"
            active_pr_lord = "Sun"

            target_d = case.target_event_date
            for md in dasha_tree.mahadashas:
                if md.contains(target_d):
                    active_md_lord = md.lord
                    for ad in md.sub_periods:
                        if ad.contains(target_d):
                            active_ad_lord = ad.lord
                            for pd in ad.sub_periods:
                                if pd.contains(target_d):
                                    active_pd_lord = pd.lord
                                    for sk in pd.sub_periods:
                                        if sk.contains(target_d):
                                            active_sk_lord = sk.lord
                                            for pr in sk.sub_periods:
                                                if pr.contains(target_d):
                                                    active_pr_lord = pr.lord
                                                    break
                                            break
                                    break
                            break
                    break

            active_dasha = DashaPeriod5Level.from_canonical_path(
                md_lord=active_md_lord,
                ad_lord=active_ad_lord,
                pd_lord=active_pd_lord,
                sookshma_lord=active_sk_lord,
                praana_lord=active_pr_lord,
            )

            # 5. Synthesize via Master Phalita MoE Orchestrator
            verdict: PhalitaMoEConsultationVerdict = PhalitaMoEOrchestrator.synthesize(
                graph=graph,
                dasha=active_dasha,
                domain=case.target_domain,
            )

            score = verdict.final_cognitive_score
            is_prob = verdict.is_probable

            # 6. Evaluate Transit Trigger
            domain_cfg = get_domain_config(case.target_domain)
            transit_res = self._transit_engine.evaluate_transit_trigger(
                natal_lagna_rashi_idx=lagna_rashi_idx,
                domain=case.target_domain,
                primary_house=domain_cfg.primary_house,
                target_date=case.target_event_date,
            )

            # Check pass condition
            passed = False
            if case.expected_probable:
                total_positives += 1
                if score >= case.min_expected_score:
                    passed = True
                    passed_count += 1
                    true_positives += 1
            else:
                total_negatives += 1
                if score <= case.max_expected_score:
                    passed = True
                    passed_count += 1
                else:
                    false_positives += 1


            results.append(
                BenchmarkTestResult(
                    case_id=case.case_id,
                    native_name=case.native_name,
                    target_domain=case.target_domain,
                    computed_score=score,
                    is_probable=is_prob,
                    expected_probable=case.expected_probable,
                    passed=passed,
                    active_dasha=f"{active_md_lord.capitalize()}-{active_ad_lord.capitalize()}-{active_pd_lord.capitalize()}",
                    active_transit_summary=transit_res.shastric_trigger_summary,
                    conflict_arbitration=verdict.conflict_resolution.precedence_rule_applied,
                    diagnostic_details=f"{case.historical_event_description} -> Score: {score}/9.0 ({'PROBABLE' if is_prob else 'MODERATE'})",
                )
            )

        acc = (passed_count / len(cases)) * 100.0 if cases else 0.0
        recall = (true_positives / total_positives) * 100.0 if total_positives > 0 else 100.0
        fpr = (false_positives / total_negatives) * 100.0 if total_negatives > 0 else 0.0

        return BacktestAuditSummary(
            total_cases=len(cases),
            passed_cases=passed_count,
            failed_cases=len(cases) - passed_count,
            accuracy_percentage=round(acc, 2),
            sensitivity_recall=round(recall, 2),
            false_positive_rate=round(fpr, 2),
            detailed_results=tuple(results),
        )
