---
id: AMP-003
title: Disaster Recovery internally disagrees on the sole-orchestrator confirmation ordinal
status: CLOSED — REJECTED (deferred; no superseding ADR warranted) — 2026-07-19
severity: Low
source: Architecture Library Validation Audit (2026-07-15)
target_documents:
  - enterprise/disaster-recovery.md (ADR-EAL-029)
---

# AMP-003: Disaster Recovery's "Fourth" vs. "Fifth" Confirmation

## Finding

Disaster Recovery §7 (Design Patterns) labels the sole-orchestrator-principle reconfirmation "the fourth consecutive confirmation," naming five confirming documents in the same sentence (Marketplace, Deployment, Scalability, High Availability, and Disaster Recovery itself). §17 (Readiness Assessment) of the same frozen document labels the identical claim "the fifth consecutive confirmation." The two sections of one document disagree with each other.

## Proposed Correction (Recommendation Only — Not Applied)

Correct §7's label from "fourth" to "fifth" to match §17 and the actual count of five named documents. This is a narrative/rhetorical device (a running tally of principle reconfirmations across documents), not an architectural claim — correcting it changes no component, interface, or decision, only the ordinal word in one sentence. Because Disaster Recovery is frozen, applying this correction requires a new ADR superseding ADR-EAL-029, per governance mode.

## Impact

- **Frozen documents affected:** Disaster Recovery (ADR-EAL-029) — a superseding ADR would be required to touch it.
- **Reversibility:** Trivial; a one-word correction with no architectural consequence.

## Resolution (Architecture Office, 2026-07-19)

**REJECTED (deferred). CLOSED.**

Rationale: The correction itself is sound ("fourth" should read "fifth"), but Disaster Recovery (ADR-EAL-029) is a frozen enterprise document describing multi-region DR that is explicitly out of scope for local-first v2.1.0 "Vistara" (`CLAUDE_START_HERE.md`). Issuing a superseding ADR to fix one cosmetic ordinal word in an out-of-scope, unimplemented document is disproportionate governance overhead. The discrepancy is a narrative tally, not an architectural claim; this AMP file itself serves as the permanent errata record. If ADR-EAL-029 is ever superseded for substantive reasons, the correction should be folded in then. No frozen document was modified.
