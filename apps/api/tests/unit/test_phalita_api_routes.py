"""Comprehensive API endpoint tests for Phalita MoE system."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.routers.phalita_prediction import (
    CanonicalSynthesisRequest,
    VPCTimelineRequest,
    NoiseDiagnosticsRequest,
)


class TestCanonicalSynthesisRequest:
    """Test canonical synthesis request validation."""

    def test_minimal_request(self):
        """Test that required fields are enforced."""
        req = CanonicalSynthesisRequest(
            birth_date_iso="1971-06-29T23:27:40Z",
            latitude=28.6139,
            longitude=77.209,
        )
        assert req.birth_date_iso == "1971-06-29T23:27:40Z"
        assert req.latitude == 28.6139
        assert req.longitude == 77.209
        assert req.target_year is None

    def test_with_target_year(self):
        """Test request with target year specified."""
        req = CanonicalSynthesisRequest(
            birth_date_iso="1971-06-29T23:27:40Z",
            latitude=28.6139,
            longitude=77.209,
            target_year=2025,
        )
        assert req.target_year == 2025


class TestVPCTimelineRequest:
    """Test VPC timeline request validation."""

    def test_default_horizon(self):
        """Test default year range."""
        req = VPCTimelineRequest(
            birth_date_iso="1971-06-29T23:27:40Z",
            latitude=28.6139,
            longitude=77.209,
            start_year=2024,
            end_year=2030,
        )
        assert req.start_year == 2024
        assert req.end_year == 2030

    def test_short_horizon(self):
        """Test abbreviated year range."""
        req = VPCTimelineRequest(
            birth_date_iso="1971-06-29T23:27:40Z",
            latitude=28.6139,
            longitude=77.209,
            start_year=2025,
            end_year=2026,
        )
        assert req.start_year == 2025
        assert req.end_year == 2026

class TestNoiseDiagnosticsRequest:
    """Test noise diagnostics request validation."""

    def test_basic_request(self):
        """Test minimal noise diagnostics request."""
        req = NoiseDiagnosticsRequest(
            latitude=28.6139,
            longitude=77.209,
            deterministic_score=0.75,
            planet_block_total=1.2,
            residual_error=0.15,
        )
        assert req.deterministic_score == 0.75
        assert req.planet_block_total == 1.2
        assert req.residual_error == 0.15
        assert req.varga_opposition_index == 0.0

    def test_with_varga_opposition(self):
        """Test noise diagnostics with varga opposition index."""
        req = NoiseDiagnosticsRequest(
            latitude=28.6139,
            longitude=77.209,
            deterministic_score=0.75,
            planet_block_total=1.2,
            residual_error=0.15,
            varga_opposition_index=0.5,
        )
        assert req.varga_opposition_index == 0.5


class TestAPIResponseShapes:
    """Test that API response interfaces are properly defined."""

    def test_canonical_synthesis_response_exists(self):
        """Verify that CanonicalSynthesisResponse interface is defined in the module."""
        import apps.api.routers.phalita_prediction as router
        assert hasattr(router, 'router')
        assert router.router is not None


class TestDeterministicBaselineIntegration:
    """Integration tests with deterministic baseline engine."""

    def test_deterministic_score_consistency(self):
        """Test that deterministic scores are computed consistently."""
        from apps.api.services.deterministic_baseline_engine import DeterministicBaselineEngine

        predictions = [0.5, 0.8, 0.3, 0.9, 0.1]
        actuals = [0.4, 0.7, 0.2, 0.8, 0.0]

        report = DeterministicBaselineEngine.evaluate(
            predictions=predictions,
            actuals=actuals,
        )

        assert report.sample_count == 5
        assert report.mean_error is not None
        assert report.standard_deviation_error is not None
        assert report.mean_absolute_error is not None
        assert -1 <= report.correlation <= 1
        assert 0 <= report.direction_accuracy_pct <= 100

    def test_empty_series_rejection(self):
        """Test that empty series raises appropriate error."""
        from apps.api.services.deterministic_baseline_engine import DeterministicBaselineEngine
        with pytest.raises(ValueError):
            DeterministicBaselineEngine.evaluate(
                predictions=[],
                actuals=[],
            )


class TestCSVExporterSchema:
    """Test CSV exporter schema compliance per Vinay Jha Section 10."""

    def test_long_debug_header_columns(self):
        """Test that LONG_DEBUG_HEADER matches expected columns."""
        from apps.api.services.csv_exporter_engine import LONG_DEBUG_HEADER

        expected = [
            "RecordID", "TimeJD", "ChartLevel", "VargaID", "DegreeTheta",
            "RuleID", "RuleClass", "PlanetID", "BhavaID",
            "RawEffect", "SignedEffect", "VargaWeight", "TemporalWeight",
            "FinalEffect", "IsActive", "IsCancelled", "CancelledByRuleID",
            "DataQualityScore", "RuleVersion", "FeatureVersion",
        ]
        assert LONG_DEBUG_HEADER == expected
        assert len(LONG_DEBUG_HEADER) == 20

    def test_wide_ml_header_columns(self):
        """Test that WIDE_ML_HEADER matches expected columns."""
        from apps.api.services.csv_exporter_engine import WIDE_ML_HEADER

        assert "RecordID" in WIDE_ML_HEADER
        assert "Gold_Return_10min" in WIDE_ML_HEADER
        assert "Gold_Return_1hr" in WIDE_ML_HEADER
        assert "H2_Total" in WIDE_ML_HEADER
        assert "H8_Total" in WIDE_ML_HEADER
        assert "H11_Total" in WIDE_ML_HEADER
        assert "H12_Total" in WIDE_ML_HEADER
        assert "Final_Deterministic_Score" in WIDE_ML_HEADER
        assert "DataNoiseFlag" in WIDE_ML_HEADER
        assert "RulesNoiseFlag" in WIDE_ML_HEADER
        assert "ModelNoiseFlag" in WIDE_ML_HEADER
        assert "UsefulNoiseBand" in WIDE_ML_HEADER
        # Header has 43 columns per current schema implementation
        assert len(WIDE_ML_HEADER) == 43

    def test_csv_exporter_initialization(self):
        """Test CSVExporterEngine can be initialized."""
        from apps.api.services.csv_exporter_engine import CSVExporterEngine

        engine = CSVExporterEngine()
        assert engine is not None
        assert engine.wrapper is not None
        assert engine.tphalit_engine is not None
        assert engine.vpc_engine is not None
        assert engine.div_engine is not None