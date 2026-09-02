"""Tests for Noise Diagnostic Engine (Section 18 Four-Quadrant Classification)."""
from __future__ import annotations

import pytest

from apps.api.services.ml.noise_diagnostic_engine import NoiseDiagnosticEngine, NoiseDiagnosticReport


class TestNoiseDiagnosticEngine:
    """Test noise diagnostic engine functionality."""

    def test_diagnose_basic(self):
        """Test basic noise diagnosis."""
        report = NoiseDiagnosticEngine.diagnose(
            latitude=28.6139,
            longitude=77.209,
            deterministic_score=0.75,
            planet_block_total=1.2,
            residual_error=0.15,
        )
        assert isinstance(report, NoiseDiagnosticReport)
        assert 0 <= report.data_noise_score <= 1
        assert 0 <= report.rules_noise_score <= 1
        assert 0 <= report.model_noise_score <= 1
        assert 0 <= report.useful_noise_bandwidth <= 1
        assert report.dominant_noise_category in ("DATA", "RULES", "MODEL", "CLEAN")
        assert isinstance(report.is_prediction_trustworthy, bool)

    def test_diagnose_high_deterministic(self):
        """Test diagnosis with high deterministic score (should be more trustworthy)."""
        report = NoiseDiagnosticEngine.diagnose(
            latitude=28.6139,
            longitude=77.209,
            deterministic_score=0.95,
            planet_block_total=1.5,
            residual_error=0.05,
        )
        assert report.is_prediction_trustworthy is True
        assert report.dominant_noise_category == "CLEAN"

    def test_diagnose_low_deterministic(self):
        """Test diagnosis with low deterministic score."""
        report = NoiseDiagnosticEngine.diagnose(
            latitude=28.6139,
            longitude=77.209,
            deterministic_score=0.2,
            planet_block_total=0.3,
            residual_error=0.5,
        )
        # Low deterministic score should increase noise flags
        assert report.data_noise_score > 0.3 or report.rules_noise_score > 0.3

    def test_diagnose_with_varga_opposition(self):
        """Test diagnosis with varga opposition index."""
class TestNoiseDiagnosticReport:
    """Test NoiseDiagnosticReport dataclass."""

    def test_report_attributes(self):
        """Test report has all required attributes."""
        report = NoiseDiagnosticReport(
            data_noise_score=0.2,
            rules_noise_score=0.3,
            model_noise_score=0.1,
            useful_noise_bandwidth=0.4,
            dominant_noise_category="RULES",
            is_prediction_trustworthy=True,
        )
        assert report.data_noise_score == 0.2
        assert report.rules_noise_score == 0.3
        assert report.model_noise_score == 0.1
        assert report.useful_noise_bandwidth == 0.4
        assert report.dominant_noise_category == "RULES"
        assert report.is_prediction_trustworthy is True

    def test_consistent_results(self):
        """Test that same inputs produce same outputs."""
        r1 = NoiseDiagnosticEngine.diagnose(
            latitude=28.6139,
            longitude=77.209,
            deterministic_score=0.75,
            planet_block_total=1.2,
            residual_error=0.15,
        )
        r2 = NoiseDiagnosticEngine.diagnose(
            latitude=28.6139,
            longitude=77.209,
            deterministic_score=0.75,
            planet_block_total=1.2,
            residual_error=0.15,
        )
        assert r1.data_noise_score == r2.data_noise_score
        assert r1.rules_noise_score == r2.rules_noise_score
        assert r1.model_noise_score == r2.model_noise_score
        assert r1.dominant_noise_category == r2.dominant_noise_category
        assert r1.is_prediction_trustworthy == r2.is_prediction_trustworthy
        report = NoiseDiagnosticEngine.diagnose(
            latitude=28.6139,
            longitude=77.209,
            deterministic_score=0.75,
            planet_block_total=1.2,
            residual_error=0.15,
            varga_opposition_index=0.8,
        )
        assert isinstance(report, NoiseDiagnosticReport)
        assert report.rules_noise_score >= 0
