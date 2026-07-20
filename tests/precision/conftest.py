"""
DB-free fixtures for precision tests.

These tests validate calculation accuracy without requiring PostgreSQL.
Fixtures provide EphemerisWrapper, HoroscopeEngine, ShadbalaEngine, and
AshtakavargaEngine instances wired to the local .se1 ephemeris files.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from apps.api.services.aspect_engine import AspectEngine
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala_engine import ShadbalaEngine

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_EPHEMERIS_PATH = str(_REPO_ROOT / "data" / "ephemeris")


@pytest.fixture(scope="session")
def ephemeris_path() -> str:
    """Path to the Swiss Ephemeris .se1 data directory."""
    path = os.environ.get("EPHEMERIS_PATH", _DEFAULT_EPHEMERIS_PATH)
    if not os.path.isdir(path):
        pytest.skip(f"Ephemeris data directory not found: {path}")
    return path


@pytest.fixture(scope="session")
def ephemeris_wrapper(ephemeris_path: str) -> EphemerisWrapper:
    """Session-scoped EphemerisWrapper pointing at local .se1 files."""
    return EphemerisWrapper(ephemeris_path=ephemeris_path, ayanamsa="lahiri")


@pytest.fixture(scope="session")
def graha_engine() -> GrahaEngine:
    return GrahaEngine()


@pytest.fixture(scope="session")
def aspect_engine() -> AspectEngine:
    return AspectEngine()


@pytest.fixture(scope="session")
def horoscope_engine(
    ephemeris_wrapper: EphemerisWrapper,
    graha_engine: GrahaEngine,
    aspect_engine: AspectEngine,
) -> HoroscopeEngine:
    return HoroscopeEngine(
        wrapper=ephemeris_wrapper,
        graha_engine=graha_engine,
        aspect_engine=aspect_engine,
    )


@pytest.fixture(scope="session")
def divisional_engine(ephemeris_wrapper: EphemerisWrapper) -> DivisionalEngine:
    return DivisionalEngine(ephemeris_wrapper)


@pytest.fixture(scope="session")
def shadbala_engine(
    divisional_engine: DivisionalEngine,
    ephemeris_wrapper: EphemerisWrapper,
) -> ShadbalaEngine:
    return ShadbalaEngine(
        divisional_engine=divisional_engine,
        ephemeris_wrapper=ephemeris_wrapper,
    )


@pytest.fixture(scope="session")
def ashtakavarga_engine() -> AshtakavargaEngine:
    return AshtakavargaEngine()
