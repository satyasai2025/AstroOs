# Jyotish Knowledge Repository — Completion Report

> Final status report for Phase 6 (Conflict Analysis) and the resulting
> freeze of the Knowledge Office.
> Prepared: 2026-07-16

---

## Executive Summary

Phase 6 — Conflict Analysis is **complete**. All previously-documented
conflicts have been reviewed, evidence-checked against the actual
codebase, and linked to their classical sources, the Rule Engine, and
the Ontology. A full-repository survey for undocumented doctrinal
disagreements surfaced 4 additional conflicts, now formally recorded.
The Knowledge Office returns to **Governance Mode**: no further content
changes without a new phase authorization.

Phase 7 (Verse Catalogue) remains **PENDING** and out of scope for this
freeze — see Roadmap.

---

## Phase 6 Results

| Metric | Count |
|---|---|
| Conflicts reviewed (carried over) | 3 |
| Conflicts newly documented | 4 |
| Total conflicts in repository | 7 |
| Resolved | 1 |
| Partially resolved | 4 |
| Unresolved | 2 |
| Conflicts with verified Rule Engine/Ontology cross-references | 7 / 7 |
| Confirmed code/knowledge-base implementation gaps documented | 3 |
| Confirmed code/ontology documentation drift found | 1 |

---

## Conflicts Reviewed and Enriched

| ID | Name | Status | Rule Engine / Ontology Finding |
|---|---|---|---|
| conflict.001 | Lagna vs Bhava 1 (house system) | Partially resolved | Code implements whole-sign Parashari default exactly as recommended (`ephemeris_wrapper.py:684`) |
| conflict.002 | Surya benefic vs malefic | Unresolved | Code implements fixed classical-malefic default (`yoga_predicates.py:49`) but not the dignity-based exception this record recommends documenting |
| conflict.003 | Surya's neutral signs (BPHS vs Phaladeepika) | Resolved | No graha friendship/enmity representation exists anywhere in the Rule Engine or Ontology — confirmed implementation gap, not a knowledge-base error |

## Conflicts Newly Documented

| ID | Name | Status | Key Finding |
|---|---|---|---|
| conflict.004 | Ayanamsa selection (Lahiri/Raman/KP/other) | Partially resolved | Codebase already supports all documented traditions via `AyanamsaSystem` enum and defaults to the recommended Lahiri choice |
| conflict.005 | Rahu/Ketu special aspects (5th/9th) | Partially resolved | Aspect Engine implements the BPHS-extension default; found and flagged a stale Ontology description (`ASPECT-SPECIAL-GRAHA` omits the nodes it actually covers) |
| conflict.006 | Rahu/Ketu exaltation signs (Gemini/Sagittarius vs Taurus/Scorpio) | Partially resolved | Code implements exactly one of three documented traditions (Gemini/Sagittarius) with no alternative path; resolves the "internal inconsistency" flagged but not resolved during Phase 5 |
| conflict.007 | Kaal Sarpa Dosha classical legitimacy | Unresolved | Confirmed zero primary-text citation and zero Rule Engine/Ontology implementation; only 2 of 20 cataloged yogas/doshas share this profile (this one and Sarpadosha) |

---

## Methodology

1. **Reviewed all 3 carried-over conflict records** against current source citations for continued accuracy.
2. **Surveyed the full repository** (catalogues, cross-references, ontology glossary, source registry — 202+ records) with targeted greps for disagreement language ("debated," "disputed," "contradicts," "some traditions," "internal inconsistency") to surface conflicts not yet promoted to formal records.
3. **Cross-checked every conflict against the actual codebase** (`apps/api/domain/`, `apps/api/services/rules/`, `apps/api/services/ontology_registry.py`, `apps/api/services/aspect_engine.py`, `packages/shared/constants.py`, `packages/shared/enums.py`) rather than asserting links from memory — every `cross_references` block in every conflict file cites a real file and line, verified by direct read or grep during this phase.
4. **Resolved where evidence permitted**, deferring to the position the codebase already implements when the knowledge base itself provided no stronger textual reason to prefer the alternative (conflict.001, conflict.004, conflict.006).
5. **Marked unresolved explicitly** where evidence was genuinely split (conflict.002) or where the disagreement is about textual standing rather than content (conflict.007) — no conflict was forced to a resolution the evidence didn't support.
6. **Documented gaps as gaps**, not fabricated links: conflict.003 and conflict.007 both state plainly that no Rule Engine or Ontology implementation exists for the relevant doctrine, rather than inventing a cross-reference to satisfy the linking requirement.

---

## What Was Found (Beyond the Conflict Records Themselves)

| # | Finding | Where | Disposition |
|---|---|---|---|
| 1 | `ASPECT-SPECIAL-GRAHA` ontology entity's description omits Rahu/Ketu despite `aspect_engine.py` implementing node special aspects | `apps/api/services/ontology_registry.py` | Out of Knowledge Office scope — filed as formal cross-office request **ER-001** (see `STATUS.md`), not fixed here |
| 2 | Graha friendship/enmity (conflict.003's subject) has zero Rule Engine or Ontology representation | `apps/api/services/rules/`, `ontology_registry.py` | Documented as an open implementation gap in conflict.003, available for a future engineering phase |
| 3 | Kaal Sarpa Dosha and Sarpadosha are the only 2 of 20 cataloged yogas/doshas with no primary-text citation | `catalogues/yogas/dosha/` | Documented in conflict.007; no catalogue change made (both records remain valid, confidence context added) |

---

## Cross-Reference Validation

- All source refs used in new/edited conflict records (`source.BPHS`, `source.saravali`, `source.traditional`, `source.jaimini-sutras`, `source.brihat-jataka-raman`, `source.kp-system`) verified to exist in `sources/texts/` with matching `id:` fields.
- No duplicate conflict IDs (conflict.001–007, all unique).
- `conflicts/_index.yaml` created (did not previously exist) indexing all 7 records with resolution-status summary.
- Every quantitative claim in each conflict's `cross_references` block (e.g. "only 2 of 20 yogas cite solely `source.traditional`") was verified by direct inspection of the cited files during this phase, not assumed.

---

## Governance

**Knowledge Office status: Governance Mode.**

Phase 6 is frozen. No further edits to `knowledge/conflicts/`,
`knowledge/catalogues/`, `knowledge/cross-references/`,
`knowledge/ontology/`, or `knowledge/sources/` should occur outside a
newly authorized phase.

**Pre-acceptance corrections (2026-07-16):**

1. **ER-001 formalized.** The out-of-scope Ontology fix surfaced by
   conflict.005 was initially suggested as an informal background
   task. Per governance requirement, that channel was replaced with a
   formal cross-office request — **ER-001**, logged in
   `knowledge/STATUS.md`'s "External Requests" section and mirrored in
   `ENGINEERING_STATUS.md`'s "Inbound Requests" section. The prior
   informal suggestion could not be withdrawn (the user had already
   started it as an independent work session before the correction was
   requested); ER-001 is the governance-of-record for that work going
   forward regardless of which channel executes it.

2. **Phase 7 provenance confirmed.** Phase 7 (Verse Catalogue) was
   checked against the pre-migration source roadmap
   (`jyotish-knowledge-base/ROADMAP.md`, prior to the 2026-07-16
   migration into `AstroOS/knowledge/`) and found there verbatim,
   already marked PENDING. It is original approved-roadmap content,
   not introduced during Phase 6, and is retained as documented per
   that verification. It remains the only open item on the roadmap and
   requires separate authorization to begin.

This mirrors the governance pattern already established by the
Engineering, Architecture, and Benchmark offices — see
`ENGINEERING_COMPLETION_REPORT.md` for the sibling report this document
follows in structure.

---

*Report prepared: 2026-07-16*
*Knowledge Office status: Governance Mode*
