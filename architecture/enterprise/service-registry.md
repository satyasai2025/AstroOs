---
title: Enterprise Service Registry
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Service Registry

## 1. Problem Statement

Three prior, frozen documents in this library each answer a design-time question:

- [Enterprise Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) — governs whether an installable extension is safely activatable.
- [Enterprise Module Registry](module-registry.md) (ADR-EAL-002) — catalogs what first-party capability units exist, for reuse and ownership purposes.
- [Enterprise Capability Registry](capability-registry.md) (ADR-EAL-003) — answers "what provides capability X," resolving a stable Capability ID to its current module-or-plugin provider.

None of these answer a fourth, distinct, runtime question: **given a provider (a module or an active plugin) that is known to implement a capability, which specific running instance of it should actually receive a request right now, and is that instance healthy?** ECR's own non-goals (Capability Registry §2) explicitly exclude "runtime service discovery/routing" — that gap is deliberate and is what this document addresses.

Without a dedicated answer to this question, systems tend to either hardcode network addresses (brittle under scaling/redeployment), reinvent ad hoc health-check/routing logic per provider (inconsistent, duplicated), or conflate design-time capability existence with runtime reachability (a capability being "Stable" in ECR says nothing about whether any instance of its provider is currently up).

The Enterprise Service Registry (ESR) is the runtime companion to the three design-time registries: it tracks live, network-addressable **service instances** — the actual running deployments that back a module or an active plugin — their health, and enough routing metadata to let request-time traffic reach a healthy instance.

## 2. Goals

| Goal | Description |
|---|---|
| **Runtime instance tracking** | Every live service instance backing a module or plugin is registered with its network address and health state. |
| **Fast, request-path-suitable lookups** | Unlike ECR (a design-time/governance surface), ESR must answer queries with latency and availability characteristics suitable for being on or near the actual request path. |
| **Health-aware routing input** | Consumers (load balancers, gateways, calling services) can exclude unhealthy instances without each reimplementing health-check logic. |
| **Clean layering under the design-time registries** | ESR references Module/Plugin/Capability identities from the existing registries; it does not redefine or re-govern module, plugin, or capability identity. |
| **Deployment elasticity** | Instances can register and deregister continuously (scale-up, scale-down, redeploy) without touching any design-time registry record. |
| **Multi-instance load distribution input** | Where multiple healthy instances exist for the same provider, ESR exposes enough information (not necessarily the routing decision itself) for a consumer or gateway to distribute load. |

**Non-goals**: ESR is not a load balancer or API gateway itself — it is the data source such components consume; it does not perform the routing decision or proxy traffic. It does not replace PLM's activation state machine (a plugin can be ACTIVE in PLM with zero currently-registered live instances in ESR during a rolling deploy — these are related but distinct signals). It does not alter module/plugin/capability identity, ownership, or design-time lifecycle in any of the three prior registries.

## 3. Architecture

```
   ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐
   │   Module Registry          │  │   Plugin Registry (PLM)    │  │   Capability Registry      │
   │   (design-time identity)    │  │   (design-time + activation)│  │   (capability → provider)  │
   └─────────────┬─────────────┘  └─────────────┬─────────────┘  └─────────────┬─────────────┘
                 │ provider identity              │ provider identity              │ resolves to
                 │ referenced, not owned          │ referenced, not owned          │ provider identity
                 └────────────────┬────────────────┴────────────────┬────────────────┘
                                  │                                  │
                    ┌─────────────▼──────────────┐                  │
                    │   Instance Registration      │  ← instances register/       │
                    │   Service                    │    deregister themselves      │
                    └─────────────┬──────────────┘                  │
                                  │                                  │
                    ┌─────────────▼──────────────┐                  │
                    │   Service Instance Directory  │  ← provider identity →      │
                    │   (runtime store)             │    {instance, address,       │
                    │                                │     health, metadata}        │
                    └─────────────┬──────────────┘                  │
                                  │                                  │
                    ┌─────────────▼──────────────┐                  │
                    │   Health Check Aggregator     │  ← active/passive health     │
                    └─────────────┬──────────────┘    signals                       │
                                  │                                  │
                    ┌─────────────▼──────────────┐                  │
                    │   Instance Query Interface    │◄─────────────────────────────┘
                    │   (request-path-suitable)      │    consumed by gateways,
                    └───────────────────────────┘    load balancers, callers
```

ESR sits *downstream* of all three design-time registries: it references their identities (module ID, plugin ID, Capability ID) but never redefines them, and it is the only one of the four registries whose query interface is designed to sit on or near the actual runtime request path.

## 4. Components

- **Instance Registration Service** — the write path: a running service instance registers itself (on startup) and deregisters (on graceful shutdown) or is reaped (on failure to heartbeat), referencing the module ID or plugin ID it implements.
- **Service Instance Directory** — the runtime store: for each provider (module or plugin identity), holds the set of currently-registered live instances, each with network address, registration timestamp, and current health status.
- **Health Check Aggregator** — collects active (polled) and/or passive (self-reported heartbeat, or inferred from request success/failure) health signals per instance and updates its status in the directory; mirrors PLM's Health & Telemetry Monitor pattern (PLM §4) but at the network-instance level rather than the plugin-lifecycle level.
- **Instance Query Interface** — the request-path-suitable read surface: given a provider identity (or a Capability ID, resolved first via ECR), returns the current set of healthy instances and their addresses.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `registerInstance(providerId, providerType, address, metadata)` | Service instance → Instance Registration Service | An instance announces itself as backing a given module or plugin identity. |
| `deregisterInstance(instanceId)` | Service instance → Instance Registration Service | Graceful removal on planned shutdown. |
| `heartbeat(instanceId, healthSignal)` | Service instance → Health Check Aggregator | Periodic liveness/health self-report. |
| `getHealthyInstances(providerId)` | Consumer (gateway/caller) → Instance Query Interface | The primary request-path query: current healthy instances for a given module/plugin identity. |
| `getInstancesForCapability(capabilityId)` | Consumer → Instance Query Interface (via ECR) | Convenience path: resolve a Capability ID via the Capability Registry first, then query instances for the resolved provider — chains ECR and ESR without merging them. |
| `reapStaleInstances()` | Health Check Aggregator (internal) → Service Instance Directory | Removes instances that have missed heartbeats beyond a defined threshold, preventing the directory from serving stale addresses indefinitely. |

## 6. Data Flow

1. A service instance implementing a module or an active plugin starts up and calls `registerInstance()`, referencing the module ID (Module Registry) or plugin ID (PLM) it implements — ESR does not validate that this ID is "correct" beyond confirming it exists in the referenced design-time registry; ownership/identity validation remains that registry's job.
2. The instance begins sending `heartbeat()` signals (or is actively polled by the Health Check Aggregator, depending on deployment model); the Directory's health status for that instance updates accordingly.
3. A consumer needing to reach a live instance of a known provider calls `getHealthyInstances(providerId)` directly, or — if it only knows a Capability ID — first resolves that ID via ECR's `resolveCapability()` (Capability Registry §5) and then calls ESR with the resolved provider identity.
4. The Instance Query Interface returns the current healthy instance set; the caller (or an intermediary gateway/load balancer consuming ESR as its data source) makes the actual routing decision — ESR itself does not proxy or route traffic.
5. On planned shutdown, the instance calls `deregisterInstance()`. On unplanned failure, missed heartbeats past a threshold trigger `reapStaleInstances()`, removing it from the healthy set without requiring the instance's own cooperation.
6. None of this activity touches the Module Registry, PLM, or ECR — a scale-up/scale-down event or a rolling redeploy is invisible to all three design-time registries, exactly as intended by the layering in §2's "clean layering" goal.

## 7. Design Patterns

- **Service registry / service discovery pattern** — the classic runtime pattern (as distinct from the design-time "catalog" pattern used by the Module Registry) for letting instances announce themselves and consumers discover current healthy endpoints, without static configuration.
- **Health-aware directory, not a routing engine** — deliberately narrow scope (data source, not decision-maker), mirroring the same separation of concerns ECR uses (mapping layer, not a merged registry) — ESR resolves "what instances exist and are they healthy," leaving load-balancing algorithm choice to the consumer/gateway layer.
- **Heartbeat + reaper (lease pattern)** — instances hold an implicit lease via periodic heartbeats; failure to renew leads to automatic removal, avoiding permanently stale directory entries without requiring graceful cooperation from failed instances.
- **Layered reference, not re-governance** — ESR references identities owned by three other registries (module ID, plugin ID, Capability ID) exactly as ECR references module/plugin identities — the same non-duplication discipline established in ADR-EAL-002 and ADR-EAL-003 is extended here rather than reinvented.

## 8. Security Considerations

- **Registration authentication** — `registerInstance()` must be restricted to instances that can prove they are an authorized deployment of the claimed provider identity (e.g., a deployment credential scoped to that module/plugin), preventing an unauthorized process from registering itself as a live instance of a sensitive provider.
- **Network address exposure scope** — the Instance Query Interface returns network addresses, which is more operationally sensitive information than either the Module Registry or ECR expose; access to `getHealthyInstances()` should be scoped to legitimate internal consumers (gateways, authorized callers), not exposed as broadly as ECR's read-open discovery surface (Capability Registry §8 default).
- **Health signal spoofing** — a compromised or misbehaving instance could self-report healthy status while actually degraded; where feasible, active (polled) health checks should be preferred over, or used to corroborate, passive self-reported heartbeats for higher-trust routing decisions.
- **Stale-entry risk as a security-relevant failure mode** — as with ECR's staleness concern (Capability Registry §8), a directory entry pointing to a decommissioned or compromised address is not merely a performance problem; the reaper's staleness threshold is a security-relevant control, not just a hygiene one.

## 9. Scalability

- **Highest write-churn of any registry in this library** — unlike the Module/Plugin/Capability registries (relatively low-frequency design-time changes), ESR's registration/heartbeat/deregistration volume scales with deployment frequency and instance count, and must be architected for that churn from the outset.
- **Request-path latency budget** — because `getHealthyInstances()` may sit on or near the actual request path (unlike ECR, which is explicitly a design-time/governance surface), ESR's read path requires materially tighter latency guarantees than any other registry in this library.
- **Horizontal scaling of the Directory itself** — the Service Instance Directory should be architected assuming its own read/write load may need independent horizontal scaling separate from any of the three design-time registries.
- **Heartbeat volume management** — at high instance counts, heartbeat frequency/aggregation strategy (batching, sampling, tiered check intervals) becomes a first-order design concern, not an afterthought.

## 10. Best Practices

- Keep ESR strictly a data source, never a routing decision-maker — the moment ESR starts making load-balancing or traffic-shaping decisions itself, its scope has silently expanded beyond this document's boundary and duplicates gateway/load-balancer responsibility.
- Require registration to reference an identity that already exists in the Module Registry or PLM; reject registration for an unknown provider ID rather than silently creating an implicit one, preserving the "clean layering" goal.
- Prefer short heartbeat intervals with automatic reaping over relying on graceful deregistration alone — ungraceful failures (crashes, network partitions) are the common case ESR must handle correctly, not the exception.
- Treat the Capability Registry → Service Registry chain (`resolveCapability()` then `getHealthyInstances()`) as the standard consumer path for "find me a healthy instance of capability X," rather than encouraging consumers to bypass ECR and hardcode provider IDs.

## 11. Common Pitfalls

- **Letting ESR absorb load-balancing logic "since it's already tracking health"** — scope creep that duplicates what dedicated load balancers/gateways already do well, and couples ESR's availability requirements to routing-decision complexity it was never designed to carry.
- **Treating PLM's ACTIVE state as equivalent to "has a live instance"** — these are related but distinct signals (§2 non-goals); a plugin can be ACTIVE in PLM's lifecycle sense while having zero registered instances in ESR during a deploy window, and conflating the two produces incorrect routing assumptions.
- **No automatic reaping, relying solely on graceful deregistration** — guarantees stale entries accumulate under any ungraceful failure mode, which is the normal failure mode in distributed systems, not a rare edge case.
- **Exposing the full Instance Query Interface as broadly as ECR's read-open search** — copying ECR's "read access is broad by design" posture (Capability Registry §8) onto ESR ignores that network addresses are materially more sensitive than capability-to-provider mappings.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Fold instance tracking into PLM's Plugin Registry** | Extend PLM to also track live network instances per plugin. | PLM's registry is a design-time/activation-state authority (ADR-EAL-001); it does not currently carry request-path-latency guarantees or heartbeat-churn architecture, and modules (which also need instance tracking) aren't governed by PLM at all — would require distorting PLM's scope or leaving modules uncovered. |
| **Fold instance tracking into the Capability Registry** | Extend ECR to also resolve directly to live network addresses. | ECR is explicitly scoped as a design-time/governance mapping layer, not a request-path component (Capability Registry §2 non-goals); merging would force ECR to meet request-path latency/availability SLAs it wasn't designed for, and would blur the same "read-only mapping vs. runtime data" distinction ADR-EAL-003 was built to preserve. |
| **No dedicated registry; rely on external service mesh/DNS-based discovery only** | Use existing infrastructure-layer service discovery (e.g., DNS, a service mesh's own registry) without a platform-level ESR. | Viable as an *implementation substrate* for ESR, but does not by itself provide the module/plugin/capability-identity-aware layering this library requires (§2's "clean layering" goal); infrastructure-layer discovery typically has no concept of a Capability ID or module/plugin identity, requiring a mapping layer on top regardless — which is what this document defines, whatever the eventual implementation substrate. |
| **Fully static configuration (no dynamic registry)** | Network addresses configured manually per environment, no self-registration. | Fails the deployment elasticity goal outright and reintroduces exactly the brittleness (§1) this document exists to solve; unworkable at any meaningful scale of independently-deployed instances. |

## 13. Migration Strategy

1. **Define the provider-identity reference contract** — establish that `registerInstance()` requires a module ID or plugin ID that already exists in the respective design-time registry, before any instance registration logic is built.
2. **Stand up the Instance Registration Service and Directory** independently of any existing ad hoc discovery mechanism (DNS entries, static config, mesh-native registry), allowing both to run in parallel initially.
3. **Onboard instances incrementally**, starting with providers that most benefit from dynamic health-aware routing (highest deployment frequency or elasticity needs), rather than a big-bang cutover.
4. **Wire the Instance Query Interface into one consuming gateway/load balancer** as a pilot, validating latency and correctness before wider adoption.
5. **Establish the Capability Registry → Service Registry chained lookup** (§10) as the recommended consumer pattern once both ECR and ESR are operating, so new consumers default to capability-based lookup rather than hardcoded provider IDs.
6. **Decommission the legacy static/ad hoc discovery mechanism** once all relevant providers are onboarded and the pilot gateway has operated within target latency/availability for a full measurement period.

## 14. Success Criteria

- 100% of onboarded providers' live instances are discoverable via `getHealthyInstances()` with no manually-maintained address configuration remaining for them.
- `getHealthyInstances()` read latency stays within the request-path-suitable target defined during implementation planning (materially tighter than ECR's design-time query latency).
- Mean time from instance failure (crash/network partition) to removal from the healthy set (via reaping) is within an agreed SLA.
- Zero incidents of traffic routed to a deregistered or reaped instance due to stale directory data.
- The Capability Registry → Service Registry chained lookup is demonstrated end-to-end for at least one representative capability, validating the intended layering across all four registries in this library.

## 15. Decision Matrix

| Criterion (weight) | Dedicated Service Registry, layered under existing registries (recommended) | Fold into PLM | Fold into Capability Registry | No dedicated registry (mesh/DNS only) | Fully static configuration |
|---|---|---|---|---|---|
| Runtime instance tracking (High) | 5 | 3 | 3 | 4 | 1 |
| Request-path latency suitability (High) | 5 | 2 | 2 | 4 | 5 |
| Clean layering / preserves prior ADRs (High) | 5 | 1 | 1 | 3 | 4 |
| Deployment elasticity (High) | 5 | 3 | 3 | 5 | 1 |
| Health-aware routing input (Medium) | 5 | 3 | 3 | 3 | 1 |
| Coverage of both modules and plugins (Medium) | 5 | 2 | 4 | 4 | 3 |
| Operational simplicity (Medium, lower new-infra = better fit) | 3 | 4 | 4 | 5 | 5 |
| **Weighted outcome** | **Best overall fit** | Fails layering + module coverage | Fails layering (ECR scope violation) | Missing identity-aware layering | Fails elasticity goal |

**Conclusion**: a dedicated Service Registry, referencing but not absorbing the three existing design-time registries, is recommended. It is the only option that meets the request-path latency and deployment-elasticity goals while preserving the layering discipline established by ADR-EAL-002 and ADR-EAL-003 — folding instance tracking into either PLM or ECR would repeat the exact scope-violation problem those ADRs were written to avoid.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-004: Dedicated Enterprise Service Registry, Layered Under the Design-Time Registries**

- **Status**: Accepted
- **Context**: The Module Registry (ADR-EAL-002), Plugin Registry (ADR-EAL-001), and Capability Registry (ADR-EAL-003) together answer what capabilities exist and who provides them, but none tracks live, network-addressable runtime instances or their health — a gap ECR's own non-goals explicitly identify.
- **Decision**: Introduce a dedicated Enterprise Service Registry, kept **independent** as the runtime registry, layered *underneath* the three existing registries by reference only. The standard consumer path is confirmed and retained as: **Capability → ECR → Module/Plugin → ESR** — a consumer resolves a Capability ID via the Capability Registry to its current module-or-plugin provider, then queries ESR for that provider's healthy live instances. ESR owns instance registration, health aggregation, and a request-path-suitable query interface; it does not alter or duplicate any design-time identity, ownership, or lifecycle state owned by the other three registries, and it does not perform routing/load-balancing itself.
- **Rationale**: The Decision Matrix (§15) shows that folding instance tracking into either PLM or ECR would violate the layering discipline both of those systems' own ADRs were built to preserve (design-time governance vs. runtime data, in ECR's case explicitly stated as a non-goal). A dedicated, independent registry is the only option meeting the request-path latency and deployment-elasticity goals without that violation, and the confirmed chained lookup (Capability → ECR → Module/Plugin → ESR) preserves each registry's single responsibility rather than collapsing two calls into one at the cost of blurred ownership.
- **Consequences**:
  - *Positive*: completes the four-layer model (identity/ownership → activation lifecycle → capability mapping → runtime instance/health), each with clean, non-overlapping responsibility; each of the four registries can independently scale and evolve to its own actual requirements (e.g., ESR's much higher write-churn and tighter latency needs vs. the other three); the retained chain gives consumers one canonical path to follow rather than multiple ad hoc shortcuts.
  - *Negative*: introduces a fourth operational component to the library, with its own availability requirements that are now closer to the critical request path than any of the other three; requires providers to integrate a registration/heartbeat client.
  - *Neutral*: consumers wanting "a healthy instance of capability X" compose two calls (ECR then ESR) rather than one — an explicit, intentional, now-confirmed trade-off preserving separation of concerns over convenience.
- **Alternatives rejected**: folding into PLM, folding into ECR, mesh/DNS-only discovery without identity-aware layering, fully static configuration — see §12 and §15.
- **Reversibility**: Reversible in principle (instance tracking could later be absorbed elsewhere via a superseding ADR), but the request-path dependency that consumers/gateways would develop on ESR makes reversal operationally costly once adopted — comparable in cost profile to reversing PLM adoption (PLM §13) rather than to ECR's low-cost reversibility (Capability Registry ADR-EAL-003).

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Registration, health aggregation, and query interface are specified at architecture level, layered consistently with all three prior frozen documents. |
| **Consistency with ADR-EAL-001/002/003** | Confirmed | References but does not alter any identity, ownership, or lifecycle state owned by the three prior registries. |
| **Technology-agnostic validation** | Ready | No binding to a specific service mesh, DNS system, or health-check protocol. |
| **Security model maturity** | Ready for design review | Registration authentication and network-address exposure scoping are defined (§8); no formal threat model performed yet. |
| **Latency/availability model** | Needs decision | Concrete SLA targets for request-path query latency (§9, §14) are flagged for implementation planning, not fixed here. |
| **Dependency on prior documents** | Depends on Module Registry, PLM, and Capability Registry remaining stable | Any future superseding ADR to those three would require a corresponding review of this document's reference contracts. |
| **Consumer chain** | Confirmed at approval | Capability → ECR → Module/Plugin → ESR retained as the canonical lookup path (ADR-EAL-004). |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Traffic-shaping metadata (not decisions)** — ESR could expose additional per-instance metadata (load, latency percentile, version) to inform, without making, routing decisions consumed by gateways/load balancers.
- **Multi-region/multi-cluster instance federation** — extending the Directory to reconcile instance visibility across regions or clusters, analogous to the cross-registry federation noted as future evolution for both the Module Registry and Capability Registry.
- **Automatic capability-maturity-aware routing hints** — combining ECR's Capability Lifecycle (Capability Registry, Appendix B) with ESR's health data so a consumer could request "a STABLE-maturity, healthy instance of capability X" in one chained query rather than two separate decisions.
- **Canary/progressive rollout support** — tagging newly-registered instances with a rollout cohort so gateways can gradually shift traffic to a new version, echoing the progressive-activation future evolution already flagged in PLM (§18) but at the instance-routing-input level rather than the activation-lifecycle level.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-004.
