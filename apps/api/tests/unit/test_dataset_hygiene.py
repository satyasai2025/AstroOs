"""
AstroOS — Dataset Hygiene (v1.1) Unit & Integration Tests
==========================================================

Explicitly validates all 6 data governance invariants:
1. Record-level (name, dob, tob) and within-subject event deduplication.
2. Coordinate bounds validation, inverted coordinate auto-recovery, and coordinate-timezone consistency.
3. Country-era aware historical LMT (asserting exact seconds) vs Civil timezone calculation.
4. Death taxonomy disambiguation (Father / Mother / Spouse / Child / Sibling / Subject).
5. Event age plausibility gates (rejecting outliers while preserving valid senior parental deaths).
6. Fail-closed honest Rodden rating derivation from primary source citations.
"""

from datetime import date, datetime, timezone
from pathlib import Path
import pytest

from apps.api.services.dataset_hygiene_v1 import (
    DatasetHygieneEngine,
    PLAUSIBILITY_BOUNDS,
    ValidatedEvent,
    ValidatedRecord,
    disambiguate_death_event,
    derive_rodden_rating_from_source,
    get_standard_time_cutoff_year,
    is_timezone_geo_consistent,
    normalize_name,
    parse_date_flex,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
RAW_CSV_PATH = REPO_ROOT / "data" / "kundalee" / "kundalee_clean.csv"


# ── INVARIANT 1: DEDUPLICATION ──────────────────────────────────────────────

def test_record_and_event_deduplication(tmp_path):
    """Asserts both record-level and within-subject event-level deduplication."""
    test_csv = tmp_path / "test_dedup.csv"
    test_csv.write_text(
        "name,gender,dob,tob,latitude,longitude,timezone,birth_time_confidence,source,event_1_type,event_1_date,event_1_description,event_2_type,event_2_date,event_2_description\n"
        "Cannonball Adderley,Male,1928-09-15,12:00,30.4383,-84.2807,America/New_York,high,Quoted BC/BR,Marriage,1955-06-01,Wedding,Marriage,1955-06-01,Wedding\n"
        "Cannonball Adderley,Male,1928-09-15,12:00,30.4383,-84.2807,America/New_York,high,Quoted BC/BR,Marriage,1955-06-01,Wedding,Marriage,1955-06-01,Wedding\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    # Exactly 1 record preserved, 1 duplicate record dropped
    assert len(pristine) == 1
    assert report.duplicates_removed == 1
    # Exactly 1 event preserved, 1 duplicate event within subject dropped
    assert len(pristine[0].events) == 1
    assert report.events_deduplicated == 1


# ── INVARIANT 2: COORDINATE SANITY & CONSISTENCY ─────────────────────────────

def test_coordinate_bounds_quarantines_invalid(tmp_path):
    """Asserts that lat > 90 that cannot be recovered is safely quarantined."""
    test_csv = tmp_path / "test_invalid_lat.csv"
    test_csv.write_text(
        "name,gender,dob,tob,latitude,longitude,timezone,birth_time_confidence,source\n"
        "Impossible Location,Male,1980-01-01,12:00,112.9833,94.2333,UTC,high,AstroDatabank\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    assert len(pristine) == 0
    assert report.coordinates_quarantined == 1


def test_inverted_coordinates_recovered(tmp_path):
    """Asserts that inverted coordinates (e.g. Mumbai lat=72.83, lon=18.97) are auto-recovered."""
    test_csv = tmp_path / "test_inverted.csv"
    test_csv.write_text(
        "name,gender,dob,tob,latitude,longitude,timezone,birth_time_confidence,source\n"
        "Mumbai Native,Male,1970-01-01,12:00,72.8300,18.9700,Asia/Kolkata,high,Quoted BC/BR\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    assert len(pristine) == 1
    rec = pristine[0]
    assert rec.coord_status == "INVERTED_AUTO_FIXED"
    assert rec.latitude == 18.9700
    assert rec.longitude == 72.8300


def test_coordinate_timezone_consistency_quarantines_mismatch(tmp_path):
    """
    A. J. Croce Fixture: lon=-106.68 (Wyoming / Mountain Time) declared under America/New_York (Eastern Time).
    Must be detected as a timezone-coordinate geographic mismatch and quarantined.
    """
    test_csv = tmp_path / "test_croce_fixture.csv"
    test_csv.write_text(
        "name,gender,dob,tob,latitude,longitude,timezone,birth_time_confidence,source\n"
        "A. J. Croce,Male,1971-09-28,08:45,41.9333,-106.6833,America/New_York,high,Bio/autobiography\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    assert len(pristine) == 0
    assert report.coordinates_quarantined == 1


def test_albany_arctic_latitude_quarantined(tmp_path):
    """
    Fernande Albany Fixture: lat=72.86 (Arctic Sea) declared for Lison, France (Europe/Paris).
    Must be detected as a 2D latitude-timezone mismatch and quarantined.
    """
    test_csv = tmp_path / "test_albany_fixture.csv"
    test_csv.write_text(
        "name,gender,dob,tob,place,latitude,longitude,timezone,birth_time_confidence,source\n"
        "\"Albany, Fernande\",Female,1889-12-22,10:00,Lison France,72.8667,-4.5333,Europe/Paris,high,Quoted BC/BR\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    assert len(pristine) == 0
    assert report.coordinates_quarantined == 1


# ── INVARIANT 3: COUNTRY-ERA LMT VS CIVIL TIME ──────────────────────────────

def test_pre_1880_historical_lmt_resolved_with_exact_seconds(tmp_path):
    """
    Asserts exact Local Mean Time (LMT) calculation down to the second for pre-1880/1890 nativities.
    St. Petersburg 30.3351°E * 240s = 7280.42s = +2h 01m 20s offset.
    Local 12:00:00 -> UTC 09:58:40.
    """
    test_csv = tmp_path / "test_alexandra.csv"
    test_csv.write_text(
        "name,gender,dob,tob,place,latitude,longitude,timezone,birth_time_confidence,source\n"
        "Alexandra Archduchess,Female,1783-08-09,12:00,St Petersburg Russia,59.9343,30.3351,UTC,high,Quoted BC/BR\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    assert len(pristine) == 1
    rec = pristine[0]
    assert rec.time_derivation == "LMT_FROM_LONGITUDE"
    assert rec.birth_dt_utc.hour == 9
    assert rec.birth_dt_utc.minute == 58
    assert rec.birth_dt_utc.second == 40


def test_modern_birth_civil_timezone_preserved(tmp_path):
    """Asserts that 1990 Scotland birth retains Civil Time (Europe/London), NOT LMT."""
    test_csv = tmp_path / "test_scotland.csv"
    test_csv.write_text(
        "name,gender,dob,tob,place,latitude,longitude,timezone,birth_time_confidence,source\n"
        "Adam Amie,Female,1990-05-01,13:11,Falkirk Scotland,56.0000,-3.7833,Europe/London,high,Quoted BC/BR\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    assert len(pristine) == 1
    rec = pristine[0]
    assert "CIVIL" in rec.time_derivation
    assert rec.time_derivation != "LMT_FROM_LONGITUDE"


# ── INVARIANT 4: DEATH DISAMBIGUATION ────────────────────────────────────────

def test_death_event_disambiguation():
    """Asserts granular death disambiguation and edge-case protection."""
    # 1. Subject's own demise
    assert disambiguate_death_event("Death of Parent", "Crime : Homicide Victimization 8 July 2022") == "Death of Subject"
    assert disambiguate_death_event("Other", "Death by Heart Attack 22 January 2021") == "Death of Subject"

    # 2. Relatives
    assert disambiguate_death_event("Death of Parent", "Death of Father 20 September 1973") == "Death of Father"
    assert disambiguate_death_event("Other", "Death of Mother 15 August 1985") == "Death of Mother"
    assert disambiguate_death_event("Death of Parent", "Death of Spouse 10 May 2000") == "Death of Spouse"
    assert disambiguate_death_event("Other", "Death of Child 12 June 1960") == "Death of Child"

    # 3. Non-death untouched
    assert disambiguate_death_event("Marriage", "Marriage ceremony") == "Marriage"


# ── INVARIANT 5: AGE PLAUSIBILITY GATES (POSITIVE & FALSE-POSITIVE) ─────────

def test_age_plausibility_gate_quarantines_outliers(tmp_path):
    """Allais Case: Birth 1912 with 'Child Birth' in 2012 (age 100) must be quarantined."""
    test_csv = tmp_path / "test_plausibility.csv"
    test_csv.write_text(
        "name,gender,dob,tob,place,latitude,longitude,timezone,birth_time_confidence,source,event_1_type,event_1_date,event_1_description\n"
        "Émile Allais,Male,1912-01-01,12:00,Paris France,48.8566,2.3522,Europe/Paris,high,Quoted BC/BR,Child Birth,2012-01-01,Birth of child\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    assert len(pristine) == 1
    # The record is retained, but the implausible child birth event is quarantined
    assert len(pristine[0].events) == 0
    assert report.events_quarantined_implausible == 1


def test_plausible_senior_parent_death_survives(tmp_path):
    """Asserts no false positives: Death of Parent at age 85 is physically plausible and preserved."""
    test_csv = tmp_path / "test_valid_parent_death.csv"
    test_csv.write_text(
        "name,gender,dob,tob,place,latitude,longitude,timezone,birth_time_confidence,source,event_1_type,event_1_date,event_1_description\n"
        "Senior Native,Male,1930-01-01,12:00,Paris France,48.8566,2.3522,Europe/Paris,high,Quoted BC/BR,Death of Mother,2015-01-01,Death of mother\n",
        encoding="utf-8",
    )

    engine = DatasetHygieneEngine(test_csv)
    pristine, report = engine.run_hygiene_pipeline()

    assert len(pristine) == 1
    assert len(pristine[0].events) == 1
    assert pristine[0].events[0].event_type == "Death of Mother"
    assert report.events_quarantined_implausible == 0


# ── INVARIANT 6: FAIL-CLOSED RODDEN RATING DERIVATION ────────────────────────

def test_honest_rodden_rating_derivation_fail_closed():
    """Asserts fail-closed rating derivation against source citations."""
    # High confidence official citations
    assert derive_rodden_rating_from_source("BC/BR in hand", "high") == "AA"
    assert derive_rodden_rating_from_source("Quoted BC/BR", "high") == "AA"
    assert derive_rodden_rating_from_source("birth certificate", "high") == "AA"

    # Memory / Bio downgraded honestly
    assert derive_rodden_rating_from_source("From memory", "high") == "A"
    assert derive_rodden_rating_from_source("Bio/autobiography", "high") == "A"

    # Rectified / In question
    assert derive_rodden_rating_from_source("Accuracy in question", "high") == "DD"
    assert derive_rodden_rating_from_source("Rectified from bio", "high") == "DD"

    # Fail-closed on empty/unknown source
    assert derive_rodden_rating_from_source("", "high") == "B"
    assert derive_rodden_rating_from_source("unknown publisher", "high") == "B"


# ── INTEGRATION TEST: PRODUCTION CSV PIPELINE ────────────────────────────────

@pytest.mark.integration
def test_real_csv_loads_and_pipeline_completes():
    """Integration test asserting that the production kundalee_clean.csv runs cleanly."""
    if not RAW_CSV_PATH.exists():
        pytest.skip(f"Dataset not present at {RAW_CSV_PATH}")

    engine = DatasetHygieneEngine(RAW_CSV_PATH)
    pristine, report = engine.run_hygiene_pipeline()

    assert report.total_raw_rows > 50000
    assert report.pristine_records_retained > 40000
    assert report.duplicates_removed > 0
    assert report.coordinates_quarantined > 0
