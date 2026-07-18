"""
AstroOS Python SDK

Official Python client for the AstroOS Vedic Astrology API.

Usage:
    from astroos import AstroOSClient, AstroOSError, ChartReportRequest, ChartReportResponse

    client = AstroOSClient(api_key="...")
    chart = client.chart.compute(
        birth_datetime_utc="1986-06-15T10:30:00+00:00",
        latitude=28.6139, longitude=77.2090,
    )
"""

from .client import AstroOSClient
from .config import SdkConfig
from .exceptions import (
    AstroOSError,
    AstroOSAuthError,
    AstroOSValidationError,
    AstroOSRateLimitError,
    AstroOSServerError,
    AstroOSNotFoundError,
)
from .models import ChartReportRequest, ChartReportResponse

__all__ = [
    "AstroOSClient",
    "SdkConfig",
    "AstroOSError",
    "AstroOSAuthError",
    "AstroOSValidationError",
    "AstroOSRateLimitError",
    "AstroOSServerError",
    "AstroOSNotFoundError",
    "ChartReportRequest",
    "ChartReportResponse",
]