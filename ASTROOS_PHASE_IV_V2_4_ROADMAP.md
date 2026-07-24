# AstroOS Phase IV / v2.4.0 Roadmap

**Version:** v2.4.0 — Phase IV
**Codename:** "Chandrika" (proposed — moonlight; a light research pass over what's already built)
**Date:** 2026-07-20
**Status:** DRAFT — awaiting confirmation before any implementation begins
**Predecessor:** v2.3.0 Phase III ("Lakshmi")

---

## Why this roadmap looks different from the old Phase IV/V drafts

The previous `ASTROOS_PHASE_IV_V2_4_ROADMAP.md` and `ASTROOS_PHASE_V_V3_0_ROADMAP.md` were removed on 2026-07-20 (see `CLAUDE_START_HERE.md`'s changelog) as "drafted on old enterprise assumptions." This draft does not resurrect them. Instead it is built from three sources only:

1. **`PHASE_III_LOCAL_FIRST_AUDIT.md`'s own explicit deferral** — real-time collaboration was scoped out of Phase III with a recommendation to revisit in Phase IV, under a reduced, local-network-only design (see below).
2. **A direct repository check**, not assumption — `docs/architecture.md` claims several Shadbala sub-components (Saptavargaja Bala, Drekkana Bala) are "not yet built"; `apps/api/services/shadbala_engine.py` shows they *are* implemented (`SaptavargajaBalaCalculator`, `DrekkanaBalaCalculator`). The documentation is stale relative to the code, not the other way around.
3. **What v2.3.0 actually shipped**, per `CLAUDE_START_HERE.md`'s "What v2.3.0 Includes" table and `docs/api-key-management.md` — used to find the honest edge of what exists today, rather than re-guessing scope.

Nothing here is committed work. Per this project's own governance pattern (see `architecture/ROADMAP.md`'s "Roadmap Rules" and `CLAUDE_START_HERE.md` rule 5, "Explain architectural changes before implementing them"), this document is a proposal for review, not an in-progress task list.

---

## Theme

**Consolidate before extending.** v2.3.0 shipped a wide surface fast (mobile, plugins, analytics, i18n, worker pools, observability, SDKs) via a concurrent build. Phase IV proposes closing documentation/reality gaps first, then taking on exactly one deferred, already-scoped feature (local-network collaboration) rather than opening new fronts.

---

## Proposed Scope

### IV.1 — Documentation & Reality Audit (housekeeping, ~1 week)

**Problem:** `docs/architecture.md` still describes some Shadbala sub-components as unbuilt when they exist in code. If one section is stale, others may be too — this needs a systematic pass, not a spot-fix.

- Audit `docs/architecture.md` section-by-section against current `apps/api/services/` and `apps/api/routers/` — flag every "not yet built / not yet done / not yet scoped" claim, verify against code, correct or remove.
- Cross-check `README.md`'s Module Build Status table and `CLAUDE_START_HERE.md`'s "What v2.3.0 Includes" table against actual routes (`app.openapi()` path list) for drift.
- Verify `tasks_phase2_data.json`/`tasks_phase3_data.json` (if a Phase III equivalent exists) match `ASTROOS_V2_STATUS.md`'s claimed completions — confirm claimed evidence files actually exist (spot-check, not exhaustive).

**Acceptance:** Every "not yet" claim in `docs/architecture.md` is either removed (feature exists) or still accurate (feature genuinely absent) — no stale claims either direction.

### IV.2 — Real-Time Collaboration, Local-Network Only (2–3 weeks)

**Problem:** Deferred from Phase III by its own audit, with a concrete reduced scope already agreed in principle — not a new idea, a pending one.

Per `PHASE_III_LOCAL_FIRST_AUDIT.md`'s recommendation:
- Local-network only (same LAN/localhost) — no relay server, no cloud signaling.
- No OT/CRDT — last-write-wins or explicit lock-based editing on shared research projects (simpler, matches single-user-plus-guests scope).
- No chat, no @mentions.
- Max 2–3 concurrent connections.
- **Disabled by default** — opt-in, feature-flagged, consistent with how mobile push notifications shipped in Phase III.

Candidate mechanism: WebSocket endpoint on the existing FastAPI app (no new service), broadcasting research-project/snapshot changes to connected local-network clients. Reuses existing auth (API keys / JWT), existing research-project domain objects — no new data model beyond a connection registry.

**Acceptance:** Two browsers on the same LAN, both pointed at one `localhost:8000` instance, see each other's research-project edits within ~1s; feature is off unless explicitly enabled; zero external dependency.

### IV.3 — Optional Local LLM Upgrade Path for the AI Engine (exploratory, no default change)

**Problem:** `CLAUDE_START_HERE.md` documents the current AI engine as "Template-based NLG ... deterministic fallback ... (no LLM)" by design. This item does not propose changing that default — it proposes documenting and prototyping an **opt-in** path for users who want richer narration, without making AstroOS depend on a cloud LLM API or any network access by default.

- Research: local inference options that run entirely on the user's machine (e.g. a locally-hosted model server the user runs themselves) versus the existing deterministic templates.
- If pursued: an `AI_BACKEND` setting (`template` default / `local_llm` opt-in), same interface `apps/api/services/ai_engine.py` already exposes, same deterministic-fallback guarantee if the backend is unavailable — mirrors the pattern `ADR-OBS-001` already used for observability's OTel upgrade path (documented, not adopted, until asked for).
- **Explicit non-goal:** no default or required call to any external/cloud AI API. This item needs your confirmation before any code is written — it's the one item here that's a genuine judgment call rather than a gap-fill.

**Acceptance (if approved):** existing deterministic behavior is 100% unchanged when `AI_BACKEND=template` (current default); switching backends is config-only, no router/schema changes.

### IV.4 — Quality Gate (concurrent with IV.1–IV.3)

- Re-run the full test suite after IV.1's doc corrections and IV.2's new WebSocket surface; add regression tests for the collaboration feature specifically (connection limit enforcement, default-off behavior, LAN-only binding).
- Extend `observability/SLO.md` with an SLI for WebSocket connection health if IV.2 proceeds.

---

## Explicitly Out of Scope (carried forward, unchanged)

Everything already ruled out in `CLAUDE_START_HERE.md` remains ruled out: Kubernetes/Helm, cloud deployment, multi-region, hosted plugin marketplace/Stripe, SaaS/multi-tenancy, plugin marketplace, Celery, webhook push notifications as a default, blockchain/crypto, VR/AR. Real-time collaboration under IV.2 is **local-network only** — it does not reopen "SaaS/multi-tenancy" or "hosted" anything.

---

## Dependencies

- IV.1 has no dependencies — pure audit, can start immediately.
- IV.2 depends on IV.1 only insofar as its own new code shouldn't be documented before it exists; otherwise independent.
- IV.3 depends on nothing technically, but is gated on your explicit go-ahead per the non-goal above.
- IV.4 runs after IV.1–IV.3 (or the subset actually approved).

---

## Success Criteria (M4 Definition — draft)

1. Zero stale "not yet built" claims in `docs/architecture.md`.
2. If IV.2 approved: two local-network clients collaborate on a research project with the feature off by default and no external service involved.
3. If IV.3 approved: AI backend is switchable via config only, default behavior provably unchanged.
4. All tests green; no regression in the 2.3.0 baseline.

---

*Status: DRAFT. Nothing in this document authorizes implementation — it is presented for your review and selection of which items (if any) to proceed with.*
