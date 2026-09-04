"""
Full Report (POST /api/v1/report/full) — unit tests for the schema layer
and the router's request construction.

The endpoint composes the existing WorkflowOrchestrator pipeline (already
covered end-to-end by workflow integration tests) plus KPEngine; what is
new here is the wire contract: FullReportRequest (birth data + pipeline
options) and FullReportResponse (the WorkflowAnalysisResponse shape plus
a kp_analysis section). These tests pin that contract without needing a
database or ephemeris engine.
"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from apps.api.schemas.workflow import FullReportRequest, FullReportResponse, WorkflowAnalysisRequest


class TestFullReportRequest:
    def test_accepts_birth_data_and_options(self):
        req = FullReportRequest(
            birth_datetime_utc="1990-01-01T05:30:00Z",
            latitude=28.6139,
            longitude=77.2090,
            ayanamsa="lahiri",
            house_system="W",
            title="Full Report",
            subject_name="Alex",
            dasha_system="vimshottari",
            include_vargas=False,
            include_kp=True,
        )
        assert req.title == "Full Report"
        assert req.subject_name == "Alex"
        assert req.dasha_system == "vimshottari"
        assert req.include_vargas is False
        assert req.include_kp is True

    def test_defaults(self):
        req = FullReportRequest(
            birth_datetime_utc="1990-01-01T05:30:00Z",
            latitude=0.0,
            longitude=0.0,
        )
        assert req.title == "Complete Astrology Report"
        assert req.subject_name == "Unnamed"
        assert req.dasha_system == "vimshottari"
        assert req.include_vargas is True
        assert req.include_kp is True
        assert req.transit_datetime_utc is None

    def test_naive_birth_datetime_rejected(self):
        with pytest.raises(ValidationError):
            FullReportRequest(
                birth_datetime_utc="1990-01-01T05:30:00",
                latitude=0.0,
                longitude=0.0,
            )


class TestFullReportResponse:
    def test_kp_analysis_is_optional_and_defaults_to_none(self):
        field = FullReportResponse.model_fields["kp_analysis"]
        assert field.is_required() is False
        assert field.default is None

    def test_chart_id_is_optional(self):
        # The full report never persists, so chart_id must be None-able.
        field = FullReportResponse.model_fields["chart_id"]
        assert field.is_required() is False
        assert field.default is None
        assert uuid.UUID in getattr(field.annotation, "__args__", ())


class TestRouterRequestConstruction:
    def test_model_construct_bypasses_chart_id_guardrail(self):
        """The router builds the pipeline request with model_construct so
        (persist=False, chart_id=None) is allowed — this endpoint is the
        anonymous-recompute path for brand-new birth data."""
        req = WorkflowAnalysisRequest.model_construct(
            birth_datetime_utc=datetime(1990, 1, 1, 5, 30, tzinfo=timezone.utc),
            latitude=28.6,
            longitude=77.2,
            ayanamsa="lahiri",
            house_system="W",
            dasha_system="vimshottari",
            include_vargas=False,
            subject_name="Test",
            persist=False,
            chart_id=None,
            research_project_id=None,
        )
        assert req.persist is False
        assert req.chart_id is None
