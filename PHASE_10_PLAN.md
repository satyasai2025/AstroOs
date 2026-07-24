# Phase 10 — Architecture Consolidation ("AI Assistant" orchestration layer)

> Status: DRAFT — awaiting Product Owner Approval. No implementation has started.
> Process: Requirements Freeze → Architecture Freeze → Database Freeze → API Contract
> Freeze → Module Contract Freeze → **Product Owner Approval** → Implementation → ...

---

## 1. Requirements Freeze

**Why now:** Per the original roadmap (`ASTROOS_VISION_V3_ROADMAP.md`), Phase 10 was
deliberately sequenced last — "over-architecting against requirements that haven't been
validated yet" was the risk of doing it earlier. Phases 1–9 are now built and have been
live-tested this session (real bugs found and fixed: timezone/tzdata, planet-name casing,
Bhava Chalit house placement, place_name never saved, Dashboard/Recompute state bug, and
the two crash/silent-failure bugs the retroactive review just caught). The individual
pieces have proven themselves — this is the point the roadmap said to do this.

**What "AI Assistant orchestration layer" means today vs. the vision:**
Your original vision doc describes: `AI Assistant → Kundli/Rule/Prediction engines →
Knowledge Graph DB → Visualization Layer`. Today, `WorkflowOrchestrator.analyze()`
(`apps/api/services/workflow_orchestrator.py`) already **functionally** does this job —
it calls the Horoscope, Divisional, Dasha, Yoga, Shadbala, Ashtakavarga, Transit, Rule,
Knowledge, Event, Verification, and Report engines in a fixed sequence and returns one
composed result. What it lacks: it's one large procedural method, not a named,
inspectable, extensible "layer" — you can't ask it "which stages ran," swap a stage,
add a new engine without editing the method body, or (future) have it explain its own
reasoning in natural language.

**In-scope for this phase:**
- R1: Refactor the fixed procedural sequence in `analyze()` into named, independently
  identifiable **stages** (e.g. a `Stage` protocol: name, inputs, outputs, run()), so the
  orchestrator becomes a declared list of stages rather than inline procedural code.
- R2: Add lightweight per-stage tracing (stage name, duration, success/failure) —
  logged, not a new UI — this both serves the long-term "AI Assistant explains its
  reasoning" goal and would have caught the `vargas` NameError bug immediately instead
  of only via manual/agent review.
- R3: Fold in the architecture-review's moderate findings as part of this consolidation,
  since they're exactly the kind of layering cleanup this phase is for:
  - Move `AdminEngine`'s raw session queries behind `UserRepository`, matching every
    other engine's pattern.
  - Route `horoscope.py`'s `list_my_charts`/`delete_chart` through `HoroscopeEngine`
    (or formally document that thin repository-only routers are the intended pattern
    for simple CRUD, and stop claiming otherwise in the file docstring).
  - Fix the two stale "no auth" docstrings (`admin.py`) so they don't mislead a future
    refactor into removing a gate that's actually load-bearing.
  - Eliminate the redundant second `get_or_create()` call in the vargas-persist path by
    threading `chart_id` through instead of re-querying.
  - Wire up the already-written rate limiter (`apps/api/middleware/rate_limit.py`) on
    `POST /workflow/analyze` at minimum — it's dead code today, protecting nothing.

**Explicitly out of scope for this phase** (per the same over-architecting caution):
- No natural-language "AI Assistant" chat interface. Phase 9's "AI Search" is already
  scoped as plain keyword search first.
- No new engines, no new astrological computations.
- No Docker/Kubernetes/Redis, no message queue, no event bus — this stays in-process,
  consistent with the standing local-first / plain-Oracle-VM deployment constraint.

## 2. Architecture Freeze

Proposed shape (subject to your approval, not started):

```
apps/api/services/orchestration/
    stage.py           # Stage protocol (name, run(context) -> context)
    stages/
        chart_stage.py       # wraps HoroscopeEngine.generate_d1
        vargas_stage.py      # wraps DivisionalEngine.compute_all
        dasha_stage.py        # wraps DashaEngine.compute_*
        yoga_stage.py
        shadbala_stage.py
        ashtakavarga_stage.py
        transit_stage.py
        rule_stage.py
        persistence_stage.py  # the get_or_create + persist_all + persist_tree calls
        events_stage.py       # _build_event_analyses, conditional on events existing
        report_stage.py
    pipeline.py         # declares the ordered stage list, runs them, collects tracing
workflow_orchestrator.py   # becomes a thin wrapper: build context from request, run pipeline, map result to WorkflowAnalysisResult
```

This is a **structural refactor of existing logic**, not new logic — every stage's body
is the existing engine call, moved rather than rewritten. Risk is mechanical-error risk
(moving code wrong), not domain-correctness risk.

## 3. Database Freeze

No schema changes required. This phase touches orchestration code only.

## 4. API Contract Freeze

No change to `POST /api/v1/workflow/analyze`'s request or response shape — this is an
internal refactor, contract stays identical. (Rate limiter wiring adds response headers
on throttling, not a contract break — 429 responses are already a documented FastAPI
convention.)

## 5. Module Contract Freeze

- `Stage` protocol: `name: str`, `async def run(self, ctx: PipelineContext) -> PipelineContext`.
- `PipelineContext`: a mutable dataclass carrying everything stages read/write today as
  loose local variables in `analyze()` (chart, vargas, dasha_tree, yoga_results, etc.) —
  effectively promoting the existing tuple-unpacking return value into a named structure.
- No change to any engine's own public interface (`HoroscopeEngine.generate_d1`,
  `DivisionalEngine.compute_all`, etc.) — stages call them exactly as `analyze()` does today.

---

## Open question for Product Owner Approval

Given the explicit "don't over-architect" caution already on record from the original
roadmap, do you want the full stage-based refactor (R1/R2) now, or just the moderate
cleanup items (R3) without the structural refactor? R3 alone is lower-risk, ships faster,
and fixes everything the retroactive review actually flagged as a problem — R1/R2 is
pure architecture investment for a "trace/explain" capability nothing has asked for yet.

**Nothing in this document has been implemented.** Awaiting your decision before
Implementation begins.
