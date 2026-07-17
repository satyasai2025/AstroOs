# Module 8 — Yoga Engine (Phase 1): Implementation Report

**Scope:** Registry → Predicate → Evaluator architecture (as approved), Phase 1 catalog
(Panch Mahapurusha, Gajakesari, major Dhana Yogas, Kendra-Trikona Raja Yoga, Neecha Bhanga Raja Yoga).
**Status:** Complete, tested, coverage-verified.
**Date:** 2026-07-10

---

## 1. What Was Built

Exactly the architecture reviewed and approved in the Yoga Engine Design
Audit — no architectural deviations. Four additions from the review
feedback are implemented as core parts of the result model, not bolted on:

| Requirement | Where it lives |
|---|---|
| Stable yoga IDs | `YogaDefinition.yoga_id` / `YogaResult.yoga_id` — e.g. `BPHS-PM-001` |
| Rule version | `rule_version` field on both, e.g. `"1.0"` |
| Dependency declaration | `YogaDefinition.requires` — e.g. `("D1", "HouseEngine", "GrahaEngine")` |
| Satisfied/missing + trace | `YogaResult.satisfied` / `.missing` / `.trace` — every yoga evaluated for every chart, present or not |

## 2. Files

```
apps/api/domain/yoga.py                  YogaDefinition, YogaResult
apps/api/services/yoga_predicates.py     Shared vocabulary (houses_from, house_of_lord, is_associated, etc.)
apps/api/services/yoga_registry.py       @register_yoga decorator, all_yogas(), get_yoga()
apps/api/services/yoga_engine.py         YogaEngine — builds context, iterates registry
apps/api/services/yogas/
  ├── panch_mahapurusha.py               BPHS-PM-001..005
  ├── gajakesari.py                      BPHS-OMY-001
  ├── dhana_yoga.py                      BPHS-DY-001, BPHS-DY-002
  ├── raja_yoga.py                       BPHS-RY-001
  └── neecha_bhanga.py                   BPHS-NBRY-001..009
```

18 yogas registered total (5 + 1 + 2 + 1 + 9).

## 3. Two Shared Primitives, Built Once

Per the design audit's own recommendation, two pieces of infrastructure
were deliberately built early rather than per-yoga:

- **`houses_from(reference_house, offset)`** — general N-th-house-from-
  any-reference-point, not a Moon-only special case. Introduced by
  Gajakesari (a small, low-risk yoga) specifically so Phase 2's Chandra
  Yogas can reuse it directly rather than each reinventing "houses from
  Moon" logic.
- **`house_of_lord(ctx, house_number)`** — where a house's ruling planet
  is *currently placed*, not just who the lord is (`HouseEngine` already
  gave "who," this adds "where"). Introduced by Dhana Yoga, reused
  directly by Kendra-Trikona Raja Yoga.

Both are verified working correctly via dedicated predicate unit tests
before any yoga evaluator depends on them.

## 4. Verified Live Against a Real Chart

```
Total yoga evaluations: 18
Present in this chart: 4
  BPHS-DY-001 Dhana Yoga (2nd-11th Lord Association)     strength=full
  BPHS-DY-002 Dhana Yoga (11th Lord in Kendra/Trikona)   strength=full
  BPHS-PM-005 Sasa Yoga                                  strength=full
  BPHS-RY-001 Kendra-Trikona Raja Yoga                   strength=full
```

Sample trace (Kendra-Trikona Raja Yoga, abbreviated):
```
Checking kendra house 7 (lord mars) vs trikona house 5 (lord saturn)
  is_associated(mars, saturn) → True
Final: rule satisfied (1 of 9 pairs matched)
```

This is the shape the review asked for — not just "Raja Yoga: yes," but
exactly which kendra/trikona pair produced it and why, auditable end to
end.

## 5. Test Suite

**69 new tests**, all passing:

| File | Tests | What it covers |
|---|---|---|
| `test_yoga_predicates.py` | 19 | `houses_from`, `is_in_kendra_from`, `house_of_lord`, `is_conjunct`, `is_associated`, `is_exchange`, `exalted_in_sign`, `dispositor_of` |
| `test_panch_mahapurusha.py` | 14 | Each of the 5 sub-yogas independently, own-sign vs exaltation paths, missing-planet handling, trace presence |
| `test_gajakesari.py` | 6 | Kendra-from-Moon (not lagna), full vs partial strength (debilitation/combustion), missing-Moon handling |
| `test_dhana_yoga.py` | 8 | Both formulations, the "same lord for both houses" vacuous-pairing guard |
| `test_raja_yoga.py` | 6 | Multi-pair checking, house-1 self-pairing exclusion, vacuous same-lord pairing exclusion |
| `test_neecha_bhanga.py` | 8 | Each of the 3 cancellation conditions independently, all-conditions-unmet case, dispositor-missing degradation, all 9 planets registered |
| `test_yoga_engine_integration.py` | 8 | Real computed charts, determinism, `evaluate_one`/`evaluate_all` consistency, full-catalog sanity check |

**Bugs found and fixed by the tests themselves, not shipped silently:**
- Neecha Bhanga's trace was incomplete on 2 of 3 conditions' "not found in
  chart" branches — the `missing` list was correct but `trace` silently
  skipped those steps, undermining the exact auditability the review
  asked for. Found by a test, fixed in the evaluator, re-verified.
- Two of my own test assumptions were wrong, not the code: a "full
  strength" Gajakesari test used Jupiter in a debilitated sign by
  accident, and a Raja Yoga substring check matched `"house 1"` inside
  `"house 10"`. Both caught immediately by the failing test, both fixed
  in the test, not the underlying logic.

## 6. Coverage

97% overall across all 10 new files; 7 of 10 at 100%. The two remaining
gaps: `yoga_registry.py`'s `clear_registry()` (a test-only utility,
correctly untested by production-facing tests) and Neecha Bhanga's
condition (b) "exaltation-lord found but doesn't satisfy" branch, which
needs a specifically constructed chart to hit and is a genuinely rare
combination.

## 7. Explicit Scope Boundaries

- **2 Dhana Yoga formulations, 1 Raja Yoga formulation** — not an
  exhaustive BPHS catalog. Phase 1's job was proving the architecture
  end-to-end on the yogas explicitly named in the approved plan, not
  maximizing coverage in one pass.
- **Not wired into any router or persistence layer** — consistent with
  `HouseEngine`'s scope decision in Module 6.5. `YogaEngine` is fully
  usable and tested standalone today; an API endpoint or a `yogas`
  database table is a separate, explicit decision.
- **Phase 2/3 not started** — Chandra Yogas, Nabhasa Yogas, Arishta
  Yogas, Sanyasa Yoga, and the remaining classical catalog remain per the
  approved phased plan.

## 8. Recommendation

Phase 1 is a working, tested foundation with the two costliest shared
primitives (`houses_from`, `house_of_lord`) already proven correct. Phase
2 (Chandra Yogas first, per the design audit's ordering — it extends
`houses_from` directly) is the natural next step whenever you're ready.
