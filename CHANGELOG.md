# Changelog

All notable changes to AstroOS are documented here at the release-summary level. For the full, dated, blow-by-blow engineering log (including in-progress work between releases), see `CHANGELOG_V2.md`.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [2.5.0] — 2026-08-26 — "Jyotish Vidya" (Classical Astrological Engines & Governance Freeze)

Major release completing the deep audit, numerical verification against classical treatises (*BPHS*, *Tajika Neelakanthi*, *Jaimini Upadesha Sutras*, *KP Readers*), and complete implementation freeze across 77 core modules with 2,844 passing unit tests.

### Added

- **KP Astrology (Krishnamurti Paddhati) System & Governance:**
  - **Ayanamsa Validation:** Strict governance check enforcing canonical `krishnamurti` ayanamsa and Placidus (`P`) cusps, returning non-blocking warnings on deviation.
  - **Retrograde Ruling Planets (RP):** Classical *KP Reader 4 Ch. 8* rule flagging retrograde RPs for delay/reversal cautions.
  - **Governed Evidence Provenance:** Event evidence steps linked to `technique_framework="KP System"` with classical treatise citations.
  - **Sub-Sub Lord (SSL) Table:** Comprehensive 2193 SSL divisions API (`/kp/ssl-table`).
  - **KP Birth Time Rectification (BTR) & Event Engine:** Multi-candidate rectification scanner and 400+ classical event evaluation catalog.
- **Jaimini Astrology System (*Jaimini Upadesha Sutras*):**
  - **Special Dashas Engine:** Shoola Dasha (9-year longevity/maraka cycle) and Mandooka Dasha (frog-jump progression).
  - **Upapada Deep Analysis:** 2nd/8th house longevity & marital stability engine (`relationship_longevity_score`).
  - **Expanded Classical Jaimini Yogas:** AK-PK Raja Yoga, AmK-DK Commerce Yoga, Srimantah AL-A11, Vipareeta Arudha, and Karakamsha Ketu Moksha.
  - **Predictive Event Timing Engine:** High-probability timing windows across career, marriage, wealth, and health.
- **Mundane Astrology & Geopolitical Forecasting:**
  - **Mundane Ingress Engine:** Chaitra Shukla Pratipada & 4 Cardinal Solar Ingresses (Mesha, Karka, Tula, Makara).
  - **Planetary Cabinet (Nava Nayakas):** 9-minister governance council with planetary friendship weighting.
  - **Mundane Eclipse Engine:** Eclipse detection, totality, path intersection, and duration impact.
  - **Kurma Chakra Engine:** 9-sector celestial tortoise geopolitical & seismic mapping across the Indian subcontinent.
  - **12 Mundane Bhavas Analysis:** Multi-dimensional national stability forecasting.
- **Compatibility & Synastry Engine:**
  - **Kuja Dosha Engine:** Tri-Bhava evaluation (Lagna, Moon, Venus) with 10 classical *pariharas* (cancellations).
  - **Dasa Kuta (10 Poruthams):** South Indian marital compatibility including Rajju & Vedha doshas.
  - **Upapada & D9 Navamsha Synastry:** Cross-chart Jaimini UL and D9 lagna/7th lord mutual harmony.
  - **Composite Chart Engine:** Shortest-arc circular midpoint relationship chart.
- **Varshaphal (Tajaka Annual Chart) System:**
  - **Panchavargiya Bala:** 5-fold Tajika planetary strength & Visheshika scale.
  - **16 Classical Tajika Yogas (Shodasha Yogas):** Ikbala, Induvara, Ithasala, Esharpha, Nakta, Yamaya, etc.
  - **Tajika Dashas:** Patyayini Dasha & Mudda Dasha annual timing.
  - **Varsheshwara & Masa Pravesh:** Year lord algorithm and monthly solar return charts.
- **Governed Knowledge Ingestion & Retrieval (RAG):**
  - **Hybrid Keyword + Semantic Vector Retrieval (RRF):** PostgreSQL full-text search + pgvector with Reciprocal Rank Fusion.
  - **Anti-Contamination Invariant:** Zero AI-generated text enters the authoritative knowledge corpus.
  - **Technique Framework Isolation:** Strict separation of Parashari, Jaimini, KP, Tajika, and Bhrigu Nadi principles.

### Verified & Frozen

- **77 Core Calculation Modules Frozen:** Verified error-free via SHA-256 hash enforcement in `FROZEN_MODULES.md`.
- **Zero-Defect Test Suite:** 2,844 unit & integration tests passing across all astrology domains.

---

## [2.4.0] — 2026-08-19 — "Chandrika" (Phase IV — Real-Time Local Collaboration & Local LLM)

Phase IV of the v2.4.0 release cycle, codenamed "Chandrika". Real-time local-network collaboration and opt-in local LLM inference enrichment, strictly preserving the local-first mandate.

### Added

- **Real-Time Collaboration (Phase IV.2):** ADR-RTC-001 — peer-to-peer WebSocket sync layer with local session coordinator.
  - **mDNS Session Discovery:** `apps/api/services/collab_discovery.py` broadcasts sessions on the LAN using zeroconf. REST management endpoints under `POST /api/v1/collab/sessions`, `DELETE /api/v1/collab/sessions/{session_id}`, `GET /api/v1/collab/sessions/discovered`.
  - **WebSocket Sync Engine:** `apps/api/routers/ws.py` `/ws/session/{session_id}` endpoint with handshake, presence notifications, sync requests/responses, and live operational updates.
  - **E2E AES-256-GCM Encryption:** `apps/api/services/collab_crypto.py` ensures all session frames are end-to-end encrypted with an ephemeral session key.
  - **Operational Transform Engine:** `apps/api/services/ot_engine.py` lightweight OT with version vectors for concurrent conflict-free document updates.
  - **CPU Quota & Sandbox Integration:** Per-device operation throttle (`MAX_PENDING_OPS_PER_PEER = 5`) executed through the shared `WorkerPool` interactive queue.
  - **Feature Gate:** Disabled by default via `ENABLE_RTCOLLAB=false`. Zero cloud relay, zero external network calls.
- **Local LLM Inference (Phase IV.3):** Opt-in enrichment path for natural language narration using locally-hosted models.
  - **Local Model Client:** `apps/api/services/local_llm_client.py` connects to OpenAI-compatible local model servers (e.g. Ollama `http://localhost:11434/v1`, LM Studio).
  - **Deterministic Fallback:** `AIEngine._maybe_enrich` silently falls back to 100% deterministic template-generated output if the local model server is down or times out.
  - **Strict Grounding:** System prompts restrict model rewriting strictly to source astrological facts without hallucinating claims.
  - **RAG Knowledge Retrieval:** `apps/api/services/knowledge_retrieval.py` grounds questions against the local Jyotish knowledge base via semantic embedding search.
  - **Configuration:** `AI_BACKEND` (`template` default / `local_llm` opt-in) in `apps/api/config.py`.
- **Quality Gate & Observability (Phase IV.4):**
  - Prometheus metrics: `rtcollab_active_connections` gauge, `rtcollab_operations_total` counter.
  - SLI/SLO updates in `observability/SLO.md`.
  - Comprehensive unit test suites covering default-off behavior, quota enforcement, LAN isolation, and deterministic fallback.

## [Unreleased] — 2026-08-15 — Divisional Charts Completed to Classical Vedic Parity

### Added

- **Seven new divisional charts (15 → 22 vargas):** D5 Panchamsha, D6 Shashthamsha, D8 Ashtamsha, D11 Rudramsha, plus the composite charts D81 Nava-Navamsha, D108 Ashtottaramsha, and D144 Dwadasamsa². Registered in `apps/api/services/divisional_engine.py`; `chart_type` Postgres enum extended by migration `0023`.
- **Custom D-n and sub-divisional D-m×n tools:** `POST /api/v1/divisional/custom/{n}` and `POST /api/v1/divisional/subdivisional/{a}x{b}`, completing the last two entries of Classical Vedic's divisional-chart menu. Expressed as dynamic codes (`"D13"`, `"D9xD12"`) resolved by a single `_resolve_calculator`, so the existing build/serialise/route pipeline is unchanged. Deliberately not persisted — `divisional_charts.chart_type` is a closed enum and widening it to an open-ended generated set would leave the column unvalidatable.
- Full report (untracked, local): `docs/divisional-charts-completion-report.md`.

### Verification

Every formula was checked against a real Classical Vedic export (2026-08-15, Pune) covering 48 longitudes, rather than trusted from a written source. D6/D8/D11 matched 47/48; D81 and D108 matched 15/15 on both sign and degree; D144 matched 14/15. The shared outlier across all vargas is Varnada Lagna, which Classical Vedic evidently derives differently — not a defect here. D144's single difference is a sign-boundary rounding artefact (0.47°, inside the ±1.2° tolerance implied by arcminute-rounded D1 input amplified 144×).

D81/D108/D144 had no published degree formula at all; composition order was derived empirically. For D108 the order proved load-bearing — `D12-of-D9` matched 15/15 while `D9-of-D12` matched 0/15 — and is now guarded by a regression test.

### Fixed

- **D5 Panchamsha even-sign table was wrong.** The sourced formula stated the even-sign targets were "the odd table reversed" (Libra, Gemini, Sagittarius, Aquarius, Aries). Cross-checking against the Classical Vedic export disproved this; reverse-engineering ~15 independent even-sign data points gave the correct table: Taurus, Virgo, Pisces, Capricorn, Scorpio — the same five planets in reverse order, each in its *other* sign. Caught only because the sourced formula was verified rather than assumed correct.

### Changed

- `"D99"` is no longer an invalid varga code — it now resolves to a custom divisor. Two tests that relied on it raising were retargeted at a structurally unparseable code (`"X99"`).

## [Unreleased] — 2026-08-10 — Dasha Engine Registry & Panel UI

### Added

- **Dasha engine registry + orchestrator:** formalized the six existing dasha systems (Vimshottari, Yogini, Ashtottari, Kalachakra, Chara, Narayana) behind `apps/api/services/dasha_registry.py` / `dasha_orchestrator.py`, mirroring the Jaimini yoga registry pattern — no changes to `DashaEngine`'s math or the `dashas` table. Added `GET /api/v1/dasha/systems`.
- **Dasha Analysis panel split:** `/charts?view=dasha` now has a persistent Dasha System switcher plus Dashboard / Timeline / Tree / Analysis / Event Timing / Reports sub-tabs (`apps/web/src/components/charts/Dasha*.tsx`), matching the architecture diagram's client layer. Reuses existing verified components (`VedhaAnalysisPanel`, `LifeEventTimeline`) rather than duplicating logic. Reports exports a flattened CSV, not JSON.
- Full report: `docs/dasha-engine-registry-and-ui-report.md`. Shoola, Lagna Kala, and KP Vimshottari engines remain deferred.

### Fixed

- **Duplicate `birth_charts` rows on repeated dasha-system switching:** `/dasha/{system}` unconditionally persisted on every call; added an optional `persist: bool = True` field to `DashaRequest` so the new system switcher can request a transient (non-persisted) compute.

## [Unreleased] — 2026-08-08 — Dev Environment

### Fixed

- **Local dev login (`ERR_CONNECTION_REFUSED`):** `apps/web/.env.local` had `NEXT_PUBLIC_API_URL=http://localhost:8000`, but the `api` launch config (`.claude/launch.json`) runs uvicorn on port `8001`. Nothing was listening on 8000, so every auth request failed at the network layer and surfaced as a generic "An unexpected error occurred" in `LoginForm`. Updated `.env.local` to point at `:8001`. This file is gitignored — the fix is local-only, not part of any commit.
- **Stale webpack chunk (`ChunkLoadError` on `/charts/history`):** leftover build manifest in `apps/web/.next` from before the dev server restart pointed the browser at a chunk hash that no longer existed. Cleared `apps/web/.next` and restarted the dev server to regenerate a consistent build.

## [Unreleased] — 2026-07-23 — Bug Fixes & Security

### Fixed

- **AMP-009:** `ReportTemplateEngine._TEMPLATES_DIR` path corrected from `apps/api/templates/reports/` (one directory above project root) to project-root `templates/reports/`. All 8 Jinja2 templates now resolve correctly.
- **AMP-010:** Added new `GET /reports/chart/html` endpoint for standalone HTML report generation, with `text/html` MIME type and `template_name` query parameter for selecting horoscope/career/marriage/health/wealth/spiritual/transit templates.
- **Security:** `dataset_import` router ungated — added `require_researcher` RBAC dependency in `apps/api/main.py` to close the security gap flagged in Phase A objective 4.
- **Documentation:** Removed stale "not yet built" claims in `docs/architecture.md` for Rule Engine, Research Engine, Saptavargaja Bala, Drekkana Bala, and divisional chart dignity computation.

## [2.3.0] — 2026-07-20 — "Lakshmi" (Phase III — Local-First Mobile & Plugins)

Phase III of the v2.3.0 release cycle, codenamed "Lakshmi". Mobile apps,
local plugin architecture, advanced analytics, i18n, and API key management —
all within the local-first mandate. Real-time collaboration deferred; hosted
marketplace replaced with local plugin directory.

### Added

- **AMP Governance (Task 1):** AMP-009 (PDF/CSV report `.model_dump()` bug) and
  AMP-010 (missing report templates directory) resolved. `apps/api/templates/reports/`
  created with 7 Jinja2 templates. PDF/CSV endpoints fixed.
- **Mobile iOS + Android (Tasks 6-8):** React Native app scaffold with cross-platform
  source. Birth chart computation, D1 SVG chart rendering, Dasha timeline with active
  period indicator. Offline-first via AsyncStorage cache with TTL eviction. Push
  notifications optional (feature-flagged). Settings screen for API URL, API key,
  push toggle, cache management. Android project with Hermes, FCM (optional).
  Store submission guide (`docs/mobile-store-submission.md`).
- **Plugin Architecture (Tasks 9-11):** ADR-PLG-001 — local sandbox plugin system.
  `plugins/registry.json` with bundled plugin manifest. `apps/cli/astroos-plugin`
  CLI with list/install/uninstall/scaffold/validate commands. Subprocess sandbox
  with CPU/memory limits. No hosted marketplace, no Stripe, no dev portal.
- **Advanced Analytics (Tasks 14-15):** `apps/api/services/analytics_engine.py` —
  `QueryBuilder` (filter chains: eq/neq/gt/gte/lt/lte/in/between, group-by) and
  `StatisticalEngine` (Pearson correlation, chi-squared test, Welch's t-test,
  Bayes factor BF10). Pure stdlib — zero external dependencies. 18 tests.
- **i18n & Localization (Tasks 16-17):** `apps/api/i18n/loader.py` translation
  loader. 5 languages: Spanish, Hindi, French, German, Arabic (25 keys each).
  No cloud translation API — static JSON files shipped with the app.
- **Public API & Keys (Task 18):** API key authentication as default. OAuth 2.0
  optional (feature-flagged). Rate limiting disabled by default for local-first.
  See `docs/api-key-management.md`.
- **QA Mobile Device Lab (Task 19):** Testing guide covering iOS (iPhone 12-14)
  and Android (Pixel 7, S23, OnePlus 11). Offline-first primary path test scenarios.
- **Security: Plugin Sandbox Audit (Task 20):** Threat model with 6 mitigations.
  Sandbox architecture document. Audit checklist for subprocess-based isolation.
- **Research Data Privacy (Task 21):** `astroos data export/delete/anonymize` CLI
  commands. Local-first privacy tools. No consent management (single-user).
  See `docs/research-data-privacy.md`.


## [2.2.0] — 2026-07-20 — "Arundhati" (Phase II)

Phase II of the v2.2.0 release cycle, codenamed "Arundhati". All features are
local-first — no Kubernetes, Helm, or cloud services.

### Added

- **AMP Governance (Task 1):** All 8 Actionable Maturity Process items resolved
  and closed. Governance audit completed. Full local-first compliance confirmed.
- **Observability & SRE (Task 8, Local-First):** Structured JSON logging with
  W3C `traceparent` correlation IDs (`trace_id`, `span_id`), request/response
  timing spans, Prometheus metrics middleware (`apps/api/observability.py`).
  Native configs for Prometheus, alert rules, and Grafana in `observability/`.
  17 new unit tests.
- **Architecture ADRs — Observability (Task 9):** ADR-OBS-001 (observability
  stack), ADR-OBS-002 (log retention policy), ADR-OBS-003 (trace propagation
  format) in `architecture/adr/`. Incident runbooks in `observability/runbooks/`.
- **SDK Public Release & DX (Task 10):** Python SDK `astroos` 2.2.0 (PyPI-ready:
  twine check passed, py.typed, clean-room wheel import verified) and TypeScript
  SDK `@astroos/sdk` 2.2.0 (npm-ready: dual ESM+CJS+types build verified via
  require/import smoke tests). New `docs/sdk/VERSIONING.md`,
  `docs/sdk/PUBLISHING.md`, Jupyter quickstart in
  `examples/notebooks/astroos_sdk_quickstart.ipynb`. Publishing is a manual,
  credentialed step.
- **Worker Pools & Batch Scaling (Task 11, Local-First):**
  `apps/api/services/worker_pool.py` with CPU/I/O/AI pools, priority queue,
  retry/backoff, dead-letter queue, local queue-depth autoscaling, Prometheus
  metrics. Batch chart-reports API (`POST /api/v1/batch/chart-reports` + poll/
  download/cancel). Job monitoring (`GET /api/v1/jobs`,
  `/jobs/monitor/html`). 20 new tests. Verifed end-to-end against real Swiss
  Ephemeris data.
- **Architecture ADRs — Worker Pools (Task 11):** ADR-WKR-001 (worker pool
  topology), ADR-WKR-002 (broker choice), ADR-WKR-003 (retry policy),
  ADR-WKR-004 (priority routing) in `architecture/adr/`.
- **AI Model Hardening & Calculator Integration (Task 13):** AI tool schema
  hardening, calculator integration into AI tools, hypothesis validation
  service, query log service, research middleware, CSV export improvements.
  Improved error handling across AI-powered features.
- **Developer Documentation & Tooling (Task 14):** Migration guide
  (`docs/migration-v2.1-to-v2.2.md`), developer onboarding guide
  (`docs/developer-onboarding.md`), pre-commit hooks config
  (`.pre-commit-config.yaml` + `docs/pre-commit-setup.md`), VS Code IDE configs
  (`.vscode/extensions.json`, `.vscode/settings.json`), deprecation policy
  (`docs/deprecation-policy.md`). CHANGELOG updated with v2.2.0 entry.

### Changed

- Version updated from 2.1.0 to 2.2.0 for all components.
- Phase II scope amended per user directive: tasks 6/7/18 (Docker, Kubernetes,
  Helm, cloud validation) permanently removed from pipeline. Local-first
  mandate reaffirmed.

### Quality

- No breaking changes to API contract, database schema, or SDK public surface.
- All existing unit, integration, regression, and precision tests pass.
- Worker pools and batch jobs verified end-to-end against real Swiss Ephemeris.
- SDK builds verified: Python `twine check` + clean import, TypeScript dual
  ESM/CJS/types build.

### Known Issues

- **AMP-009 / AMP-010 (carried from Phase F):** PDF and HTML report rendering
  (`ReportTemplateEngine.render_pdf`/`render_html`) do not work. CSV export
  works correctly. Both AMPs are Proposed, not yet approved. See
  `architecture/decisions/`.
- **Premature v2.1.0 documentation in CLAUDE_START_HERE.md:** The "Current
  Version" field still reads v2.1.0. The "Recent Documentation Changes" section
  below it contains the accurate Phase II entries.

## [2.1.0] — 2026-07-19 — "Vistara" (Local-First Enhancement)

Phase I of the v2.1.0 release cycle, codenamed "Vistara". All features are local-first — no Kubernetes, Helm, or cloud services.

### Added

- **Shadbala Engine (Phase I.2):** Full 6-fold planetary strength computation covering Naisargika, Dig, Drik, Chesta, Sthana (Uchcha, Kendradi, Drekkana, Saptavargaja, Ojayugmarasyamsa), and Kala Bala (Paksha, Tribhaga, Ayana, Nathonnata, Dina-Hora, Yuddha) sub-components. All 9 grahas supported.
- **Ashtakavarga Engine (Phase I.2):** Bhinnashtakavarga for all 7 classical grahas, Sarvashtakavarga summation (classical total = 337), Shodhana (Trikona + Ekadhipatya) reduction passes.
- **Swiss Ephemeris Precision (Phase I.2):** Golden-reference precision tests in `tests/precision/` validating planet positions within <1 arc-second. Graceful Moshier polynomial fallback when `.se1` files are absent.
- **D3.js Chart Visualizations (Phase I.3):** North Indian diamond-style chart rendering, interactive Dasha timeline with Mahadasha→Pratyantar countdown, Nakshatra/Pada interactive selector with search.
- **Dark Mode (Phase I.3):** Light/dark theme toggle persisted to `localStorage`. Respects system `prefers-color-scheme`.
- **Research Tools (Phase I.4):** Research project CRUD UI at `/research/projects`, snapshot/version comparison, CSV/JSON export with knowledge citations, research mode toggle (logs all queries for reproducibility), hypothesis validation workflow (flag/confirm/reject AI-generated sources).
- **Yoga Detection Enhancements (Phase I.5):** Phase 2 yogas (Chandra, Nabhasa, Arishta, Sanyasa, Solar, Gajakesari, Neecha Bhanga) added. Strength scoring (0–100) per yoga. Composite/multi-planet/house yoga detection. Activation timeline during Dasha periods. Counter-example (weakness) conditions.
- **Governance Compliance:** All 8 AMPs resolved. Governance audit report generated. Full local-first compliance confirmed.

### Changed

- Version updated from 2.0.0 to 2.1.0.
- Documentation updated for local-first setup: README, API reference, troubleshooting guide, contributing guide, `scripts/dev.sh` launcher.

### Quality

- Precision tests added for planetary positions, Shadbala components, and Ashtakavarga bindus. All existing unit/integration/regression tests pass.
# Changelog

All notable changes to AstroOS are documented here at the release-summary level. For the full, dated, blow-by-blow engineering log (including in-progress work between releases), see `CHANGELOG_V2.md`.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [2.0.0] — 2026-07-19 — General Availability

First stable release of AstroOS as a complete, local-first Vedic Astrology Research Platform. All dependencies pinned, all tests passing, all phases A–H frozen.

### Added
- Local-first architecture with Next.js frontend, FastAPI backend, PostgreSQL database, and Swiss Ephemeris — all running on a single local machine with no external service dependencies for core functionality.
- Unified Analysis Pipeline: `POST /api/v1/workflow/analyze`, connecting the Rule Engine, Knowledge Engine, and Report Engine against real (not placeholder) data.
- Full analysis dashboard frontend (`apps/web/src/app/dashboard/`, `apps/web/src/components/workflow/`) with 10 result panels (Chart, Vargas, Dasha, Yogas, Strength, Transits, Rules, Knowledge, Verification, Report).
- Birth-place search with geocoding + timezone auto-resolution (`/geocode/search`, `/geocode/timezone`), with manual-coordinate override.
- Role-based access control (`require_role`, `require_authenticated`, `require_researcher`, `require_admin`) applied at the router level.
- Research Engine, Benchmark Execution, Knowledge Graph/Citation/Conflict/Explanation engines, AI layer (Chart Comparison, Research Assistant, Hypothesis Generator, Enhanced QA).
- Report generation (Jinja2 + WeasyPrint), PDF/CSV export, 7 report templates.
- Official Python SDK (models, exceptions, client) and TypeScript SDK (Zod schemas).
- Production observability: Prometheus metrics, `/health/live`, `/health/ready`.
- API surface expanded to 116 OpenAPI paths (13 previously-unrouted modules wired into `apps/api/main.py`).

### Fixed / Removed
- Deleted fabricated research datasets `ASTRO-RS-EVENT-v1.0.0` and its three derivatives (`RS-HEALTH`, `RS-WEALTH`, `RS-SPIRITUAL` v0.1.0) — see GD-RDO-001. Note: still present in the already-published `v1.0.0-alpha` tag's history; resolved going forward via a new tag, not a history rewrite (see Governance Audit Phase 5).
- Rotated the RS256 JWT signing key after discovering the previous one was committed to git history in `638f65d`.
- Deduplicated the `RS-COHORT` dataset.

### Fixed (2026-07-19, post-audit resolution pass)
- CI workflow YAML indentation corrected — parses and runs.
- Database migration chain repaired (renumbered `0006_performance_indexes` → `0010`, single linear head).
- TypeScript SDK now builds (added missing `zod` dependency; fixed a masked camelCase/snake_case field-naming bug in the report methods).
- Frontend now typechecks and lints clean (rewrote `ReportExport.tsx` to match the codebase's existing conventions instead of relying on undeclared dependencies; added a missing ESLint flat config).
- Added root `LICENSE` (MIT).
- Pinned all 24 backend dependencies to exact, verified-installed versions.
- Reconciled version numbers — all manifests now read `2.0.0`.

### Fixed (2026-07-19, full test-suite validation pass)
- Ran the complete test suite for real against a live database: 1759 unit/component + 2 integration + 31 regression tests, all passing. Found and fixed 13 real pre-existing bugs surfaced along the way: an async/sync mock mismatch in `AdminEngine` tests, three chart-comparison test fixtures that landed exactly on a similarity-scoring boundary, three natural-language intent-routing gaps in `EnhancedQAResponder` ("strong" vs "strength", "dignities" vs "dignity", unrecognized planet names falling through to the wrong fallback), a hypothesis-ranking bug where `HypothesisGenerator` never used its own `priority` field and could truncate away the most relevant hypothesis, and stale hardcoded rule-count assertions (36 → the real, duplicate-free 47).

### Known Issues (remaining — see `GA_RELEASE_GOVERNANCE_AUDIT.md`)
- Docker production build has not been executed end-to-end — this sandbox has no Docker daemon and no WSL distributions installed at all, not just a missing PATH entry.

## [1.0.0-alpha] — 2026-07-17

- Tagged directly by the repository owner (`d98fd01`). See `ALPHA_RELEASE_READINESS_REPORT.md` and `FOUNDATION_RELEASE_REVIEW.md`'s dated addendum for what this tag does and does not contain.
