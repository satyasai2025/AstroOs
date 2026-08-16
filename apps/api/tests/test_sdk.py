"""Tests for Python SDK — Phase G"""

import pytest
from sdks.python.astroos.exceptions import AstroOSError, AstroOSAuthError, AstroOSRateLimitError


def test_astroos_error_base():
    e = AstroOSError("test error")
    assert e.message == "test error"
    assert str(e) == "test error"


def test_astroos_errors_inherit():
    ae = AstroOSAuthError("auth failed")
    assert isinstance(ae, AstroOSError)
    
    re = AstroOSRateLimitError("rate limited")
    assert isinstance(re, AstroOSError)


from sdks.python.astroos.models import ChartReportRequest, ChartReportResponse


def test_chart_report_request_model():
    req = ChartReportRequest(birth_datetime_utc="2020-01-01T00:00:00Z", latitude=10.0, longitude=20.0)
    assert req.ayanamsa == "lahiri"
    assert req.house_system == "W"
    assert req.title is None


def test_chart_report_request_with_optional():
    req = ChartReportRequest(
        birth_datetime_utc="2020-01-01T00:00:00Z",
        latitude=10.0,
        longitude=20.0,
        title="My Report",
        subject_name="Test Subject"
    )
    assert req.title == "My Report"
    assert req.subject_name == "Test Subject"