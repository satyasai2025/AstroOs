# AstroOS v2.1.0 "Vistara" — Portable Task Plan
>
> Exported from Cowork session. Share this file with any Claude session (Desktop, Web, VS Code).
> **Critical**: Respect `CLAUDE_START_HERE.md` at all times. No K8s, no Helm, no cloud.
>
> ---
>
> ## Dependencies
>
> Tasks execute **sequentially** in this order. No skipping without explicit approval.
>
> ```
> #1 → #6 → #7 → #8 → #11 → #12 → #13 → #14 → #15
> ```
>
> ---
>
> ## Task 1: Resolve Open AMP Governance Decisions
> **Owner**: Architecture-office &mdash; **Blocks**: #6
>
> Read all 8 AMP files in `architecture/decisions/` (AMP-001 through AMP-008). For each: decide ACCEPT or REJECT, update the referenced document, close the AMP. Write a resolution report to `architecture/AMP-RESOLUTION-REPORT.md`.
>
> ---
>
> ## Task 2: Documentation & Developer Experience (#6)
> **Owner:** Engineering-office &mdash; **Blocks**: #7
>
> 1. Update `README.md` with accurate local-first setup (PostgreSQL, FastAPI, Next.js, Redis optional).
> 2. Expand `docs/` with: API reference (OpenAPI examples), troubleshooting local setup, contribution guide.
> 3. Add docstrings to all public FastAPI services, Pydantic models.
> 4. Create `scripts/dev.sh` to start API + frontend with hot reload.
> 5. Cross-check `CLAUDE_START_HERE.md` accuracy.
>
> **Success: New contributor can set up local dev in <30 minutes.**
>
> ---
>
> ## Task 7: Calculation Accuracy   Precision (Shadbala, Ashtakavarga) (#7)
> **Owner**: Engineering-office &mdash; **Blocks**: #8
>
> 1. Verify Swiss Ephemeris `.se1` integration.
> 2. Implement Shadbala engine (`apps/api/services/shadbala_engine.py`) — 6-fold strength calculation.
> 3. Implement Ashtakavarga engine (`apps/api/services/ashtakavarga_engine.py`) — bindu, Sarvashtakavarga.
> 4. Build precision test suite in `tests/precision/` against verified ephemeris tables.
> 5. Graceful message when `.se1` absent with Moshier fallback warning.
>
> **Success: Planet Position within 1 arc-second. All Shadbala scores computed. Ashtakavarga bindu per house.**
>
> ---
>
> ## Task 8: UI/UX Enhancements (#8)
> **Owner**: Engineering-office (Frontend) &mdash; **Blocks**: #11
>
> 1. Build D1/D9/Vargas chart visualization using D3.js (`/charts` page).
> 2. Interactive Nakshatra/Pada selector with lookup.
> 3. Dasha timeline visualization (Mahadasha → Pratyantar) with countdown.
> 4. Chart comparison page (`/charts/compare` — side-by-side D1 + D9).
> 5. Keyboard navigation (ARIA labels).
> 6. Dark mode toggle (localStorage, persists sessions).
>
> **Success: Charts render responsive. All interactive. Dark mode toggle works.**
>
> ---
>
> ## Task 11: Research Tools (#11)
> **Owner**: Engineering-office (Research) &mdash; **Blocks**: #12
>
> 1. Build Research Project CRUD UI at `/research/projects`.
> 2. Snapshot comparison tools.
> 3. CSV/JSON export with knowledge citations.
> 4. Research mode toggle (logs all queries for reproducibility).
> 5. Hypothesis validation workflow (flag AI-generated sources for confirmation).
>
> **Success: Researcher can create project, capture snapshots, compare versions, export data.**
>
> ---
>
> ## Task 12: Enhanced Yoga Detection (#12)
> **Owner**: Engineering (AI/Knowledge) &mdash; **Blocks**: #13
>
> 1. Implement Phase 2 Yogas: Chandra, NAbhasa, Arishta (in `apps/api/services/yogas/phase2/`).
> 2. Yoga strength scoring 0-100.
> 3. Composite yoga detection (multi-planet/house).
> 4. Yoga activation timeline during Dasha periods.
> 5. Yoga counter-examples (weakness conditions).
>
> **Success: 30+ new yoga types, strength scoring, activation times in timeline. 100 coverage.**
>
> ---
>
> ## Task 13: System Quality Gate (#13)
> **Owner**: QA-office &mdash; **Blocks**: #14
>
> 1. Full test suite after each phase.
> 2. Precision tests for calculations.
> 3. UI accessibility tests.
> 4. Research export validation.
> 5. Maintain 1100+ passing tests.
>
> **Code: run `pytest .` and log to `TASK_ERRORS.md` if any failures.**
>
> ---
>
> ## Task 14: Governance Enforcement (#14)
> **Owner**: Governance Office &mdash; **Blocks**: #15
>
> Verify no K8/Helm/Cloud creep. Audit against `CLAUDE_START_HERE.md`. Confirm ADR compliance. Write governance compliance report to `architecture/GOVERNANCE_v2_1_AUDIT.md`.
>
> **Exit: no violation found or all violations documented with remediation plan.
>
> ---
>
> ## Task 15: Release (#15)
> **Owner**: Release Office — **Final task**
>
> 1. Update `CHANGELOG.md` with each Phase I feature.
> 2. Run security scans (`.github/workflows/ci.yml` + Trivy Bandit).
> 3. Write `RELEASE_NOTES_v2.1.0.md`.
> 4. Tag `v2.1.0` (`git tag v2.1.0`).
> 5. Generate internal audit report (`RELEASE_AUDIT_v2.1.0.md`).
>
> **Done: Tag pushed. Release documented. GA readiness confirmed.**
>
> ---
>
> ## Orchestrator Logic
>
> This agent follows the exact same rules as the Cowork scheduler:
>
> 1. Read the task list above — each has been numbered and described.
> 2. Start at Task 1 (AMP governance). It has no dependencies.
> 3. Execute the task fully, capture the result.
> 4. Move to the next task (Task 6). Repeat Step 3 for each task in order.
> 5. After Task #15, write "PHASE_I_COMPLETION_REPORT.md" — summarize all 9 tasks, their outputs, and any open issues.
> 6. Exit.
>
> **Critical**: Never modify business logic without explicit permission. Always read `CLAUDE_START_HERE.md`. If a task fails, log to `TASK_ERRORS.md` and stop.
>
> ---
>
> ## Metadata passed from Cowork session
>
> - Project: AstroOS v2.1.0 "Vistara"
> - Architecture: Local-First (PostgreSQL localhost, FastAPI + Next.js local)
> - No Kubernetes, no Helm, no cloud, no multi-region
> - Deleted tasks (#2, #3, #4, #5, #9, #10) — they contained removed infrastructure scope
> - Active tasks: #1 (Governance AMPs), #6-#15 (Vistara deliverables)