# AstroOS API Exposure Assessment

> Follow-up to [FINAL_ENGINEERING_AUDIT.md](FINAL_ENGINEERING_AUDIT.md) §2 ("API surface gap"). Classifies every domain module that currently has **no** `APIRouter` into one of three categories, based on actual import/consumption tracing (not naming guesses). **No routers were added — classification only.**
> Date: 2026-07-16

## Method

For each unrouted `apps/api/domain/*.py` module, I traced:
1. Which service(s) build on its domain objects (`grep` for `domain.<module>` imports).
2. Which of those services are, in turn, called by an already-routed engine (`horoscope_engine`, `divisional_engine`, `dasha_engine`, `event_engine`, `auth_service`).
3. Whether the module produces a self-contained deliverable a client would plausibly request directly (a report, a score, a rendered image, a query result) versus a value that only makes sense as an ingredient inside another module's response.

Two roadmap modules — **Module 5 (Graha Engine)** and **Module 7 (Aspect Engine)** — have no separate domain file at all; their output is embedded directly in `domain/horoscope.py`'s `D1Chart`, which is already served by the Horoscope router. They're excluded from this table because they're already exposed, just not as standalone endpoints.

---

## 1. Intended Internal Services (no router required)

Modules whose entire consumer set is other internal engines. No client-facing deliverable exists independent of the routed response(s) they already feed into.

| Module | File | Confirmed consumers | Why internal |
|---|---|---|---|
| Astronomy Foundation (Module 2) | `domain/ephemeris.py` | `domain/horoscope.py`, `routers/horoscope.py`, `ephemeris_wrapper.py`, `graha_engine.py`, `aspect_engine.py`, `house_engine.py`, all 17 `shadbala/*.py` components, `yoga_predicates.py` | Raw ephemeris value objects (longitude, dignity, retrograde flags). Every routed feature already depends on it transitively; its status is already surfaced via `/api/healthz`. No independent "give me a raw ephemeris reading" client use case. |
| House / Bhava Engine (Module 6) | `domain/house.py` | `house_engine.py` → consumed by `fact_builder.py`, `shadbala/kendradi_bala.py`, `yoga_engine.py`, `yoga_predicates.py` | House cusp/classification data is an ingredient for Yoga, Shadbala, and Fact extraction. It is never requested as an end in itself — house data is only ever meaningful inside a chart, and chart output is already served by Horoscope/Divisional. |

---

## 2. Candidate Public APIs

Modules that produce a distinct, self-contained deliverable a client would plausibly call directly — analogous in kind to the already-routed Horoscope/Divisional/Dasha/Events endpoints. Each has a dedicated `*_engine.py` service designed to be invoked as a unit, not just as a helper called mid-pipeline by something else.

| Module | File | Deliverable | Current reachability |
|---|---|---|---|
| Yoga Engine (Module 8) | `domain/yoga.py` | Detected planetary combinations (yogas) for a chart | **Zero** — not called by any routed engine; only consumed by its own 12 `services/yogas/*.py` implementations and referenced inside `domain/events.py`/`domain/research.py` as an embeddable sub-object |
| Shadbala Engine (Module 9) | `domain/shadbala.py` | Six-fold planetary strength scores | **Zero** — same pattern as Yoga: self-contained engine (17 `services/shadbala/*.py` components), never called by a routed engine |
| Ashtakavarga Engine (Module 10) | `domain/ashtakavarga.py` | Bindu (point) tables per rashi | **Zero** — self-contained engine, never called by a routed engine |
| Transit Engine (Module 11) | `domain/transit.py` | Current planetary transits against a natal chart | **Partial** — already embedded inside Events' `EventAstrologicalContext` via `fact_builder.py`, but there is no way to request transit data *without* going through an event; a standalone "current transits" query is a distinct, common request |
| Timeline Engine (Module 15) | `domain/timeline.py` | Chronological, Dasha-grouped, cluster-annotated view composed from Events | **Zero** direct route — has its own `timeline_engine.py`; natural companion to the existing Events router, same relationship Divisional has to Horoscope |
| Knowledge Engine (Module 20) | `domain/knowledge.py` | Classical text citations, interpretation rules, karakatvas | **Zero** — fully self-contained with its own repository (`knowledge_repository.py`); no other engine reads it. This is the "Knowledge Office" named in the governing mission — currently has no external integration point at all |
| Research Engine (Module 17) | `domain/research.py` | Research projects/experiments/query results over stored chart snapshots | **Zero** direct route, but it is the hub every one of Report, Statistics, and Visualization builds on — this is the "Research Data Office" named in the governing mission |
| Statistics Engine (Module 18) | `domain/statistics.py` | Distributions, cross-tabs, descriptive stats over a research cohort | **Zero** — consumed by `report_engine.py`, `ai_engine.py`, `visualization_engine.py`, but never invoked by a routed engine itself |
| Report Engine (Module 19) | `domain/report.py` | Composed, client-facing report document | **Zero** — the natural top-level deliverable of the Research cluster; consumes Research/Statistics/Timeline/Verification internally but nothing currently calls it from an HTTP request |
| Export Engine (Module 21) | `domain/export_domain.py` | Rendered report exported to CSV/JSON/PDF etc. | **Zero** — consumes `report.py`; needs Report to be reachable first, but is itself a distinct requestable action |
| Visualization Engine (Module 22) | `domain/visualization.py` | Rendered chart/report visualization (image/SVG) | **Zero** — self-contained, single consumer of Research/Statistics/Timeline data for rendering |
| Admin Portal (Module 23) | `domain/admin.py` | System health, user summaries, module registry | **Zero** — needed by any admin UI (e.g. `apps/web`); should be role-gated, not public, but still requires its own router to be usable at all |
| AI Engine (Module 24) | `domain/ai.py` | Template-based natural-language narration with citations | **Zero** — consumes Yoga/Shadbala/Ashtakavarga/Statistics/Verification/Timeline domain objects to generate text; a natural "explain my chart" endpoint |

---

## 3. Supporting Libraries

Cross-cutting substrates that other engines are built *on*, not features a client would call by name. Promoting these to routes would expose implementation detail, not a product capability.

| Module | File | Role | Evidence |
|---|---|---|---|
| Astrology Ontology (Module 12) | `domain/ontology.py` | Reference registry of classical entities/relationships (signs, nakshatras, stable IDs) | Docstring is explicit: *"Module 13 consumes this, it does not define it."* Tracing `ontology_registry.py`'s actual callers found **none** — it is fully built and tested (Module 12 "Complete") but not currently wired into any other service either. Worth a note on its own: this is arguably orphaned internal infrastructure, not merely "used internally." |
| Rule Engine substrate — Facts + Rules (Module 13) | `domain/facts.py`, `domain/rules.py` | `Fact`/`FactRegistry` is, by explicit design, *"the ONLY vocabulary the Rule Engine is allowed to read"*; `Rule`/`Condition` are the declarative data the generic rule evaluator consumes | Confirmed consumed only by `fact_builder.py`, `fact_registry.py`, `rule_engine.py`, and (already routed) `event_engine.py`. Zero standalone client meaning outside that pipeline. |
| Verification Engine (Module 16) | `domain/verification.py` | Maps rule-engine predictions to recorded life events, scoring alignment/evidence strength | Consumed only by `research_engine.py`'s embedded snapshots, `report_engine.py`, `ai_engine.py`, and its own `verification_engine.py`. It is a scoring step inside Research/Report's pipeline, not a deliverable on its own — a client would need a research context (rules + events already loaded) for "verify" to mean anything. |
| SDK & Public API domain objects (Module 25) | `domain/sdk.py` | API versioning, error envelope, pagination schema, SDK config | Explicitly cross-cutting response-shape plumbing meant to be *used by* other routers' responses, not an endpoint itself. Consumed only by `sdk_service.py`. |

---

## 4. Summary Table

| Category | Modules | Count |
|---|---|---|
| Intended internal services | Astronomy Foundation, House/Bhava Engine | 2 |
| Candidate public APIs | Yoga, Shadbala, Ashtakavarga, Transit, Timeline, Knowledge, Research, Statistics, Report, Export, Visualization, Admin Portal, AI Engine | 13 |
| Supporting libraries | Astrology Ontology, Rule Engine (Facts + Rules), Verification, SDK domain objects | 4 |

19 modules assessed (of the ~20 originally flagged as unrouted in the audit — `domain/user.py` is excluded, as it is the Auth module's own domain object and already backs the routed `auth` router).

## 5. Explicitly Not Done

No `APIRouter` was added, modified, or scaffolded for any module in this assessment, per instruction. This is a classification and evidence document only — a candidate list for a future, separately-approved Engineering Request to decide which of the 13 "Candidate public API" modules to wire up, in what order, and behind what auth/versioning scheme.

---

*Assessment performed: 2026-07-16*
