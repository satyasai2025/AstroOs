"""
Tests for Analytics Engine (Phase III.4)
"""
import math
from apps.api.services.analytics_engine import (
    QueryBuilder, StatisticalEngine, CohortQuery, FilterClause,
)


class TestQueryBuilder:
    def test_filter_eq(self):
        data = [{"planet": "Sun"}, {"planet": "Moon"}, {"planet": "Mars"}]
        q = CohortQuery(filters=[FilterClause("planet", "eq", "Sun")])
        result = QueryBuilder.execute(data, q)
        assert result.total_records == 1
        assert result.groups["all"][0]["planet"] == "Sun"

    def test_filter_gt(self):
        data = [{"degrees": 10}, {"degrees": 20}, {"degrees": 5}]
        q = CohortQuery(filters=[FilterClause("degrees", "gt", 10)])
        result = QueryBuilder.execute(data, q)
        assert result.total_records == 1

    def test_filter_between(self):
        data = [{"val": 5}, {"val": 15}, {"val": 25}]
        q = CohortQuery(filters=[FilterClause("val", "between", [10, 20])])
        result = QueryBuilder.execute(data, q)
        assert result.total_records == 1

    def test_group_by(self):
        data = [{"sign": "Aries"}, {"sign": "Taurus"}, {"sign": "Aries"}]
        q = CohortQuery(group_by="sign")
        result = QueryBuilder.execute(data, q)
        assert "Aries" in result.groups
        assert "Taurus" in result.groups
        assert len(result.groups["Aries"]) == 2


class TestStatisticalEngine:
    def test_pearson_perfect_positive(self):
        data = [{"x": i, "y": i} for i in range(10)]
        result = StatisticalEngine.pearson_correlation(data, "x", "y")
        assert abs(result.r - 1.0) < 1e-5

    def test_pearson_perfect_negative(self):
        data = [{"x": i, "y": -i} for i in range(10)]
        result = StatisticalEngine.pearson_correlation(data, "x", "y")
        assert abs(result.r - (-1.0)) < 1e-5

    def test_pearson_no_correlation(self):
        data = [{"x": i, "y": i % 2} for i in range(10)]
        result = StatisticalEngine.pearson_correlation(data, "x", "y")
        assert abs(result.r) < 0.5

    def test_pearson_insufficient_data(self):
        data = [{"x": 1, "y": 2}]
        result = StatisticalEngine.pearson_correlation(data, "x", "y")
        assert result.n == 1
        assert result.r == 0.0

    def test_chi_square_independent(self):
        obs = [[10, 20], [20, 40]]
        result = StatisticalEngine.chi_square_test(obs)
        assert not result.significant  # proportional

    def test_chi_square_dependent(self):
        obs = [[50, 5], [5, 50]]
        result = StatisticalEngine.chi_square_test(obs)
        assert result.significant

    def test_chi_square_small_table(self):
        obs = [[5]]
        result = StatisticalEngine.chi_square_test(obs)
        assert result.dof == 0

    def test_ttest_equal_samples(self):
        a = [10, 11, 10, 12, 11]
        b = [10, 11, 10, 12, 11]
        result = StatisticalEngine.t_test_independent(a, b)
        assert not result.significant

    def test_ttest_different_samples(self):
        a = [10, 11, 10, 12, 11]
        b = [50, 55, 48, 52, 53]
        result = StatisticalEngine.t_test_independent(a, b)
        assert result.significant
        assert result.mean_a < result.mean_b

    def test_ttest_insufficient_data(self):
        result = StatisticalEngine.t_test_independent([1], [2])
        assert not result.significant

    def test_bayes_factor(self):
        result = StatisticalEngine.bayes_factor_ttest(3.0, 30)
        assert result.bf10 > 1.0
        assert "evidence for H1" in result.interpretation

    def test_bayes_factor_null(self):
        result = StatisticalEngine.bayes_factor_ttest(0.1, 10)
        assert result.bf10 < 1.0

    def test_range_checks(self):
        """Correlation r stays within [-1, 1] for edge cases."""
        data = [{"x": i * 1e10, "y": i * 1e10} for i in range(5)]
        result = StatisticalEngine.pearson_correlation(data, "x", "y")
        assert -1.0 <= result.r <= 1.0
