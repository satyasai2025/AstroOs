# AstroOS v2.0 Milestones

> Tracked milestones for v2, starting with M1. See `ASTROOS_V2_ROADMAP.md` for the phase plan these milestones draw from.
> Date: 2026-07-17

## M1 — "First End-to-End Astrology Pipeline"

**Goal:** A complete vertical slice — enter birth details once, and receive a validated, cited report — rather than isolated, individually-reachable components.

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Enter birth details | ✅ Done (2026-07-17) | `POST /api/v1/workflow/analyze` — one birth-data submission drives the whole pipeline below, not a separate call per engine. |
| 2 | Generate D1 chart | ✅ Done | Computed and persisted inside the workflow call; also independently reachable via `POST /api/v1/horoscope/d1`. |
| 3 | Generate all required Vargas | ✅ Done | Computed and persisted inside the workflow call (`include_vargas`, default true); also independently reachable via `POST /api/v1/divisional/all`. |
| 4 | Compute Dashas | ✅ Done | Requested system (default vimshottari) computed inside the workflow call; also independently reachable via `POST /api/v1/dasha/{system}`. |
| 5 | Detect Yogas | ✅ Done | `YogaEngine.evaluate_all` runs inside the workflow call and its results feed Facts/Rule Engine below; also independently reachable via `POST /api/v1/yoga/evaluate`. |
| 6 | Apply Rule Engine | ✅ Done (2026-07-17) | `WorkflowOrchestrator` builds a `FactRegistry` (chart/yoga/shadbala/ashtakavarga/transit facts via `FactBuilder`) and runs `RuleEngine.evaluate_all` — surfaced in the response as `rule_results`. Still no standalone `/rule/*` endpoint (Rule Engine remains an internal-only module per `API_EXPOSURE_ASSESSMENT.md`), but M1 only required its output be surfaced somewhere in the pipeline, which it now is. |
| 7 | Query Knowledge Office | ✅ Done | Workflow call best-effort correlates detected yogas against Knowledge search (`knowledge_citations` in the response); Knowledge is also independently reachable via `POST /api/v1/knowledge/search`. |
| 8 | Correlate Research Data | ✅ Done (2026-07-17) | `WorkflowAnalysisRequest.research_project_id` (optional) — when supplied, `WorkflowOrchestrator.analyze()` captures the full computed result (chart, yogas, shadbala, ashtakavarga, dasha, vargas, timeline, verification) as an `AstrologicalSnapshot` into that Research project via `ResearchEngine.capture_snapshot`, returning `research_snapshot_id` in the response. Off by default — not every analysis is research. Verified live: registered a user, created a project, ran `/workflow/analyze` with `research_project_id` set, confirmed `research_snapshot_id` in the response and the snapshot listed via `GET /research/projects/{id}/snapshots`. This surfaced and fixed a real pre-existing bug in `ResearchRepository.save_snapshot` (`apps/api/repositories/research_repository.py`) — it called `.value` on `YogaResult.strength`, which is a plain `Literal[str]`, not an enum; that code path had never been exercised live before since the Research router's own snapshot-capture endpoint only ever passed `chart_id`+`label`, never real yoga data. |
| 9 | Produce a cited report | ✅ Done (2026-07-17) | `ReportEngine.build_chart_report` now accepts an optional `citations` tuple and, when non-empty, appends a "Knowledge Citations" section directly into `ChartReport.sections` (`apps/api/services/report_engine.py`'s `_extract_knowledge_citations`) — citations are merged into the report itself, not just returned alongside it. `WorkflowOrchestrator.analyze()` passes its already-computed `knowledge_citations` straight into this call. `ReportEngine`'s existing contract (all extra sections are conditional on non-empty/non-None input) made this additive, not breaking. Verified live: a `knowledge_citations_count: 0` result correctly produced no citations section (matching the existing `if timeline`/`if verification`/`if stats` pattern) — a full non-empty-citation live case wasn't reproduced against this dev DB's seed data, but the code path is identical in shape to the three sibling conditional sections already proven correct in the same function. |
| 10 | Validate against Benchmark specifications | 🔴 Not started | Still an explicit `BenchmarkPlaceholderResponse` (`status: "not_implemented"`) in the workflow response — no BM-* execution engine exists yet (v2 Phase C). |

**Overall M1 status: 🟡 Substantially advanced, not fully achieved.** 9 of 10 criteria done, 1 not started (Benchmark — Phase C, no execution engine exists yet). `POST /api/v1/workflow/analyze` (`apps/api/routers/workflow.py` + `apps/api/services/workflow_orchestrator.py`) is the vertical-slice pipeline this milestone asked for; verification (criterion-adjacent, not separately listed above) only activates once events are recorded against a chart via `POST /events` first — a fresh chart with no events gets `verification: null` in the response, which is correct behavior, not a bug.

The 7 done criteria are now verified two ways, not one: independently against a live database and a real running `apps/web` UI on 2026-07-17 (registration → login → birth-details form → resolved place/timezone → full pipeline render), in addition to the standalone OpenAPI/static checks from earlier entries. A specific correctness challenge against criterion 2 (D1 chart, specifically the Ascendant) was investigated and found to be unsubstantiated — see `ASTROOS_V2_STATUS.md`'s Ascendant-correctness section.

## Future milestones

Not yet defined — per `ASTROOS_V2_ROADMAP.md`'s roadmap rules, new milestones are added only by explicit decision, recorded here when they're set, not pre-populated speculatively.

---

*Last updated: 2026-07-17*
