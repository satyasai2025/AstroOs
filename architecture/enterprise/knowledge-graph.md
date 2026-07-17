---
title: Enterprise Knowledge Graph
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Knowledge Graph

## 1. Problem Statement

Two frozen documents already model relationships between entities, each narrowly and correctly scoped to its own purpose: [Dependency Management](dependency-management.md) (EDM, ADR-EAL-007) models **provider dependency edges** specifically — with cycle detection and version-range validation, a purpose-built graph for one relationship type. [Semantic Search](semantic-search.md) (ADR-EAL-031) finds **similarity** between content — an unstructured, embedding-based retrieval paradigm, not an explicit relationship model at all.

Neither answers a more general question: **"this research finding informed the design of this capability," "this Digital Twin mirrors this tenant," "this knowledge-base entry relates to this capability"** — explicit, typed, structured relationships between arbitrary platform entities that are neither a dependency (EDM's narrow scope) nor a similarity score (Semantic Search's different paradigm). The Enterprise Knowledge Graph (EKG) is that general-purpose typed relationship layer — referencing existing entity identities from whatever registry already owns them, never redefining EDM's dependency semantics or Semantic Search's similarity computation, and optionally incorporating both as specific, read-only relationship types among many.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Entity identity for any graph node | Every prior document with its own registry (Capability Registry, Module Registry, Research Platform's Findings Repository, Multi Tenancy's Tenant Registry, Digital Twin's Twin Registry, etc.) | A graph node is always a reference to an already-existing entity ID — EKG never mints a new identity for something another document already owns. |
| Provider dependency relationships specifically | [Dependency Management](dependency-management.md) (ADR-EAL-007) | EDM remains the sole authority for dependency edges (cycle detection, version validation); EKG may optionally mirror EDM's edges as one read-only relationship type among many, never redefining or duplicating EDM's own validation logic. |
| Similarity-based relationships | [Semantic Search](semantic-search.md) (ADR-EAL-031) | A "semantically similar to" relationship type may be populated from Semantic Search's results, read-only — EKG does not recompute similarity itself. |
| Capturing new relationships as they're declared | [Event Bus](event-bus.md) (ADR-EAL-014) | An ordinary EEB subscriber ingests relationship-relevant events, consistent with the pattern already established by ENF, EOA, Digital Twin, and Semantic Search. |
| Relationship query authorization | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | Unchanged `checkPermission()`. |
| Tenant-scoped relationship visibility | [Multi Tenancy](multi-tenancy.md) (ADR-EAL-021) | Query results respect the unchanged isolation guarantee. |
| Graph query/traversal failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Existing taxonomy, new `err.knowledgegraph.*` codes. |

**Scope boundary:** this document does not modify any of the thirty-one prior documents, including EDM's dependency semantics and Semantic Search's similarity computation. It is a general-purpose, referencing-only relationship layer for relationships neither of those two documents models.

## 2. Goals

| Goal | Description |
|---|---|
| **Typed, explicit relationships between existing entities** | A named Relationship Type Catalog (e.g., "informed_by," "relates_to," "mirrors") expresses connections without inventing new entity identities. |
| **No duplication of EDM's dependency semantics** | Dependency-specific validation (cycles, version ranges) remains entirely EDM's; EKG may reference those edges read-only. |
| **No duplication of Semantic Search's similarity computation** | Similarity relationships, where included, are read-only reflections of Semantic Search's own results. |
| **Deterministic graph traversal** | Multi-hop relationship queries are a deterministic computation over declared edges, not an AI judgment call. |
| **Event-driven relationship capture** | New relationships are captured via ordinary Event Bus subscription where a source event already signals one. |

**Non-goals**: EKG does not perform dependency validation (EDM's role); it does not compute similarity (Semantic Search's role); it does not mint new entity identities for anything another document already owns; and it does not let an AI-backed capability declare a relationship as fact without a deterministic or human-asserted basis — an AI-backed capability may *suggest* a candidate relationship for human/governance confirmation, never assert one unilaterally into the graph.

## 3. Architecture

```
   ┌───────────────────────────┐        ┌───────────────────────────┐
   │   Relationship Type Catalog    │        │ Dependency Management (EDM)   │
   │   (new)                        │◄──────┤ — dependency edges mirrored,   │
   └─────────────┬─────────────┘        │   read-only, not owned         │
                 │                       └───────────────────────────┘
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Graph Store (new)             │◄──────┤ Semantic Search               │
   │   — edges reference existing     │        │ — similarity results mirrored, │
   │     entity IDs only              │        │   read-only, not owned         │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Graph Query Engine (new)      │◄──────┤ Event Bus — ordinary            │
   │   — deterministic traversal      │        │ subscriber capturing new        │
   └───────────────────────────┘        │ declared relationships           │
                                        └───────────────────────────┘
```

## 4. Components

- **Relationship Type Catalog** *(new)* — a closed, named set of relationship types (e.g., "informed_by," "relates_to," "mirrors," and, as read-only reflections, "depends_on" from EDM and "semantically_similar_to" from Semantic Search) — new types are added deliberately, never informally.
- **Graph Store** *(new)* — the durable edge store; every node is a reference to an existing entity ID owned by another document's registry — EKG owns the edges, never the entities.
- **Graph Query Engine** *(new)* — deterministic multi-hop traversal and relationship queries, respecting Multi Tenancy's unchanged isolation guarantee.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `declareRelationship(sourceEntityRef, relationshipType, targetEntityRef, assertedBy)` | Human/governance action, or a deterministic process → Graph Store | Declares a typed relationship; `assertedBy` records whether it's human-declared, mirrored from EDM/Semantic Search, or system-derived. |
| `suggestRelationship(sourceEntityRef, relationshipType, targetEntityRef, confidence)` | An AI-backed capability (per ADR-EAL-011, unchanged) → a pending-suggestion queue, not the Graph Store directly | AI may suggest a candidate relationship; it is never written to the graph as fact without separate confirmation. |
| `queryRelationships(entityRef, relationshipTypes, depth)` | Caller → Graph Query Engine | Deterministic traversal, respecting tenant scope. |

## 6. Data Flow

1. A relationship is declared via `declareRelationship()` — either by a human/governance action, mirrored read-only from EDM's existing dependency edges, or mirrored read-only from Semantic Search's similarity results.
2. Where an AI-backed capability identifies a *candidate* relationship (e.g., noticing two research findings might be related), it calls `suggestRelationship()` into a pending queue — never directly into the Graph Store — preserving the unbroken AI orchestration-only principle: AI proposes, it does not assert.
3. A human or governance process reviews pending suggestions and, if confirmed, calls `declareRelationship()` itself — the graph's actual content is always attributable to a deterministic source or a confirmed human decision.
4. `queryRelationships()` performs deterministic multi-hop traversal, filtered by Multi Tenancy's unchanged isolation guarantee.
5. Any failure classifies via EEHF's existing taxonomy with a new `err.knowledgegraph.*` code.

## 7. Design Patterns

- **Reference, never redefine — extended to relationship data itself** — every node references an existing entity; two specific relationship types (dependency, similarity) are read-only reflections of documents that already compute them, continuing the exact discipline established by ECR's identity-referencing model.
- **AI suggests, humans/determinism assert — the eighth confirmation** — extending the AI orchestration-only principle to relationship *assertion* specifically: an AI-backed capability may notice a pattern, but the graph's actual, queryable content always has a deterministic or human-confirmed origin, never an unreviewed AI claim.
- **Closed, deliberately-curated relationship type catalog** — mirrors the Audit Framework's own closed Mandatory Audit Event Catalog discipline (Audit Framework §11): a relationship-type catalog that grows informally loses its usefulness as a queryable, well-understood vocabulary.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Fail-Closed Validation** (ESA catalog) applies to `suggestRelationship()` — an unconfirmed AI suggestion must never be queryable as if it were an asserted fact.
- **Principle: Least-Privilege** (ESA catalog) applies to `declareRelationship()` — asserting a relationship (especially one implying sensitive association between entities) should be authorized narrowly.
- **Tenant isolation must hold across relationship traversal** — a multi-hop query must never surface a path that would leak cross-tenant association, consistent with Multi Tenancy's unchanged guarantee.

## 9. Scalability

- **Graph traversal depth should be bounded** — an unbounded multi-hop query could become expensive; the Graph Query Engine should enforce a maximum traversal depth by default.
- **Mirrored relationship types (dependency, similarity) scale with their source documents' own update cadence** — EKG's ingestion of these is read-only and event-driven, inheriting EDM's and Semantic Search's own respective volumes rather than introducing an independent scaling axis.

## 10. Best Practices

- Always reference an existing entity ID — never let EKG become a place where a new, EKG-only identity is created for something another document could have registered instead.
- Keep the Relationship Type Catalog closed and deliberately curated — resist ad hoc type proliferation.
- Route AI-identified candidate relationships through `suggestRelationship()`'s pending queue, never directly into the Graph Store.

## 11. Common Pitfalls

- **Letting an AI-backed capability assert relationships directly into the graph** — the single most important boundary in this document, extending the orchestration-only principle to relationship data itself.
- **Duplicating EDM's cycle detection or version validation inside EKG** — if a "dependency-like" relationship needs that validation, it belongs in EDM, not reinvented here.
- **Recomputing similarity inside EKG instead of mirroring Semantic Search's results** — repeats the exact duplication this library has avoided since EDM's own founding audit finding.
- **Unbounded relationship-type proliferation** — an uncurated catalog becomes as unusable as no catalog at all.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Fold Knowledge Graph into EDM** | Extend EDM's dependency graph to carry general-purpose relationships too. | Would distort EDM's purpose-built cycle-detection/version-validation model with unrelated relationship semantics; violates "no redesign of approved modules." |
| **Fold Knowledge Graph into Semantic Search** | Model explicit relationships as just another similarity signal. | Conflates two genuinely different retrieval paradigms (explicit typed edges vs. embedding similarity); Semantic Search's own document is correctly scoped to similarity alone. |
| **Let AI-backed capabilities assert relationships directly** | Skip the suggestion/confirmation step for efficiency. | Directly violates the unbroken AI orchestration-only principle; would make the graph's content only as reliable as an unreviewed model output. |
| **An open, ungoverned relationship-type vocabulary** | Allow any caller to invent a new relationship type freely. | Fails the "closed, curated catalog" goal, producing an unmanageably inconsistent graph over time. |

## 13. Migration Strategy

1. **Stand up the Relationship Type Catalog and Graph Store**, seeding a small, deliberately-curated initial type set.
2. **Mirror EDM's dependency edges and Semantic Search's similarity results read-only** as the first two relationship types, validating that neither's own validation/computation logic is duplicated.
3. **Enable human/governance-declared relationships for a small pilot set of entities** before broad adoption.
4. **Enable AI-suggested candidate relationships only after the human-confirmation workflow is validated**, never skipping directly to auto-assertion.

## 14. Success Criteria

- Every graph node references an existing entity ID — zero new identities minted by EKG.
- Zero duplication of EDM's dependency validation or Semantic Search's similarity computation within EKG itself.
- Zero AI-suggested relationships written directly to the Graph Store without human/governance confirmation.
- A bounded, multi-hop relationship query is demonstrated end-to-end, respecting tenant isolation.

## 15. Decision Matrix

| Criterion (weight) | General-purpose, reference-only relationship layer with AI-suggests/human-confirms (recommended) | Fold into EDM | Fold into Semantic Search | AI asserts relationships directly | Ungoverned relationship-type vocabulary |
|---|---|---|---|---|---|
| Avoids duplicating EDM/Semantic Search (High) | 5 | 1 | 1 | 4 | 4 |
| Preserves AI orchestration-only principle (High) | 5 | 4 | 4 | 1 | 4 |
| Respects "no redesign of approved modules" (High) | 5 | 1 | 1 | 4 | 4 |
| Queryable, consistent relationship vocabulary (Medium) | 5 | 3 | 3 | 3 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 2 | 2 | 4 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails charter boundary | Fails paradigm-separation goal | Fails AI-principle | Fails vocabulary-consistency goal |

**Conclusion**: a general-purpose, reference-only relationship layer — with AI limited to suggestion, never direct assertion — is recommended, preserving every boundary this library has established across EDM, Semantic Search, and the AI orchestration-only principle.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-032: Enterprise Knowledge Graph as a Reference-Only Relationship Layer, AI-Suggests/Human-Confirms**

- **Status**: Accepted
- **Context**: No document models general-purpose, typed relationships between arbitrary platform entities; EDM and Semantic Search each correctly model a narrower, different relationship concept (dependency validation, similarity) that EKG must not duplicate or redefine.
- **Decision**: Introduce a Relationship Type Catalog, Graph Store (nodes reference existing entity IDs only), and Graph Query Engine (deterministic traversal). EDM's dependency edges and Semantic Search's similarity results may be mirrored read-only as specific relationship types. AI-backed capabilities may only suggest candidate relationships into a pending queue — never assert directly into the Graph Store. **No modification to any of the thirty-one prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option avoiding duplication of EDM's and Semantic Search's own logic while preserving the unbroken AI orchestration-only principle, extended here specifically to relationship assertion.
- **Consequences**:
  - *Positive*: platform entities gain a general-purpose, queryable relationship layer without any duplicated validation/computation logic; AI can still contribute value (suggesting candidate relationships) without compromising graph integrity.
  - *Negative*: AI-suggested relationships require a human/governance confirmation step before becoming queryable, adding latency between "AI noticed a pattern" and "it's usable in the graph" — an intentional trade-off for integrity.
  - *Neutral*: the Relationship Type Catalog starts small and grows only deliberately.
- **Alternatives rejected**: folding into EDM, folding into Semantic Search, AI asserting directly, an ungoverned type vocabulary — see §12 and §15.
- **Reversibility**: Fully reversible — the Graph Store and Query Engine can be decommissioned without affecting EDM, Semantic Search, or any entity registry they reference.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Relationship Type Catalog, Graph Store, and Query Engine are specified at architecture level. |
| **Avoids duplicating EDM/Semantic Search** | Confirmed | Both are referenced read-only, never redefined. |
| **AI suggestion/confirmation boundary** | Confirmed | Extends the unbroken orchestration-only principle to relationship assertion specifically. |
| **FUTURE-phase caveat** | Explicitly noted | As with Digital Twin and Semantic Search, practical utility depends on how many entities across a given deployment have relationships worth capturing explicitly. |
| **Technology-agnostic validation** | Ready | No binding to a specific graph database technology. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Automated relationship-confirmation workflows** — using the Workflow Engine to route AI-suggested relationships through a formal review/approval sequence, rather than an ad hoc governance check.
- **Cross-reference with Agent Platform** — the next-but-one FUTURE-phase item may consume EKG's relationship data to inform agent reasoning, without this document anticipating that design.
- **Graph-informed impact analysis alongside EDM** — a future integration combining EKG's general relationships with EDM's own `getDependents()` for richer, combined impact analysis, without either document absorbing the other.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-032.
