"""
AstroOS — EphemerisWrapper Concurrency Regression Test

Reproduces the bug fixed in this repair pass: EphemerisWrapper.calculate()
conditionally mutates process-global pyswisseph state (via swe.set_sid_mode)
based on the requested ayanamsa. Without the internal lock, concurrent calls
with different ayanamsas can interleave their check-set-calculate sequence
and silently compute planetary positions under the WRONG ayanamsa.

This test does not mock pyswisseph — it exercises the real C library against
the real .se1 data files in data/ephemeris/, because the bug this guards
against is a real interaction with process-global C state that a mock
cannot reproduce.

Requires: a working pyswisseph install and the .se1 files already present
in data/ephemeris/. No database or Redis required.
"""

import threading
from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper

pytestmark = pytest.mark.integration

_EPHEMERIS_PATH = "data/ephemeris"

# Two ayanamsas whose values differ by several degrees at any given date —
# if the lock fails, results computed "as Lahiri" will leak into results
# that should have been computed "as Raman" (or vice versa), and the
# assertions below will catch that as a longitude mismatch.
_AYANAMSA_A = "lahiri"
_AYANAMSA_B = "raman"

_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
_LAT = 28.6139   # New Delhi
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    """
    Single shared EphemerisWrapper instance — mirrors production usage via
    apps.api.dependencies.get_ephemeris_wrapper. Tests MUST use one shared
    instance, not one per test, or they are not testing the actual
    production code path.
    """
    return EphemerisWrapper(ephemeris_path=_EPHEMERIS_PATH, ayanamsa=_AYANAMSA_A)


def _reference_longitude(wrapper: EphemerisWrapper, ayanamsa: str) -> float:
    """Sequential, single-threaded calculation used as the ground truth."""
    result = wrapper.calculate(
        dt=_BIRTH_DT, latitude=_LAT, longitude=_LON, ayanamsa=ayanamsa,
    )
    sun = next(p for p in result.planet_positions if p.planet == "sun")
    return sun.sidereal_longitude


def test_sequential_calculations_differ_between_ayanamsas(wrapper: EphemerisWrapper) -> None:
    """
    Sanity check: Lahiri and Raman ayanamsas genuinely produce different
    sidereal longitudes for the same moment (they differ by ~0.5-1 degree
    depending on era). If this assertion fails, the two test ayanamsas
    aren't actually distinguishable and the concurrency test below would
    be meaningless.
    """
    lon_a = _reference_longitude(wrapper, _AYANAMSA_A)
    lon_b = _reference_longitude(wrapper, _AYANAMSA_B)
    assert abs(lon_a - lon_b) > 0.01, (
        "Test ayanamsas produced identical longitudes — "
        "test fixture cannot distinguish a race condition."
    )


def test_concurrent_calculations_do_not_cross_contaminate(
    wrapper: EphemerisWrapper,
) -> None:
    """
    The actual regression test.

    Fires many concurrent calculate() calls alternating between two
    ayanamsas from multiple threads (mirroring asyncio.to_thread usage in
    the routers) and asserts every result matches its OWN requested
    ayanamsa, not whichever ayanamsa another thread set global state to.

    Before the fix: this test is flaky and periodically fails as
    _AYANAMSA_A results occasionally come back with _AYANAMSA_B's
    longitude (or vice versa), because two threads can interleave the
    check-set-calculate sequence in EphemerisWrapper.calculate().

    After the fix: wrapper._lock serializes the critical section, so every
    result is correct regardless of thread interleaving.
    """
    reference_a = _reference_longitude(wrapper, _AYANAMSA_A)
    reference_b = _reference_longitude(wrapper, _AYANAMSA_B)

    results: dict[int, tuple[str, float]] = {}
    errors: list[Exception] = []
    lock_for_results = threading.Lock()

    def _worker(idx: int) -> None:
        try:
            ayanamsa = _AYANAMSA_A if idx % 2 == 0 else _AYANAMSA_B
            result = wrapper.calculate(
                dt=_BIRTH_DT, latitude=_LAT, longitude=_LON, ayanamsa=ayanamsa,
            )
            sun = next(p for p in result.planet_positions if p.planet == "sun")
            with lock_for_results:
                results[idx] = (ayanamsa, sun.sidereal_longitude)
        except Exception as exc:  # pragma: no cover - failure path
            with lock_for_results:
                errors.append(exc)

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(40)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, f"Worker thread(s) raised: {errors}"
    assert len(results) == 40, "Not all worker threads completed."

    for idx, (ayanamsa, longitude) in results.items():
        expected = reference_a if ayanamsa == _AYANAMSA_A else reference_b
        assert longitude == pytest.approx(expected, abs=1e-6), (
            f"Thread {idx} requested {ayanamsa} but got a longitude matching "
            f"the other ayanamsa — process-global pyswisseph state leaked "
            f"across concurrent calculate() calls."
        )
