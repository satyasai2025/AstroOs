---
title: Enterprise Module Registry
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Module Registry

## 1. Problem Statement

As a platform grows, its own first-party capability surface — the set of internally-owned functional units ("modules") that make up the product — tends to accumulate the same problems that plugin ecosystems face, even without any third-party extensibility:

- **Duplicate capability creation** — teams re-implement a capability that already exists elsewhere in the platform because there is no authoritative, queryable catalog of what already exists.
- **Unclear ownership** — no single record of which team/owner is accountable for a given module, complicating incident response and change approval.
- **Hidden coupling** — modules depend on each other's internals informally (shared database tables, imported internals) rather than through declared, versioned interfaces, making safe evolution difficult.
- **No reuse discovery path** — "reuse before creating" (an active platform principle) is unenforceable if there's no mechanism to discover reusable capabilities before starting new work.
- **Inconsistent module boundaries** — without a registry enforcing a definition of "module," the term is used loosely, and scope boundaries drift over time.

The Enterprise Module Registry (EMR) is the authoritative catalog of the platform's own first-party modules — their identity, ownership, exposed interfaces, versions, and interdependencies — so that "reuse before creating" and "avoid duplicate capabilities" are enforceable, not aspirational.

### Relationship to Enterprise Plugin Lifecycle Management (PLM)

This document's scope is distinct from, but must interlock with, the frozen [Enterprise Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001):

| | **Module Registry (this document)** | **Plugin Registry (PLM, §3–4)** |
|---|---|---|
| Subject | First-party, always-present platform capability units | Installable, independently-lifecycled extensions (first- or third-party) |
| Cardinality | Fixed by platform release; changes through normal release process | Dynamic; can be installed/removed at runtime |
| Lifecycle | Tracked for catalog/reuse purposes; not state-machine-driven activation | Full state machine (DISCOVERED → ACTIVE → ... → REMOVED) |
| Primary goal | Discoverability and reuse; prevent duplicate capability creation | Safe runtime extensibility; isolation and failure containment |

A module *may* also expose one or more of its capabilities as a plugin extension point (i.e., a module can be a plugin *host*), but the Module Registry does not manage plugin activation state — that remains PLM's responsibility. This boundary is treated as authoritative for both documents; any future overlap must be resolved via a superseding ADR to both, not by informal convention.

**Approved decision (ADR-EAL-002, accepted)**: the Module Registry and Plugin Registry remain permanently separate architectural components — they are not merged, and neither absorbs the other. Modules represent first-party core platform capabilities and form part of the architectural baseline; plugins represent optional extension packages with their own independent lifecycle, discovery, versioning, installation, activation, and compatibility model (PLM). Where a capability needs to be discoverable *regardless* of whether it happens to live in a module or a plugin, that cross-cutting concern is addressed by a separate, future **Enterprise Capability Registry** (see §18 and the next document in this library), which maps capabilities to their underlying module or plugin without changing the ownership, schema, or authority of either existing registry.

## 2. Goals

| Goal | Description |
|---|---|
| **Single source of truth** | One authoritative catalog of every first-party module: identity, owner, version, status. |
| **Reuse enforcement** | Reuse before creating is checkable — proposing a new module requires querying the registry for overlapping capability first. |
| **Explicit interfaces** | Every module's externally-consumable capability is declared as a versioned interface, not inferred from internal implementation. |
| **Ownership clarity** | Every module has exactly one accountable owner (team or role) recorded at all times. |
| **Dependency transparency** | Inter-module dependencies are declared and queryable, enabling impact analysis before a breaking change. |
| **Deprecation governance** | Modules can be formally deprecated and retired on a governed timeline, not silently abandoned. |
| **Low-friction adoption** | Registering and querying the registry must be lower effort than not doing so, or teams will bypass it. |

**Non-goals**: EMR is not a runtime service mesh/discovery system (it is a design-time and governance catalog, not a request-routing layer), and it does not manage plugin activation lifecycle (see PLM boundary above).

## 3. Architecture

```
                    ┌─────────────────────────┐
                    │   Module Catalog          │  ← authoritative record:
                    │   (registry store)        │    identity, owner, version,
                    └────────────┬─────────────┘    status, interfaces
                                 │
                    ┌────────────▼─────────────┐
                    │   Registration &          │  ← validates submissions,
                    │   Curation Service        │    enforces schema + ownership
                    └────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                       │
┌─────────▼────────┐  ┌──────────▼─────────┐  ┌──────────▼─────────┐
│ Capability        │  │ Dependency Graph   │  │ Deprecation &       │
│ Search / Discovery │  │ Engine             │  │ Retirement Tracker  │
└─────────┬────────┘  └──────────┬─────────┘  └──────────┬─────────┘
          │                      │                       │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Consumers:               │
                    │   design review tooling,    │
                    │   ADR/RFC process, CI       │
                    │   "duplicate capability"    │
                    │   checks                    │
                    └───────────────────────────┘
```

The EMR is a design-time governance system: it does not sit in any runtime request path. It is consulted during the **Audit** and **Research** phases of the Standard Workflow (this document's own lifecycle is a live example — any new module proposal must query it first) and during design review.

## 4. Components

- **Module Catalog** — the durable store of module records: identity, current version, status (Active / Deprecated / Retired), owning team, and a pointer to its declared interface set.
- **Registration & Curation Service** — validates new/updated module submissions against the schema, enforces that every module has exactly one recorded owner, and rejects submissions with incomplete interface declarations.
- **Capability Search / Discovery** — a query surface (by keyword, capability tag, or interface shape) that lets a proposer check "does this already exist?" before creating a new module — the mechanism that makes "reuse before creating" enforceable rather than aspirational.
- **Dependency Graph Engine** — maintains the declared inter-module dependency graph, supporting impact analysis ("what depends on module X") ahead of breaking changes.
- **Deprecation & Retirement Tracker** — governs the formal deprecation timeline for a module: announcement, grace period, dependent-migration tracking, and final retirement.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `registerModule(descriptor)` | Module owner → Registration Service | Submit a new module's identity, owner, version, and declared interfaces. |
| `updateModule(moduleId, descriptor)` | Module owner → Registration Service | Update version/interface/ownership metadata for an existing module. |
| `searchCapabilities(query)` | Proposer (human or CI check) → Discovery | Query for existing modules matching a capability description, keyword, or interface shape — the "reuse before creating" gate. |
| `getDependents(moduleId)` | Any consumer → Dependency Graph Engine | Impact-analysis query: what declares a dependency on this module. |
| `declareDependency(moduleId, dependsOnModuleId, versionRange)` | Module owner → Registration Service | Record a formal inter-module dependency. |
| `deprecate(moduleId, timeline)` | Module owner/governance → Deprecation Tracker | Initiate a governed deprecation with an announced retirement date. |
| `getModule(moduleId)` | Any consumer → Module Catalog | Read-only lookup of a module's current record. |

As with PLM, these are logical/conceptual interfaces; concrete transport is an implementation decision out of scope here.

## 6. Data Flow

1. A team proposing a new capability first calls `searchCapabilities()` against the Discovery surface — this step is procedurally mandatory per the "reuse before creating" principle, ideally enforced as a required step in the design-review workflow (e.g., a design document cannot enter Review without evidence of this query).
2. If no existing module satisfies the need, the team submits `registerModule()` with a full descriptor (owner, version, declared interfaces, initial dependencies).
3. The Registration & Curation Service validates the descriptor against schema and ownership completeness; incomplete submissions are rejected with a specific diagnostic (mirroring PLM's fail-fast validation pattern).
4. On acceptance, the Module Catalog persists the record with status **Active**, and the Dependency Graph Engine ingests any declared dependencies.
5. Over the module's life, `updateModule()` calls record new versions and interface changes; the Dependency Graph Engine is queried by dependents before they accept an upgrade, mirroring PLM's Compatibility Checker pattern but at design-time rather than runtime activation-time.
6. When a module is no longer needed, `deprecate()` initiates the Deprecation & Retirement Tracker workflow: dependents are enumerated via `getDependents()`, notified, and given a governed migration window before the module's status moves to **Retired**.

## 7. Design Patterns

- **Catalog / registry pattern** — the same conceptual pattern as PLM's Plugin Registry, applied at design-time governance granularity rather than runtime lifecycle granularity.
- **Gatekeeper on creation, not just on change** — unlike many registries that only govern change, EMR's primary enforcement point is *before* a new module is created (the mandatory discovery-search step), directly targeting the duplicate-capability problem in §1.
- **Graph-based impact analysis** — the Dependency Graph Engine mirrors PLM's Dependency Resolver graph model, but is queried for impact analysis (who depends on this) rather than activation-order computation.
- **Governed deprecation lifecycle** — a lighter-weight, design-time analog of PLM's DISABLING/DISABLED/REMOVED states, adapted for modules that don't have a runtime activation lifecycle of their own.

## 8. Security Considerations

- **Write-access governance** — only a module's recorded owner (or a designated governance role) may submit `updateModule()` or `deprecate()` calls affecting that module; the Registration & Curation Service must enforce this, not merely document it as policy.
- **No secrets in descriptors** — module descriptors (interfaces, dependency declarations) are metadata only; they must never carry credentials, connection strings, or other secret material, mirroring the manifest-hygiene rule in PLM §8.
- **Audit trail on ownership transfer** — reassigning a module's owner is a sensitive operation and must be logged with actor, prior owner, new owner, and timestamp, given its downstream effect on who can authorize changes.
- **Read access is broad by design** — because discoverability is a core goal (§2), the Capability Search surface should default to open read access across the organization; restricting read access undermines the "reuse before creating" enforcement mechanism.

## 9. Scalability

- **Read-heavy workload** — Capability Search and `getModule`/`getDependents` queries will vastly outnumber registration/update writes; the Module Catalog should be optimized (indexed, cacheable) for its read path, mirroring the Registry read/write split noted in PLM §9.
- **Dependency graph queries can be precomputed** — `getDependents` (impact analysis) is a natural candidate for a maintained reverse-index rather than a live graph traversal on every query, especially as module count grows.
- **Search relevance at scale** — as the catalog grows, keyword/tag search alone will degrade in usefulness; this document flags (without specifying) that capability-shape or semantic search may become necessary — see §18 Future Evolution.
- **Federation across organizational units** — if multiple engineering organizations maintain separate registries, a future federation layer would need to reconcile identity and avoid duplicate registration across registries, not just within one.

## 10. Best Practices

- Make the discovery-search step a procedurally enforced gate in the design-review workflow, not a suggested courtesy — an unenforced "please check first" is routinely skipped.
- Require exactly one owner per module at all times; "no owner" or "co-owned with no tiebreaker" states should be schema-invalid, not merely discouraged.
- Version module interfaces independently from the module's internal implementation version, so consumers depend on a stable declared contract rather than incidental internal versioning.
- Treat deprecation as a first-class, governed workflow with a mandatory notice period — never silently delete a module record a live dependent still references.
- Keep module descriptors declarative metadata only; resist the temptation to let the registry become a second, informally-authoritative copy of implementation details that will drift from reality.

## 11. Common Pitfalls

- **Registry as documentation theater** — a catalog that is populated once and never kept current is worse than no catalog, because it actively misleads reuse decisions; staleness must be actively governed (e.g., periodic ownership attestation).
- **Skipping the discovery-search gate under deadline pressure** — the single most common failure mode that reintroduces duplicate capabilities; this is a process risk, not just a tooling risk, and must be backed by review-workflow enforcement, not goodwill alone.
- **Conflating module boundary with team/org boundary** — defining "module" purely along org-chart lines rather than capability cohesion produces registry entries that don't map to a coherent, reusable unit.
- **No distinction between "deprecated" and "retired"** — silently removing a deprecated module's record before dependents have migrated causes exactly the kind of breakage this registry exists to prevent.
- **Treating this registry as a runtime service directory** — conflating EMR's design-time governance role with a runtime service-discovery/mesh concern leads to inappropriate latency and availability expectations being placed on what should be a low-traffic governance system.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **No registry; rely on documentation/tribal knowledge** | Capability discovery via wikis, chat history, or asking around. | Directly fails the "reuse before creating" and "avoid duplicate capabilities" principles at any meaningful organizational scale; status quo this document replaces. |
| **Code-derived auto-catalog (static analysis of repositories)** | Automatically infer a module catalog by scanning source code/import graphs. | Attractive for staying "current," but infers interfaces and ownership rather than having them declared and governed; produces a catalog of *what exists* without the ownership/governance metadata (owner, deprecation status) that is core to this document's goals. May be a valuable *input/validation* signal for EMR in the future (see §18) rather than a replacement for a governed, declarative catalog. |
| **Fold module cataloging into the Plugin Registry (PLM)** | Reuse PLM's Plugin Registry component for first-party modules too, avoiding a second store. | Rejected due to differing cardinality, lifecycle, and goal: PLM's registry is built around a runtime activation state machine; forcing always-present, non-activatable modules through that model would either distort PLM's state machine or require bypassing most of it, undermining PLM's own design integrity. Kept as two documents with an explicit boundary (§1) instead. |
| **Fully manual governance board approval for every module** | A human review board is the sole gate for registering/deprecating modules, with no queryable catalog. | Provides governance but not discoverability; doesn't scale, and doesn't solve the core "can't find what exists" problem — a catalog is still needed even if a board also approves changes to it. |

## 13. Migration Strategy

1. **Stand up the Module Catalog and backfill it** with descriptors for existing first-party modules, including a best-effort reconstruction of ownership and interfaces where not already documented.
2. **Publish the Capability Search surface read-only** organization-wide before enforcing any write-side governance, so teams can start benefiting from discoverability immediately.
3. **Introduce the discovery-search gate as advisory** in the design-review workflow (recommended, not blocking) for an initial period, to surface friction in the query experience before it becomes mandatory.
4. **Make the discovery-search step procedurally mandatory** once the advisory period shows acceptable query-experience quality — no new module proposal proceeds to Architecture phase without a recorded search.
5. **Enforce single-owner and schema completeness** on all new registrations immediately; backfill records may be grandfathered with a flagged "ownership pending attestation" status rather than blocked retroactively.
6. **Introduce the governed deprecation workflow** for any module retirement from this point forward, replacing any prior ad hoc retirement practice.

## 14. Success Criteria

- 100% of first-party modules have a catalog record with a single recorded owner and declared interfaces.
- Zero new modules created without a preceding, recorded discovery-search query (post-enforcement).
- Measurable reduction in duplicate-capability incidents (tracked qualitatively via design review findings) after enforcement begins, relative to the pre-registry baseline.
- 100% of module deprecations follow the governed timeline (announcement → dependent notification → migration window → retirement) with no silent removals.
- Dependency impact analysis (`getDependents`) returns results fast enough to be used inline during design review, not as an offline/batch process.

## 15. Decision Matrix

| Criterion (weight) | Centralized Module Catalog + mandatory discovery gate (recommended) | No registry / tribal knowledge | Code-derived auto-catalog only | Folded into PLM's Plugin Registry | Manual governance board only |
|---|---|---|---|---|---|
| Reuse enforcement (High) | 5 | 1 | 3 | 3 | 2 |
| Ownership clarity (High) | 5 | 1 | 2 | 3 | 4 |
| Dependency transparency (High) | 5 | 1 | 3 | 3 | 2 |
| Deprecation governance (Medium) | 5 | 1 | 1 | 3 | 4 |
| Currency / staleness resistance (Medium) | 3 | 1 | 5 | 3 | 2 |
| Design integrity (does not distort another system) (Medium) | 5 | 5 | 4 | 1 | 5 |
| Low-friction adoption (High) | 3 | 5 | 4 | 2 | 1 |
| **Weighted outcome** | **Best overall fit** | Fails core goals | Strong on currency, weak on governance | Fails design-integrity relative to PLM | Fails scale/discoverability |

**Conclusion**: the centralized Module Catalog with a mandatory discovery-search gate is recommended. Its main weakness relative to alternatives is adoption friction and currency risk (§11), both of which are mitigated procedurally in the Migration Strategy (§13) rather than architecturally — an accepted trade-off, consistent with the treatment of complexity in ADR-EAL-001.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-002: Centralized Module Registry, Distinct from the Plugin Registry**

- **Status**: Accepted
- **Context**: The platform needs a governed, queryable catalog of its own first-party modules to make "reuse before creating" and "avoid duplicate capabilities" enforceable. A related but distinct system, the PLM Plugin Registry (ADR-EAL-001), already governs runtime plugin lifecycle.
- **Decision**: Establish a separate Enterprise Module Registry with its own Module Catalog, Registration & Curation Service, Capability Search, Dependency Graph Engine, and Deprecation Tracker — explicitly not folded into the PLM Plugin Registry. The Module Registry and Plugin Registry remain permanently separate architectural components; modules represent first-party core platform capabilities and form part of the architectural baseline, while plugins represent optional extension packages with independent lifecycle, discovery, versioning, installation, activation, and compatibility (owned by PLM). These registries are not to be merged. Instead, a future **Enterprise Capability Registry** is planned to map capabilities to either modules or plugins, without changing the ownership of either existing registry.
- **Rationale**: Modules (always-present, first-party, non-activatable in the runtime-state-machine sense) and plugins (dynamically installable/removable, runtime-lifecycled) differ enough in cardinality, lifecycle, and primary goal (discoverability/reuse vs. runtime isolation/safety) that a shared registry would compromise either system's design integrity (§12 alternatives). The Decision Matrix (§15) confirms the folded-in alternative scores lowest on design integrity among viable options. Cross-cutting capability discovery — the legitimate need that might otherwise motivate merging the two registries — is better served by a thin mapping layer (the future Enterprise Capability Registry) that references both registries by identity rather than absorbing either one's ownership or schema.
- **Consequences**:
  - *Positive*: each registry stays optimized for its actual purpose; EMR can evolve its search/discovery capabilities without runtime-safety constraints, and PLM can evolve its state machine without design-time governance constraints; cross-cutting capability lookup becomes possible later without retrofitting either registry.
  - *Negative*: two registries to operate and keep the boundary between clear, plus (once built) a third mapping layer to keep in sync with both; risk of future scope creep at the boundary (a module that also wants runtime plugin-like lifecycle) must be resolved via a future ADR, not informal convention (flagged explicitly in §1).
  - *Neutral*: requires module owners to learn a second, related-but-different governance surface from plugin authors.
- **Alternatives rejected**: no registry, code-derived-only catalog, folded into PLM, manual board only — see §12 and §15.
- **Reversibility**: Reversible before broad adoption (catalog could be merged into PLM's registry with schema changes); increasingly costly to reverse once dependency graph and deprecation history accumulate. The future Enterprise Capability Registry is additive and does not reduce this reversibility.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Catalog, discovery, dependency graph, and deprecation model are specified at architecture level. |
| **Boundary with PLM** | Confirmed at approval | §1 and ADR-EAL-002 (Accepted) define the boundary as permanent; registries remain separate, reconciled only via the planned Enterprise Capability Registry mapping layer. |
| **Technology-agnostic validation** | Ready | No binding to a specific datastore, search technology, or transport. |
| **Security model maturity** | Ready for design review | Write-governance and audit-on-ownership-transfer are defined; no threat model performed yet. |
| **Process enforceability** | Needs decision | The mandatory discovery-search gate (§10, §13) depends on integration with the design-review workflow itself, which is an organizational/process decision outside this document's authority to unilaterally mandate. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Enterprise Capability Registry (approved direction, next document)** — a dedicated mapping layer that indexes capabilities across both the Module Registry and the PLM Plugin Registry, letting a consumer ask "who provides capability X" without caring whether the answer is a module or a plugin, and without either registry ceding ownership of its own records. This is the approved mechanism (ADR-EAL-002) for cross-cutting discovery, superseding any notion of merging the two registries.
- **Semantic/capability-shape search** — moving beyond keyword/tag search toward matching on declared interface shape or behavioral description, addressing the search-relevance-at-scale concern in §9; directly relevant to the Capability Registry's discovery surface.
- **Code-derived catalog validation** — using static analysis (§12) not as a replacement catalog but as a *drift detector*, flagging when actual inter-module imports diverge from declared dependencies in the registry.
- **Cross-registry federation** — reconciling multiple organizational registries (§9) if the platform's engineering organization grows to a scale with independently-operated registries.
- **Automated reuse suggestions in design tooling** — surfacing Capability Search results proactively within the design-review workflow itself, rather than requiring a manual query step, once the mandatory-gate process (§13 step 4) is stable.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-002.
