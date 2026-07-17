---
title: Enterprise Capability Registry
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Capability Registry

## 1. Problem Statement

Two prior, frozen documents in this library each govern a distinct registry:

- [Enterprise Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) — the **Plugin Registry**, governing dynamically-lifecycled, independently-versioned extension packages.
- [Enterprise Module Registry](module-registry.md) (ADR-EAL-002) — the **Module Registry**, governing always-present, first-party core platform capabilities.

ADR-EAL-002 explicitly decided these two registries must remain separate and must not be merged, because they differ in cardinality, lifecycle model, and primary governance goal. That decision is sound, but it leaves a real gap: **a consumer asking "what in this platform provides capability X" has no single place to look.** They must know in advance whether the capability they need lives in a module or a plugin, then query the correct registry — and if they guess wrong, they may conclude the capability doesn't exist and create a duplicate, directly undermining the "reuse before creating" principle that motivated the Module Registry in the first place.

The Enterprise Capability Registry (ECR) closes this gap. It is a thin, read-oriented mapping layer that indexes capabilities by what they *do*, and resolves each capability to its provider — whether that provider is a module (Module Registry) or a plugin (Plugin Registry) — without taking ownership of, or duplicating, either underlying registry's records.

## 2. Goals

| Goal | Description |
|---|---|
| **Unified discovery** | A single query surface answers "what provides capability X," regardless of whether the provider is a module or a plugin. |
| **Zero ownership transfer** | ECR never becomes the authoritative record for a module or plugin; it only references records that live in their respective registries. |
| **Non-duplication of data** | Capability descriptions in ECR point to the source-of-truth registry rather than copying mutable fields (version, status) that could drift. |
| **Provider-agnostic consumers** | Tooling built against ECR (e.g., design-review "reuse before creating" checks) should not need provider-specific logic. |
| **Low staleness risk** | Because ECR is a mapping layer, not a second source of truth, it must be kept synchronized with both underlying registries with a bounded, known staleness window. |

**Non-goals**: ECR does not manage lifecycle state for modules or plugins (both remain owned by their respective registries), does not perform runtime service discovery/routing, and does not replace either registry's own search surface — it supplements them for the specific cross-cutting question neither can answer alone.

## 3. Architecture

```
   ┌───────────────────────────┐        ┌───────────────────────────┐
   │   Module Registry          │        │   Plugin Registry          │
   │   (source of truth,        │        │   (source of truth,        │
   │    ADR-EAL-002)             │        │    ADR-EAL-001)             │
   └─────────────┬─────────────┘        └─────────────┬─────────────┘
                 │  capability                          │  capability
                 │  declarations                         │  declarations
                 │  (reference, not copy)                │  (reference, not copy)
                 └───────────────┬────────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Capability Index         │  ← maps capability →
                    │   (mapping store)          │    {provider type, provider ID}
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Sync / Reconciliation    │  ← keeps the index current
                    │   Service                  │    against both registries
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Unified Capability       │  ← the single query surface
                    │   Search                   │    consumers actually use
                    └───────────────────────────┘
```

ECR sits *beside*, not *above*, the two existing registries. It has no write authority over either — the Module Registry's Registration & Curation Service and PLM's Lifecycle Controller remain the sole writers of their own records.

## 4. Components

- **Capability Index** — the mapping store: for each globally unique Capability ID (see Appendix A), records the resolution chain **Capability → Module or Plugin → Version → Status → Dependencies → Interfaces → Documentation**. Every field past the Capability ID itself is a *reference or last-synced projection* sourced from the owning registry (Module Registry or PLM's Plugin Registry) — never an independently authored value. The Capability Index remains, by definition, a read-only mapping layer: it owns the capability-to-provider mapping and nothing else; it never owns business data.
- **Sync / Reconciliation Service** — subscribes to change events from both the Module Registry and the Plugin Registry (registration, update, deprecation for modules; register/activate/quarantine/remove for plugins) and updates the Capability Index accordingly, so the index never has to be manually maintained.
- **Unified Capability Search** — the query surface consumers actually use; answers "what provides capability X" and returns enough identity/type information for the caller to follow through to the correct home registry for full detail (version, status, owner, lifecycle state).

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `searchCapability(query)` | Consumer → Unified Capability Search | The primary cross-cutting discovery query; returns matches tagged with provider type (Module/Plugin) and provider ID, keyed by Capability ID. |
| `resolveCapability(capabilityId)` | Consumer → Capability Index | Direct lookup of a globally unique Capability ID (e.g., `cap.chart.compute`) to its current provider reference and resolution chain (Module/Plugin → Version → Status → Dependencies → Interfaces → Documentation). |
| `onModuleRegistryEvent(event)` | Module Registry → Sync Service | Inbound event subscription: module registered/updated/deprecated/retired. |
| `onPluginRegistryEvent(event)` | Plugin Registry (PLM) → Sync Service | Inbound event subscription: plugin registered/activated/quarantined/removed. |
| `reindex(providerType, providerId)` | Sync Service → Capability Index | Idempotent re-sync of a single provider's capability declarations, used both on live events and for periodic drift correction. |

ECR exposes no write interface to end consumers — all writes to the index originate from the Sync Service reacting to the two source registries' own events, never from a direct external call, which is what preserves the "zero ownership transfer" goal.

## 6. Data Flow

1. A module owner registers or updates a module in the Module Registry (per that document's §6), or a plugin author registers/activates a plugin in PLM (per that document's §6/data flow) — each declaring the capabilities it provides as part of its existing manifest/descriptor, each capability tagged with a globally unique Capability ID following the naming convention in Appendix A (e.g., `cap.chart.compute`). **No new declaration step is introduced by ECR**; it consumes capability declarations that are already part of each registry's existing schema — only the ID convention itself is a new, lightweight requirement on both source registries' existing manifests.
2. That registration/update/lifecycle event is published on each registry's existing event bus (Module Registry's registration events; PLM's lifecycle events, §6 of that document).
3. The Sync/Reconciliation Service consumes both event streams and calls `reindex()` for the affected provider, updating the Capability Index with the current capability-to-provider mapping.
4. A consumer (a developer doing "reuse before creating" research, or automated design-review tooling) calls `searchCapability()` against the Unified Capability Search.
5. Results are returned tagged by provider type and ID; the consumer follows the reference to the Module Registry or Plugin Registry (as applicable) for authoritative, current detail — ECR itself never claims to be the source of truth for that detail.
6. If a plugin is quarantined or a module is deprecated, the corresponding event flows through the same path, and the Capability Index reflects the change on the next sync cycle — bounding staleness to the sync latency, not to a manual re-catalog effort.

## 7. Design Patterns

- **Materialized view / read-model pattern** — the Capability Index is a derived, denormalized read-model over two independent sources of truth, rebuilt from their events rather than being independently authored — the standard way to unify query access across systems without merging their ownership.
- **Event-driven synchronization** — mirrors the event-emission pattern already established in PLM (§6, "every transition emits a lifecycle event") and extends it as the mechanism keeping ECR current, rather than inventing a new integration style.
- **Anti-corruption layer (partial)** — the Sync Service translates two differently-shaped source schemas (module descriptor vs. plugin manifest) into one common capability-mapping shape, without forcing either source registry to change its own schema.
- **CQRS-style separation** — ECR is a pure query-side component; all commands (register, update, deprecate, activate, quarantine) continue to be issued against the two owning registries, never against ECR.

## 8. Security Considerations

- **Read-only exposure by default** — since ECR has no legitimate write path from external consumers, its attack surface is inherently limited to the Sync Service's event subscriptions and the Unified Capability Search's read queries; there is no `registerCapability()` call to secure because one should not exist.
- **Event feed integrity** — the Sync Service must trust its two event sources' authenticity (it is, in effect, a privileged subscriber to both PLM's and the Module Registry's internal event streams); event feed access should be scoped so ECR can only subscribe, never publish, to either source registry's event bus.
- **No new secret surface** — because ECR only stores capability-to-provider mappings and pointers, not descriptors' full detail, it introduces no new location where credentials or sensitive configuration could be duplicated.
- **Referential staleness is a security-relevant failure mode, not just a UX one** — if the index lags a plugin's quarantine event, a consumer could be pointed toward a provider that is no longer safely active; the Sync Service's staleness bound (§9) is therefore a security-relevant success criterion, not merely a performance one.

## 9. Scalability

- **Read-dominant by design** — like both underlying registries, ECR's query volume will vastly exceed its (event-driven, not consumer-driven) write volume; the Capability Index should be optimized purely for search/lookup performance.
- **Eventual consistency is acceptable, but must be bounded** — ECR does not need to be transactionally consistent with either source registry (that would couple it too tightly, reintroducing the ownership problem ADR-EAL-002 avoided), but the Sync Service's event-to-index latency must have a defined, monitored upper bound.
- **Independent scaling from either source registry** — because ECR only consumes events and serves reads, it can scale its query-serving tier independently of write load on the Module Registry or PLM.
- **Periodic reconciliation as a backstop** — in addition to event-driven sync, a periodic full `reindex()` sweep against both registries should exist to correct any missed events, bounding worst-case staleness even under event-delivery failures.

## 10. Best Practices

- Never let ECR's Capability Index become a second authoritative copy of module/plugin detail (version, owner, lifecycle state) — it stores references and enough denormalized data to make search useful, and nothing that would tempt a consumer to skip following the reference back to the source registry.
- Build the Sync Service against each source registry's existing event contract; do not introduce a bespoke "capability declared" event type in either registry solely to feed ECR if the existing registration/lifecycle events already carry the needed information.
- Keep `searchCapability()` results explicitly tagged with provider type — never let a search result look identical for a module-provided and plugin-provided capability, since their operational characteristics (always-present vs. independently lifecycled) differ meaningfully for the consumer's next decision.
- Treat periodic full reconciliation as mandatory infrastructure, not an optional nice-to-have, given that event-driven sync alone cannot guarantee zero missed events over a long operational lifetime.

## 11. Common Pitfalls

- **Letting ECR quietly become a third registry with its own write API** — the moment a "just add a capability directly to ECR" shortcut appears (e.g., for a capability that doesn't yet have a home in either registry), the zero-ownership-transfer goal (§2) is broken and the ADR-EAL-002 boundary erodes by the back door.
- **Copying mutable fields into the index for convenience** — caching a plugin's lifecycle state or a module's version directly in the Capability Index invites drift the moment the source registry changes state faster than sync runs; only the reference/pointer should be treated as reliable, with denormalized fields explicitly labeled as "last known, may be stale."
- **Skipping the periodic reconciliation sweep** — relying solely on event delivery without a backstop turns any missed event (network partition, bus outage) into permanent, silent staleness.
- **Treating ECR search as a replacement for either registry's own detailed search** — ECR answers "which registry and which ID," not "give me full detail"; consumers who stop there without following through to the source registry may act on incomplete information (e.g., missing a module's current deprecation status).

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Merge Module Registry and Plugin Registry** | Combine both into one registry with a shared schema. | Explicitly rejected by ADR-EAL-002 (Accepted); would compromise both registries' design integrity per that ADR's rationale. Superseding this would require its own ADR overriding an already-accepted decision, which is out of scope here. |
| **No cross-cutting registry; require consumers to check both manually** | Leave the gap in §1 unaddressed; document a manual "check both registries" process. | Fails the core discoverability goal that motivated this document; relies on consumer diligence rather than tooling, the same failure mode flagged for the pre-registry state in the Module Registry document (§1). |
| **ECR as a second source of truth (copies full records)** | Build ECR as a full duplicate catalog containing complete module and plugin detail, not just references. | Reintroduces the exact drift/staleness risk both prior documents were designed to avoid; a full copy would need its own governance to stay authoritative, effectively creating a third registry with ownership ambiguity. |
| **Push-based registration into ECR instead of event-driven sync** | Require module/plugin owners to separately register their capabilities directly with ECR. | Adds a manual step duplicating information already present in each registry's existing descriptor/manifest; violates the "no new declaration step" principle in §6 and creates a drift risk if an owner updates one registry but forgets to update ECR. |

## 13. Migration Strategy

1. **Build the Sync Service against existing event streams** from both the Module Registry and PLM's Plugin Registry — no schema change is required in either source registry, since both already declare capabilities as part of their existing manifests/descriptors.
2. **Run an initial full `reindex()` sweep** across all currently-registered modules and plugins to populate the Capability Index from a cold start.
3. **Expose Unified Capability Search read-only** to a limited pilot group (e.g., design-review facilitators) to validate result quality and staleness bounds before wider rollout.
4. **Integrate Unified Capability Search into the Module Registry's mandatory discovery-search gate** (Module Registry §13, step 4) so that gate now checks both modules and plugins in one query, rather than requiring a separate plugin-specific check.
5. **Establish the periodic full-reconciliation job** as standing infrastructure before declaring ECR generally available, not as a follow-up task.
6. **Roll out organization-wide** once staleness-bound monitoring (§9) has been observed operating within target for a full measurement period.

## 14. Success Criteria

- A single `searchCapability()` query returns matches spanning both modules and plugins, correctly tagged by provider type, for a representative sample of known cross-cutting queries.
- Measured event-to-index sync latency stays within the defined staleness bound (target to be set during implementation planning) under normal event bus operation.
- Zero instances of ECR being used as a write target for capability data that should have been registered in the Module Registry or Plugin Registry instead (a process/governance metric, not just a technical one).
- The Module Registry's discovery-search gate (its §13 migration step 4) is successfully backed by ECR, eliminating the need for a separate manual plugin-registry check during "reuse before creating" research.
- Periodic reconciliation sweep completes and corrects any drift within its scheduled window, with discrepancies logged and trending toward zero over time.

## 15. Decision Matrix

| Criterion (weight) | ECR as read-only mapping/event-sync layer (recommended) | Merge the two registries | No cross-cutting registry (manual check) | ECR as a second source of truth (full copy) | Push-based manual registration into ECR |
|---|---|---|---|---|---|
| Unified discovery (High) | 5 | 5 | 1 | 5 | 4 |
| Preserves ADR-EAL-002 boundary (High) | 5 | 1 | 5 | 3 | 4 |
| Non-duplication / drift risk (High) | 5 | 3 | 5 | 1 | 2 |
| Low-friction adoption (Medium) | 4 | 2 | 1 | 3 | 2 |
| Operational simplicity (Medium, lower new-infra = better fit) | 3 | 4 | 5 | 2 | 3 |
| Staleness/consistency risk (Medium, lower risk = better fit) | 4 | 5 | 5 | 1 | 2 |
| **Weighted outcome** | **Best overall fit** | Violates accepted ADR-EAL-002 | Fails core discoverability goal | Fails non-duplication goal | Adds manual step, drift risk |

**Conclusion**: a read-only mapping layer synchronized via events from both source registries is recommended. It is the only option that simultaneously satisfies unified discovery, preserves the already-accepted ADR-EAL-002 boundary, and avoids introducing a new drift-prone data copy — the same non-duplication principle both prior documents were built around.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-003: Enterprise Capability Registry as a Read-Only, Event-Synchronized Mapping Layer**

- **Status**: Accepted
- **Context**: ADR-EAL-002 (Accepted) established that the Module Registry and Plugin Registry remain permanently separate, and directed that any cross-cutting capability discovery need be met by a future Enterprise Capability Registry that maps capabilities to modules or plugins without changing either registry's ownership.
- **Decision**: Implement the Enterprise Capability Registry as a read-only Capability Index, populated and kept current by a Sync/Reconciliation Service consuming existing change events from both the Module Registry and PLM's Plugin Registry, exposing a single Unified Capability Search surface to consumers. Every capability is identified by a globally unique, stable Capability ID (naming convention in Appendix A, e.g. `cap.chart.compute`, `cap.rule.evaluate`, `cap.ai.summary`). For a given Capability ID, the index resolves the chain **Capability → Module or Plugin → Version → Status → Dependencies → Interfaces → Documentation**, entirely by reference/last-synced projection — ECR has no write interface for external consumers, stores no authoritative copies of provider records, and never owns business data. Each capability additionally progresses through the lifecycle defined in Appendix B (Proposed → Experimental → Stable → Deprecated → Removed), tracked as index metadata derived from the same source-registry events, not as separately authored state.
- **Rationale**: This design directly fulfills ADR-EAL-002's mandate — it resolves the cross-cutting discovery gap (§1) without merging, duplicating, or transferring ownership of either source registry, and reuses the event-emission pattern already established by both source registries (PLM §6; Module Registry §6) rather than introducing a new integration paradigm. Globally unique Capability IDs make the mapping addressable and stable across provider changes (a capability can move from one module/plugin implementation to another without the ID itself changing), and the Proposed→Removed lifecycle gives consumers a maturity signal independent of the underlying provider's own lifecycle state. The Decision Matrix (§15) shows every alternative either violates the accepted ADR-EAL-002 boundary, fails the core discoverability goal, or reintroduces the drift/staleness risk both prior documents were designed to eliminate.
- **Consequences**:
  - *Positive*: closes the cross-registry discovery gap; keeps both source registries' design integrity intact; adds no new write-governance burden since ECR has no write API; stable Capability IDs decouple "what a consumer depends on" from "which specific module/plugin currently implements it."
  - *Negative*: introduces a third operational component (Sync Service + Capability Index) that must be monitored for staleness; eventual consistency means a brief window exists where the index can lag a source registry's true state; both source registries must adopt the Capability ID naming convention in their manifests, a small but real integration cost.
  - *Neutral*: consumers must understand that ECR answers "who provides this, and at what maturity" but not "give me full current detail" — they must follow references back to the owning registry.
- **Alternatives rejected**: merging the registries, no cross-cutting registry, ECR as a full second source of truth, push-based manual registration — see §12 and §15.
- **Reversibility**: Fully reversible and low-risk to reverse — because ECR holds no authoritative data (only a derived index and ID scheme), it can be decommissioned at any time by simply removing the Sync Service and Unified Capability Search, with no data-loss impact on either source registry.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Index, sync mechanism, and unified search are specified at architecture level, consistent with both source registries' existing event models. |
| **Consistency with ADR-EAL-002** | Confirmed | Design directly implements the mandate in the accepted decision; introduces no merge or ownership transfer. |
| **Technology-agnostic validation** | Ready | No binding to a specific event bus, index technology, or transport. |
| **Security model maturity** | Ready for design review | Read-only exposure and event-feed-integrity considerations are defined (§8); no formal threat model performed yet. |
| **Staleness/consistency model** | Needs decision | A concrete staleness-bound target (§9, §14) is flagged for implementation planning rather than fixed in this architecture document. |
| **Dependency on source registries** | Depends on both frozen documents (PLM, Module Registry) remaining stable | Any future change to either source registry's event schema (via a superseding ADR) would require a corresponding review of this document's Sync Service design. |
| **Capability ID scheme** | Confirmed at approval | Global uniqueness and naming convention defined in Appendix A; both source registries must adopt it in their manifests. |
| **Capability Lifecycle model** | Confirmed at approval | Proposed → Experimental → Stable → Deprecated → Removed defined in Appendix B, derived from source-registry events, not separately authored. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Provider-type-aware ranking** — surfacing modules preferentially over plugins (or vice versa) in search results depending on consumer context (e.g., a "reuse before creating" query for a core capability may prefer a stable module over a plugin still in DEGRADED state).
- **Health/lifecycle-state-aware search filtering** — filtering out plugins currently in QUARANTINED or REJECTED state (PLM lifecycle) from default search results, since ECR's Sync Service already receives those events.
- **Extension to future provider types** — if the platform later introduces a third kind of capability provider beyond modules and plugins, ECR's mapping model is designed to extend to a third source-registry subscription without structural change, provided that provider type also emits equivalent lifecycle/registration events.
- **Capability graph, not just capability list** — evolving the Capability Index into a graph that also captures capability-to-capability relationships (composition, overlap, near-duplicates), supporting more sophisticated "reuse before creating" analysis than exact/keyword matching alone.

---

## Appendix A: Capability Identifier Scheme

Every capability indexed by ECR carries a **globally unique, stable Capability ID**, independent of which module or plugin currently implements it.

**Naming convention**: `cap.<domain>.<action>`

- `cap` — fixed prefix identifying the token as a Capability ID (distinguishes it at a glance from a module ID or plugin ID in logs, search results, and documentation).
- `<domain>` — a lowercase, single-word (or hyphen-free, dot-free) noun identifying the functional area the capability belongs to, e.g. `chart`, `rule`, `ai`.
- `<action>` — a lowercase verb or verb phrase identifying what the capability does within that domain, e.g. `compute`, `evaluate`, `summary`.

Examples: `cap.chart.compute`, `cap.rule.evaluate`, `cap.ai.summary`.

**Properties the scheme must guarantee:**

- **Global uniqueness** — enforced by the Capability Index at registration/sync time; a collision (two providers declaring the same Capability ID) is rejected with a diagnostic identifying both claimants, not silently overwritten.
- **Stability over provider change** — a Capability ID must not change when the underlying module or plugin implementing it changes, is replaced, or is migrated between provider types (a capability moving from a plugin implementation to a module implementation keeps its ID). This is what allows consumers to depend on the *capability*, not the *provider*.
- **No embedded version or provider identity** — the ID itself never encodes a version number or a specific module/plugin name; that information lives in the resolution chain (§4, §6), not the identifier, so the ID remains stable across the Capability Lifecycle (Appendix B) and across provider changes.
- **Namespacing is domain-first, not provider-first** — domains are organized around functional area (`chart`, `rule`, `ai`, etc.), not around which team or provider owns them, keeping the ID meaningful to consumers regardless of internal ownership structure (which is tracked separately via the Module Registry's ownership field or the Plugin Registry's authorship metadata).

## Appendix B: Capability Lifecycle

Independent of the underlying module's or plugin's own lifecycle state (Module Registry Active/Deprecated/Retired; PLM's full activation state machine), each Capability ID carries its own maturity signal, reflecting how safe the *capability* is to depend on:

```
 PROPOSED
     │
     ▼
 EXPERIMENTAL
     │
     ▼
  STABLE
     │
     ▼
 DEPRECATED
     │
     ▼
  REMOVED
```

- **PROPOSED** — the Capability ID has been reserved and declared (by a module owner or plugin author) but the capability is not yet consumable; present in the index for planning/reservation purposes only. Consumers should not build against a PROPOSED capability.
- **EXPERIMENTAL** — the capability is implemented and discoverable via `searchCapability()`/`resolveCapability()`, but its interface may still change without the deprecation guarantees of STABLE. Intended for early consumers who accept churn risk.
- **STABLE** — the capability's interface is considered settled; changes follow normal interface-versioning discipline rather than free-form iteration. This is the maturity level "reuse before creating" searches should generally prefer.
- **DEPRECATED** — the capability is still resolvable but is scheduled for removal; the Capability Index surfaces the deprecation and, where known, a recommended replacement Capability ID. Mirrors the Module Registry's governed deprecation workflow (Module Registry §6, §10) but tracked at the capability level rather than the whole-module level.
- **REMOVED** — the Capability ID no longer resolves to an active provider. The ID itself is never reused for a different capability (permanent retirement of the identifier), preserving historical referential integrity for anything that logged or documented the old ID.

**Governance notes:**

- Capability Lifecycle state is derived from, and must stay consistent with, the underlying provider's own lifecycle events (a plugin entering PLM's REMOVED state, or a module entering Module Registry's Retired status, must drive the corresponding capability toward DEPRECATED/REMOVED) — it is not a separately authored value that could drift from the provider's true state.
- A capability can only reach STABLE once it has at least one provider in a stable/active state in its home registry (Module Registry "Active," or PLM "ACTIVE" with acceptable health) — the Sync Service enforces this precondition rather than allowing manual promotion.
- Multiple providers may implement the same Capability ID over time (e.g., during a migration from a plugin implementation to a module implementation); the Capability Lifecycle tracks the capability's maturity across that transition, while the resolution chain (§4) always reflects the *current* provider.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-003.
