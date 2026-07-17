# Module 8 — Yoga Engine (Phase 3): Implementation Report

**Scope:** Sanyasa Yoga, remaining classical yogas (solar yogas, Amala, Kalasarpa),
plus version-bumped cancellation refinements to two Phase 2 yogas.
**Architecture:** Unchanged from Phase 1/2 (Registry → Predicate → Evaluator, same result model).
**Status:** Complete, tested, coverage-verified.
**Date:** 2026-07-10

---

## 1. What Was Built

8 more yogas registered — **38 total** across all three phases:

| Category | yoga_ids | Count |
|---|---|---|
| Sanyasa Yoga | `BPHS-SY-001`, `BPHS-SY-002` | 2 |
| Solar yogas (Other Major Yoga) | `BPHS-OMY-002/003/004/005` | 4 |
| Amala / Kalasarpa (Other Major Yoga) | `BPHS-OMY-006/007` | 2 |

Plus, distinct from new yogas: **two existing Phase 2 yogas were
refined and version-bumped**, not silently changed.

## 2. Rule Versioning, Actually Exercised

This is the first point in the catalog where the review's own
requirement — "rule_version: 1.0, important for reproducible research if
rules evolve" — gets used for a real evolution, not just declared:

| yoga_id | Change | Old → New version |
|---|---|---|
| `BPHS-CY-004` Kemadruma Yoga | Added cancellation: Moon in a kendra from lagna | 1.0 → 1.1 |
| `BPHS-ARY-003` Shakata Yoga | Added cancellation: Jupiter in kendra from lagna, or Jupiter exalted | 1.0 → 1.1 |

Both were explicitly flagged as base-condition-only in the Phase 2
report, with a tracked deferral to "Phase 3." This closes that specific
deferral — not the complete classical cancellation set for either yoga,
which is noted in both evaluators' docstrings and covered by a
dedicated test each.

**Why this matters concretely:** a chart with an isolated Moon sitting in
a kendra house now evaluates to `is_present=False` under 1.1 where it
would have been `True` under 1.0. Anyone re-running research computed
under 1.0 will see a real, visible difference — exactly the scenario
`rule_version` exists to make legible instead of silently inconsistent.

## 3. Structural Reuse, Not New Logic

The four solar yogas (Vosi, Vasi, Ubhayachari, plus Budhaditya) are the
Sunapha/Anapha/Durudhara/Chandra-Mangala structure from Phase 2, counted
from the Sun instead of the Moon. Same `houses_from()` and
`planets_in_house()` calls, same shape, zero new predicates. This is the
second confirmation (after Phase 2's Chandra Yogas) that building
`houses_from()` as a genuinely reference-point-agnostic primitive in
Phase 1 was the right call.

Kalasarpa Yoga is the second "aggregate, whole-chart" yoga (after the
Nabhasa Ashraya Yogas) — it checks all 7 classical grahas' positions
relative to the Rahu-Ketu axis simultaneously — and it required no
interface changes to fit `evaluate(ctx) -> YogaResult | None`, the same
confirmation the Nabhasa Yogas already provided in Phase 2.

## 4. Verified Live Against Two Different Real Charts

```
Chart 1 (1990-06-15, New Delhi):    12 of 38 yogas present
Chart 2 (1975-12-25, New York):      7 of 38 yogas present
```

Different charts producing different, plausible subsets — not a fixed
or suspiciously identical result set — is itself a basic correctness
signal, checked directly.

## 5. Test Suite

**33 new tests**, all passing:

| File | Tests | Notes |
|---|---|---|
| `test_sanyasa_yoga.py` | 8 | Both formulations; missing-planet handling |
| `test_solar_yogas.py` | 13 | All 4 yogas; confirms the Moon-exclusion rule for Vasi/Vosi; confirms Sun (not lagna) is the reference point |
| `test_other_classical_yogas.py` | 10 | Amala (both reference points), Kalasarpa (both hemispheres, straddling case, missing Rahu/Ketu) |
| Regression additions | 6 | Dedicated cancellation tests for Kemadruma/Shakata, plus updated docstring-content checks and the integration suite's version-number assertions |

**A real behavior change caught 6 pre-existing tests immediately, as
intended.** Adding the Kemadruma/Shakata cancellation logic broke 6
Phase 2 tests whose fixtures happened to place Moon/Jupiter in house 1
(always a kendra) — exactly the auditability payoff the review asked
for: the test suite caught the version's real effect on existing
fixtures immediately, rather than the change passing silently. Fixed by
moving those fixtures to non-kendra houses for the base-condition tests
and adding dedicated tests for the new cancellation paths.

## 6. Coverage

98% overall across all 13 yoga files, 11 of 13 at 100%. `chandra_yoga.py`
(99%) and `other_classical_yogas.py` (99%) have one defensive/unreachable
line each; `neecha_bhanga.py` (88%) is unchanged from Phase 1 — not
touched in this phase.

## 7. Explicit Scope Boundaries (Still Standing)

- **Nabhasa Dala/Akriti/Sankhya sub-categories remain deferred** — not
  revisited in Phase 3. Same reasoning as Phase 2: more cross-text
  variation than is responsibly implementable from recall.
- **Not wired into any router or persistence layer** — consistent with
  every prior phase and `HouseEngine`.
- **Kemadruma/Shakata cancellation logic is now more complete, not
  complete** — one classical exception each was added; others (e.g.
  aspect-based exceptions) remain, and are named as such in both
  evaluators' docstrings.

## 8. Recommendation

All three planned phases of the Yoga Engine are now built: 38 yogas,
631 tests, 98% coverage, live-verified against multiple real charts.
Per your original sequencing, Shadbala is the natural next module —
it will draw on the same Graha/House engines, plus the yoga presence
data this engine now produces, whenever you're ready to start that
design audit.
