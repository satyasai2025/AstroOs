---
title: Enterprise Dependency Management
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Dependency Management

## 1. Problem Statement

**Audit finding, per the "reuse before creating" / "avoid duplicate capabilities" principles governing this library:** two of the six frozen documents already contain their own, independently-specified dependency-graph logic:

- [Enterprise Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) specifies a **Dependency Resolver** component (PLM §4) that builds a directed graph across plugins pending activation, rejects cycles, and enforces version-range compatibility between plugin dependencies (PLM §7).
- [Enterprise Module Registry](module-registry.md) (ADR-EAL-002) specifies a **Dependency Graph Engine** component (Module Registry §4) that maintains a declared inter-module dependency graph and supports impact analysis ("what depends on module X").

These are, at the level of the underlying problem, the same capability — directed-graph construction, cycle detection, version-range-aware edge validation, and impact-analysis traversal — applied twice, independently, to two different provider types. This is precisely the pattern the Module Registry itself was built to prevent (Module Registry §1: "duplicate capability creation ... teams re-implement a capability that already exists elsewhere"). It was not caught earlier because each engine was specified inside a document scoped to a single provider type, and neither document's audit phase cross-checked against the other's internals.

A second, related gap: **neither engine models a cross-provider dependency.** PLM's resolver only reasons about plugin-to-plugin edges; the Module Registry's engine only reasons about module-to-module edges. There is no defined mechanism today for declaring "this plugin depends on this module" or "this module depends on this plugin" — a real dependency shape that will occur in practice (per the Module Registry's own §1 boundary note, a module may host plugin extension points, and the reverse — a plugin depending on a core module's capability — is at least as common).

The Enterprise Dependency Management (EDM) document proposes a single, shared dependency-graph capability — construction, cycle detection, version-range validation, and impact analysis — usable by any provider type (module, plugin, or a future provider type), including cross-provider edges, so this capability is defined once rather than n times.

**Scope boundary on this document, respecting the "no redesign of approved modules" constraint on this charter:** this document does **not** modify, replace, or redesign PLM's Dependency Resolver or the Module Registry's Dependency Graph Engine as specified in their frozen, approved documents. Those remain valid and in effect exactly as written. This document instead (a) establishes EDM as the canonical shared engine for any *new* dependency-management need — including the previously-unmodeled cross-provider case — and (b) surfaces, as an explicit open question for your decision (§16, §17), whether and how PLM's and the Module Registry's existing internal components should eventually be migrated to consume EDM instead of their own independent logic. That migration, if approved, would require its own superseding ADR against ADR-EAL-001 and/or ADR-EAL-002 — a separate, explicit approval this document does not presume.

## 2. Goals

| Goal | Description |
|---|---|
| **Single dependency-graph capability** | Directed-graph construction, cycle detection, version-range edge validation, and impact-analysis traversal are implemented once, not per provider type. |
| **Cross-provider dependency support** | A dependency edge can be declared between any two providers regardless of type (module→module, plugin→plugin, module→plugin, plugin→module), closing the gap identified in §1. |
| **Non-disruption of frozen decisions** | Adoption does not require, and does not itself perform, any change to PLM (ADR-EAL-001) or the Module Registry (ADR-EAL-002) as currently specified. |
| **Consistent semantics** | The same cycle-rejection behavior, version-range semantics, and impact-analysis query shape apply regardless of which provider types are involved in a given edge. |
| **Reusable by future documents** | Any future Enterprise Architecture Library document that needs dependency modeling (as EDM's own existence was motivated by two prior documents needing it) can consume EDM rather than re-specifying graph logic a third time. |

**Non-goals**: EDM does not itself decide whether PLM or the Module Registry should migrate to it (that is an explicit open decision, §16); it does not manage activation ordering or lifecycle state (PLM's role) or ownership/catalog metadata (Module Registry's role) — it owns only the graph/edge/cycle/impact-analysis capability itself.

## 3. Architecture

```
   ┌───────────────────────────┐   ┌───────────────────────────┐
   │   Module Registry            │   │   Plugin Registry (PLM)     │
   │   (existing Dependency Graph  │   │   (existing Dependency        │
   │    Engine, unchanged)         │   │    Resolver, unchanged)       │
   └───────────────────────────┘   └───────────────────────────┘
         (status quo — both remain in effect exactly as frozen;
          see §1 scope boundary and §16 open question)

                    ┌─────────────────────────┐
                    │   Dependency Declaration   │  ← any provider (module,
                    │   Intake                   │    plugin, future types)
                    └────────────┬─────────────┘    declares edges here
                                 │
                    ┌────────────▼─────────────┐
                    │   Dependency Graph Engine   │  ← shared: construction,
                    │   (EDM, shared/canonical)   │    cycle detection,
                    └────────────┬─────────────┘    version-range validation
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                       │
┌─────────▼────────┐  ┌──────────▼─────────┐  ┌──────────▼─────────┐
│ Cycle Detector     │  │ Version-Range        │  │ Impact Analysis     │
│                     │  │ Validator            │  │ (getDependents)     │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

EDM is drawn here as a new, parallel capability available for adoption — the diagram deliberately shows the existing PLM/Module Registry components as unchanged boxes, not as consumers of EDM, because that consumption relationship is the open question in §16, not a decision made by this document.

## 4. Components

- **Dependency Declaration Intake** — accepts a dependency edge declaration from any provider type: source provider identity (module ID or plugin ID), target provider identity (module ID or plugin ID), and a version range constraint on the target.
- **Dependency Graph Engine** — the shared core: builds the directed graph across all declared edges (regardless of provider type mix) and exposes construction/query operations to the three specialized components below.
- **Cycle Detector** — identifies cycles in the graph and rejects the offending declaration(s), returning the specific cycle path as a diagnostic — functionally equivalent to what PLM §4/§7 and Module Registry §4/§7 each already specify independently, now expressed once.
- **Version-Range Validator** — checks that a declared dependency's version-range constraint against the target's current version is satisfiable, using the same semantics regardless of whether the source/target are modules or plugins.
- **Impact Analysis (`getDependents`)** — reverse-graph traversal answering "what depends on provider X," usable for any provider type, including mixed module/plugin dependency chains that neither existing engine can currently traverse.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `declareDependency(sourceId, sourceType, targetId, targetType, versionRange)` | Provider owner → Dependency Declaration Intake | Declares an edge; `sourceType`/`targetType` are each `Module` or `Plugin` (or a future provider type), enabling cross-provider edges. |
| `validateGraph(scope)` | Caller (e.g., an activation/registration flow) → Dependency Graph Engine | Runs cycle detection and version-range validation across a specified scope (e.g., all pending activations), returning a pass/fail with specific diagnostics on failure. |
| `getDependents(providerId, providerType)` | Any consumer → Impact Analysis | Reverse-graph query: what declares a dependency on this provider, regardless of the dependents' own provider type. |
| `getDependencies(providerId, providerType)` | Any consumer → Dependency Graph Engine | Forward query: what this provider declares a dependency on. |

These interfaces are intentionally shaped to be callable by PLM's or the Module Registry's existing components *if* a future migration decision (§16) approves that integration — but neither existing document is required to call them today.

## 6. Data Flow

1. A provider owner (module or plugin) declares a dependency edge via `declareDependency()`, specifying both endpoints' provider type and a version-range constraint — the same declaration shape regardless of whether the edge is same-type (module→module, plugin→plugin) or cross-type (module→plugin, plugin→module).
2. The Dependency Graph Engine incorporates the edge into its shared graph structure.
3. Before any dependent operation that requires a valid graph (e.g., a hypothetical future activation flow, or simply a design-review impact-analysis query), `validateGraph()` is invoked, running the Cycle Detector and Version-Range Validator across the relevant scope.
4. A failure at either check blocks the operation being gated (in whatever calling context invoked `validateGraph()`) and returns a specific diagnostic — the same fail-fast discipline already established in PLM (§7) and the Module Registry (§7), now shared rather than duplicated.
5. `getDependents()`/`getDependencies()` serve impact-analysis queries for any caller, including — for the first time in this library — a query that can traverse a mixed module/plugin dependency chain in one call.

## 7. Design Patterns

- **Shared library / extracted common capability** — the textbook response to the audit finding in §1: two independent implementations of the same underlying algorithm (graph construction, cycle detection, version-range checking) are consolidated into one, consumed (potentially) by multiple callers, directly following the "reuse before creating" principle this entire library is built around.
- **Graph-based dependency modeling** — reuses the same conceptual model already validated twice in this library (PLM §7, Module Registry §7), simply generalized across provider type.
- **Fail-fast validation** — consistent with every other registry in this library: cycles and unsatisfiable version ranges block the operation with a specific diagnostic rather than a generic failure.
- **Additive adoption, not forced migration** — EDM is introduced as a new, independently-usable capability rather than as a breaking replacement, respecting the charter's "no redesign of approved modules" boundary; existing consumers are not required to switch.

## 8. Security Considerations

- **Write-access governance mirrors the declaring provider's own registry** — a `declareDependency()` call should be authorized under the same ownership rules already established for the provider making the declaration (Module Registry §8 for a module source, PLM §8-equivalent authorization for a plugin source), not a separate, weaker permission model.
- **No secrets in dependency declarations** — as with every manifest/schema pattern in this library, a dependency edge is metadata only (identities and version ranges), never a place for credential material.
- **Cross-provider edges as an audit-relevant event** — a dependency newly crossing from one provider type to another (e.g., a plugin taking a hard dependency on a core module) is architecturally significant enough that it should be logged distinctly, since it changes the blast radius/impact-analysis picture for that module in a way a same-type dependency might not.

## 9. Scalability

- **Read-heavy for impact analysis, write-light for declarations** — mirrors the read/write split already established for the Module Registry (§9) and Capability Registry (§9); `getDependents()`/`getDependencies()` should be optimized independently of the comparatively rare `declareDependency()` write path.
- **Single shared graph scales better than two independent ones for cross-cutting queries** — a cross-provider impact-analysis question ("what, across modules and plugins combined, depends on this") is a single graph traversal in EDM's model versus being architecturally impossible in the current two-engine model without an ad hoc bridge.
- **Cycle detection cost scales with total edge count, not per-provider-type edge count** — consolidating into one graph means cycle-detection algorithmic complexity is a function of total declared edges across all provider types; this is a reasonable trade given the alternative (two separate, smaller graphs) cannot detect a cycle that spans both types at all.

## 10. Best Practices

- Treat a dependency edge's provider-type pair as first-class metadata, not an afterthought — cross-provider edges are the entire reason this consolidation closes a real gap, not just a deduplication exercise.
- Keep EDM's own interfaces free of any provider-type-specific business logic (activation ordering, ownership semantics) — those remain PLM's and the Module Registry's respective responsibilities; EDM answers "is this graph valid" and "who depends on what," nothing else.
- When (if) a migration of PLM's or the Module Registry's internal engine to EDM is proposed in the future, require it to go through its own explicit ADR against the relevant frozen document, per §1's scope boundary — never treat such a migration as an implied consequence of this document's approval.

## 11. Common Pitfalls

- **Treating this document's approval as silent authorization to modify PLM or the Module Registry** — the single most important pitfall to avoid given the charter's "no redesign of approved modules" constraint; this document proposes a new, additive capability, not a mandate to refactor two already-frozen documents.
- **Re-duplicating the same capability a third time** — if a future document (e.g., a hypothetical dependency concern for the Service Registry or Configuration Framework) is drafted without checking EDM first, the exact problem in §1 recurs; this is the discovery-search discipline the Module Registry (§10) already established, now applicable to EDM itself as a registered capability.
- **Conflating "dependency exists" with "dependency is currently healthy"** — EDM validates declared graph structure and version compatibility; it does not know whether a dependency's *runtime* instance is currently healthy (that's the Service Registry's concern, ESR §2) — a valid graph edge says nothing about live reachability.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Leave both existing engines as-is; do nothing** | Accept the duplication identified in §1 as a sunk cost and do not build a shared capability. | Directly contradicts the "reuse before creating" / "avoid duplicate capabilities" principles this library is chartered to enforce; also leaves the cross-provider dependency gap permanently unaddressed. |
| **Immediately migrate PLM and Module Registry to consume a new shared engine** | Build EDM and simultaneously refactor both frozen documents to delegate to it. | Violates the explicit charter boundary "no redesign of approved modules" without a separate approval step for each; this document instead proposes the shared capability and defers the migration decision explicitly (§16) rather than bundling an unauthorized redesign into this approval. |
| **Build cross-provider dependency support as a bolt-on to whichever of the two existing engines is "closer"** | E.g., extend the Module Registry's Dependency Graph Engine to also accept plugin identities. | Would itself be a redesign of an approved module (Module Registry, ADR-EAL-002) without a dedicated ADR for that specific change, and picking one engine to extend re-creates an asymmetric, single-provider-type-biased model rather than a genuinely shared one. |
| **Model dependencies through the Capability Registry instead** | Extend ECR (ADR-EAL-003) to also carry dependency-graph semantics. | ECR is explicitly scoped (Capability Registry §2 non-goals) as a read-only capability-to-provider mapping layer; dependency-graph construction, cycle detection, and version validation are a different capability with different write/validation semantics, and forcing it into ECR would repeat the same scope-distortion risk already avoided when ESR was kept separate from ECR (Service Registry §12). |

## 13. Migration Strategy

This document's own adoption path is deliberately narrow, consistent with §1's scope boundary:

1. **Stand up EDM as a new, independently-usable capability**, with no required integration into PLM or the Module Registry at this stage.
2. **Adopt EDM for the previously-unmodeled cross-provider dependency case first** — since no existing engine covers this today, there is no frozen-document boundary to respect here; this is the lowest-friction, highest-value initial use.
3. **Use EDM for any future Enterprise Architecture Library document that needs dependency modeling**, per the discovery-search discipline in §11, rather than specifying graph logic independently again.
4. **Separately propose, if desired, a dedicated ADR against ADR-EAL-001 (PLM)** to migrate its Dependency Resolver to consume EDM — a distinct decision, requiring its own audit/review cycle under this charter, not a consequence of this document.
5. **Separately propose, if desired, a dedicated ADR against ADR-EAL-002 (Module Registry)** to migrate its Dependency Graph Engine to consume EDM — likewise a distinct, separately-approved decision.
6. **Only after both (if approved) migrations land** would the two original, now-redundant engine specifications be formally superseded — this document does not assume that outcome.

## 14. Success Criteria

- Cross-provider dependency declarations (module↔plugin) are expressible and validatable for the first time in this library, closing the gap identified in §1.
- No new dependency-graph logic is specified in any subsequent Enterprise Architecture Library document without first checking EDM (a discovery-search-gate success metric, mirroring Module Registry §14).
- Zero unauthorized modifications to PLM's or the Module Registry's frozen specifications as a side effect of this document's adoption.
- If a future migration ADR for PLM and/or the Module Registry is approved, cycle-detection and version-validation behavior observed post-migration is equivalent to (not a regression from) the original engines' documented behavior.

## 15. Decision Matrix

| Criterion (weight) | Shared EDM capability, additive adoption (recommended) | Do nothing (accept duplication) | Immediate forced migration of both engines | Bolt cross-provider support onto one existing engine | Fold into Capability Registry (ECR) |
|---|---|---|---|---|---|
| Closes duplicate-capability finding (High) | 5 | 1 | 5 | 3 | 3 |
| Cross-provider dependency support (High) | 5 | 1 | 5 | 3 | 4 |
| Respects "no redesign of approved modules" (High) | 5 | 5 | 1 | 2 | 3 |
| Consistency of semantics across provider types (Medium) | 5 | 1 | 5 | 2 | 3 |
| Reusable for future documents (Medium) | 5 | 1 | 4 | 2 | 3 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 5 | 2 | 3 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails core principle | Fails charter boundary | Asymmetric, still a redesign | Fails ECR's own scope (non-goal) |

**Conclusion**: introducing EDM as a new, additive, shared capability — without forcing an immediate migration of the two existing frozen engines — is recommended. It is the only option that both closes the duplicate-capability/cross-provider gap identified in §1 and respects the charter's explicit prohibition on redesigning already-approved modules without separate authorization.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-007: Shared Enterprise Dependency Management Capability, Adopted Additively**

- **Status**: Accepted
- **Context**: Audit of the frozen library (§1) found that PLM's Dependency Resolver (ADR-EAL-001) and the Module Registry's Dependency Graph Engine (ADR-EAL-002) independently implement the same underlying capability (graph construction, cycle detection, version-range validation, impact analysis) for different provider types, with no support for cross-provider (module↔plugin) dependency edges. This duplication runs counter to the "reuse before creating" principle this library exists to enforce.
- **Decision**: Introduce a shared Enterprise Dependency Management (EDM) capability — Dependency Declaration Intake, a shared Dependency Graph Engine, Cycle Detector, Version-Range Validator, and Impact Analysis — usable by any provider type including cross-provider edges. EDM is retained as a **shared architectural capability**, adopted additively. **This decision does not modify or migrate PLM or the Module Registry** — both remain exactly as frozen, with no changes to their existing internal dependency components. Whether and how those two frozen documents should eventually migrate to consume EDM is an **explicit open question**, left as a future ADR against ADR-EAL-001 and/or ADR-EAL-002 respectively, if and only if ever required — not decided or implied by this ADR.
- **Rationale**: The Decision Matrix (§15) shows this is the only option that both closes the duplication/cross-provider gap and respects the charter's "no redesign of approved modules" boundary; immediate forced migration or a bolt-on to one existing engine would each constitute an unauthorized redesign of a frozen document.
- **Consequences**:
  - *Positive*: closes a real, previously-unaddressed cross-provider dependency gap immediately; establishes a reusable capability for future documents, directly preventing a third independent implementation of the same graph logic; fully respects existing frozen decisions.
  - *Negative*: for a transitional period, the library will have *three* dependency-graph-shaped components in existence (PLM's, the Module Registry's, and EDM) if no migration is ever approved — a known, accepted, and explicitly flagged trade-off rather than an oversight.
  - *Neutral*: consumers of PLM or the Module Registry today are entirely unaffected; only new/cross-provider use cases interact with EDM initially.
- **Alternatives rejected**: do nothing, immediate forced migration, bolt-on to one existing engine, folding into ECR — see §12 and §15.
- **Reversibility**: Fully reversible — EDM can be decommissioned without impact to PLM or the Module Registry, since neither depends on it under this decision; reversibility would only become more constrained if a future, separate migration ADR were approved and executed.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Shared graph engine, cross-provider edge model, and interfaces are specified at architecture level. |
| **Respect for "no redesign of approved modules"** | Confirmed by design | §1 scope boundary and ADR-EAL-007 explicitly defer any change to PLM/Module Registry internals to a separate, future approval. |
| **Technology-agnostic validation** | Ready | No binding to a specific graph database or algorithm implementation. |
| **Open decision requiring your explicit input** | **Confirmed left open, at your direction** | Migration of PLM's Dependency Resolver and/or the Module Registry's Dependency Graph Engine to consume EDM is explicitly deferred to a future ADR, if and only if ever required (approved decision). No migration is authorized by this document. |
| **Security model maturity** | Ready for design review | Write-access governance mirroring the declaring provider's own registry is defined (§8); no formal threat model performed yet. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Migration ADRs for PLM and/or Module Registry (explicitly deferred, not committed)** — should you choose to pursue consolidation of the existing engines onto EDM, each would be scoped as its own future ADR per §13/§16.
- **Extension to additional future provider types** — if a future document introduces a new registry/provider type (following the pattern already anticipated in the Service Registry's own future evolution, §18 of that document), EDM's provider-type-agnostic edge model is designed to extend to it without structural change.
- **Dependency-aware impact analysis feeding the Capability Registry** — a future integration could let ECR's search surface (Capability Registry §5) optionally show "capabilities that would be affected if this dependency changed," combining EDM's impact analysis with ECR's capability mapping without merging the two systems.
- **Version-range policy sophistication** — evolving the Version-Range Validator beyond simple semver-range checking toward richer compatibility policies, mirroring the compatibility-matrix future evolution already noted conceptually in PLM.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-007.
