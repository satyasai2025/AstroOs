# AstroOS Ontology Registry Integration Assessment

> Engineering Request **ER-002 — CLOSED 2026-07-16.** Follow-up to [API_EXPOSURE_ASSESSMENT.md](API_EXPOSURE_ASSESSMENT.md) §3, which flagged `ontology_registry.py`'s zero-caller status as "worth a note on its own... arguably orphaned internal infrastructure." This assessment determines whether Module 12 (Astrology Ontology) is intentionally unused, awaiting future integration, obsolete, or should already be a dependency of another module. **Investigation and classification only — no code changed.** The dependency-model decision this assessment surfaces has been referred to the Architecture Office as **[AMP-008](architecture/decisions/AMP-008-ontology-registry-dependency-model.md)**; no implementation should proceed until that AMP is approved.
> Date: 2026-07-16

## Method

1. Traced actual imports of `OntologyRegistry` / `build_default_ontology` across `apps/`, `tests/`, `packages/` by direct grep — not naming guesses or docstring claims.
2. Read Module 12's own docstring for its stated integration intent.
3. Cross-checked that stated intent against Module 13's (Rule Engine) own scope-defining docstring, since Module 12 names Module 13 as its intended consumer.
4. Searched for `TODO`/`FIXME` markers referencing ontology anywhere in the codebase.
5. Searched sibling "internal Python API only" modules (per API_EXPOSURE_ASSESSMENT.md's 16-module list) for whether *they* have internal callers, to establish whether Module 12's zero-caller status is normal for this codebase's unrouted modules or an outlier.
6. Searched for domain modules that duplicate data the Ontology already provides canonically, as concrete evidence for "should already depend on it" rather than a speculative claim.

---

## 1. Findings — Current State

**Zero production imports, confirmed.** `OntologyRegistry` and `build_default_ontology` (`apps/api/services/ontology_registry.py`) are imported by exactly one file in the entire repository: `tests/unit/test_ontology_registry.py`. No router, no `*_engine.py`, no repository, no other domain module references them.

```
apps/api/services/ontology_registry.py:15:  from apps.api.domain.ontology import OntologyEntity, OntologyRelationship
tests/unit/test_ontology_registry.py:7-8:   (imports OntologyEntity/OntologyRelationship/OntologyRegistry/build_default_ontology)
```

`apps/api/services/fact_registry.py`'s docstring mentions "OntologyRegistry (Module 12)" only as a design-pattern analogy ("same minimal-access discipline as OntologyRegistry — no querying, no inference") — it does not import or call it.

**Not an outlier among unrouted modules — an outlier among *internally uncalled* modules.** API_EXPOSURE_ASSESSMENT.md already established that 16 of 27 modules have no HTTP router. But most of those 16 are still consumed by another internal engine. `fact_builder.py` alone — the Rule Engine's fact-extraction pipeline — imports six of them directly:

```
apps/api/services/fact_builder.py:24-30
  AshtakavargaEngine, FactRegistry, GrahaEngine, HouseEngine, ShadbalaEngine, TransitEngine, YogaEngine
```

Ontology is not among them. It is the only fully-built, fully-tested module in the entire 27-module inventory with **no internal consumer of any kind** — not routed, and not called by any other engine either.

**Fully built.** 12 entity types (Graha, Rashi, Bhava, Nakshatra, Pada, Yoga, Bala, Dasha, Aspect, Karaka, Varga, Event), populated by reusing already-verified data from Module 8 (Yoga Registry), Module 9 (Shadbala Engine), and `packages/shared/constants.py`, rather than asserting new classical facts of its own.

**Fully tested.** 30 unit tests: 8 on `OntologyRegistry`'s storage/lookup mechanics in isolation, 22 on the fully populated default ontology. Notably, 6 of those 22 tests cross-validate the Ontology's data *against* Yoga Registry, Shadbala Engine, and `yoga_predicates` constants (e.g. `test_yoga_count_matches_module_8_registry`, `test_bala_count_matches_shadbala_implemented_components`, `test_no_new_classical_facts_asserted_beyond_existing_constants`). This means the only coupling that currently exists between Ontology and the rest of the system is **test-only and one-directional**: the test suite imports production modules to verify the Ontology mirrors them correctly; no production code imports back.

**No TODO/FIXME markers** reference ontology integration anywhere in `apps/`.

---

## 2. Intent vs. Actual Architecture — A Documented Contradiction

`apps/api/domain/ontology.py`'s module docstring states its own intended relationship to the Rule Engine explicitly:

> "Deliberately NOT a knowledge graph (no Neo4j/RDF/OWL/SPARQL), NOT a query/inference engine, and NOT Rule Engine behavior — **Module 13 consumes this, it does not define it.**"

This is a forward reference: Module 12 was written expecting Module 13 (Rule Engine) to be its consumer.

But `apps/api/domain/facts.py` — Module 13's own definition of the *only* vocabulary it is permitted to read — states a narrower, incompatible scope:

> "A Fact is a single standardized, named value derived from an existing calculation engine's output... This is **the ONLY vocabulary the Rule Engine is allowed to read from**; it never sees a `D1Chart`, a `YogaResult`, a `BalaComponentResult`, **or any other engine-internal object directly**."

An `OntologyEntity` or `OntologyRelationship` is exactly the kind of "engine-internal object" this sentence excludes by name (it is listed alongside `D1Chart`/`YogaResult`/`BalaComponentResult` as the category of thing Facts deliberately abstract away from). Module 13 as actually built — `RuleEngine`, `FactRegistry`, `FactBuilder`, all confirmed via `fact_builder.py`'s import list above — architecturally *cannot* consume Module 12 without violating its own stated single-vocabulary discipline.

**Reading:** this is not a bug in either file. It reads as a later, deliberate architectural decision (Rule Engine → Facts-only, a narrower and more disciplined design than "consume the Ontology directly") that superseded an earlier stated intent (Rule Engine → Ontology) which was written into Module 12's docstring and never updated afterward. Both docstrings are still present and now disagree with each other about Module 13's relationship to Module 12.

---

## 3. Evaluated Against the Four Questions

**1. Is it intentionally unused?**
No evidence supports this. Nothing in the code, tests, or documentation frames Module 12 as a deliberately inert, decorative, or reference-only artifact. Its docstring actively names an intended consumer. `ENGINEERING_INDEX.md` and `ENGINEERING_ROADMAP.md` list it as "✅ Complete" alongside every other module, with no "reference only" or "not for consumption" annotation the way, say, `domain/sdk.py` is explicitly annotated as "cross-cutting response-shape plumbing meant to be used by other routers' responses" (API_EXPOSURE_ASSESSMENT.md §3) — SDK's non-standalone role is stated; Ontology's is not.

**2. Is it awaiting future integration?**
Partially — but the specific integration point it names (Module 13) is now architecturally closed off by Module 13's own later, narrower design (§2 above). It is better described as a **stalled/superseded integration** than an actively-awaited one: the plan referenced in its own docstring did not happen, and the module that was supposed to consume it evolved a design that structurally excludes it.

**3. Is it obsolete?**
No. It has not been superseded by newer code, it passes its full test suite, and it continues to accurately mirror the systems it describes (Yoga Registry, Shadbala Engine, `packages/shared/constants.py`) — its own tests would fail if it drifted out of sync with any of them, which is the actual signature of obsolescence. "Complete but unconsumed" is a different condition than "outdated."

**4. Should another module already depend on it?**
Yes, concretely. `apps/api/services/ai_engine.py` (Module 24) maintains its own hardcoded name table and formatting helpers:

```python
# apps/api/services/ai_engine.py:27-38
_RASHI_NAMES = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

def _planet_name(p: str) -> str:
    return p.capitalize()

def _rashi_name(r: str) -> str:
    return r.capitalize()
```

This duplicates, by hand, exactly the canonical name data `OntologyRegistry.get_entity("RASHI-ARIES").name` / `GRAHA-SUN.name` already provide — data that is already built, already tested, and already verified consistent with the same `packages/shared` constants AI Engine's own list was presumably copied from. This is a present, concrete duplication risk (two independently-maintained sources of the same 21 names that could silently diverge if either list is ever edited without the other), not a hypothetical one. No other unrouted module (`knowledge_engine.py`, `knowledge_repository.py`, `report_engine.py`) was found duplicating Ontology data this directly.

---

## 4. Recommendation and Routing

Per this Engineering Request's scope, this is a classification and evidence document only — no code was changed to `ontology_registry.py` or `ai_engine.py`, and none should be until a governance decision is made. This is not an engineering decision to make unilaterally: it is a dependency-model question between two already-approved module designs (Module 12 and Module 13's Facts-only discipline), which is the Architecture Office's domain.

**Routing:** ER-002 is closed with this document as its deliverable. The two decisions below have been filed as **AMP-008** (`architecture/decisions/AMP-008-ontology-registry-dependency-model.md`) for the Architecture Office to decide:

1. **Reconcile the two conflicting docstrings** — `domain/ontology.py`'s "Module 13 consumes this" claim vs. `domain/facts.py`'s Facts-only exclusivity claim. AMP-008 presents three options (correct the docstring and close the question / build a bounded FactBuilder translation path / defer as a tracked gap) without selecting one.
2. **Module 24 (AI Engine)'s duplication of `_RASHI_NAMES`/`_planet_name`/`_rashi_name`** — AMP-008 presents adopting Ontology as the canonical source vs. accepting the duplication as low-risk, without selecting one.
3. **No urgency to delete or deprecate Module 12.** It is correct, low-maintenance, self-verifying infrastructure. The finding here is "unintegrated," not "unnecessary" — removing it would not simplify anything, since its 30 tests are the only thing currently confirming Yoga/Shadbala/constants haven't silently drifted apart from each other.

**Only once the Architecture Office selects an option in AMP-008** should a new, separately-scoped Engineering Request be opened to implement the approved design.

---

## Summary

| Question | Answer |
|---|---|
| Intentionally unused? | **No** — nothing marks it as reference-only; its own docstring names an intended consumer |
| Awaiting future integration? | **Partially** — its named integration point (Module 13) is architecturally closed off by Module 13's own later Facts-only design |
| Obsolete? | **No** — current, fully tested, and self-verifying against the systems it describes |
| Should another module already depend on it? | **Yes** — Module 24 (AI Engine) concretely duplicates data it already provides (`ai_engine.py:27-38`) |

---

*Assessment performed: 2026-07-16 in response to ER-002.*
