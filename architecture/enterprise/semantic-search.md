---
title: Enterprise Semantic Search
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Semantic Search

## 1. Problem Statement

The [Capability Registry](capability-registry.md) (ECR, ADR-EAL-003) already provides a search surface — but its own Future Evolution section named exactly the gap this document closes: *"Semantic/capability-shape search — moving beyond keyword/tag search toward matching on declared interface shape or behavioral description"* (Capability Registry §18). This document generalizes that idea beyond capability discovery alone: a reusable semantic search capability applicable to any indexed content (capabilities, research findings, knowledge entries, documentation) — never a redefinition of ECR's own frozen search surface, but a general-purpose engine ECR (or any other document) could optionally integrate with later, via its own separate decision.

The central design question this document must answer precisely, continuing the AI orchestration-only principle unbroken across seven documents now: **where exactly does AI's role end and deterministic computation begin in a semantic search system?** The answer: **generating an embedding (a vector representation of content) is an ordinary AI-backed capability** — there is no "deterministic ground truth" embedding to compute instead. But **matching a query to results — similarity computation, ranking, filtering — is a deterministic algorithm operating on those embeddings**, exactly the same way the AI Platform's Prompt Template Registry treats a prompt as a governed artifact and Research Platform's Statistical Execution Engine computes findings deterministically. AI produces an input artifact; it does not make the search decision.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Generating content/query embeddings | [AI Platform Architecture](ai-platform-architecture.md) (ADR-EAL-011) | An ordinary AI-backed capability invocation through the unchanged Model Gateway — embedding generation is orchestrated, not a new AI infrastructure. |
| What is being indexed (a capability, for one use case) | [Capability Registry](capability-registry.md) (ADR-EAL-003) | Where a Capability ID is the indexed content, this document references it unchanged; ECR's own search surface remains untouched and may optionally integrate with this engine later, via its own future decision. |
| Incremental re-indexing on content change | [Event Bus](event-bus.md) (ADR-EAL-014) | An ordinary EEB subscriber triggers re-embedding/re-indexing when indexed content changes — ranked and searched, not a new sync mechanism. |
| Full corpus re-index (multi-step) | [Workflow Engine](workflow-engine.md) (ADR-EAL-013) | A bulk rebuild (extract → embed → index → verify) is an ordinary workflow definition; a single-item incremental update is not — it's one call, not a multi-step process, so it is *not* forced into a workflow unnecessarily. |
| Search access authorization | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | Unchanged `checkPermission()`. |
| Tenant-scoped search results | [Multi Tenancy](multi-tenancy.md) (ADR-EAL-021) | Search results respect the unchanged isolation guarantee — no cross-tenant result leakage. |
| Indexing/search failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Existing taxonomy, new `err.semanticsearch.*` codes. |

**Scope boundary:** this document does not modify any of the thirty prior documents, including ECR's own search surface. It is a general-purpose engine other documents may choose to integrate with in the future, not a mandate that any of them do so now.

## 2. Goals

| Goal | Description |
|---|---|
| **Embedding generation as an ordinary AI-backed capability** | No new AI infrastructure — reuses the AI Platform's Model Gateway unchanged. |
| **Deterministic matching, ranking, and filtering** | The actual search decision (what matches, in what order) is a deterministic algorithm over embeddings, never an AI judgment call. |
| **Incremental indexing via Event Bus subscription** | Content changes trigger re-indexing without polling. |
| **Full reindex as an ordinary workflow, incremental update as a single call** | Right-sized reuse — not every process is forced into the Workflow Engine. |
| **No redefinition of ECR's existing search surface** | ECR's keyword/tag search remains exactly as frozen; this document is available for it to optionally consume later. |

**Non-goals**: this document does not replace ECR's search interface; it does not let an AI-backed capability decide search relevance/ranking directly — that remains a deterministic computation over AI-generated embeddings; and it does not mandate that any existing document integrate with it.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Content change event          │  ← ordinary EEB event (unchanged)
   │   (e.g., research finding        │
   │    published, capability          │
   │    registered)                    │
   └─────────────┬─────────────┘
                 │ subscribed (ordinary EEB subscriber)
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Embedding Pipeline (new)       │──────►│ AI Platform Model Gateway    │
   │                                 │        │ (unchanged) — generates       │
   │                                 │        │  the embedding vector          │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │ embedding (deterministic input from here on)
   ┌─────────────▼─────────────┐
   │   Vector Index (new)            │  ← deterministic similarity/ANN
   │                                 │    structure
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Search Query Engine (new)     │  ← deterministic ranking/
   │                                 │    filtering, tenant-scoped
   └───────────────────────────┘
```

## 4. Components

- **Embedding Pipeline** *(new)* — calls the AI Platform's unchanged Model Gateway to generate a vector embedding for a piece of content or a search query; this is the document's only AI-involving component, and it produces an artifact (the embedding), never a search decision.
- **Vector Index** *(new)* — a deterministic similarity/nearest-neighbor structure over generated embeddings; querying it is a reproducible computation, not a model inference.
- **Search Query Engine** *(new)* — applies deterministic ranking and filtering (including Multi Tenancy's unchanged isolation guarantee) to Vector Index results before returning them.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `indexContent(contentId, contentRef)` | Content owner or EEB subscriber (on change event) → Embedding Pipeline → Vector Index | Generates and indexes an embedding for a piece of content. |
| `search(query, tenantScope, filters)` | Caller → Search Query Engine | Embeds the query (via the same Embedding Pipeline), then deterministically ranks/filters Vector Index matches, respecting tenant scope. |
| `reindexCorpus(contentSetRef)` | Operator (or Scheduling-dispatched trigger) → Workflow Engine (`startWorkflow()`, unchanged) | Starts a full, multi-step reindex — extract, embed, index, verify — as an ordinary workflow. |

## 6. Data Flow

1. Content changes (a research finding published, a capability registered, a document updated) publish their existing events on the unchanged Event Bus; the Embedding Pipeline, an ordinary subscriber, receives them and calls `indexContent()`.
2. The Embedding Pipeline generates an embedding via the AI Platform's unchanged Model Gateway and writes it to the Vector Index — a deterministic structure from this point forward.
3. A search query is embedded the same way, then the Search Query Engine performs a deterministic similarity computation against the Vector Index, applies filters (including Multi Tenancy's unchanged isolation guarantee), and returns ranked results — no AI-backed capability makes the ranking decision.
4. A full corpus reindex, being multi-step, executes as an ordinary Workflow Engine definition; a single incremental update does not — it's one call through the Embedding Pipeline directly.
5. Any failure classifies via EEHF's existing taxonomy with a new `err.semanticsearch.*` code.

## 7. Design Patterns

- **AI produces an artifact, determinism makes the decision — the seventh confirmation** — following AI Platform, Research Platform, Workflow Engine, Event Bus (implicitly, via its non-AI nature), Digital Twin, and now Semantic Search: wherever AI and determinism meet in this library, AI's role is bounded to producing an input (a narration, a finding's wording, an embedding), never the decision itself.
- **Right-sized process modeling — not every action needs the Workflow Engine** — a single incremental re-index is one call, not a workflow; only the genuinely multi-step full-corpus rebuild is expressed as one. This is a deliberate refinement of the sole-orchestrator principle: it governs *multi-step* processes, not every single action in the library.
- **Fulfilling, not redefining, a prior document's own flagged future work** — ECR's Future Evolution section (Capability Registry §18) named this exact capability; this document delivers it generally, available for ECR to adopt later by its own separate decision, never by unilateral integration now.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Least-Privilege** (ESA catalog) applies to `search()` — results must never cross Multi Tenancy's isolation boundary, enforced by the Search Query Engine's filtering, not left to caller discipline.
- **Embeddings can leak information about their source content** — even without returning the raw content, a poorly-secured Vector Index could allow inference about indexed content's nature; access to the index itself should be scoped consistently with the underlying content's own access controls.
- **No secrets embedded as indexed content** — consistent with the manifest/data-hygiene discipline applied throughout this library.

## 9. Scalability

- **Incremental indexing scales with content-change rate**, an EEB-subscriber load profile identical to any other subscriber (Event Bus §9).
- **Search query volume is likely the dominant load** — the Vector Index and Search Query Engine should be optimized for query-time performance independently of indexing throughput, the now-familiar read/write asymmetry established throughout this library.
- **Full corpus reindex is infrequent and resource-intensive** — appropriately modeled as a deliberate, scheduled (via Scheduling, unchanged) workflow rather than a routine operation.

## 10. Best Practices

- Never let an AI-backed capability perform the ranking/matching decision directly — only embedding generation is AI-backed; everything downstream is deterministic.
- Model single-item updates as direct calls and only multi-step, full-corpus operations as Workflow Engine definitions — don't force every action through orchestration.
- Enforce tenant isolation at the Search Query Engine's filtering stage, not as an afterthought applied by the caller.

## 11. Common Pitfalls

- **Letting an AI-backed capability directly return "relevant" results instead of deterministic similarity ranking over embeddings** — collapses the artifact/decision boundary this document is built around.
- **Forcing incremental single-item indexing through the Workflow Engine "for consistency"** — unnecessary process overhead; the sole-orchestrator principle governs multi-step processes, not every action.
- **Treating this document as a mandate for ECR to adopt semantic search now** — it is available, not required; ECR's own frozen document is unmodified.
- **Skipping tenant-scoped filtering on search results** — a cross-tenant leak through search would violate Multi Tenancy's core guarantee.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Let an AI-backed capability perform search ranking directly** | Ask an LLM to judge which results are "most relevant." | Violates the confirmed AI orchestration-only principle; also produces non-reproducible, unauditable ranking, unlike deterministic similarity computation. |
| **Redefine ECR's search surface to be this engine** | Merge this capability directly into the Capability Registry's existing search. | Violates "no redesign of approved modules"; ECR remains unmodified, with optional future integration as its own separate decision. |
| **Force every indexing operation through the Workflow Engine** | Model even single-item updates as workflows. | Unnecessary overhead for a single-call operation; the sole-orchestrator principle is about not building a *second* orchestrator, not about routing every action through the existing one regardless of complexity. |
| **No tenant-scoping at the search layer** | Rely on the underlying content's own access control alone. | Risks a cross-tenant leak specifically through the search/ranking path, which the Search Query Engine is explicitly responsible for closing. |

## 13. Migration Strategy

1. **Stand up the Embedding Pipeline against the AI Platform's existing Model Gateway**, validating embedding generation for a small, low-risk content set first.
2. **Build the Vector Index and Search Query Engine**, validating deterministic ranking and tenant-scoped filtering before broad content indexing.
3. **Wire incremental indexing via Event Bus subscription** for content types that already publish change events.
4. **Implement full corpus reindex as an ordinary Workflow Engine definition**, reserved for deliberate, infrequent use.
5. **Offer integration to ECR's own future semantic-search evolution (Capability Registry §18) as an available option**, not a forced migration.

## 14. Success Criteria

- Embedding generation is confirmed as an ordinary AI Platform capability invocation — zero new AI infrastructure.
- Zero instances of an AI-backed capability performing the search ranking/matching decision directly.
- Incremental indexing is confirmed as event-driven, not polled.
- Full corpus reindex is confirmed as an ordinary Workflow Engine definition; single-item updates are confirmed as direct calls, not workflows.
- Zero cross-tenant result leakage, verified by test.

## 15. Decision Matrix

| Criterion (weight) | AI-generated embeddings + deterministic matching/ranking (recommended) | AI performs ranking directly | Redefine ECR's search surface | Force all indexing through Workflow Engine | No tenant-scoping at search layer |
|---|---|---|---|---|---|
| Preserves AI orchestration-only principle (High) | 5 | 1 | 4 | 4 | 4 |
| Respects "no redesign of approved modules" (ECR) (High) | 5 | 4 | 1 | 4 | 4 |
| Reproducible, auditable ranking (High) | 5 | 1 | 4 | 4 | 3 |
| Right-sized process modeling (Medium) | 5 | 3 | 3 | 1 | 4 |
| Tenant isolation preserved (High) | 5 | 3 | 3 | 3 | 1 |
| **Weighted outcome** | **Best overall fit** | Fails AI-principle | Fails charter boundary | Fails right-sizing goal | Fails isolation goal |

**Conclusion**: AI-generated embeddings paired with deterministic matching, ranking, and tenant-scoped filtering — available to, but never imposed on, ECR's own search surface — is recommended.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-031: Enterprise Semantic Search as AI-Generated Embeddings with Deterministic Matching**

- **Status**: Accepted
- **Context**: The Capability Registry's own Future Evolution section named semantic search as a planned gap; no document has defined it. The central design risk is conflating AI's role (embedding generation) with the actual search decision (matching/ranking), which must remain deterministic per the confirmed AI orchestration-only principle.
- **Decision**: Introduce an Embedding Pipeline (an ordinary AI Platform capability invocation), a deterministic Vector Index, and a deterministic Search Query Engine with tenant-scoped filtering. Incremental indexing is event-driven (EEB subscription); full corpus reindex is an ordinary Workflow Engine definition; single-item updates are not forced into a workflow. **No modification to any of the thirty prior documents**, including ECR's own search surface, which may optionally integrate with this engine later via its own separate decision.
- **Rationale**: The Decision Matrix (§15) shows this is the only option preserving the AI orchestration-only principle, the "no redesign of approved modules" boundary, and tenant isolation simultaneously, while right-sizing process modeling rather than over-applying the Workflow Engine.
- **Consequences**:
  - *Positive*: semantic search becomes available platform-wide as a general capability; ECR's own flagged future evolution now has a concrete, adoptable engine; the AI/determinism boundary is precise and auditable.
  - *Negative*: introduces a new AI-Platform-dependent component (the Embedding Pipeline), meaning its availability is coupled to the Model Gateway's own uptime.
  - *Neutral*: ECR integration is optional and deferred — no immediate change to that document's own search behavior.
- **Alternatives rejected**: AI performs ranking directly, redefining ECR's search surface, forcing all indexing through the Workflow Engine, no tenant-scoping — see §12 and §15.
- **Reversibility**: Fully reversible — the Embedding Pipeline, Vector Index, and Search Query Engine can be decommissioned without affecting ECR or any other prior document.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Embedding Pipeline, Vector Index, and Search Query Engine are specified at architecture level. |
| **AI/determinism boundary precision** | Confirmed | Embedding generation (AI) vs. matching/ranking (deterministic) is explicit and structurally enforced. |
| **Respect for ECR's frozen search surface** | Confirmed | No modification; optional future integration only. |
| **FUTURE-phase caveat** | Explicitly noted | As with Digital Twin, this document's practical value depends on deployment-specific content volume and embedding-model choice, both implementation-phase decisions. |
| **Technology-agnostic validation** | Ready | No binding to a specific embedding model or vector database technology. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **ECR integration decision** — a future, separately-approved ADR could formally wire the Capability Registry's own search to consume this engine, fulfilling Capability Registry §18 concretely.
- **Cross-reference with Knowledge Graph** — the next FUTURE-phase item may provide relationship-aware retrieval that complements this document's similarity-based search, without this document anticipating that design.
- **Hybrid keyword + semantic ranking** — combining ECR's existing keyword/tag approach with this document's embedding-based similarity as a blended ranking signal, as a future refinement rather than a redefinition of either.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-031.
