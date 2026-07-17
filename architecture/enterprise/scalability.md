---
title: Enterprise Scalability
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Scalability

## 1. Problem Statement

[Deployment](deployment.md) (ADR-EAL-026) defines how an artifact gets built, promoted, and placed as a running instance; [Service Registry](service-registry.md) (ESR, ADR-EAL-004) tracks instances once they exist. Neither answers a prior question: **how many instances of a given capability's provider should be running at any given time, and what triggers adding or removing capacity?** That is capacity/scaling policy, and no prior document owns it.

This document is scoped precisely, using the relationship framing confirmed at approval:

**Uses** (Scalability actively drives these mechanisms to do its work):
- **Capability Registry** — a scaling policy is defined per Capability ID, resolved through the standard Capability → ECR → Module/Plugin → ESR chain to know what's actually being scaled.
- **Workflow Engine** — a scale-up or scale-down action is an ordinary Workflow Engine definition (provision → call Deployment's unchanged `deploy()` → ESR registration → PLM/Module Registry activation, or the reverse for scale-down) — never a second orchestrator.
- **Event Bus** — scaling decisions and completions (scale-up triggered, scale-down completed) publish as ordinary events for any interested subscriber.

**Consumes** (Scalability reads from these as inputs/gates, without owning them):
- **IAM (Identity & Access)** — scaling actions, especially scale-down/termination, are gated by the unchanged `checkPermission()`.
- **Licensing** — a tenant's plan may cap maximum instance count or scaling tier; Scalability reads this via Licensing's unchanged entitlement query, never redefining entitlement itself.
- **Configuration (ECF)** — scaling thresholds (CPU%, queue depth, min/max instances) are ordinary, layered ECF configuration values.

**Does NOT own** (explicitly out of scope, even though each is adjacent enough to invite scope creep):
- **Identity** — no authentication/authorization mechanism of its own; strictly consumes Identity & Access's unchanged gate.
- **Scheduling** — no time-based triggering mechanism of its own; a periodic capacity check dispatches *to* a Scalability capability from Scheduling, per that document's own permanent when-not-how principle (ADR-EAL-016) — Scalability never implements a timer.
- **Observability** — no metrics collection/storage pipeline of its own; reads scaling-relevant signals from EOA's existing Metrics Store as an ordinary consumer, never operating or redefining the observability pipeline itself.
- **Error Handling** — no new error taxonomy; scaling-action failures classify via EEHF's existing taxonomy with namespaced codes, exactly like every other document in this library.
- **Deployment** — no artifact build/promote/placement mechanism of its own; a scale-up action's "get a new instance running" step is literally a call into Deployment's unchanged `deploy()` — Scalability decides *how many*, Deployment remains the sole authority on *how an artifact gets onto an instance*.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| What is being scaled | Capability Registry (ADR-EAL-003) | Scaling policy is defined per Capability ID. |
| Executing a scale action | Workflow Engine (ADR-EAL-013) | Scale-up/down is an ordinary workflow definition; Deployment's `deploy()` is one of its steps. |
| Announcing scaling decisions | Event Bus (ADR-EAL-014) | Ordinary `publish()` — no new pub/sub mechanism. |
| Authorizing a scale action | Identity & Access (ADR-EAL-018) | Unchanged `checkPermission()`. |
| Capping instance count by plan tier | Licensing (ADR-EAL-022) | Unchanged entitlement query. |
| Scaling thresholds | Configuration Framework (ADR-EAL-005) | Ordinary layered config. |
| Scaling-relevant metrics | Observability Architecture (ADR-EAL-010) | Read-only consumption of EOA's existing Metrics Store — not owned. |
| Failure classification | Error Handling Framework (ADR-EAL-009) | Existing taxonomy, new `err.scalability.*` codes — not a new taxonomy. |
| Time-based capacity checks | Scheduling (ADR-EAL-016) | Scheduling dispatches to a Scalability capability at the right time; Scalability owns no timer. |
| Instance placement mechanics | Deployment (ADR-EAL-026) | `deploy()` is called as a workflow step; Scalability never re-implements placement. |

**Scope boundary:** this document does not modify any of the twenty-six prior documents. It is deliberately narrow — a scaling policy and decision layer that drives existing mechanisms rather than duplicating any of them.

## 2. Goals

| Goal | Description |
|---|---|
| **Per-capability scaling policy** | Min/max instance count, scale-up/down thresholds, defined per Capability ID. |
| **Scale actions as ordinary workflows** | Every scale-up/down is a Workflow Engine definition, reusing Deployment's `deploy()` and ESR's registration unchanged. |
| **License-aware capacity limits** | Maximum scale is capped per the tenant's Licensing entitlement, read not redefined. |
| **Strict non-ownership of five adjacent domains** | Identity, Scheduling, Observability, Error Handling, and Deployment are each explicitly not owned, even though scaling logic naturally touches all five. |
| **Decoupled scaling-event visibility** | Scaling decisions are observable to any interested subscriber via the unchanged Event Bus. |

**Non-goals**: Scalability does not implement authentication/authorization, a timer/scheduler, a metrics pipeline, an error taxonomy, or artifact deployment mechanics — each remains entirely owned by its respective, unchanged document.

## 3. Architecture

```
   ┌───────────────────────────┐        ┌───────────────────────────┐
   │   Scaling Policy Registry       │◄──────┤ Capability Registry (ECR)     │
   │   (new)                        │        │ + Configuration Framework      │
   │                                 │        │ + Licensing (unchanged, both) │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Scaling Decision Engine      │◄──────┤ Observability Architecture   │
   │   (new)                        │        │ (EOA) — read-only metrics     │
   └─────────────┬─────────────┘        │  consumption, not owned       │
                 │                       └───────────────────────────┘
                 │ decision made
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Scale Action Workflow        │──────►│ Workflow Engine (unchanged)  │
   │   (new definition, not a new    │        │ → Deployment.deploy()         │
   │    engine)                      │        │ → ESR registration             │
   └─────────────┬─────────────┘        │ → PLM/Module Registry           │
                 │                       │   activation (all unchanged)    │
   ┌─────────────▼─────────────┐        └───────────────────────────┘
   │   Event Bus (unchanged)         │
   │   publish("scaling.*")          │
   └───────────────────────────┘

   Gated throughout by Identity & Access's checkPermission() (unchanged);
   failures classify via EEHF's existing taxonomy (unchanged).
```

## 4. Components

- **Scaling Policy Registry** *(new)* — per-Capability-ID policy: min/max instances, scale-up/down thresholds (sourced from ECF), and a maximum-scale cap read from Licensing's entitlement for the owning tenant.
- **Scaling Decision Engine** *(new)* — evaluates current metrics (read-only from EOA's existing Metrics Store) against the policy's thresholds to decide whether a scale action is warranted; performs no metrics collection of its own.
- **Scale Action Workflow** *(new workflow definition, not a new engine)* — the concrete scale-up/down sequence, expressed as an ordinary Workflow Engine definition whose steps call Deployment's unchanged `deploy()` (scale-up) or a graceful drain/deregister sequence (scale-down), with ESR registration and PLM/Module Registry activation following their own unchanged paths.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineScalingPolicy(capabilityId, minInstances, maxInstances, thresholds)` | Policy owner → Scaling Policy Registry | Declares a capability's scaling policy; `maxInstances` is capped by Licensing's entitlement for the tenant, read via the unchanged entitlement query. |
| `evaluateScaling(capabilityId)` | Scheduling-dispatched trigger, or an event-driven check → Scaling Decision Engine | Reads current metrics from EOA (read-only) and the policy's thresholds; returns a scale decision or no-op. |
| `executeScaleAction(capabilityId, direction, count)` | Scaling Decision Engine → Workflow Engine (`startWorkflow()`, unchanged) | Starts the Scale Action Workflow; every step within it is authorized via Identity & Access's unchanged `checkPermission()`. |

## 6. Data Flow

1. A policy is defined via `defineScalingPolicy()`, referencing a Capability ID (Capability Registry, unchanged) and thresholds sourced from ECF (unchanged); its maximum instance count is capped by a read-only query against Licensing's entitlement (unchanged) for the owning tenant.
2. A capacity check is triggered — dispatched by Scheduling at a configured interval, per that document's own when-not-how principle, or in response to an observed event — and calls `evaluateScaling()`.
3. The Scaling Decision Engine reads current metrics from EOA's existing Metrics Store (read-only, not owned) and compares them against the policy's thresholds.
4. If a scale action is warranted, `executeScaleAction()` starts the Scale Action Workflow via the Workflow Engine's unchanged `startWorkflow()`; each step (provisioning, calling Deployment's `deploy()`, ESR registration, activation) is authorized via Identity & Access's unchanged `checkPermission()`.
5. The workflow publishes its decision and outcome (`scaling.triggered`, `scaling.completed`) on the unchanged Event Bus.
6. Any failure at any step classifies via EEHF's existing taxonomy with a new `err.scalability.*` code — no new error format.

## 7. Design Patterns

- **Policy-and-decision layer over existing mechanisms, never a duplicate of any of them** — the organizing discipline of this entire document; every "Uses" relationship drives an existing, unchanged mechanism, and every "Does NOT own" boundary is a deliberate refusal to duplicate one.
- **Read-only consumption without ownership** — Scalability's relationship to Observability (metrics) and Licensing (entitlement caps) is read-only consumption, the same discipline EOA itself uses when consuming events it doesn't generate (EOA §7).
- **Scale action as an ordinary workflow, continuing the sole-orchestrator principle** — directly extends the same discipline already applied in Marketplace (fulfillment) and Deployment (build/promote/deploy) — the Workflow Engine remains the only orchestration mechanism in the library (ADR-EAL-023), and this document adds no exception.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Least-Privilege** (ESA catalog) applies to scale-down/termination actions specifically — these are more consequential than scale-up and should be gated by a permission scoped accordingly via Identity & Access.
- **Principle: Fail-Closed Validation** (ESA catalog) applies to the Scaling Decision Engine — an inability to read current metrics or resolve a policy should result in no action, never a default scale action.
- **License-cap enforcement is read-only, never a bypass path** — the Scaling Policy Registry reads Licensing's entitlement cap but has no mechanism to grant or alter entitlement itself, preserving Licensing's exclusive ownership of that decision.

## 9. Scalability

*(A brief, self-referential note: this document's own architecture is deliberately lightweight, consistent with its narrow "Does NOT own" scope.)* The Scaling Decision Engine's evaluation frequency is bounded by Scheduling's dispatch interval, not by this document's own timer (it has none); read-only metrics consumption from EOA should not itself become a load concern given EOA's own established query-latency separation (EOA §9).

## 10. Best Practices

- Always express a scaling policy per Capability ID — never as an implicit, ungoverned autoscaling rule bolted directly onto infrastructure.
- Read Licensing's entitlement cap at policy-evaluation time rather than caching it indefinitely, so a plan downgrade is reflected promptly.
- Route every scale action through the Workflow Engine — never implement a shortcut that calls Deployment's `deploy()` directly outside a workflow definition.
- Keep the "Does NOT own" boundaries visible in any future extension of this document — the temptation to add "just a small timer" or "just a small metrics cache" is exactly how scope creep into Scheduling's or Observability's domain would begin.

## 11. Common Pitfalls

- **Implementing a timer inside Scalability "for convenience"** — violates Scheduling's own confirmed, permanent when-not-how principle; any periodic check must be dispatched from Scheduling.
- **Caching or duplicating metrics inside Scalability** — begins to encroach on Observability's ownership of the telemetry pipeline; always read live (or EOA-cached) data, never build a parallel metrics store.
- **Calling Deployment's `deploy()` directly outside a Workflow Engine definition** — reintroduces exactly the second-orchestrator risk this library has repeatedly closed off since Marketplace and Deployment.
- **Treating the Licensing cap as a suggestion rather than a hard limit** — undermines Licensing's own entitlement guarantee.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **A monolithic autoscaler owning metrics, timing, and deployment directly** | Build a single component that collects its own metrics, runs its own timer, and deploys instances directly. | Violates all three "Does NOT own" boundaries at once (Observability, Scheduling, Deployment) — exactly the scope creep this document is structured to prevent. |
| **No formal scaling policy; manual capacity management** | Leave instance-count decisions to ad hoc operator action. | Fails the core capacity-policy goal and provides no license-aware capping. |
| **Scale actions executed outside the Workflow Engine** | A bespoke scaling executor rather than a workflow definition. | Violates the sole-orchestrator principle (ADR-EAL-023) reconfirmed across Marketplace and Deployment. |
| **Uncapped scaling regardless of license tier** | Ignore Licensing's entitlement when deciding maximum instance count. | Removes a legitimate commercial control Licensing already exists to enforce. |

## 13. Migration Strategy

1. **Define scaling policies for a small number of capabilities first**, referencing existing Capability IDs and ECF-sourced thresholds.
2. **Wire the Scaling Decision Engine's metrics read against EOA's existing Metrics Store**, validating read-only consumption before any action is automated.
3. **Implement the Scale Action Workflow as an ordinary Workflow Engine definition**, validating that a scale-up correctly calls Deployment's unchanged `deploy()` and results in a properly-registered, activated instance.
4. **Wire Scheduling to dispatch periodic capacity checks**, never embedding timing logic directly in Scalability.
5. **Validate the Licensing cap is enforced** by attempting to exceed it and confirming denial.

## 14. Success Criteria

- Every scaling policy is scoped to an existing Capability ID; zero ungoverned autoscaling rules.
- 100% of scale actions execute as Workflow Engine definitions calling Deployment's unchanged `deploy()` — zero direct calls outside a workflow.
- Zero metrics collection or storage owned by Scalability — confirmed read-only consumption of EOA's existing Metrics Store.
- Zero timer/scheduling logic owned by Scalability — confirmed all periodic checks are Scheduling-dispatched.
- A license-tier scaling cap is demonstrated blocking an over-limit scale-up request.

## 15. Decision Matrix

| Criterion (weight) | Narrow policy/decision layer, strict non-ownership of five adjacent domains (recommended) | Monolithic autoscaler | No formal policy | Scale actions outside Workflow Engine | Uncapped scaling |
|---|---|---|---|---|---|
| Respects "Does NOT own" boundaries (High) | 5 | 1 | 4 | 3 | 4 |
| Reuses Workflow Engine as sole orchestrator (High) | 5 | 2 | 4 | 1 | 4 |
| License-aware capacity limits (Medium) | 5 | 3 | 1 | 3 | 1 |
| Capacity-policy goal achieved (High) | 5 | 4 | 1 | 4 | 4 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 2 | 5 | 3 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails ownership boundaries | Fails core goal | Fails orchestrator principle | Fails licensing goal |

**Conclusion**: a narrow scaling policy and decision layer — using the Capability Registry, Workflow Engine, and Event Bus; consuming Identity & Access, Licensing, and Configuration; and explicitly not owning Identity, Scheduling, Observability, Error Handling, or Deployment — is recommended, exactly per the directed relationship map.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-027: Enterprise Scalability as a Policy/Decision Layer With an Explicit Five-Domain Non-Ownership Boundary**

- **Status**: Accepted
- **Context**: No prior document defines capacity/instance-count scaling policy; Deployment places artifacts and ESR tracks instances, but neither decides how many should exist or when to add/remove capacity.
- **Decision**: Introduce a Scaling Policy Registry, Scaling Decision Engine, and Scale Action Workflow (an ordinary Workflow Engine definition). **Confirmed relationship map**: Uses = Capability Registry, Workflow Engine, Event Bus. Consumes = Identity & Access, Licensing, Configuration Framework. Does NOT own = Identity, Scheduling, Observability, Error Handling, Deployment. **No modification to any of the twenty-six prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option achieving the capacity-policy goal while respecting every one of the five explicit non-ownership boundaries and the Workflow Engine's sole-orchestrator status.
- **Consequences**:
  - *Positive*: capacity decisions are policy-driven, license-aware, and fully auditable via existing mechanisms; no new metrics, timer, error-taxonomy, auth, or deployment mechanism is introduced.
  - *Negative*: Scalability's own decision quality is entirely dependent on the freshness/quality of metrics it reads from EOA, since it owns no metrics pipeline of its own.
  - *Neutral*: periodic capacity checks require Scheduling to be wired correctly; Scalability has no fallback timer of its own by design.
- **Alternatives rejected**: monolithic autoscaler, no formal policy, scale actions outside the Workflow Engine, uncapped scaling — see §12 and §15.
- **Reversibility**: Fully reversible — the Scaling Policy Registry, Decision Engine, and Workflow definition can be decommissioned without affecting any of the five domains it deliberately does not own.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Policy Registry, Decision Engine, and Scale Action Workflow are specified at architecture level. |
| **Confirmed relationship map honored** | Confirmed | Uses/Consumes/Does-NOT-own exactly as directed at approval. |
| **Sole-orchestrator principle preserved** | Confirmed | Scale actions execute exclusively as Workflow Engine definitions. |
| **Technology-agnostic validation** | Ready | No binding to a specific autoscaling platform or metrics backend. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Predictive scaling** — using historical metrics (still read-only from EOA) to anticipate demand rather than react to threshold breaches, as a refinement of the Scaling Decision Engine's own logic.
- **Cross-capability scaling coordination** — if scaling one capability's dependency (via EDM's existing graph) implies a related capacity need elsewhere, a future refinement could surface that as a recommendation, without Scalability taking ownership of EDM's dependency model.
- **Cost-aware scaling decisions** — for AI-backed capabilities specifically, integrating with the AI Platform's Cost & Usage Meter, echoing the same cost-aware idea already flagged as future evolution in the AI Platform, Workflow Engine, and Scheduling documents.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-027.
