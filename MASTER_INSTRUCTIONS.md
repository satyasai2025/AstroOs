# AstroOS v2.1.0 "Vistara" — Master Task Instructions
>
> Handoff package for Claude Pro / high-token-limit model.
>
> ---
>
> ## Critical: Read CLAUDE_START_HERE.md FIRST
>
> The file `CLAUDE_START_HERE.md` in the project root is the **entry point** for all AI-assisted development. It overrides any assumptions from earlier conversations.
>
> **Key points from CLAUDE_START_HERE.md:**
> - AstroOS v2.0.0 is GA and frozen
> - Active development is **v2.1.0 "Vistara"**
> - **Local-First, single-user** personal research platform
> - **No Docker, no Kubernetes, no Helm, no cloud, no multi-region, no enterprise infrastructure**
> - Stack: Next.js (Frontend) → FastAPI (Backend) → PostgreSQL (local) → Swiss Ephemeris
> - Redis is optional (JWT denylist only, gracefully disabled if absent)
>
> ---
>
> ## Project Location
>
> All files are at: `C:\Users\rkmau\Downloads\ReplitplusClaude\AstroOS\`
>
> This is a full AstroOS v2.0.0 GA release. The repository contains:
> - `apps/api/` — FastAPI backend
> - `apps/web/` — Next.js frontend
> - `packages/` — shared constants, enums
> - `database/` — SQLAlchemy + Alembic migrations
> - `tests/` — unit + integration tests (1103+ passing)
> - `docs/` — architecture docs
> - `sdks/` — Python + TypeScript SDKs
> - `architecture/` — ADRs, decisions, enterprise library
> - `VISTARA_TASK_PLAN.md` — the task list (below)
>
> ---
>
> ## Workflow Rules
>
> 1. **Always use the repository documents** as authoritative source, not prior chat context
> 2. **Read CLAUDE_START_HERE.md** before any changes
> 3. **No K8s, no Helm, no cloud, no multi-region, no enterprise infrastructure** — those were eliminated
> 4. **Local-first** is the architecture: PostgreSQL on localhost, FastAPI + Next.js local
> 5. **Follow Clean Architecture**: Domain → Repository → Service → Router
> 6. **Never modify business logic** unless explicitly requested
> 7. **Every feature must have tests**
> 8. **Implement one module at a time** — complete before moving on
> 9. **Never continue automatically** — explain architecture, DB, API, folder changes first
> 10. **Always complete one task before moving to the next**
>
> ---
>
> ## Six-Phase Workflow for Each Task
>
> Every task follows this exact workflow:
>
> | Phase | What to do | Success criteria |
> |-------|-----------|-----------------|
> | **Analyze** | Read requirements, review existing code | Requirements understood; plan approved |
> | **Design** | Architecture confirmed with relevant docs | Architecture confirmed |
> | **Build** | Implement the code/files | Implementation complete |
> | **Validate** | Run tests, verify behaviour | All tests/passes |
> | **Govern** | Review against CLAUDE_START_HERE.md, ADRs, quality checks | Security, quality, documentation complete |
> | **Freeze** | No pending changes; ready for next task | Ready to proceed |
>
> ---
>
> ## Task Execution Order (Dependency Chain)
>
> ```
> #1 → #6 → #7 → #8 → #11 → #12 → #13 → #14 → #15
> ```
>
> **Strictly sequential.** Do not skip tasks. Do not start #7 until #6 is frozen.
>
> ---
>
> ## TASK #1: Resolve Open AMP Governance Decisions
>
> **Owner:** Architecture-office
> **Goal:** Close 8 open Architecture Maintenance Proposals (AMPs)
>
> **Location:** `architecture/decisions/AMP-001.md` through `AMP-008.md`
>
> **Steps:**
> 1. Read each AMP file
> 2. For each: decide ACCEPT or REJECT
> 3. If ACCEPT: modify the referenced document per the AMP's recommendation
> 4. Write a resolution report: `architecture/AMP-RESOLUTION-REPORT.md`
> 5. Close the AMP (update status to "Resolved" in the document heading)
>
> **AMPs:**
> - AMP-001: Disaster Recovery presumes Multi Tenancy's "tenant tier" before it exists (Medium)
> - AMP-002: Stale contradictory note in STATUS.md (Low)
> - AMP-003: Disaster Recovery internal ordinal inconsistency ("fourth" vs "fifth") (Low)
> - AMP-004: Semantic Search / Knowledge Graph ordinal drift ("seventh"/"eighth") (Low)
> - AMP-005: Digital Twin cardinal/ordinal phrasing inconsistency (Low/Informational)
> - AMP-006: "Category: enterprise" field does not distinguish roadmap phases (Low)
> - AMP-007: Completion Report undercounts distinct audit-catalog proposals (Informational)
> - AMP-008: Ontology Registry (Module 12) has no approved dependency model (Medium)
>
> **Success:** All 8 AMPs resolved and documented in a report.
>
> ---
>
> ## TASK #6: Documentation & Developer Experience
>
> **Owner:** Engineering-office
> **Goal:** Make the project accessible to new contributors
>
> **Files to update:**
> - `README.md` — verify setup steps match local-first architecture, update version to v2.1.0
> - `docs/` — expand with:
>   - API reference (OpenAPI examples)
>   - Troubleshooting guide for local setup
>   - Contribution guide
> - All public services: add docstrings
> - `scripts/dev.sh` — one-command dev startup script
> - `CLAUDE_START_HERE.md` — verify accuracy
>
> **Success criteria:** A new developer can go from git clone to running app in <30 minutes following the docs.
>
> ---
>
> ## TASK #7: Calculation Accuracy & Precision (Shadbala, Ashtakavarga)
>
> **Owner:** Engineering-office (Backend)
> **Goal:** Implement missing calculation modules
>
> **Files to create/update:**
> - `apps/api/services/shadbala_engine.py` — 6-fold strength calculation
> - `apps/api/services/ashtakavarga_engine.py` — bindu, Sarvashtakavarga
> - `tests/precision/` — precision test suite against ephemeris tables
>
> **Reference:** Swiss Ephemeris for Vedic calculations. Graceful Moshier fallback if `.se1` absent.
>
> **Success criteria:**
> - Planet position within 1 arc-second
> - All Shadbala scores computed (Sthana, Dig, Kala, Cheshta, Naisargika, Drik)
> - Ashtakavarga bindu per house correctly computed
> - Tests passing
>
> ---
>
> ## TASK #8: UI/UX Enhancements
>
> **Owner:** Engineering-office (Frontend)
> **Goal:** Build chart visualizations and improve UX
>
> **Files to create/update:**
> - `apps/web/src/app/charts/` — D1/D9/Vargas chart visualization using D3.js
> - `apps/web/src/components/nakshatra/` — Nakshatra/Pada selector
> - `apps/web/src/components/dasha/` — Dasha timeline visualization
> - `apps/web/src/app/charts/compare/` — Chart comparison page
> - Dark mode toggle in existing components
>
> **Tech stack:** Next.js 15, React 19, TypeScript, TailwindCSS, D3.js
>
> **Success criteria:**
> - Charts render responsive
> - All interactive (hover, click, zoom)
> - Dark mode toggle works (localStorage persisted)
> - Keyboard navigation (ARIA labels)
>
> ---
>
> ## TASK #11: Research Tools
>
> **Owner:** Engineering-office (Research)
> **Goal:** Build research project management features
>
> **Files to create/update:**
> - `apps/web/src/app/research/projects/` — Research Project CRUD UI
> - Snapshot comparison tools
> - CSV/JSON export with knowledge citations
> - Research mode toggle (logs all queries)
> - Hypothesis validation workflow
>
> **Success criteria:**
> - Researcher can create project, capture snapshots, compare versions, export data
> - Research mode logs all queries for reproducibility
>
> ---
>
> ## TASK #12: Enhanced Yoga Detection
>
> **Owner:** Engineering (AI/Knowledge)
> **Goal:** Expand yoga detection capabilities
>
> **Files to create/update:**
> - `apps/api/services/yogas/phase2/` — Phase 2 yoga modules:
>   - Chandra yogas
>   - Nabhasa yogas
>   - Arishta yogas
> - Yoga strength scoring (0-100)
> - Composite yoga detection
> - Yoga activation timeline (Dasha periods)
> - Yoga counter-examples (weakness conditions)
>
> **Success criteria:**
> - 30+ new yoga types detected
> - Strength scoring for each
> - Activation times linked to Dasha timeline
> - 100% test coverage on new code
>
> ---
>
> ## TASK #13: System Quality Gate
>
> **Owner:** QA-office
> **Goal:** Ensure quality across all changes
>
> **Steps:**
> 1. Run full test suite: `PYTHONPATH=. pytest tests/ -v`
> 2. Run precision tests for calculations
> 3. Run UI accessibility tests
> 4. Validate research export functionality
> 5. Log any failures to `TASK_ERRORS.md`
>
> **Success criteria:** 1100+ tests passing, 0 failures, or all failures documented with fix plan
>
> ---
>
> ## TASK #14: Governance Enforcement
>
> **Owner:** Governance Office
> **Goal:** Verify no scope creep
>
> **Steps:**
> 1. Audit all changes against `CLAUDE_START_HERE.md`
> 2. Verify no K8s/Helm/Cloud/infrastructure references introduced
> 3. Confirm ADR compliance
> 4. Write governance compliance report: `architecture/GOVERNANCE_v2_1_AUDIT.md`
>
> **Success criteria:** Zero violations, or all violations documented with remediation plan
>
> ---
>
> ## TASK #15: Release v2.1.0
>
> **Owner:** Release Office
> **Goal:** Prepare and tag v2.1.0 release
>
> **Steps:**
> 1. Update `CHANGELOG.md` with all v2.1.0 features
> 2. Run security scans (Trivy, Bandit via CI)
> 3. Write `RELEASE_NOTES_v2.1.0.md`
> 4. Tag: `git tag v2.1.0`
> 5. Generate `RELEASE_AUDIT_v2.1.0.md`
>
> **Success criteria:** Tag created, release notes written, GA readiness confirmed, changelog updated
>
> ---
>
> ## Orchestrator Execution Logic
>
> ```
> 1. Read this file and VISTARA_TASK_PLAN.md
> 2. Read CLAUDE_START_HERE.md from the project root
> 3. Read README.md and architecture/INDEX.md
> 4. Start with Task #1 (it has no dependencies)
> 5. For each task:
>    a. Explain architecture changes needed
>    b. Explain database changes (if any)
>    c. Explain API changes (if any)
>    d. Explain folder/file changes
>    e. Generate code
>    f. Run relevant tests
>    g. Mark complete
> 6. Move to next task only when current is fully done and frozen
> 7. After Task #15, write PHASE_I_COMPLETION_REPORT.md
> ```
>
> ---
>
> ## Files That Must Be Read Before Starting
>
> 1. `CLAUDE_START_HERE.md` — entry point, must-read
> 2. `README.md` — project overview
> 3. `architecture/INDEX.md` — architecture library table of contents
> 4. `architecture/STATUS.md` — current status of all docs
> 5. `architecture/ROADMAP.md` — governance rules, roadmap
> 6. `CHANGELOG.md` — what changed in v2.0.0
> 7. `VISTARA_TASK_PLAN.md` — this file
>
> ---
>
> *Prepared 2026-07-19 for AstroOS v2.1.0 "Vistara" handoff*