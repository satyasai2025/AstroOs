---
id: AMP-008
title: Ontology Registry (Module 12) has no approved dependency model — contradicts its own docstring and is duplicated by AI Engine
status: Proposed — Awaiting Approval
severity: Medium
source: Engineering Request ER-002 (2026-07-16) — see ONTOLOGY_REGISTRY_INTEGRATION_ASSESSMENT.md
target_documents:
  - apps/api/domain/ontology.py (Module 12)
  - apps/api/domain/facts.py (Module 13)
  - apps/api/services/ai_engine.py (Module 24)
---

# AMP-008: Ontology Registry Has No Approved Dependency Model

## Finding

ER-002 investigated why `apps/api/services/ontology_registry.py` (Module 12, Astrology Ontology) has zero production callers despite being fully built and fully tested — the only module in the 27-module inventory with no internal consumer of any kind (confirmed by direct import trace; see `ONTOLOGY_REGISTRY_INTEGRATION_ASSESSMENT.md`). Two concrete findings from that investigation require an architectural decision, not an engineering one:

1. **Contradictory module intent, both still shipped.** `domain/ontology.py`'s docstring states "Module 13 consumes this, it does not define it" — naming the Rule Engine as Module 12's intended consumer. But `domain/facts.py` (Module 13's own vocabulary definition) states Facts are "the ONLY vocabulary the Rule Engine is allowed to read from... it never sees... any other engine-internal object directly" — a category that includes `OntologyEntity`/`OntologyRelationship` by the same sentence's own logic. Module 13 as built cannot consume Module 12 without violating Module 13's own stated design discipline. No document says which claim is authoritative.

2. **Present, growing duplication.** `apps/api/services/ai_engine.py:27-38` hand-maintains its own `_RASHI_NAMES` list and `_planet_name`/`_rashi_name` capitalize-based helpers — data `OntologyRegistry` already provides canonically, tested, and cross-verified against `packages/shared/constants.py`. Two independently-maintained sources of the same name data can silently diverge.

Per instruction, no code has been changed for either finding. This AMP surfaces the decision; it does not select an option.

## Proposed Correction (Recommendation Only — Not Applied)

Two separate dependency-model decisions are needed. The Architecture Office should decide each independently — they do not need the same answer.

### Decision A — Module 12 ↔ Module 13 (Rule Engine) relationship

- **Option A1 (correct the docstring, close the question):** Remove `domain/ontology.py`'s "Module 13 consumes this" claim. Formally record that the Rule Engine's Facts-only discipline (Module 13, as actually built) supersedes Module 12's earlier stated intent. Ontology remains descriptive/reference infrastructure with no Rule Engine integration, now or planned. Lowest risk, no runtime change, resolves the contradiction by retiring the stale claim.
- **Option B1 (bounded translation, preserve both disciplines):** Have `FactBuilder` — Module 13's sole engine-to-Fact translator — optionally read specific Ontology fields (e.g., dignity relationships, karaka significations) and emit them as ordinary Facts, the same way it already translates `GrahaEngine`/`ShadbalaEngine`/etc. output. This fulfills the original "Module 13 consumes this" intent *through* the Fact layer rather than a direct import, preserving Module 13's "Facts are the only vocabulary" rule while finally giving Module 12 a real consumer. Requires new FactBuilder code and a new ADR/ER once approved.
- **Option C1 (defer, tracked gap):** Leave the contradiction as a documented, tracked gap with no immediate correction — record in governance that Module 13 does not and will not consume Module 12 without further decision, revisit if a concrete rule ever needs ontology-level metadata.

### Decision B — Module 12 ↔ Module 24 (AI Engine) relationship

- **Option A2 (adopt Ontology as AI Engine's name source):** Replace `ai_engine.py`'s hardcoded `_RASHI_NAMES`/`_planet_name`/`_rashi_name` with lookups against `build_default_ontology()`, eliminating the duplication. No architectural conflict analogous to Decision A exists here — AI Engine has no equivalent "only this vocabulary" constraint.
- **Option B2 (leave as-is, accept duplication):** Treat the 21-name overlap as low-risk enough not to warrant a dependency (small, rarely-changing data; introducing a new cross-module import has its own maintenance cost). Record the risk as accepted, not overlooked.

## Impact

- **Runtime code affected if corrected:** `apps/api/domain/ontology.py` (docstring only, under A1/C1) or `apps/api/services/fact_builder.py` + `domain/ontology.py` (new code, under B1) or `apps/api/services/ai_engine.py` (under A2). No frozen architecture document (`architecture/enterprise/*`, ADR-EAL-*) is affected — this AMP concerns runtime module dependency structure, not the Enterprise Architecture Library.
- **Reversibility:** All options are fully reversible — no data migration, no schema change, no external API contract affected (Module 12 has no HTTP route). Option B1 is the only one requiring new code; A1, C1, A2, and B2 are documentation or small, isolated edits.
- **Urgency:** Low. `ontology_registry.py` is correct, tested, and self-verifying against the systems it mirrors — nothing is currently broken. This AMP addresses design-intent clarity and a latent duplication-drift risk, not an active defect.

## Status

Awaiting approval. No file has been modified by this AMP. Per governance workflow: once the Architecture Office selects an option for Decision A and/or Decision B, a new, separately-scoped Engineering Request should be opened to implement the approved design — no implementation should proceed from this AMP directly.
