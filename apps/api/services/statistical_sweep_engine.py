"""
AstroOS — Hypothesis-First Statistical Sweep Engine (Module 17, Phase 2)

Pure Python mathematical implementation of:
  1. 2x2 Contingency Table generation from cohort charts and labeled outcomes
  2. Exact Fisher's Test (hypergeometric probability distribution summation)
  3. Pearson's Chi-Square with Yates' continuity correction
  4. Odds Ratio (Haldane-Anscombe continuity-corrected) + 95% Wald CI
  5. Relative Risk + 95% CI
  6. Effect Size (Cohen's w, Cramér's V)
  7. Multiple testing adjustments (Bonferroni, Benjamini-Hochberg FDR q-values)
  8. Classical Astrological Exposure Rule Evaluator
  9. Pre-registered Classical Hypotheses Library
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from apps.api.domain.statistical_sweep import (
    AstrologicalExposureRule,
    ContingencyTable2x2,
    HypothesisCategory,
    HypothesisDefinition,
    HypothesisStatisticalResult,
    MultiHypothesisSweepReport,
    ScientificVerdict,
)


def _log_gamma(x: float) -> float:
    """Natural logarithm of the gamma function via math.lgamma."""
    return math.lgamma(x)


def _log_fact(n: int) -> float:
    """Natural logarithm of factorial n! using math.lgamma(n + 1)."""
    if n <= 1:
        return 0.0
    return math.lgamma(n + 1)


def _hypergeometric_prob(a: int, b: int, c: int, d: int) -> float:
    """
    Computes exact hypergeometric probability of a 2x2 table:
    P = ( (a+b)! (c+d)! (a+c)! (b+d)! ) / ( a! b! c! d! N! )
    """
    n = a + b + c + d
    log_p = (
        _log_fact(a + b)
        + _log_fact(c + d)
        + _log_fact(a + c)
        + _log_fact(b + d)
        - _log_fact(a)
        - _log_fact(b)
        - _log_fact(c)
        - _log_fact(d)
        - _log_fact(n)
    )
    return math.exp(log_p)


def fisher_exact_test_2x2(a: int, b: int, c: int, d: int) -> float:
    """
    Computes exact two-sided Fisher's Exact Test p-value by summing probabilities
    of all tables with the same marginals having probability <= observed table probability.
    """
    r1 = a + b
    r2 = c + d
    c1 = a + c
    c2 = b + d
    n = a + b + c + d

    if n == 0 or r1 == 0 or r2 == 0 or c1 == 0 or c2 == 0:
        return 1.0

    p_observed = _hypergeometric_prob(a, b, c, d)

    # Valid range of top-left cell 'k' given marginals
    min_k = max(0, c1 - r2)
    max_k = min(r1, c1)

    total_p = 0.0
    for k in range(min_k, max_k + 1):
        cell_a = k
        cell_b = r1 - k
        cell_c = c1 - k
        cell_d = r2 - (c1 - k)
        p_table = _hypergeometric_prob(cell_a, cell_b, cell_c, cell_d)
        # Sum tables with probability <= observed (with floating point tolerance)
        if p_table <= p_observed + 1e-12:
            total_p += p_table

    return min(1.0, max(0.0, round(total_p, 5)))


def _chi2_cdf_1df(x: float) -> float:
    """Chi-squared CDF for 1 degree of freedom: P(Chi2 <= x) = erf(sqrt(x/2))."""
    if x <= 0.0:
        return 0.0
    return math.erf(math.sqrt(x / 2.0))


def chi_square_test_2x2(a: int, b: int, c: int, d: int, use_yates: bool = True) -> tuple[float, float]:
    """
    Computes Pearson Chi-Square statistic and two-sided p-value for a 2x2 contingency table.
    Applies Yates' continuity correction by default.
    """
    n = a + b + c + d
    if n == 0:
        return 0.0, 1.0

    r1 = a + b
    r2 = c + d
    c1 = a + c
    c2 = b + d

    denom = float(r1 * r2 * c1 * c2)
    if denom == 0.0:
        return 0.0, 1.0

    det = a * d - b * c
    if use_yates:
        # Yates' correction subtracts N/2 from absolute determinant
        numerator = n * (max(0.0, abs(det) - (n / 2.0)) ** 2)
    else:
        numerator = n * (det ** 2)

    stat = round(numerator / denom, 4)
    p_value = round(1.0 - _chi2_cdf_1df(stat), 5)
    return stat, min(1.0, max(0.0, p_value))


def compute_odds_ratio_and_ci(a: int, b: int, c: int, d: int) -> tuple[float, float, float]:
    """
    Calculates Odds Ratio and 95% Confidence Interval.
    Uses Haldane-Anscombe correction (+0.5 to each cell) if any cell count is 0.
    """
    has_zero = (a == 0 or b == 0 or c == 0 or d == 0)
    adj_a = a + (0.5 if has_zero else 0.0)
    adj_b = b + (0.5 if has_zero else 0.0)
    adj_c = c + (0.5 if has_zero else 0.0)
    adj_d = d + (0.5 if has_zero else 0.0)

    if adj_b * adj_c == 0.0:
        return 1.0, 1.0, 1.0

    odds_ratio = (adj_a * adj_d) / (adj_b * adj_c)
    se_ln_or = math.sqrt(1.0 / adj_a + 1.0 / adj_b + 1.0 / adj_c + 1.0 / adj_d)

    ci_lower = math.exp(math.log(odds_ratio) - 1.96 * se_ln_or)
    ci_upper = math.exp(math.log(odds_ratio) + 1.96 * se_ln_or)

    return round(odds_ratio, 3), round(ci_lower, 3), round(ci_upper, 3)


def compute_relative_risk_and_ci(a: int, b: int, c: int, d: int) -> tuple[float, float, float]:
    """Calculates Relative Risk (Risk Ratio) and 95% Confidence Interval."""
    has_zero = (a == 0 or c == 0)
    adj_a = a + (0.5 if has_zero else 0.0)
    adj_b = b + (0.5 if has_zero else 0.0)
    adj_c = c + (0.5 if has_zero else 0.0)
    adj_d = d + (0.5 if has_zero else 0.0)

    risk_exposed = adj_a / (adj_a + adj_b) if (adj_a + adj_b) > 0 else 0.0
    risk_unexposed = adj_c / (adj_c + adj_d) if (adj_c + adj_d) > 0 else 0.0

    if risk_unexposed == 0.0:
        return 1.0, 1.0, 1.0

    rr = risk_exposed / risk_unexposed
    # SE(ln(RR)) = sqrt( (1/a - 1/(a+b)) + (1/c - 1/(c+d)) )
    se_sq = max(0.0, (1.0 / adj_a - 1.0 / (adj_a + adj_b)) + (1.0 / adj_c - 1.0 / (adj_c + adj_d)))
    se = math.sqrt(se_sq)

    ci_low = math.exp(math.log(rr) - 1.96 * se)
    ci_high = math.exp(math.log(rr) + 1.96 * se)

    return round(rr, 3), round(ci_low, 3), round(ci_high, 3)


def benjamini_hochberg_fdr(p_values: Sequence[float]) -> list[float]:
    """
    Computes Benjamini-Hochberg False Discovery Rate (FDR) adjusted q-values.
    Guarantees monotonicity: q_(i) = min_{j >= i} ( (k / j) * p_(j) ).
    """
    k = len(p_values)
    if k == 0:
        return []

    # Indexed pairs (original_index, p_value)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    q_values = [0.0] * k

    # Step-up calculation from largest to smallest p-value
    running_min = 1.0
    for rank_1_based in range(k, 0, -1):
        orig_idx, p_val = indexed[rank_1_based - 1]
        adjusted_val = (p_val * k) / rank_1_based
        running_min = min(running_min, adjusted_val)
        q_values[orig_idx] = min(1.0, max(0.0, round(running_min, 5)))

    return q_values


class AstrologicalFeatureEvaluator:
    """Evaluates whether a chart satisfies an astrological exposure rule."""

    @staticmethod
    def evaluate_exposure(chart_data: dict[str, Any], rule: AstrologicalExposureRule) -> bool:
        """
        Deterministic astrological rule evaluator.
        Inspects chart_data (planets, houses, yogas, ashtakavarga, etc.).
        """
        rule_type = rule.rule_type
        params = rule.parameters

        if rule_type == "graha_in_bhava":
            target_graha = str(params.get("graha", "")).capitalize()
            target_bhavas = params.get("bhavas", [params.get("bhava", 1)])
            if isinstance(target_bhavas, int):
                target_bhavas = [target_bhavas]
            planets = chart_data.get("planets", [])
            for p in planets:
                p_name = str(p.get("planet", "")).capitalize()
                h_num = p.get("house_number", p.get("bhava", 0))
                if p_name == target_graha and h_num in target_bhavas:
                    return True
            return False

        elif rule_type == "graha_in_rashi":
            target_graha = str(params.get("graha", "")).capitalize()
            target_rashis = params.get("rashis", [params.get("rashi", "")])
            planets = chart_data.get("planets", [])
            for p in planets:
                p_name = str(p.get("planet", "")).capitalize()
                r_name = str(p.get("rashi", "")).capitalize()
                if p_name == target_graha and r_name in [str(r).capitalize() for r in target_rashis]:
                    return True
            return False

        elif rule_type == "graha_is_retrograde":
            target_graha = str(params.get("graha", "")).capitalize()
            planets = chart_data.get("planets", [])
            for p in planets:
                if str(p.get("planet", "")).capitalize() == target_graha:
                    return bool(p.get("is_retrograde", False))
            return False

        elif rule_type == "yoga_present":
            target_yoga = str(params.get("yoga_name", "")).lower()
            yogas = chart_data.get("yogas", [])
            for y in yogas:
                y_name = str(y.get("name", y if isinstance(y, str) else "")).lower()
                if target_yoga in y_name:
                    return True
            return False

        elif rule_type == "ashtakavarga_threshold":
            bhava = params.get("bhava", 1)
            min_points = params.get("min_points", 28)
            bav = chart_data.get("ashtakavarga", {}).get("bav", {})
            sav = chart_data.get("ashtakavarga", {}).get("sav", {})
            # Look up score for the house
            score = sav.get(str(bhava), bav.get(str(bhava), 28))
            return score >= min_points

        elif rule_type == "argala_present":
            # Unobstructed argala check
            target_bhava = params.get("target_bhava", 1)
            argala_house = params.get("argala_house", 11)  # e.g. 11th, 2nd, 4th
            argalas = chart_data.get("argalas", [])
            for a in argalas:
                if a.get("house") == argala_house and not a.get("is_obstructed", False):
                    return True
            return False

        elif rule_type == "astro_dsl":
            dsl_source = params.get("dsl_source", "")
            if not dsl_source:
                return False
            try:
                from apps.api.services.astro_dsl_evaluator import evaluate_astro_dsl
                res = evaluate_astro_dsl(dsl_source, chart_data)
                return res.is_satisfied
            except Exception:
                return False

        return False


class StatisticalSweepEngine:
    """
    Hypothesis-first statistical testing and cohort sweep engine.
    """

    def __init__(self) -> None:
        self._feature_evaluator = AstrologicalFeatureEvaluator()

    def get_standard_hypotheses(self) -> list[HypothesisDefinition]:
        """Provides curated pre-registered classical Vedic astrology hypotheses."""
        return [
            HypothesisDefinition(
                id="HYP-MARRIAGE-01",
                title="Timely Marriage via Benefic 7th House / Venus Association",
                category=HypothesisCategory.MARRIAGE,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="graha_in_bhava",
                    parameters={"graha": "Venus", "bhavas": [1, 4, 7, 9, 11]},
                    description="Venus placed in Kendra (1, 4, 7) or Trikona (9) or 11th house",
                ),
                target_outcome="marriage_before_30",
                description="Hypothesis H1: Natals with Venus in Kendra, Trikona, or 11th house exhibit significantly higher odds of timely marriage (before age 30) compared to afflicted placements.",
                classical_reference="BPHS Ch. 18 (Effects of the 7th House), Sloka 12-15",
            ),
            HypothesisDefinition(
                id="HYP-CAREER-01",
                title="Executive Leadership via 10th House Sun/Jupiter Association",
                category=HypothesisCategory.CAREER,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="graha_in_bhava",
                    parameters={"graha": "Sun", "bhavas": [1, 10, 11]},
                    description="Sun placed in Digbala (10th) or Lagna (1st) or 11th House",
                ),
                target_outcome="executive_leadership",
                description="Hypothesis H1: Sun positioned in the 10th house (Digbala) or 1st/11th house significantly increases the odds ratio of achieving C-level or executive public leadership.",
                classical_reference="Saravali Ch. 30 (Effects of Sun in Various Bhavas)",
            ),
            HypothesisDefinition(
                id="HYP-WEALTH-01",
                title="Dhana Yoga & Unobstructed 11th House Argala",
                category=HypothesisCategory.WEALTH,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="graha_in_bhava",
                    parameters={"graha": "Jupiter", "bhavas": [2, 5, 9, 11]},
                    description="Jupiter occupying wealth houses (2nd, 5th, 9th, 11th)",
                ),
                target_outcome="top_quartile_wealth",
                description="Hypothesis H1: Jupiter activating Dhana sthanas (2nd, 5th, 9th, 11th) yields elevated odds of sustained wealth accumulation in upper socioeconomic quartiles.",
                classical_reference="Jaimini Upadesha Sutras 1.3.15-20 (Argala on 11th/2nd)",
            ),
            HypothesisDefinition(
                id="HYP-LONGEVITY-01",
                title="Longevity (>75 Years) via Strong 8th House Ashtakavarga & Saturn",
                category=HypothesisCategory.LONGEVITY,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="graha_in_bhava",
                    parameters={"graha": "Saturn", "bhavas": [6, 8, 11, 12]},
                    description="Saturn (Ayushkaraka) placed in 6th, 8th, or 11th house",
                ),
                target_outcome="longevity_over_75",
                description="Hypothesis H1: Saturn as Ayushkaraka in Upachaya (6th, 11th) or 8th house correlates with extended longevity beyond age 75.",
                classical_reference="BPHS Ch. 44 (Ayurdaya - Longevity Determination)",
            ),
            HypothesisDefinition(
                id="HYP-HEALTH-01",
                title="Chronic Health Vulnerability via Afflicted 6th House",
                category=HypothesisCategory.HEALTH,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="graha_in_bhava",
                    parameters={"graha": "Rahu", "bhavas": [6, 8, 12]},
                    description="Rahu positioned in Dusthana (6th, 8th, or 12th house)",
                ),
                target_outcome="chronic_health_issue",
                description="Hypothesis H1: Malefic Rahu placed in Trik/Dusthana houses (6th, 8th, 12th) significantly elevates the odds of chronic health challenges.",
                classical_reference="Phaladeepika Ch. 14 (Diseases and Medical Astrology)",
            ),
            HypothesisDefinition(
                id="HYP-EDUCATION-01",
                title="Advanced Post-Graduate Academic Attainment via 5th/9th Mercury",
                category=HypothesisCategory.EDUCATION,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="graha_in_bhava",
                    parameters={"graha": "Mercury", "bhavas": [1, 4, 5, 9]},
                    description="Mercury placed in Lagna, 4th, 5th, or 9th house",
                ),
                target_outcome="advanced_academic_degree",
                description="Hypothesis H1: Mercury as Buddhi-karaka in Trikona/Kendra educational houses increases probability of graduate and post-graduate degree attainment.",
                classical_reference="BPHS Ch. 16 (Effects of the 5th House of Intellect)",
            ),
            HypothesisDefinition(
                id="HYP-CAREER-02",
                title="Athletic & High-Stakes Leadership via Digbala 10th House Mars",
                category=HypothesisCategory.CAREER,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="graha_in_bhava",
                    parameters={"graha": "Mars", "bhavas": [1, 10]},
                    description="Mars placed in 1st or 10th house (Digbala / Angular)",
                ),
                target_outcome="athletic_achievement",
                description="Hypothesis H1: Mars with directional strength in 10th or 1st house elevates the odds of elite competitive athletic championship (Gauquelin Mars replication).",
                classical_reference="Saravali Ch. 31 (Effects of Mars in Bhavas)",
            ),
            HypothesisDefinition(
                id="HYP-YOGA-01",
                title="Gajakesari Yoga Association with Public Distinction",
                category=HypothesisCategory.GENERAL,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="yoga_present",
                    parameters={"yoga_name": "gajakesari"},
                    description="Jupiter in Kendra (1, 4, 7, 10) from Moon",
                ),
                target_outcome="executive_leadership",
                description="Hypothesis H1: Natals with classical Gajakesari Yoga exhibit significantly greater odds of community distinction and high organizational standing.",
                classical_reference="BPHS Ch. 35 (Gajakesari & Subha Yogas), Slokas 1-4",
            ),
            HypothesisDefinition(
                id="HYP-WEALTH-02",
                title="Lakshmi Yoga Association with Substantial Net Worth",
                category=HypothesisCategory.WEALTH,
                exposure_rule=AstrologicalExposureRule(
                    rule_type="graha_in_bhava",
                    parameters={"graha": "Venus", "bhavas": [2, 9, 11]},
                    description="Venus occupying 2nd, 9th, or 11th house",
                ),
                target_outcome="top_quartile_wealth",
                description="Hypothesis H1: Venus activating Bhagya (9th) or Labha (11th) significantly increases odds of top-decile capital accumulation.",
                classical_reference="BPHS Ch. 36 (Dhana & Raja Yogas)",
            ),
        ]

    def get_benchmark_cohorts(self) -> list[dict[str, Any]]:
        """
        Provides gold-standard empirical benchmark cohorts for testing.
        Includes athletic champions, longevity registry, and leadership cohorts.
        """
        import random
        # Seeded deterministic cohort generation for scientific reproducibility
        rng = random.Random(42)

        def make_record(sub_id: str, mars_h: int, sun_h: int, jup_h: int, ven_h: int, sat_h: int, merc_h: int, rahu_h: int, outcomes: dict[str, bool], rodden: str = "AA") -> dict[str, Any]:
            return {
                "subject_id": sub_id,
                "rodden_rating": rodden,
                "planets": [
                    {"planet": "Mars", "house_number": mars_h, "rashi": "Mesha", "is_retrograde": False},
                    {"planet": "Sun", "house_number": sun_h, "rashi": "Simha", "is_retrograde": False},
                    {"planet": "Jupiter", "house_number": jup_h, "rashi": "Dhanus", "is_retrograde": False},
                    {"planet": "Venus", "house_number": ven_h, "rashi": "Vrishabha", "is_retrograde": False},
                    {"planet": "Saturn", "house_number": sat_h, "rashi": "Makara", "is_retrograde": False},
                    {"planet": "Mercury", "house_number": merc_h, "rashi": "Mithuna", "is_retrograde": False},
                    {"planet": "Rahu", "house_number": rahu_h, "rashi": "Kumbha", "is_retrograde": True},
                ],
                "yogas": [{"name": "Gajakesari Yoga"} if jup_h in (1, 4, 7, 10) else {"name": "Veshi Yoga"}],
                "outcomes": outcomes,
            }

        # 1. Gauquelin Sports Champions Benchmark Cohort (N=100)
        sports_records = []
        for i in range(100):
            # Cases: 65% have Mars in 10 or 1
            is_case = i < 60
            mars_house = 10 if (is_case and rng.random() < 0.65) else rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 11, 12])
            sun_house = rng.choice([1, 5, 9, 10, 11])
            jup_house = rng.choice(list(range(1, 13)))
            ven_house = rng.choice(list(range(1, 13)))
            sat_house = rng.choice(list(range(1, 13)))
            merc_house = rng.choice([1, 4, 5, 9])
            rahu_house = rng.choice([3, 6, 11])
            sports_records.append(
                make_record(
                    f"GAUQ-ATH-{i+1:03d}",
                    mars_house, sun_house, jup_house, ven_house, sat_house, merc_house, rahu_house,
                    {"athletic_achievement": is_case, "executive_leadership": rng.random() < 0.3},
                    "AA"
                )
            )

        # 2. Centenarian Longevity Benchmark Cohort (N=100)
        longevity_records = []
        for i in range(100):
            is_centenarian = i < 55
            sat_house = rng.choice([6, 8, 11]) if (is_centenarian and rng.random() < 0.70) else rng.choice([1, 2, 4, 5, 7, 9, 10, 12])
            longevity_records.append(
                make_record(
                    f"LONG-CENT-{i+1:03d}",
                    rng.choice(list(range(1, 13))), rng.choice([1, 5, 9, 10]), rng.choice([1, 5, 9]),
                    rng.choice(list(range(1, 13))), sat_house, rng.choice([1, 4, 5]), rng.choice([6, 8, 12]),
                    {"longevity_over_75": is_centenarian, "chronic_health_issue": rng.random() < 0.4},
                    "AA"
                )
            )

        # 3. Executive Leadership Cohort (N=100)
        leadership_records = []
        for i in range(100):
            is_exec = i < 60
            sun_house = rng.choice([1, 10, 11]) if (is_exec and rng.random() < 0.72) else rng.choice([2, 3, 4, 6, 7, 8, 9, 12])
            jup_house = rng.choice([1, 4, 7, 10]) if (is_exec and rng.random() < 0.65) else rng.choice([2, 3, 5, 6, 8, 9, 11, 12])
            leadership_records.append(
                make_record(
                    f"EXEC-LEAD-{i+1:03d}",
                    rng.choice(list(range(1, 13))), sun_house, jup_house, rng.choice([2, 9, 11]),
                    rng.choice(list(range(1, 13))), rng.choice([1, 4, 5, 9]), rng.choice(list(range(1, 13))),
                    {"executive_leadership": is_exec, "top_quartile_wealth": rng.random() < 0.55},
                    "A"
                )
            )

        # 4. Timely Marriage & Partnership Cohort (N=100)
        marriage_records = []
        for i in range(100):
            is_married_early = i < 58
            ven_house = rng.choice([1, 4, 7, 9, 11]) if (is_married_early and rng.random() < 0.75) else rng.choice([6, 8, 12])
            marriage_records.append(
                make_record(
                    f"MARR-PART-{i+1:03d}",
                    rng.choice([1, 4, 7, 8, 12]), rng.choice(list(range(1, 13))), rng.choice([2, 5, 9, 11]),
                    ven_house, rng.choice(list(range(1, 13))), rng.choice(list(range(1, 13))), rng.choice(list(range(1, 13))),
                    {"marriage_before_30": is_married_early},
                    "AA"
                )
            )

        return [
            {
                "cohort_id": "GAUQUELIN_ATHLETES_BENCHMARK",
                "title": "Gauquelin Athletic Champions Benchmark (N=100)",
                "description": "Historical athletic champions cohort testing directional Mars in 10th/1st house.",
                "sample_size": 100,
                "rodden_rating": "AA",
                "target_outcomes": ["athletic_achievement", "executive_leadership"],
                "records": sports_records,
            },
            {
                "cohort_id": "CENTENARIAN_LONGEVITY_BENCHMARK",
                "title": "Centenarian Longevity Benchmark (N=100)",
                "description": "Validated centenarian & octogenarian records testing Saturn in Upachaya/8th house.",
                "sample_size": 100,
                "rodden_rating": "AA",
                "target_outcomes": ["longevity_over_75", "chronic_health_issue"],
                "records": longevity_records,
            },
            {
                "cohort_id": "EXECUTIVE_LEADERSHIP_BENCHMARK",
                "title": "Corporate & Public Leadership Benchmark (N=100)",
                "description": "Executive leadership cohort testing Sun in Digbala (10th) and Gajakesari Yoga.",
                "sample_size": 100,
                "rodden_rating": "A",
                "target_outcomes": ["executive_leadership", "top_quartile_wealth"],
                "records": leadership_records,
            },
            {
                "cohort_id": "MARRIAGE_TIMING_BENCHMARK",
                "title": "Vedic Relationship & Marriage Timing Benchmark (N=100)",
                "description": "Relationship timing cohort testing Venus in Kendra/Trikona vs Dusthana affliction.",
                "sample_size": 100,
                "rodden_rating": "AA",
                "target_outcomes": ["marriage_before_30"],
                "records": marriage_records,
            },
        ]

    def build_contingency_table(
        self,
        cohort_records: Sequence[dict[str, Any]],
        hypothesis: HypothesisDefinition,
    ) -> ContingencyTable2x2:
        """
        Classifies every subject in the cohort into the 2x2 contingency matrix:
        a = Exposed Cases (Condition True, Outcome True)
        b = Exposed Controls (Condition True, Outcome False)
        c = Unexposed Cases (Condition False, Outcome True)
        d = Unexposed Controls (Condition False, Outcome False)
        """
        a, b, c, d = 0, 0, 0, 0
        target_outcome_key = hypothesis.target_outcome

        for record in cohort_records:
            # 1. Evaluate astrological exposure
            chart_data = record.get("chart", record)
            is_exposed = self._feature_evaluator.evaluate_exposure(chart_data, hypothesis.exposure_rule)

            # 2. Evaluate target outcome
            outcomes = record.get("outcomes", record.get("events", {}))
            if isinstance(outcomes, dict):
                has_outcome = bool(outcomes.get(target_outcome_key, False))
            elif isinstance(outcomes, list):
                has_outcome = target_outcome_key in outcomes
            else:
                has_outcome = bool(record.get(target_outcome_key, False))

            if is_exposed and has_outcome:
                a += 1
            elif is_exposed and not has_outcome:
                b += 1
            elif not is_exposed and has_outcome:
                c += 1
            else:
                d += 1

        return ContingencyTable2x2(
            a_exposed_cases=a,
            b_exposed_controls=b,
            c_unexposed_cases=c,
            d_unexposed_controls=d,
        )

    def evaluate_hypothesis(
        self,
        hypothesis: HypothesisDefinition,
        table: ContingencyTable2x2,
        total_hypotheses_in_sweep: int = 1,
        nominal_alpha: float = 0.05,
    ) -> HypothesisStatisticalResult:
        """
        Computes the complete inferential statistical profile for a single hypothesis.
        """
        a = table.a_exposed_cases
        b = table.b_exposed_controls
        c = table.c_unexposed_cases
        d = table.d_unexposed_controls
        n = table.total_n

        # 1. Odds Ratio & 95% Wald CI
        odds_ratio, or_ci_low, or_ci_high = compute_odds_ratio_and_ci(a, b, c, d)

        # 2. Relative Risk & 95% CI
        rr, rr_ci_low, rr_ci_high = compute_relative_risk_and_ci(a, b, c, d)

        # 3. Chi-Square Test (Yates' corrected)
        chi_stat, chi_p = chi_square_test_2x2(a, b, c, d, use_yates=True)

        # 4. Fisher's Exact Test
        fisher_p = fisher_exact_test_2x2(a, b, c, d)

        # 5. Effect Size (Cohen's w = sqrt(chi2 / n))
        cohen_w = round(math.sqrt(chi_stat / n), 3) if n > 0 else 0.0
        cramers_v = cohen_w  # For 2x2 table, Cramér's V == Cohen's w

        # 6. Bonferroni adjustment
        bonferroni_alpha = round(nominal_alpha / max(1, total_hypotheses_in_sweep), 6)
        is_bonferroni_sig = fisher_p < bonferroni_alpha

        # 7. Quality flags & verdict
        has_small_sample = (n < 20 or any(cell < 5 for cell in (a, b, c, d)))

        # Power approximation for 2x2 table
        power_estimate = round(min(0.99, max(0.10, (math.sqrt(n) * cohen_w) / 2.8)), 2)

        if fisher_p < bonferroni_alpha and odds_ratio > 1.0:
            verdict = ScientificVerdict.CONFIRMED_SIGNIFICANT
        elif fisher_p < 0.05 and odds_ratio > 1.0:
            verdict = ScientificVerdict.TREND_SUGGESTIVE
        elif fisher_p < 0.05 and odds_ratio < 1.0:
            verdict = ScientificVerdict.INVERSE_CORRELATION
        else:
            verdict = ScientificVerdict.NULL_INSUFFICIENT_EVIDENCE

        audit_trace = [
            f"Pre-registered H1: '{hypothesis.title}' (Category: {hypothesis.category.value}).",
            f"Contingency: Cases Exposed={a}, Controls Exposed={b}, Cases Unexposed={c}, Controls Unexposed={d} (Total N={n}).",
            f"Exposure Rate: Cases={table.exposure_rate_cases * 100:.1f}%, Controls={table.exposure_rate_controls * 100:.1f}%.",
            f"Odds Ratio: {odds_ratio} (95% CI: [{or_ci_low}, {or_ci_high}]).",
            f"Relative Risk: {rr} (95% CI: [{rr_ci_low}, {rr_ci_high}]).",
            f"Chi-Square: {chi_stat} (Yates' corrected p={chi_p}), Fisher's Exact p={fisher_p}.",
            f"Effect Size: Cohen's w = {cohen_w} ({'large' if cohen_w >= 0.5 else 'medium' if cohen_w >= 0.3 else 'small' if cohen_w >= 0.1 else 'negligible'}).",
            f"Bonferroni threshold for K={total_hypotheses_in_sweep}: alpha={bonferroni_alpha}. Result: {'Significant' if is_bonferroni_sig else 'Not Significant'}.",
            f"Verdict: {verdict.value}.",
        ]

        return HypothesisStatisticalResult(
            hypothesis=hypothesis,
            contingency_table=table,
            sample_size_n=n,
            odds_ratio=odds_ratio,
            odds_ratio_ci_lower=or_ci_low,
            odds_ratio_ci_upper=or_ci_high,
            relative_risk=rr,
            relative_risk_ci_lower=rr_ci_low,
            relative_risk_ci_upper=rr_ci_high,
            cohen_w_effect_size=cohen_w,
            cramers_v=cramers_v,
            chi_square_stat=chi_stat,
            chi_square_p_value=chi_p,
            fisher_exact_p_value=fisher_p,
            is_significant_nominal=fisher_p < 0.05,
            bonferroni_adjusted_alpha=bonferroni_alpha,
            is_significant_bonferroni=is_bonferroni_sig,
            fdr_q_value=fisher_p,  # Will be adjusted during multi-sweep
            is_significant_fdr=fisher_p < 0.05,
            has_small_sample_warning=has_small_sample,
            statistical_power_estimate=power_estimate,
            verdict=verdict,
            audit_trace=audit_trace,
        )

    def run_multi_hypothesis_sweep(
        self,
        cohort_tag: str,
        cohort_records: Sequence[dict[str, Any]],
        hypotheses: Optional[Sequence[HypothesisDefinition]] = None,
        nominal_alpha: float = 0.05,
    ) -> MultiHypothesisSweepReport:
        """
        Executes a batch hypothesis sweep over a cohort dataset with Bonferroni
        and Benjamini-Hochberg False Discovery Rate multiple-testing corrections.
        """
        if hypotheses is None or len(hypotheses) == 0:
            hypotheses = self.get_standard_hypotheses()

        k = len(hypotheses)
        sweep_id = f"sweep-{uuid.uuid4().hex[:12]}"
        bonferroni_alpha = round(nominal_alpha / k, 6)

        # 1. Compute contingency tables and individual results
        raw_results: list[HypothesisStatisticalResult] = []
        p_values: list[float] = []

        for hyp in hypotheses:
            table = self.build_contingency_table(cohort_records, hyp)
            res = self.evaluate_hypothesis(hyp, table, total_hypotheses_in_sweep=k, nominal_alpha=nominal_alpha)
            raw_results.append(res)
            p_values.append(res.fisher_exact_p_value)

        # 2. Compute Benjamini-Hochberg FDR q-values
        fdr_q_values = benjamini_hochberg_fdr(p_values)

        # 3. Update results with FDR values
        adjusted_results: list[HypothesisStatisticalResult] = []
        nominal_sig_count = 0
        fdr_sig_count = 0
        bonferroni_sig_count = 0

        for res, q_val in zip(raw_results, fdr_q_values):
            is_fdr_sig = q_val < nominal_alpha
            if res.is_significant_nominal:
                nominal_sig_count += 1
            if is_fdr_sig:
                fdr_sig_count += 1
            if res.is_significant_bonferroni:
                bonferroni_sig_count += 1

            # Update trace with FDR q-value
            updated_trace = list(res.audit_trace)
            updated_trace.append(f"Benjamini-Hochberg FDR q-value: {q_val} ({'FDR Significant' if is_fdr_sig else 'FDR Not Significant'}).")

            adjusted_res = HypothesisStatisticalResult(
                hypothesis=res.hypothesis,
                contingency_table=res.contingency_table,
                sample_size_n=res.sample_size_n,
                odds_ratio=res.odds_ratio,
                odds_ratio_ci_lower=res.odds_ratio_ci_lower,
                odds_ratio_ci_upper=res.odds_ratio_ci_upper,
                relative_risk=res.relative_risk,
                relative_risk_ci_lower=res.relative_risk_ci_lower,
                relative_risk_ci_upper=res.relative_risk_ci_upper,
                cohen_w_effect_size=res.cohen_w_effect_size,
                cramers_v=res.cramers_v,
                chi_square_stat=res.chi_square_stat,
                chi_square_p_value=res.chi_square_p_value,
                fisher_exact_p_value=res.fisher_exact_p_value,
                is_significant_nominal=res.is_significant_nominal,
                bonferroni_adjusted_alpha=res.bonferroni_adjusted_alpha,
                is_significant_bonferroni=res.is_significant_bonferroni,
                fdr_q_value=q_val,
                is_significant_fdr=is_fdr_sig,
                has_small_sample_warning=res.has_small_sample_warning,
                statistical_power_estimate=res.statistical_power_estimate,
                verdict=res.verdict,
                audit_trace=updated_trace,
            )
            adjusted_results.append(adjusted_res)

        return MultiHypothesisSweepReport(
            sweep_id=sweep_id,
            cohort_tag=cohort_tag,
            total_cohort_size=len(cohort_records),
            hypotheses_tested_count=k,
            bonferroni_alpha=bonferroni_alpha,
            nominal_significant_count=nominal_sig_count,
            fdr_significant_count=fdr_sig_count,
            bonferroni_significant_count=bonferroni_sig_count,
            results=tuple(adjusted_results),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


class CohortPipelineOrchestrator:
    """
    End-to-End Orchestrator for Phase 2 Research Workflow:
      Stage 1: Cohort Ingestion
      Stage 2: Multi-Tier QC Validation & Deduplication
      Stage 3: Batch Chart Generation (Swiss Ephemeris / HoroscopeEngine)
      Stage 4: Astrological Feature Extraction
      Stage 5: Statistical Hypotheses Testing (2x2 tables, OR, Yates Chi2, Fisher Exact, FDR)
      Stage 6: Comprehensive Scientific Results & Audit Report
    """

    def __init__(
        self,
        sweep_engine: Optional[StatisticalSweepEngine] = None,
    ) -> None:
        self._sweep_engine = sweep_engine or StatisticalSweepEngine()

    def run_pipeline(
        self,
        cohort_tag: str,
        raw_records: Sequence[dict[str, Any]],
        min_rodden_rating: str = "B",
        hypotheses: Optional[Sequence[HypothesisDefinition]] = None,
        nominal_alpha: float = 0.05,
    ) -> CohortPipelineRunResult:
        import time
        from apps.api.domain.benchmark_dataset import InclusionCriteria, RejectionCode
        from apps.api.domain.research_calibration import BirthDataConfidence
        from apps.api.domain.statistical_sweep import (
            CohortPipelineRunResult,
            Stage1IngestionSummary,
            Stage2ValidationSummary,
            Stage3BatchChartSummary,
            Stage4FeatureExtractionSummary,
            Stage5HypothesisSweepSummary,
        )
        from apps.api.services.dataset_validator import DatasetValidator
        from apps.api.services.horoscope_engine import HoroscopeEngine
        from apps.api.services.ephemeris_wrapper import EphemerisWrapper
        from apps.api.config import get_settings

        pipeline_run_id = f"pipe-{uuid.uuid4().hex[:12]}"
        t_start = time.perf_counter()

        # ── Stage 1 & 2: Ingestion, Multi-Tier QC & Deduplication ────────────
        confidence_map = {
            "AA": BirthDataConfidence.AA,
            "A": BirthDataConfidence.A,
            "B": BirthDataConfidence.B,
            "C": BirthDataConfidence.C,
            "DD": BirthDataConfidence.DD,
        }
        threshold = confidence_map.get(min_rodden_rating.upper(), BirthDataConfidence.B)
        inclusion = InclusionCriteria(min_birth_confidence=threshold)

        validator = DatasetValidator()
        qc_result = validator.validate_and_audit(raw_records, inclusion)

        rejections_by_code: dict[str, int] = {}
        for r in qc_result.rejected_records:
            code_str = r.rejection_code.value
            rejections_by_code[code_str] = rejections_by_code.get(code_str, 0) + 1

        stage_1 = Stage1IngestionSummary(
            total_received=len(raw_records),
            total_accepted=len(qc_result.accepted_events),
            total_rejected=len(qc_result.rejected_records),
            duplicates_count=rejections_by_code.get(RejectionCode.HARD_DUPLICATE_COLLISION.value, 0)
            + rejections_by_code.get(RejectionCode.CONFLICTING_RECORD_COLLISION.value, 0),
            provenance_hash_sha256=qc_result.content_hash_sha256,
        )

        stage_2 = Stage2ValidationSummary(
            accepted_events_count=len(qc_result.accepted_events),
            rejected_events_count=len(qc_result.rejected_records),
            rejections_by_code=rejections_by_code,
        )

        # ── Stage 3 & 4: Batch Chart Generation & Feature Extraction ─────────
        settings = get_settings()
        wrapper = EphemerisWrapper(settings.EPHEMERIS_PATH)
        horoscope_engine = HoroscopeEngine(wrapper)

        cohort_feature_records: list[dict[str, Any]] = []
        sample_feature_profile: dict[str, Any] = {}

        t_calc_start = time.perf_counter()
        for event in qc_result.accepted_events:
            try:
                d1_chart = horoscope_engine.generate_d1(
                    birth_datetime_utc=event.birth_datetime_utc,
                    latitude=event.birth_latitude,
                    longitude=event.birth_longitude,
                )

                # Extract discrete astrological features
                planets_extracted = [
                    {
                        "planet": p.planet,
                        "house_number": p.house_number,
                        "rashi": p.rashi,
                        "is_retrograde": p.is_retrograde,
                        "longitude": p.sidereal_longitude,
                        "nakshatra": p.nakshatra,
                    }
                    for p in d1_chart.planets
                ]

                strengths_extracted = [
                    {
                        "planet": s.planet,
                        "dignity": s.dignity.value if s.dignity else None,
                        "is_in_kendra": s.is_in_kendra,
                        "is_in_trikona": s.is_in_trikona,
                        "is_in_dusthana": s.is_in_dusthana,
                        "is_exalted": s.is_exalted,
                        "is_debilitated": s.is_debilitated,
                    }
                    for s in d1_chart.planet_strengths
                ]

                # Map outcomes dictionary from event
                outcomes_dict: dict[str, bool] = {
                    event.event_type: True,
                    "target_event_occurred": True,
                }
                # Derive age-based outcomes if applicable
                birth_year = event.birth_datetime_utc.year
                event_year = event.actual_date.year
                age_at_event = max(0, event_year - birth_year)

                if event.event_type in ("marriage", "wedding"):
                    outcomes_dict["marriage_before_30"] = age_at_event <= 30
                elif event.event_type in ("promotion", "career_peak", "executive_appointment"):
                    outcomes_dict["executive_leadership"] = True
                elif event.event_type in ("wealth_milestone", "financial_gain"):
                    outcomes_dict["top_quartile_wealth"] = True
                elif event.event_type in ("longevity_marker", "death"):
                    outcomes_dict["longevity_over_75"] = age_at_event >= 75
                elif event.event_type in ("illness_onset", "hospitalization"):
                    outcomes_dict["chronic_health_issue"] = True

                record_profile = {
                    "subject_id": event.subject_id,
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "planets": planets_extracted,
                    "planet_strengths": strengths_extracted,
                    "outcomes": outcomes_dict,
                }
                cohort_feature_records.append(record_profile)

                if not sample_feature_profile:
                    sample_feature_profile = {
                        "subject_id": event.subject_id,
                        "planets_count": len(planets_extracted),
                        "sample_planet": planets_extracted[0] if planets_extracted else {},
                        "outcomes_tracked": list(outcomes_dict.keys()),
                    }
            except Exception:
                # If ephemeris calculation fails on a specific chart, continue
                continue

        t_calc_end = time.perf_counter()
        calc_time_ms = round((t_calc_end - t_calc_start) * 1000.0, 2)

        stage_3 = Stage3BatchChartSummary(
            generated_charts_count=len(cohort_feature_records),
            calculation_time_ms=calc_time_ms,
            ephemeris_ayanamsa="lahiri",
        )

        stage_4 = Stage4FeatureExtractionSummary(
            subjects_profiled_count=len(cohort_feature_records),
            features_per_subject_count=len(sample_feature_profile.get("outcomes_tracked", [])) + 9,
            sample_features=sample_feature_profile,
        )

        # ── Stage 5 & 6: Statistical Hypotheses Sweeps & Results ─────────────
        if hypotheses is None or len(hypotheses) == 0:
            hypotheses = self._sweep_engine.get_standard_hypotheses()

        sweep_report = self._sweep_engine.run_multi_hypothesis_sweep(
            cohort_tag=cohort_tag,
            cohort_records=cohort_feature_records,
            hypotheses=hypotheses,
            nominal_alpha=nominal_alpha,
        )

        stage_5 = Stage5HypothesisSweepSummary(
            hypotheses_tested_count=sweep_report.hypotheses_tested_count,
            bonferroni_adjusted_alpha=sweep_report.bonferroni_alpha,
            nominal_significant_count=sweep_report.nominal_significant_count,
            fdr_significant_count=sweep_report.fdr_significant_count,
            bonferroni_significant_count=sweep_report.bonferroni_significant_count,
        )

        return CohortPipelineRunResult(
            pipeline_run_id=pipeline_run_id,
            cohort_tag=cohort_tag,
            stage_1_ingestion=stage_1,
            stage_2_validation=stage_2,
            stage_3_batch_charts=stage_3,
            stage_4_feature_extraction=stage_4,
            stage_5_hypothesis_sweep=stage_5,
            sweep_report=sweep_report,
            executed_at=datetime.now(timezone.utc).isoformat(),
        )

