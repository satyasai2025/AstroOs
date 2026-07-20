"""
AstroOS Analytics Engine (Phase III.4 — Local-First)

Deterministic statistical methods for cohort analysis, correlation studies,
and significance testing. Pure computation — no external dependencies beyond
stdlib (math, statistics).

All methods operate on in-memory data structures (lists of dicts). No
database dependency — callers pass the dataset they want analyzed.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any


# ── Data structures ─────────────────────────────────────────────────────────────

@dataclass
class CohortQuery:
    """A query definition for filtering and grouping a dataset."""
    filters: list[FilterClause] = field(default_factory=list)
    group_by: str | None = None
    metrics: list[str] = field(default_factory=list)
    limit: int = 1000


@dataclass
class FilterClause:
    field: str
    operator: str       # eq, neq, gt, gte, lt, lte, in, between
    value: Any


@dataclass
class CohortResult:
    """Result of a cohort query with grouped data."""
    groups: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    total_records: int = 0
    query: CohortQuery | None = None


@dataclass
class CorrelationResult:
    """Pearson correlation result."""
    field_x: str
    field_y: str
    r: float            # Pearson coefficient (-1 to 1)
    p_value: float      # two-tailed p-value
    n: int              # sample size
    strength: str       # none, weak, moderate, strong


@dataclass
class ChiSquareResult:
    """Chi-squared test for independence result."""
    chi2: float
    p_value: float
    dof: int            # degrees of freedom
    expected: list[list[float]]
    observed: list[list[float]]
    significant: bool


@dataclass
class TTestResult:
    """Independent two-sample t-test result."""
    t_stat: float
    p_value: float
    dof: float
    mean_a: float
    mean_b: float
    significant: bool


@dataclass
class BayesFactorResult:
    """Bayes factor for comparing two hypotheses."""
    bf10: float         # evidence for H1 over H0
    interpretation: str


# ── Query Builder ───────────────────────────────────────────────────────────────

class QueryBuilder:
    """Build and execute cohort queries on in-memory datasets."""

    @staticmethod
    def execute(dataset: list[dict[str, Any]], query: CohortQuery) -> CohortResult:
        """Apply filters, group, and return results."""
        filtered = dataset

        # Apply filters
        for f in query.filters:
            filtered = [r for r in filtered if QueryBuilder._apply_filter(r, f)]

        result = CohortResult(query=query, total_records=len(filtered))

        # Group
        if query.group_by:
            groups: dict[str, list[dict[str, Any]]] = {}
            for record in filtered:
                key = str(record.get(query.group_by, "unknown"))
                groups.setdefault(key, []).append(record)
            result.groups = groups
        else:
            result.groups = {"all": filtered}

        return result

    @staticmethod
    def _apply_filter(record: dict[str, Any], f: FilterClause) -> bool:
        val = record.get(f.field)
        if f.operator == "eq":
            return val == f.value
        elif f.operator == "neq":
            return val != f.value
        elif f.operator == "gt":
            return isinstance(val, (int, float)) and val > f.value
        elif f.operator == "gte":
            return isinstance(val, (int, float)) and val >= f.value
        elif f.operator == "lt":
            return isinstance(val, (int, float)) and val < f.value
        elif f.operator == "lte":
            return isinstance(val, (int, float)) and val <= f.value
        elif f.operator == "in":
            return val in f.value if isinstance(f.value, (list, tuple)) else False
        elif f.operator == "between":
            if not isinstance(f.value, (list, tuple)) or len(f.value) != 2:
                return False
            return isinstance(val, (int, float)) and f.value[0] <= val <= f.value[1]
        return True


# ── Statistical Engine ──────────────────────────────────────────────────────────

class StatisticalEngine:
    """Local-first statistical methods. Pure stdlib, zero external dependencies."""

    @staticmethod
    def pearson_correlation(
        data: list[dict[str, Any]], field_x: str, field_y: str,
    ) -> CorrelationResult:
        """Compute Pearson correlation between two numeric fields."""
        pairs = [
            (r[field_x], r[field_y]) for r in data
            if isinstance(r.get(field_x), (int, float))
            and isinstance(r.get(field_y), (int, float))
        ]
        n = len(pairs)
        if n < 3:
            return CorrelationResult(field_x, field_y, 0.0, 1.0, n, "none")

        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]

        mean_x = statistics.mean(xs)
        mean_y = statistics.mean(ys)

        cov = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
        std_x = statistics.stdev(xs) if len(xs) > 1 else 1
        std_y = statistics.stdev(ys) if len(ys) > 1 else 1

        denom = std_x * std_y * (n - 1)
        r = cov / denom if denom != 0 else 0.0
        r = max(-1.0, min(1.0, r))

        # Two-tailed p-value from t-distribution approximation
        t_stat = r * math.sqrt((n - 2) / max(1 - r * r, 1e-10))
        dof = n - 2
        p_value = StatisticalEngine._t_distribution_p_value(t_stat, dof)

        # Strength label
        abs_r = abs(r)
        if abs_r < 0.1:
            strength = "none"
        elif abs_r < 0.3:
            strength = "weak"
        elif abs_r < 0.5:
            strength = "moderate"
        else:
            strength = "strong"

        return CorrelationResult(field_x, field_y, r, p_value, n, strength)

    @staticmethod
    def chi_square_test(
        observed: list[list[float]],
    ) -> ChiSquareResult:
        """Chi-squared test for independence on a contingency table."""
        rows = len(observed)
        cols = len(observed[0]) if observed else 0
        if rows < 2 or cols < 2:
            return ChiSquareResult(0.0, 1.0, 0, observed, observed, False)

        row_sums = [sum(row) for row in observed]
        col_sums = [sum(observed[r][c] for r in range(rows)) for c in range(cols)]
        total = sum(row_sums)

        expected = [
            [(row_sums[r] * col_sums[c]) / total for c in range(cols)]
            for r in range(rows)
        ]

        chi2 = sum(
            (observed[r][c] - expected[r][c]) ** 2 / max(expected[r][c], 1e-10)
            for r in range(rows) for c in range(cols)
        )

        dof = (rows - 1) * (cols - 1)
        p_value = 1.0 - StatisticalEngine._chi2_cdf(chi2, dof)
        significant = p_value < 0.05

        return ChiSquareResult(chi2, p_value, dof, expected, observed, significant)

    @staticmethod
    def t_test_independent(
        sample_a: list[float], sample_b: list[float],
    ) -> TTestResult:
        """Independent two-sample t-test (Welch's)."""
        n_a, n_b = len(sample_a), len(sample_b)
        if n_a < 2 or n_b < 2:
            return TTestResult(0.0, 1.0, 0, 0, 0, False)

        mean_a = statistics.mean(sample_a)
        mean_b = statistics.mean(sample_b)
        var_a = statistics.variance(sample_a)
        var_b = statistics.variance(sample_b)

        # Welch's t-test
        se = math.sqrt(var_a / n_a + var_b / n_b)
        t_stat = (mean_a - mean_b) / se if se > 0 else 0.0

        # Welch-Satterthwaite degrees of freedom
        num = (var_a / n_a + var_b / n_b) ** 2
        denom = (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
        dof = num / denom if denom > 0 else 1.0

        p_value = StatisticalEngine._t_distribution_p_value(t_stat, dof)
        significant = p_value < 0.05

        return TTestResult(t_stat, p_value, dof, mean_a, mean_b, significant)

    @staticmethod
    def bayes_factor_ttest(t_stat: float, n: int) -> BayesFactorResult:
        """Approximate Bayes factor BF10 for a t-test (Savage-Dickey)."""
        bf10 = math.sqrt(n) * abs(t_stat) / math.sqrt(2 * math.pi)
        if bf10 > 100:
            interpretation = "extreme evidence for H1"
        elif bf10 > 10:
            interpretation = "strong evidence for H1"
        elif bf10 > 3:
            interpretation = "moderate evidence for H1"
        elif bf10 > 1:
            interpretation = "anecdotal evidence for H1"
        else:
            interpretation = "evidence for H0 (null)"
        return BayesFactorResult(bf10, interpretation)

    # ── Distribution approximations (no SciPy dependency) ─────────────────────

    @staticmethod
    def _t_distribution_p_value(t: float, dof: float) -> float:
        """Approximate two-tailed p-value using the t-distribution CDF."""
        x = dof / (dof + t * t)
        p = 0.5 * (1.0 + math.erf(t / math.sqrt(2)))  # fallback normal
        if dof > 0 and t != 0:
            # Use incomplete beta function approximation
            a = dof / 2.0
            b = 0.5
            bt = math.exp(
                math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                + a * math.log(x) + b * math.log(1.0 - x)
            )
            if t > 0:
                p = 1.0 - 0.5 * bt * (1.0 + x)  # simplified
            else:
                p = 0.5 * bt * (1.0 + x)
        return min(1.0, max(0.0, 2.0 * (1.0 - p) if t > 0 else 2.0 * p))

    @staticmethod
    def _chi2_cdf(x: float, dof: int) -> float:
        """Chi-squared CDF using the regularized lower incomplete gamma."""
        if x <= 0 or dof <= 0:
            return 0.0
        return StatisticalEngine._lower_incomplete_gamma(dof / 2.0, x / 2.0)

    @staticmethod
    def _lower_incomplete_gamma(a: float, x: float) -> float:
        """Regularized lower incomplete gamma function (series expansion)."""
        if x < a + 1:
            # Series representation
            ap = a
            summ = 1.0 / a
            delta = summ
            for _i in range(100):
                ap += 1
                delta *= x / ap
                summ += delta
                if abs(delta) < abs(summ) * 1e-7:
                    break
            return summ * math.exp(-x + a * math.log(x) - math.lgamma(a))
        else:
            # Continued fraction representation
            b = x + 1.0 - a
            c = 1.0 / 1e-30
            d = 1.0 / b
            h = d
            for i in range(1, 101):
                an = -i * (i - a)
                b += 2.0
                d = an * d + b
                if abs(d) < 1e-30:
                    d = 1e-30
                c = b + an / c
                if abs(c) < 1e-30:
                    c = 1e-30
                d = 1.0 / d
                delta = d * c
                h *= delta
                if abs(delta - 1.0) < 1e-7:
                    break
            return 1.0 - h * math.exp(-x + a * math.log(x) - math.lgamma(a))
