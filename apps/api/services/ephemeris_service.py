"""
AstroOS — Ephemeris Service

Wraps the pyswisseph C library (Swiss Ephemeris 2.10).
Responsibilities for Module 2-pre:
  - Set the ephemeris data-file path at startup.
  - Detect at runtime whether official SE2 files are loaded or the library
    has fallen back to the built-in Moshier approximation.
  - Expose a status DTO consumed by the health-check endpoint.

No chart generation lives here — that is Module 2.

Detection strategy
------------------
`swe.calc_ut(jd, planet, swe.FLG_SWIEPH)` returns (position_tuple, retflag).
The retflag integer encodes which engine was actually used:
  - retflag & swe.FLG_SWIEPH (2) → official .se1 files
  - retflag & swe.FLG_MOSEPH (4) → Moshier fallback (no data files found)
  - retflag < 0 → hard error from the C library

We test with JD 2451545.0 (J2000.0, 2000-01-01 12:00 TT) because it is
a well-known, stable reference point with no edge-case concerns.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import swisseph as swe

logger = logging.getLogger(__name__)

# J2000.0 — stable test epoch; no edge cases, results well-documented.
_TEST_JD = 2451545.0


class EphemerisMode(str, Enum):
    """Which calculation engine Swiss Ephemeris is actually using."""

    OFFICIAL = "swiss_ephemeris"
    """Official .se1 binary files are loaded — highest precision."""

    MOSHIER = "moshier"
    """Built-in polynomial approximation — no files needed, lower precision."""

    UNKNOWN = "unknown"
    """Could not perform a test calculation (library error)."""


@dataclass(frozen=True)
class EphemerisStatusDTO:
    """
    Service-layer DTO describing the current ephemeris engine state.

    Returned by EphemerisService.get_status(); the router converts this
    to an HTTP schema. Never import Pydantic into this module.
    """

    mode: EphemerisMode
    """Actual calculation engine in use."""

    path: str
    """Configured ephemeris path (may or may not contain .se1 files)."""

    se1_files: list[str] = field(default_factory=list)
    """Sorted list of .se1 files found in *path*."""

    official_data: bool = False
    """True iff mode == OFFICIAL — shortcut for callers."""

    test_longitude: Optional[float] = None
    """Sun longitude at J2000.0 used for the detection calculation (°)."""

    error: Optional[str] = None
    """Set when the test calculation itself raised a C-library error."""


class EphemerisService:
    """
    Thin stateful wrapper around pyswisseph.

    Lifecycle:
      - Instantiated once by the DI layer (or lifespan hook).
      - initialize() must be called before any calculation.
      - get_status() can be called repeatedly; it re-runs the detection each
        time so the health check always reflects the current file state.
    """

    def __init__(self, ephemeris_path: str) -> None:
        self._path = os.path.abspath(ephemeris_path)
        self._initialized = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def initialize(self) -> None:
        """
        Set the Swiss Ephemeris file path and open the library.
        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._initialized:
            return
        swe.set_ephe_path(self._path)
        self._initialized = True
        logger.info(
            "Swiss Ephemeris initialized",
            extra={"path": self._path},
        )

    def close(self) -> None:
        """Release file handles held by the C library. Call on shutdown."""
        swe.close()
        self._initialized = False

    # ── Status detection ──────────────────────────────────────────────────────

    def get_status(self) -> EphemerisStatusDTO:
        """
        Probe the library and return the current engine status.

        Thread-safe: pyswisseph uses a process-level global path, so this
        is called from a single async task (the health endpoint) only.
        """
        if not self._initialized:
            self.initialize()

        se1_files = self._list_se1_files()
        mode, longitude, error = self._probe_engine()

        return EphemerisStatusDTO(
            mode=mode,
            path=self._path,
            se1_files=se1_files,
            official_data=(mode == EphemerisMode.OFFICIAL),
            test_longitude=longitude,
            error=error,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _list_se1_files(self) -> list[str]:
        """Return sorted list of .se1 filenames found at the configured path."""
        if not os.path.isdir(self._path):
            return []
        try:
            return sorted(
                f for f in os.listdir(self._path) if f.endswith(".se1")
            )
        except OSError:
            return []

    def _probe_engine(
        self,
    ) -> tuple[EphemerisMode, Optional[float], Optional[str]]:
        """
        Run a test calculation at J2000.0 and inspect the returned flags.

        Returns (mode, sun_longitude_at_J2000, error_message).
        """
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        try:
            xx, retflag = swe.calc_ut(_TEST_JD, swe.SUN, flags)
        except Exception as exc:  # C-level errors surface as Python exceptions
            logger.warning("Swiss Ephemeris probe failed: %s", exc)
            return EphemerisMode.UNKNOWN, None, str(exc)

        if retflag < 0:
            return EphemerisMode.UNKNOWN, None, f"swe.calc_ut retflag={retflag}"

        longitude = round(float(xx[0]), 6)

        if retflag & swe.FLG_MOSEPH:
            logger.info(
                "Swiss Ephemeris: using Moshier fallback "
                "(official .se1 files not found at %s)",
                self._path,
            )
            return EphemerisMode.MOSHIER, longitude, None

        # retflag & FLG_SWIEPH — official files are loaded
        logger.info(
            "Swiss Ephemeris: official data files active at %s",
            self._path,
        )
        return EphemerisMode.OFFICIAL, longitude, None
