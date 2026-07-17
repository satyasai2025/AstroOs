"""
AstroOS Python SDK

Official Python client for the AstroOS Vedic Astrology API.

Usage:
    from astroos import AstroOSClient

    client = AstroOSClient(api_key="...")
    chart = client.chart.compute(
        birth_datetime_utc="1986-06-15T10:30:00+00:00",
        latitude=28.6139, longitude=77.2090,
    )
"""

from .client import AstroOSClient
from .config import SdkConfig

__all__ = ["AstroOSClient", "SdkConfig"]
