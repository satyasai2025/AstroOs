"""
Unit tests — Wikidot case-study corpus (Workstream 4).

Validates all 13 JSON fixtures in datasets/wikidot-cases/ for:
- Required top-level fields
- Valid janma_nakshatra (must be a known Nakshatra enum value)
- ISO 8601 event_date format
- Valid life_domain values (including the three new ones added in this pass)
- Confidence tier values
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_CORPUS_DIR = _REPO_ROOT / "datasets" / "wikidot-cases"

_REQUIRED_TOP_FIELDS = {
    "person_name", "chart_id", "source", "confidence_tier",
    "recorded_birth_time", "birth_data", "disclosed_events",
    "wikidot_page_url", "wikidot_extract_ok",
}

_VALID_CONFIDENCE_TIERS = {"A", "B", "C"}

_VALID_LIFE_DOMAINS = {
    "health", "mental_wellbeing", "family", "relationship",
    "career", "finance", "education", "relocation", "legal",
    "spiritual", "power", "transformation", "achievement", "other",
    # Legacy uppercase variants also allowed (raw JSON uses uppercase)
    "HEALTH", "MENTAL_WELLBEING", "FAMILY", "RELATIONSHIP",
    "CAREER", "FINANCE", "EDUCATION", "RELOCATION", "LEGAL",
    "SPIRITUAL", "POWER", "TRANSFORMATION", "ACHIEVEMENT", "OTHER",
}

_VALID_NAKSHATRAS = {
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni",
    "uttara_phalguni", "hasta", "chitra", "swati", "vishakha", "anuradha",
    "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "shravana",
    "dhanishtha", "shatabhisha", "purva_bhadrapada", "uttara_bhadrapada", "revati",
}

_VALID_VALENCES = {"TRIGGER", "CRISIS", "RESIDUAL", "MIXED", "SUPPORTIVE"}


def _all_fixtures():
    assert _CORPUS_DIR.is_dir(), f"Corpus directory missing: {_CORPUS_DIR}"
    return sorted(_CORPUS_DIR.glob("*.json"))


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


class TestCorpusCompleteness:
    def test_exactly_13_fixtures_present(self):
        files = _all_fixtures()
        assert len(files) == 13, (
            f"Expected 13 corpus fixtures, found {len(files)}: {[f.name for f in files]}"
        )

    def test_expected_slugs_present(self):
        expected = {
            "donald_trump.json", "indira_gandhi.json", "narendra_modi.json",
            "arvind_kejriwal.json", "rajiv_gandhi.json", "atal_bihari_vajpayee.json",
            "barack_obama.json", "mahatma_gandhi.json", "jawaharlal_nehru.json",
            "vladimir_putin.json", "nelson_mandela.json", "winston_churchill.json",
            "mao_zedong.json",
        }
        present = {f.name for f in _all_fixtures()}
        missing = expected - present
        assert not missing, f"Missing fixture files: {missing}"


class TestFixtureSchema:
    @pytest.fixture(params=[f.name for f in sorted(Path(
        Path(__file__).resolve().parent.parent.parent.parent.parent / "datasets" / "wikidot-cases"
    ).glob("*.json"))], ids=lambda x: x)
    def fixture_data(self, request):
        path = _CORPUS_DIR / request.param
        return request.param, _load(path)

    def test_required_top_level_fields(self, fixture_data):
        name, data = fixture_data
        missing = _REQUIRED_TOP_FIELDS - set(data.keys())
        assert not missing, f"{name}: missing fields {missing}"

    def test_chart_id_format(self, fixture_data):
        name, data = fixture_data
        chart_id = data.get("chart_id", "")
        assert chart_id.startswith("WKD-"), f"{name}: chart_id must start with WKD-"

    def test_confidence_tier_valid(self, fixture_data):
        name, data = fixture_data
        tier = data.get("confidence_tier", "")
        assert tier in _VALID_CONFIDENCE_TIERS, (
            f"{name}: confidence_tier={tier!r} not in {_VALID_CONFIDENCE_TIERS}"
        )

    def test_birth_data_nakshatra_valid(self, fixture_data):
        name, data = fixture_data
        bd = data.get("birth_data", {})
        nak = bd.get("janma_nakshatra", "").lower()
        assert nak in _VALID_NAKSHATRAS, (
            f"{name}: janma_nakshatra={nak!r} not a valid nakshatra"
        )

    def test_birth_data_pada_range(self, fixture_data):
        name, data = fixture_data
        bd = data.get("birth_data", {})
        pada = bd.get("nakshatra_pada")
        assert pada in {1, 2, 3, 4}, f"{name}: nakshatra_pada={pada!r} must be 1-4"

    def test_birth_data_ayanamsa(self, fixture_data):
        name, data = fixture_data
        bd = data.get("birth_data", {})
        assert bd.get("ayanamsa") == "lahiri", f"{name}: ayanamsa must be 'lahiri'"

    def test_wikidot_url_format(self, fixture_data):
        name, data = fixture_data
        url = data.get("wikidot_page_url", "")
        assert "vedicastrology.wikidot.com" in url, (
            f"{name}: wikidot_page_url missing expected domain"
        )

    def test_disclosed_events_non_empty(self, fixture_data):
        name, data = fixture_data
        events = data.get("disclosed_events", [])
        assert events, f"{name}: disclosed_events must not be empty"

    def test_event_dates_iso_format(self, fixture_data):
        import re
        name, data = fixture_data
        iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for ev in data.get("disclosed_events", []):
            dt = ev.get("event_date", "")
            assert iso_re.match(dt), f"{name}: event_date={dt!r} must be YYYY-MM-DD"

    def test_event_life_domains_valid(self, fixture_data):
        name, data = fixture_data
        for ev in data.get("disclosed_events", []):
            domain = ev.get("life_domain", "")
            assert domain in _VALID_LIFE_DOMAINS, (
                f"{name}: life_domain={domain!r} is not a valid LifeDomain"
            )

    def test_event_valences_valid(self, fixture_data):
        name, data = fixture_data
        for ev in data.get("disclosed_events", []):
            valence = ev.get("valence", "")
            assert valence in _VALID_VALENCES, (
                f"{name}: valence={valence!r} not in {_VALID_VALENCES}"
            )
