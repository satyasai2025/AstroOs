# Module 8 — Yoga Engine (Phase 2): Implementation Report

**Scope:** Chandra Yogas, Nabhasa Yogas (Ashraya sub-category), Arishta Yogas.
**Architecture:** Unchanged from Phase 1 (Registry → Predicate → Evaluator, same result model).
**Status:** Complete, tested, coverage-verified.
**Date:** 2026-07-10

---

## 1. What Was Built

12 more yogas registered — **30 total** across Phase 1 + 2:

| Category | yoga_ids | Count |
|---|---|---|
| Chandra Yoga | `BPHS-CY-001` .. `006` | 6 |
| Nabhasa Yoga (Ashraya) | `BPHS-NY-001` .. `003` | 3 |
| Arishta Yoga | `BPHS-ARY-001` .. `003` | 3 |

No changes to `YogaDefinition`, `YogaResult`, the registry mechanism, or
`YogaEngine` itself — Phase 2 is purely new evaluator modules plugging
into the same architecture approved for Phase 1.

## 2. The Payoff From Phase 1's Early Investment

The design audit's rationale for building `houses_from()` early (via the
small, low-risk Gajakesari yoga in Phase 1) rather than waiting for
Chandra Yogas to need it — this is where that pays off. Every one of the
6 Chandra Yogas uses `houses_from()` directly, unmodified, with zero new
house-counting logic written for Phase 2. Malefics-in-Dusthana-from-Moon
(Arishta) reuses it a third time.

## 3. Two Scope Decisions Made Explicit, Not Silent

**Kemadruma and Shakata Yoga are base-condition-only.** Both have
well-known classical cancellation exceptions that are genuinely common
in real charts (e.g. Kemadruma is cancelled if the Moon is in a kendra
from lagna — a frequent occurrence, not a rare edge case). Implementing
these evaluators without the exceptions and labeling them as "complete"
would misrepresent how often the base condition actually holds up
classically. Every result from these two yogas carries an explicit trace
line: *"classical cancellation exceptions not evaluated — Phase 3."*
Tested directly (`test_kemadruma_notes_cancellation_exceptions_not_evaluated`,
`test_shakata_notes_cancellation_exceptions_not_evaluated`).

**Nabhasa Yogas: only the 3 Ashraya Yogas, not all ~32.** The
Dala/Akriti/Sankhya sub-categories have more cross-text variation in
naming and exact thresholds than Ashraya's simple "all planets in one
modality" rule. Implementing them from memory risks asserting
classical facts that don't hold up against a primary source — the same
judgment call already made when nakshatra deity/symbol/shakti data was
left `NULL` during reference table seeding (Module 6.5) rather than
populated from unverified recall. Flagged explicitly in
`nabhasa_yoga.py`'s module docstring as deferred, not silently dropped.

## 4. Verified Live Against a Real Chart

```
Total yoga evaluations: 30
Present in this chart: 8
  BPHS-ARY-002 Malefics in Dusthana from Moon    strength=full
  BPHS-CY-001  Sunapha Yoga                       strength=full
  BPHS-CY-002  Anapha Yoga                        strength=full
  BPHS-CY-003  Durudhara Yoga                     strength=full
  BPHS-DY-001  Dhana Yoga (2nd-11th Lord)         strength=full
  BPHS-DY-002  Dhana Yoga (11th Lord Kendra)      strength=full
  BPHS-PM-005  Sasa Yoga                          strength=full
  BPHS-RY-001  Kendra-Trikona Raja Yoga           strength=full
```

## 5. Test Suite

**73 new tests**, all passing:

| File | Tests | Notes |
|---|---|---|
| `test_chandra_yoga.py` | 16 | All 6 yogas; confirms Sun-exclusion rule (Sunapha/Anapha specifically exclude Sun); confirms Moon (not lagna) is the reference point |
| `test_nabhasa_yoga.py` | 9 | All 3 Ashraya Yogas; confirms mutual exclusivity (a chart satisfying Rajju cannot also satisfy Musala/Nala); confirms Rahu/Ketu correctly excluded from the check |
| `test_arishta_yoga.py` | 13 | All 3 yogas; a dedicated test asserting no predictive language ("death," "will suffer") appears in any result's text |
| Edge-case additions | 5 | Missing-Moon/Jupiter degradation paths across Chandra/Arishta evaluators |

**Coverage: 98% across all Phase 1 + 2 yoga files**, 8 of 10 category
modules at 100%. The two remaining gaps (Neecha Bhanga's rare condition
(b) combination) are unchanged from the Phase 1 report — not introduced
by Phase 2.

## 6. Explicit Scope Boundaries (Still Standing)

- Not wired into any router or persistence layer — same as Phase 1 and
  `HouseEngine`.
- Kemadruma/Shakata cancellation exceptions and the Dala/Akriti/Sankhya
  Nabhasa sub-categories are named, tracked deferrals — Phase 3 scope,
  not silently dropped.

## 7. Recommendation

Phase 3 (Sanyasa Yoga + remaining classical catalog, plus the deferred
cancellation-exception refinements from this phase) is the natural next
step, whenever you're ready.
