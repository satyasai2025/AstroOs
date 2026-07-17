---
id: AMP-004
title: Semantic Search's "seventh confirmation" claim is off-by-one from its own enumerated list
status: Proposed — Awaiting Approval
severity: Low
source: Architecture Library Validation Audit (2026-07-15)
target_documents:
  - enterprise/semantic-search.md (ADR-EAL-031)
  - enterprise/knowledge-graph.md (ADR-EAL-032)
---

# AMP-004: Off-by-One in the AI-Orchestration-Only Confirmation Count

## Finding

Semantic Search §7 states: "AI produces an artifact, determinism makes the decision — the seventh confirmation," then names exactly six instances in the same sentence (AI Platform, Research Platform, Workflow Engine, Event Bus, Digital Twin, and Semantic Search itself). The label is one higher than the enumerated list supports. Knowledge Graph §7 continues the sequence as "the eighth confirmation," propagating the same drift forward.

## Proposed Correction (Recommendation Only — Not Applied)

Correct Semantic Search's label from "seventh" to "sixth," and Knowledge Graph's from "eighth" to "seventh," to align the ordinal labels with the actual enumerated instances. As with AMP-003, this is a narrative tally, not an architectural claim — no component, boundary, or decision changes. Both documents are frozen; corrections require a new ADR superseding ADR-EAL-031 and/or ADR-EAL-032, per governance mode.

## Impact

- **Frozen documents affected:** Semantic Search (ADR-EAL-031) and Knowledge Graph (ADR-EAL-032) — superseding ADRs would be required to touch either.
- **Reversibility:** Trivial; word-level correction with no architectural consequence.

## Status

Awaiting approval. No frozen document has been modified by this AMP.
