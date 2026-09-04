"""
AstroOS — Offline SQLite Vault & Ephemeris Verification Unit Tests
===================================================================
Tests embedded SQLite offline chart persistence, sync queue tracking,
and offline Swiss Ephemeris data integrity.
"""

from pathlib import Path
import tempfile
import pytest

from apps.api.services.offline_vault_sync import (
    DEFAULT_OFFLINE_DB_PATH,
    OfflineChartRecord,
    OfflineVaultSyncManager,
)


@pytest.fixture
def temp_vault():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_offline.db"
        yield OfflineVaultSyncManager(db_path=db_path)


def test_ephemeris_bundle_verification(temp_vault: OfflineVaultSyncManager):
    """Verify Swiss Ephemeris offline bundle verification logic."""
    status = temp_vault.verify_ephemeris_bundle("data/ephemeris")
    assert "ephemeris_dir" in status
    assert status["seas_18_present"] is True
    assert status["semo_18_present"] is True
    assert status["sepl_18_present"] is True
    assert status["is_fully_offline_ready"] is True
    assert "600 BCE to 2400 CE" in status["total_range"]


def test_offline_chart_crud(temp_vault: OfflineVaultSyncManager):
    """Verify saving, retrieving, and listing offline charts."""
    chart = temp_vault.save_offline_chart(
        chart_id="test-chart-101",
        native_name="Arjun Sharma",
        birth_date_iso="1992-10-24T14:30:00+00:00",
        latitude=28.6139,
        longitude=77.2090,
        city_name="New Delhi, India",
        domain="career",
        notes="Consultation regarding upcoming Dasha change",
        consultation_payload={"timeline": [{"dasha": "Jupiter", "tier": "PRATYAKSHA_PHALA"}]}
    )
    assert chart.chart_id == "test-chart-101"
    assert chart.native_name == "Arjun Sharma"
    assert chart.is_synced is False

    # Retrieve
    retrieved = temp_vault.get_offline_chart("test-chart-101")
    assert retrieved is not None
    assert retrieved.native_name == "Arjun Sharma"
    assert retrieved.latitude == 28.6139
    assert "PRATYAKSHA_PHALA" in retrieved.consultation_payload_json

    # List
    charts = temp_vault.list_offline_charts()
    assert len(charts) == 1
    assert charts[0].chart_id == "test-chart-101"


def test_offline_sync_queue(temp_vault: OfflineVaultSyncManager):
    """Verify sync queue management and cloud reconciliation status."""
    temp_vault.save_offline_chart(
        chart_id="chart-sync-1",
        native_name="Priya Patel",
        birth_date_iso="1995-04-12T08:15:00+00:00",
        latitude=23.0225,
        longitude=72.5714,
    )
    temp_vault.save_offline_chart(
        chart_id="chart-sync-2",
        native_name="Rahul Verma",
        birth_date_iso="1988-11-30T19:45:00+00:00",
        latitude=19.0760,
        longitude=72.8777,
    )

    pending = temp_vault.get_pending_sync_queue()
    assert len(pending) == 2
    assert {c.chart_id for c in pending} == {"chart-sync-1", "chart-sync-2"}

    # Mark chart-sync-1 as synced
    synced_count = temp_vault.mark_charts_synced(["chart-sync-1"])
    assert synced_count == 1

    remaining = temp_vault.get_pending_sync_queue()
    assert len(remaining) == 1
    assert remaining[0].chart_id == "chart-sync-2"
