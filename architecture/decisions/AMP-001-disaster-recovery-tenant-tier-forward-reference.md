---
id: AMP-001
title: Disaster Recovery presumes Multi Tenancy's "tenant tier" before it exists
status: CLOSED — ACCEPTED (Option C, defer as tracked gap) — 2026-07-19
severity: Medium
source: Architecture Library Validation Audit (2026-07-15)
target_documents:
  - enterprise/disaster-recovery.md (ADR-EAL-029)
  - enterprise/multi-tenancy.md (ADR-EAL-021)
---

# AMP-001: Disaster Recovery's Tenant-Tier Forward Reference

## Finding

Disaster Recovery's reuse map (§1) and goals (§2) state that RTO/RPO targets "may vary by tenant tier" and that DR "reads Multi Tenancy's existing tenant construct." Multi Tenancy's own frozen document (§18) lists "Tenant tiering" as a **future refinement, not yet built** — "a future refinement distinguishing tenant tiers... building on the Tenant Registry's lifecycle state rather than a new mechanism." No tier field exists on the Tenant Registry today. Disaster Recovery presumes a construct its cited source document explicitly defers.

## Proposed Correction (Recommendation Only — Not Applied)

One of the following, to be decided by governance, not by this AMP:

- **Option A (documentation-only fix):** Soften Disaster Recovery's language to make the dependency conditional and explicit — e.g., "RTO/RPO targets may optionally vary by tenant tier, if and when Multi Tenancy implements tenant tiering (Multi Tenancy §18); until then, RTO/RPO targets are flat across all tenants." This requires a new ADR superseding ADR-EAL-029 (Disaster Recovery is frozen) to make the edit.
- **Option B (build the dependency):** Prioritize implementing Multi Tenancy's tenant tiering (already flagged as its own future evolution item) via a new ADR superseding ADR-EAL-021, so Disaster Recovery's existing language becomes accurate rather than aspirational.
- **Option C (defer):** Accept the forward reference as a known, tracked gap requiring no immediate document change, provided it is recorded as an implementation-phase blocker (tenant tiering must exist before DR's tier-based RTO/RPO logic can be built).

This AMP does not select an option — it surfaces the choice for governance decision.

## Impact

- **Frozen documents affected if corrected:** Disaster Recovery (ADR-EAL-029) and/or Multi Tenancy (ADR-EAL-021) — either requires a new ADR to supersede/amend, per the "no redesign of approved modules without a governance decision" discipline.
- **Reversibility:** Fully reversible; this is a documentation/dependency-sequencing gap, not a runtime defect. No system behavior depends on this today since neither document is implemented yet.

## Resolution (Architecture Office, 2026-07-19)

**ACCEPTED — Option C (defer as tracked gap). CLOSED.**

Rationale: AstroOS v2.1.0 "Vistara" is a local-first, single-user platform. Multi Tenancy and Disaster Recovery are unimplemented enterprise documents describing multi-tenant/multi-region concerns that are explicitly out of current scope (`CLAUDE_START_HERE.md`). No runtime behavior depends on the forward reference, so no superseding ADR is warranted now. The gap is hereby recorded as an implementation-phase blocker: tenant tiering (Multi Tenancy §18) must exist before Disaster Recovery's tier-based RTO/RPO logic may be built. Options A/B (superseding ADRs) are declined as disproportionate for out-of-scope documents. No frozen document was modified.
