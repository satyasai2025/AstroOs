"""
AstroOS — Technique Persistence Integration Test

End-to-end DB round-trip for the generic Technique framework:

    structured JSON  ->  import pipeline  ->  PostgreSQL  (committed)
                     ->  NEW session + cleared registries (= fresh process)
                     ->  reconstruct rules from PG  ->  execute via existing
                         RuleEngine/TechniqueEngine

Acceptance: a persisted technique is executable ENTIRELY from PostgreSQL data,
with NO technique-specific Python module imported. Marriage Timing (unrelated
to Eye Health) proves genericity through the same pipeline.

This test manages its OWN engine bound to TEST_DATABASE_URL (falling back to
DATABASE_URL) and requires the 0021 technique tables to already exist
(`alembic upgrade head`). It deliberately does NOT use the shared
test_engine/db_session fixtures, whose create_all/drop_all would be destructive
against a real database. It cleans up only the rows it creates. Skips when no
database URL is configured.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.domain.facts import Fact
from apps.api.domain.technique import ProvenanceStatus, TriggerStatus
from apps.api.domain.technique_import import SourceType, TechniqueSource
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.technique_import_pipeline import (
    TechniqueImportPipeline,
    ValidationSample,
    persist_import,
)
import apps.api.services.rule_registry as rule_registry_module
import apps.api.services.technique_registry as technique_registry_module

pytestmark = pytest.mark.asyncio

_DB_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
_KEY = "marriage_timing_itest"

_MARRIAGE_PAYLOAD = {
    "technique_id": _KEY,
    "name": "Marriage Timing (integration)",
    "version": 1,
    "tradition": "Parashari",
    "objective": "marriage_timing",
    "source_references": ["integration fixture"],
    "rules": [
        {
            "rule_id": "MARRIT-001", "name": "Venus Mahadasha activation",
            "origin": "explicit", "role": "primary", "priority": 8,
            "conditions": [
                {"type": "condition", "fact_key": "dasha.current_lord",
                 "operator": "eq", "value": "venus", "description": "Venus MD"}
            ],
        },
        {
            "rule_id": "MARRIT-002", "name": "Venus in a kendra (shukra alias)",
            "origin": "explicit", "role": "supporting", "priority": 6,
            "conditions": [
                {"type": "condition", "fact_key": "planet.shukra.house",
                 "operator": "one_of", "value": [1, 4, 7, 10], "description": "Venus kendra"}
            ],
        },
        {
            "rule_id": "MARRIT-003", "name": "Composite (DERIVED)",
            "origin": "derived", "role": "supporting", "priority": 3,
            "conditions": [
                {"type": "condition", "fact_key": "marriage.flag",
                 "operator": "eq", "value": "on", "description": "chained fact"}
            ],
        },
    ],
}


def _facts(**kw) -> FactRegistry:
    reg = FactRegistry()
    for key, value in kw.items():
        reg.add_fact(Fact(key.replace("__", "."), value, "test"))
    return reg


def _assert_disposable_db(url: str) -> None:
    """Refuse to run against a non-disposable database.

    The integration suite's autouse fixtures run AstroBase.metadata.drop_all at
    session teardown. Pointing TEST_DATABASE_URL at the dev database therefore
    WIPES it. This guard hard-fails if the target looks like the app's own DB
    (matches DATABASE_URL, or the database name is not an explicit *_test_db /
    *_test), so a DB-backed test can only ever hit a throwaway database.
    """
    app_url = os.environ.get("DATABASE_URL")
    if app_url and url == app_url:
        pytest.fail(
            "TEST_DATABASE_URL must NOT equal DATABASE_URL — pointing tests at "
            "the app DB would drop_all its tables. Use a disposable DB such as "
            "astroos_test_db."
        )
    db_name = url.rsplit("/", 1)[-1].split("?")[0].lower()
    if not (db_name.endswith("_test_db") or db_name.endswith("_test")):
        pytest.fail(
            f"Refusing to run DB-backed tests against {db_name!r}: the database "
            "name must end in '_test_db' or '_test' (a disposable database). "
            "The integration suite runs drop_all on teardown."
        )


@pytest_asyncio.fixture
async def engine():
    if not _DB_URL:
        pytest.skip("No TEST_DATABASE_URL / DATABASE_URL set; DB round-trip is opt-in.")
    _assert_disposable_db(_DB_URL)
    eng = create_async_engine(_DB_URL)
    # Ensure the 0021 tables exist; skip (don't error) if migrations weren't run.
    async with eng.connect() as conn:
        exists = await conn.scalar(text("SELECT to_regclass('public.techniques')"))
    if not exists:
        await eng.dispose()
        pytest.skip("Technique tables missing — run `alembic upgrade head` first.")
    yield eng
    # cleanup: remove only our rows (cascades to sources + validation cases)
    async with eng.begin() as conn:
        await conn.execute(
            text("DELETE FROM techniques WHERE technique_key = :k"), {"k": _KEY}
        )
    await eng.dispose()


async def test_technique_db_round_trip(engine, monkeypatch):
    Session = async_sessionmaker(engine, expire_on_commit=False)

    # ── clean slate for this key ─────────────────────────────────────────────
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM techniques WHERE technique_key = :k"), {"k": _KEY}
        )

    # ── import (pipeline) ────────────────────────────────────────────────────
    source = TechniqueSource(
        source_type=SourceType.STRUCTURED, reference=_KEY,
        excerpt="integration excerpt", payload=_MARRIAGE_PAYLOAD,
    )
    sample = ValidationSample(
        "venus-dasha-kendra",
        _facts(dasha__current_lord="venus", planet__venus__house=7),
        expect_triggered=True,
    )
    result = TechniqueImportPipeline().run(source, samples=(sample,))
    # normalization ran: shukra -> venus inside the persisted condition
    assert "planet.venus.house" in result.technique.required_inputs

    # ── persist to PostgreSQL and COMMIT ─────────────────────────────────────
    async with Session() as write:
        model = await persist_import(write, result)
        tech_uuid = model.id
        await write.commit()
    assert tech_uuid is not None

    # sources + validation cases landed (verify in an independent connection)
    async with engine.connect() as conn:
        n_src = await conn.scalar(
            text("SELECT count(*) FROM technique_sources WHERE technique_id = :i"),
            {"i": tech_uuid})
        n_val = await conn.scalar(
            text("SELECT count(*) FROM technique_validation_cases WHERE technique_id = :i"),
            {"i": tech_uuid})
    assert n_src == 1
    assert n_val == 1

    # ── simulate a FRESH process: wipe the runtime registries ────────────────
    # Both registries now store entries in a shared Registry helper
    # (services/_registry.py) rather than a bare module-level dict; swap out
    # each one's internal storage the same way the old `_REGISTRY` dicts
    # were swapped.
    monkeypatch.setattr(rule_registry_module._registry, "_items", {})
    monkeypatch.setattr(technique_registry_module._registry, "_items", {})
    assert rule_registry_module.get_rule("MARRIT-001") is None
    assert technique_registry_module.get_technique(_KEY) is None

    # ── reconstruct purely from PostgreSQL in a NEW session ──────────────────
    from apps.api.repositories.technique_repository import TechniqueRepository

    async with Session() as read:
        technique = await TechniqueRepository(read).load_and_register_current(_KEY)
    assert technique is not None

    # rule bodies came back from the DB (no Python module defined them)
    assert rule_registry_module.get_rule("MARRIT-001") is not None
    assert rule_registry_module.get_rule("MARRIT-002") is not None

    # provenance preserved across the round-trip; DERIVED stays DERIVED
    prov = {r.rule_id: r.provenance for r in technique.rule_refs}
    assert prov["MARRIT-001"] is ProvenanceStatus.SOURCE_DERIVED
    assert prov["MARRIT-003"] is ProvenanceStatus.DERIVED

    # ── execute through the untouched engines ────────────────────────────────
    out = TechniqueEngine().execute(
        technique, _facts(dasha__current_lord="venus", planet__venus__house=7)
    )
    triggered = {t.rule_id: t.status for t in out.triggers}
    assert triggered["MARRIT-001"] is TriggerStatus.TRIGGERED
    assert triggered["MARRIT-002"] is TriggerStatus.TRIGGERED
    # derived rule depends on a chained fact not present -> explicit missing data
    assert triggered["MARRIT-003"] is TriggerStatus.INSUFFICIENT_DATA
    assert out.confidence > 0
