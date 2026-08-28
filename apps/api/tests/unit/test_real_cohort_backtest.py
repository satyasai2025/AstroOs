"""
Unit tests for the Real Labeled Cohort Backtest pipeline
(production gate + honest exploratory certification).

Uses the real on-disk corpus at datasets/wikidot-cases/ — no fabricated
birth data. The end-to-end test copies a small subset to tmp to keep
Swiss-Ephemeris calls fast.
"""

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from apps.api.domain.prediction_validation import PredictionCategory
from apps.api.services.real_cohort_backtest import (
    CorpusAudit,
    LIFE_DOMAIN_TO_CATEGORY,
    ProductionGate,
    _research_category,
    load_real_cohort,
    load_research_batch_cohort,
    run_real_cohort_backtest,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = REPO_ROOT / "datasets" / "wikidot-cases"


# ---------------------------------------------------------------------------
# Pure logic (no ephemeris)
# ---------------------------------------------------------------------------


def test_life_domain_mapping_is_documented_and_total():
    assert LIFE_DOMAIN_TO_CATEGORY["POWER"] is PredictionCategory.CAREER
    assert LIFE_DOMAIN_TO_CATEGORY["ACHIEVEMENT"] is PredictionCategory.CAREER
    assert LIFE_DOMAIN_TO_CATEGORY["FAMILY"] is PredictionCategory.MARRIAGE
    assert LIFE_DOMAIN_TO_CATEGORY["WEALTH"] is PredictionCategory.FINANCE
    assert LIFE_DOMAIN_TO_CATEGORY["HEALTH"] is PredictionCategory.HEALTH
    assert LIFE_DOMAIN_TO_CATEGORY["RELOCATION"] is PredictionCategory.RELOCATION


def test_gate_rejects_small_corpus_honestly():
    audit = CorpusAudit(
        files_seen=13,
        charts_built=13,
        verified_outcomes_by_category={"career": 24, "general": 10},
    )
    verdict = ProductionGate().evaluate(audit)
    assert verdict.production_grade is False
    assert verdict.verdict_label == "EXPLORATORY"
    assert any("Insufficient unique charts" in r for r in verdict.reasons)
    assert any("career" in r and "30" in r for r in verdict.reasons)


def test_gate_passes_when_thresholds_met():
    audit = CorpusAudit(
        files_seen=40,
        charts_built=42,
        verified_outcomes_by_category={"career": 60, "marriage": 31},
    )
    verdict = ProductionGate().evaluate(audit)
    assert verdict.production_grade is True
    assert verdict.verdict_label == "PRODUCTION_GRADE"


def test_gate_flags_corpus_with_no_scoreable_outcomes():
    audit = CorpusAudit(files_seen=50, charts_built=50, verified_outcomes_by_category={})
    verdict = ProductionGate().evaluate(audit)
    assert verdict.production_grade is False
    assert any("No verified outcomes" in r for r in verdict.reasons)


# ---------------------------------------------------------------------------
# Real-corpus loader (Swiss Ephemeris)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not CASE_DIR.is_dir(), reason="real corpus not present")
def test_loader_builds_real_cohort_with_audit():
    members, audit = load_real_cohort(CASE_DIR, min_birth_tier="A")
    assert audit.files_seen == len(list(CASE_DIR.glob("*.json")))
    assert audit.charts_built >= 10
    assert len(members) == audit.charts_built

    subject_names = {m.subject_name for m in members}
    assert "Vladimir Putin" in subject_names

    # Verified career outcomes exist and are audited per category.
    assert audit.verified_outcomes_by_category.get("career", 0) >= 10

    # Every chart carries its exact-date outcomes bound to the file chart_id.
    putin = next(m for m in members if m.subject_name == "Vladimir Putin")
    assert all(o.chart_id.startswith("WKD-") for o in putin.outcomes)
    assert any(
        o.observed_date.year == 1999 and o.category is PredictionCategory.CAREER
        for o in putin.outcomes
    )


@pytest.mark.skipif(not CASE_DIR.is_dir(), reason="real corpus not present")
def test_loader_tier_filter_never_silently_passes():
    members, audit = load_real_cohort(CASE_DIR, min_birth_tier="AA")
    # Case-level tiers in this corpus are A/B — an AA-only policy must
    # exclude everything and say why.
    assert members == []
    assert audit.charts_built == 0
    assert len(audit.skipped_charts) == audit.files_seen
    assert all("below AA" in reason for _, reason in audit.skipped_charts)


# ---------------------------------------------------------------------------
# End-to-end on a real subset (2 charts to keep ephemeris work bounded)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not CASE_DIR.is_dir(), reason="real corpus not present")
def test_end_to_end_real_backtest_is_exploratory_graded(tmp_path):
    for fname in ("vladimir_putin.json", "winston_churchill.json"):
        shutil.copy(CASE_DIR / fname, tmp_path / fname)

    bundle = run_real_cohort_backtest(
        case_dir=tmp_path,
        dataset_name="real_subset_smoke",
        target_start=date(1999, 1, 1),
        target_end=date(2001, 6, 30),
        event_types=["job_change"],
    )

    br = bundle.backtest_report
    assert br.total_subjects == 2
    assert br.dataset_name == "real_subset_smoke"
    assert br.total_predictions >= 0
    assert br.cohort_run.temporal_leakage_detected is False

    # 2 charts can never be production-grade — the gate must say so loudly.
    assert bundle.gate_verdict.production_grade is False
    assert bundle.gate_verdict.verdict_label == "EXPLORATORY"
    assert bundle.headline.startswith("[EXPLORATORY]")


# ---------------------------------------------------------------------------
# Impossible-event rejection + research-batch adapter
# ---------------------------------------------------------------------------


def _write_case(tmp_path: Path, name: str, payload: dict) -> None:
    (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")


@pytest.mark.skipif(not CASE_DIR.is_dir(), reason="real corpus not present")
def test_impossible_birth_date_event_is_rejected_not_scored(tmp_path):
    """An event stamped on the birth date (corrupted import signature)
    must be audited and rejected — never counted as an outcome."""
    _write_case(
        tmp_path,
        "poisoned_case.json",
        {
            "person_name": "Poisoned Import",
            "chart_id": "POISON-001",
            "confidence_tier": "A",
            "recorded_birth_time": {
                "date": "1950-01-01",
                "time_utc": "12:00:00",
                "latitude": 28.6139,
                "longitude": 77.2090,
            },
            "disclosed_events": [
                {
                    "event_date": "1950-01-01",  # == birth date — impossible
                    "event_date_precision": "exact_date",
                    "life_domain": "FAMILY",
                    "valence": "TRIGGER",
                    "verification_status": "OFFICIAL_DOCUMENT",
                    "source": "corrupted import",
                },
                {
                    "event_date": "1980-06-15",  # legitimate
                    "event_date_precision": "exact_date",
                    "life_domain": "FAMILY",
                    "valence": "TRIGGER",
                    "verification_status": "OFFICIAL_DOCUMENT",
                    "source": "clean event",
                },
            ],
        },
    )
    members, audit = load_real_cohort(tmp_path)
    assert audit.charts_built == 1
    assert any("event_date==birth_date" in r for _, r in audit.skipped_events)
    member = members[0]
    # Only the legitimate event survived.
    assert len(member.outcomes) == 1
    assert member.outcomes[0].observed_date.year == 1980


def test_research_category_keyword_mapping():
    assert (
        _research_category("Family & Relations / Relationship / Marriage >15 Yrs")
        is PredictionCategory.MARRIAGE
    )
    assert (
        _research_category("Career & Professions / Writers / Fiction")
        is PredictionCategory.CAREER
    )
    assert _research_category("Some Unknown Category") is PredictionCategory.GENERAL


@pytest.mark.skipif(
    not (REPO_ROOT / "data" / "research_batches").is_dir(), reason="batches not present"
)
def test_research_batch_adapter_honestly_yields_empty_on_corrupted_corpus():
    """The 9k-case research batches carry NO ratings and 100% birth-date
    events. The adapter must produce an EMPTY cohort with a full audit —
    not silently score garbage."""
    members, audit = load_research_batch_cohort(
        REPO_ROOT / "data" / "research_batches"
    )
    assert audit.charts_built == 0
    assert members == []
    # Every case was skipped for a documented reason (tier U below A).
    assert len(audit.skipped_charts) > 0
    assert all("below A" in reason for _, reason in audit.skipped_charts)


def test_research_batch_adapter_accepts_clean_case(tmp_path):
    """A corrected record (real rating + real event date) flows through
    the same adapter with zero code changes."""
    _write_case(
        tmp_path,
        "clean_batch.json",
        {
            "cases": [
                {
                    "person": {
                        "name": "Clean Native",
                        "dob": "1960-03-05",
                        "tob": "09:30",
                        "latitude": 19.0760,
                        "longitude": 72.8777,
                        "rodden_rating": "AA",
                    },
                    "life_events": [
                        {
                            "type": "Marriage",
                            "event_date": "1960-03-05",  # poisoned — must reject
                            "category": "Relationship / Marriage",
                            "verified": True,
                        },
                        {
                            "type": "Marriage",
                            "event_date": "1985-11-30",  # legitimate
                            "category": "Relationship / Marriage",
                            "verified": True,
                            "source": "registry record",
                        },
                    ],
                }
            ]
        },
    )
    members, audit = load_research_batch_cohort(tmp_path, min_birth_tier="AA")
    assert audit.charts_built == 1
    assert audit.verified_outcomes_by_category.get("marriage", 0) == 1
    assert len(members[0].outcomes) == 1
    assert members[0].outcomes[0].observed_date.year == 1985



# ---------------------------------------------------------------------------
# AstroDatabank CSV adapter helpers + real-file smoke
# ---------------------------------------------------------------------------

ADB_CSV = Path(r"c:/Users/rkmau/Downloads/astro_data_combined (1).csv")


def test_adb_latlon_parser():
    from apps.api.services.real_cohort_backtest import _parse_adb_latlon

    assert _parse_adb_latlon("45n10") == pytest.approx(45 + 10 / 60, abs=1e-6)
    assert _parse_adb_latlon("9e10") == pytest.approx(9 + 10 / 60, abs=1e-6)
    assert _parse_adb_latlon("23s3006") == pytest.approx(
        -(23 + 30 / 60 + 6 / 3600), abs=1e-6
    )
    assert _parse_adb_latlon("97w09") == pytest.approx(-(97 + 9 / 60), abs=1e-6)
    assert _parse_adb_latlon("garbage") is None


def test_adb_jd_conversion():
    from apps.api.services.real_cohort_backtest import _jd_to_utc_datetime
    from datetime import datetime, timezone as tz

    # JD 2451544.5 == 2000-01-01 00:00 UTC (canonical check value)
    assert _jd_to_utc_datetime(2451544.5) == datetime(2000, 1, 1, tzinfo=tz.utc)


def test_adb_event_segment_parsing():
    from apps.api.services.real_cohort_backtest import _parse_event_segment

    # Full text date
    d, code = _parse_event_segment(
        "Work : Prize  15 June 1903   (Nobel Prize for Physics)", []
    )
    assert d == date(1903, 6, 15)
    assert "Nobel Prize" in code

    # Julian entry prefers the printed Gregorian parenthetical
    d, _ = _parse_event_segment(
        "Death of Child  4 April 1560 Jul.Cal. (14 Apr 1560 greg.)   (Son beheaded)",
        [],
    )
    assert d == date(1560, 4, 14)

    # Year-only text pairs with a structured same-year date
    d, code = _parse_event_segment(
        "Death of Mate  1868   (Husband executed)", [(1868, 5, 12)]
    )
    assert d == date(1868, 5, 12)
    assert code.strip().startswith("Death of Mate")

    # Year-only with no structured match -> partial -> rejected
    assert (
        _parse_event_segment("Relationship : Marriage  1987   (Sherry Williams)", [])
        is None
    )


@pytest.mark.skipif(not ADB_CSV.exists(), reason="AstroDatabank CSV not on disk")
def test_adb_loader_real_smoke_with_limit():
    from apps.api.services.real_cohort_backtest import load_astrodatabank_csv

    members, audit = load_astrodatabank_csv(ADB_CSV, min_birth_tier="A", limit=5)
    assert audit.charts_built >= 3  # first rows include B/C ratings → skipped
    assert len(members) == audit.charts_built

    total_outcomes = sum(len(m.outcomes) for m in members)
    assert total_outcomes >= 1

    # Skips must be documented, never silent.
    reasons = {r for _, r in audit.skipped_charts}
    assert any("below A" in r for r in reasons)


