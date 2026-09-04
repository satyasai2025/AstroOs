"""
Unit tests for the VedicAstrology.Wikidot governed knowledge-ingestion fixtures.

These tests are fully offline: they load the static YAML fixtures under
knowledge/sources/vedicastrology_wikidot/ and exercise the existing domain
dataclasses (IngestedDocument, IngestedChunk, SourceReliabilityRecord). No
live DB connection and no network calls are made here.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from apps.api.domain.knowledge_ingestion import DocumentStatus, IngestedChunk, IngestedDocument
from apps.api.domain.knowledge_reliability import (
    ReviewStatus,
    SourceReliabilityTier,
    TechniqueFramework,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_FIXTURE_ROOT = _REPO_ROOT / "knowledge" / "sources" / "vedicastrology_wikidot"
_CONFLICTS_FILE = _REPO_ROOT / "knowledge" / "conflicts" / "vedicastrology_wikidot_conflicts.yaml"

_EXCLUDED_FIXTURES = {"_source.yaml", "validation_requirements.yaml"}

_DISALLOWED_VERIFICATION_STATUSES = {"CANONICAL", "SUPPORTED"}
_DISALLOWED_LIFECYCLE_STATES = {"CANONICAL", "PROMOTED", "VALIDATED"}


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _page_fixture_files():
    assert _FIXTURE_ROOT.is_dir(), f"Fixture directory missing: {_FIXTURE_ROOT}"
    return sorted(p for p in _FIXTURE_ROOT.glob("*.yaml") if p.name not in _EXCLUDED_FIXTURES)


def _all_items():
    items = []
    for fixture_path in _page_fixture_files():
        fixture = _load_yaml(fixture_path)
        for item in fixture.get("items", []) or []:
            items.append((fixture_path.name, item))
    return items


class TestFixturesExistAndParse:
    def test_source_fixture_exists(self):
        source_path = _FIXTURE_ROOT / "_source.yaml"
        assert source_path.is_file()
        fixture = _load_yaml(source_path)
        assert fixture["name"] == "VedicAstrology.Wikidot"
        assert fixture["url"] == "http://vedicastrology.wikidot.com/overview"

    def test_at_least_one_page_fixture_present(self):
        files = _page_fixture_files()
        assert len(files) >= 1, "Expected at least one extracted-page YAML fixture"

    def test_validation_requirements_fixture_exists(self):
        path = _FIXTURE_ROOT / "validation_requirements.yaml"
        assert path.is_file()
        fixture = _load_yaml(path)
        assert "requirements" in fixture
        for req in fixture["requirements"]:
            assert req["status"] == "NOT_YET_BENCHMARKED"


class TestProvenanceRetained:
    """Every extracted item must retain source, source_url, and verification_status."""

    def test_all_items_have_required_provenance_fields(self):
        items = _all_items()
        assert items, "No extracted items found in fixtures"
        for filename, item in items:
            assert item.get("source") == "VedicAstrology.Wikidot", filename
            assert item.get("source_url", "").startswith("http://vedicastrology.wikidot.com"), (
                filename,
                item.get("title"),
            )
            assert item.get("verification_status"), (filename, item.get("title"))
            assert item.get("item_type"), (filename, item.get("title"))
            assert item.get("technique_framework"), (filename, item.get("title"))


class TestNoAutoPromotion:
    """Candidate rules and claims must never be auto-promoted."""

    def test_no_item_marked_canonical_or_supported(self):
        items = _all_items()
        for filename, item in items:
            status = item.get("verification_status", "")
            assert status not in _DISALLOWED_VERIFICATION_STATUSES, (
                f"{filename}: {item.get('title')} has disallowed verification_status={status}"
            )

    def test_no_item_lifecycle_state_beyond_documented_or_unvalidated(self):
        items = _all_items()
        for filename, item in items:
            lifecycle = item.get("lifecycle_state", "DOCUMENTED")
            assert lifecycle not in _DISALLOWED_LIFECYCLE_STATES, (
                f"{filename}: {item.get('title')} has disallowed lifecycle_state={lifecycle}"
            )
            assert lifecycle in {"DOCUMENTED", "UNVALIDATED"}, (
                f"{filename}: {item.get('title')} has unexpected lifecycle_state={lifecycle}"
            )

    def test_rule_items_have_condition_and_conclusion_summaries(self):
        items = _all_items()
        rule_items = [item for _, item in items if item.get("item_type") == "RULE"]
        assert rule_items, "Expected at least one RULE-type extracted item"
        for item in rule_items:
            assert item.get("condition_summary"), item.get("title")
            assert item.get("conclusion_summary"), item.get("title")
            # Rules must never carry executable condition_dsl from this ingestion path.
            assert "condition_dsl" not in item

    def test_unverified_claims_requiring_validation_have_suggested_approach(self):
        items = _all_items()
        flagged = [item for _, item in items if item.get("requires_validation") is True]
        assert flagged, "Expected at least one requires_validation=true item"
        for item in flagged:
            assert item.get("suggested_validation_approach"), item.get("title")
            assert item.get("item_type") in {"UNVERIFIED_CLAIM", "RULE"}, item.get("title")


class TestDomainObjectConstruction:
    """Construct real IngestedDocument/IngestedChunk objects from fixture data and validate them."""

    def test_construct_document_and_chunk_from_first_fixture(self):
        files = _page_fixture_files()
        assert files
        fixture = _load_yaml(files[0])
        items = fixture.get("items", []) or []
        assert items, f"{files[0]} has no items"

        source_id = uuid.uuid5(uuid.NAMESPACE_URL, "VedicAstrology.Wikidot")
        document_id = uuid.uuid5(uuid.NAMESPACE_URL, fixture.get("page_url", files[0].stem))

        document = IngestedDocument(
            document_id=document_id,
            source_id=source_id,
            title=f"VedicAstrology.Wikidot — {fixture.get('page_title', files[0].stem)}",
            language="English/Hindi",
            tradition="Parashari",
            status=DocumentStatus.CHUNKED,
            metadata={"page_url": fixture.get("page_url"), "is_canonical": False},
        )
        assert document.status == DocumentStatus.CHUNKED
        assert document.metadata["is_canonical"] is False

        item = items[0]
        content = f"{item.get('title', '')}\n\n{item.get('claim', '')}".strip()
        chunk = IngestedChunk(
            chunk_id="CHK-TESTFIXTURE-0000",
            document_id=document_id,
            source_id=source_id,
            chapter_section=item.get("section", "general"),
            page_location=fixture.get("page_url", ""),
            passage_reference=item.get("title", "item"),
            chunk_index=0,
            content=content,
            content_hash_sha256=hashlib.sha256(content.strip().encode("utf-8")).hexdigest(),
            technique_framework=TechniqueFramework.PARASHARI,
            is_ai_extracted=True,
        )
        # Must not raise ProvenanceIntegrityError.
        chunk.validate_provenance()
        assert chunk.evidence_level.value == "UNVALIDATED"
        assert chunk.lifecycle_state.value == "DOCUMENTED"


class TestSourceReliabilityYaml:
    def test_tier_is_informal_tradition_and_review_status_unreviewed(self):
        fixture = _load_yaml(_FIXTURE_ROOT / "_source.yaml")
        reliability = fixture["reliability"]
        assert reliability["tier"] == SourceReliabilityTier.INFORMAL_TRADITION.value
        assert reliability["review_status"] == ReviewStatus.UNREVIEWED.value

    def test_note_declares_not_canonical(self):
        fixture = _load_yaml(_FIXTURE_ROOT / "_source.yaml")
        assert "Not canonical" in fixture["note"]


class TestConflictsLogged:
    def test_conflicts_file_exists_and_has_active_disputes(self):
        assert _CONFLICTS_FILE.is_file()
        fixture = _load_yaml(_CONFLICTS_FILE)
        conflicts = fixture.get("conflicts", [])
        assert conflicts, "Expected at least one logged conflict"
        for conflict in conflicts:
            assert conflict["status"] == "ACTIVE_DISPUTE"
            assert conflict["technique_framework"] in {tf.value for tf in TechniqueFramework}
