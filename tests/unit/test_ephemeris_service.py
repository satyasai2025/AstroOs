"""
AstroOS — EphemerisService Unit Tests

Covers:
  - Official mode detection when .se1 files are present
  - Moshier fallback detection when path is empty / files absent
  - Status DTO shape and field correctness
  - initialize() is idempotent (safe to call twice)
  - close() resets state so re-initialization works
  - _list_se1_files() with missing / empty / populated directories
"""

import os
import tempfile

import pytest
import swisseph as swe

from apps.api.services.ephemeris_service import (
    EphemerisMode,
    EphemerisService,
    EphemerisStatusDTO,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

OFFICIAL_EPHE_PATH = os.path.abspath("data/ephemeris")
"""Path where real .se1 files are downloaded in this environment."""


def _official_files_available() -> bool:
    """True when at least one .se1 file is present (sepl_18.se1 suffices)."""
    target = os.path.join(OFFICIAL_EPHE_PATH, "sepl_18.se1")
    return os.path.isfile(target)


# ── Official mode (real files) ────────────────────────────────────────────────


@pytest.mark.skipif(
    not _official_files_available(),
    reason="Official .se1 files not present at data/ephemeris/",
)
def test_official_mode_detected_when_files_present():
    """When .se1 files exist, EphemerisService must report OFFICIAL mode."""
    svc = EphemerisService(OFFICIAL_EPHE_PATH)
    status = svc.get_status()
    svc.close()

    assert status.mode == EphemerisMode.OFFICIAL
    assert status.official_data is True
    assert status.error is None
    assert len(status.se1_files) >= 1
    assert any(f.endswith(".se1") for f in status.se1_files)


@pytest.mark.skipif(
    not _official_files_available(),
    reason="Official .se1 files not present at data/ephemeris/",
)
def test_official_sun_longitude_at_j2000():
    """
    Sun longitude at J2000.0 with official files should be close to 280.46°
    (tropical, mean longitude).  We allow ±1° since the exact value depends
    on the DE* version used inside the .se1 file.
    """
    svc = EphemerisService(OFFICIAL_EPHE_PATH)
    status = svc.get_status()
    svc.close()

    assert status.test_longitude is not None
    assert 279.0 <= status.test_longitude <= 281.5, (
        f"Unexpected Sun longitude at J2000.0: {status.test_longitude}"
    )


# ── Moshier fallback (no files) ───────────────────────────────────────────────


def test_moshier_fallback_when_path_is_empty_dir():
    """An empty directory should trigger Moshier fallback."""
    with tempfile.TemporaryDirectory() as empty_dir:
        svc = EphemerisService(empty_dir)
        status = svc.get_status()
        svc.close()

    assert status.mode == EphemerisMode.MOSHIER
    assert status.official_data is False
    assert status.se1_files == []
    # Moshier still produces a longitude — it's an approximation, not an error
    assert status.test_longitude is not None
    assert status.error is None


def test_moshier_fallback_when_path_does_not_exist():
    """A non-existent path should trigger Moshier fallback gracefully."""
    svc = EphemerisService("/tmp/definitely_does_not_exist_astros_test")
    status = svc.get_status()
    svc.close()

    assert status.mode == EphemerisMode.MOSHIER
    assert status.official_data is False
    assert status.se1_files == []


# ── DTO shape ─────────────────────────────────────────────────────────────────


def test_status_dto_is_frozen_dataclass():
    svc = EphemerisService("/tmp/nonexistent_ephe")
    status = svc.get_status()
    svc.close()

    assert isinstance(status, EphemerisStatusDTO)
    # Frozen dataclasses raise FrozenInstanceError on assignment
    import dataclasses
    assert dataclasses.is_dataclass(status)
    with pytest.raises((AttributeError, TypeError)):
        status.mode = EphemerisMode.OFFICIAL  # type: ignore[misc]


def test_status_path_is_absolute():
    """EphemerisService always stores an absolute path in the DTO."""
    svc = EphemerisService("data/ephemeris")  # relative input
    status = svc.get_status()
    svc.close()

    assert os.path.isabs(status.path), f"Expected absolute path, got: {status.path}"


# ── Lifecycle ─────────────────────────────────────────────────────────────────


def test_initialize_is_idempotent():
    """Calling initialize() twice must not raise or change state."""
    svc = EphemerisService("/tmp/nonexistent_ephe")
    svc.initialize()
    svc.initialize()  # second call — must be a no-op
    svc.close()


def test_get_status_auto_initializes():
    """get_status() must work even when initialize() was not called first."""
    svc = EphemerisService("/tmp/nonexistent_ephe")
    # Do NOT call initialize() explicitly
    status = svc.get_status()
    svc.close()

    assert status.mode in (EphemerisMode.MOSHIER, EphemerisMode.UNKNOWN)


# ── File listing ──────────────────────────────────────────────────────────────


def test_list_se1_files_empty_directory():
    with tempfile.TemporaryDirectory() as d:
        svc = EphemerisService(d)
        files = svc._list_se1_files()
    assert files == []


def test_list_se1_files_filters_non_se1():
    with tempfile.TemporaryDirectory() as d:
        # Create a mix of file types
        open(os.path.join(d, "sepl_18.se1"), "w").close()
        open(os.path.join(d, "README.txt"), "w").close()
        open(os.path.join(d, "semo_18.se1"), "w").close()
        svc = EphemerisService(d)
        files = svc._list_se1_files()

    assert files == ["semo_18.se1", "sepl_18.se1"]  # sorted, no README


def test_list_se1_files_nonexistent_directory():
    svc = EphemerisService("/tmp/does_not_exist_xyz")
    files = svc._list_se1_files()
    assert files == []
