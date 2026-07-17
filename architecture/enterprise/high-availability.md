---
title: Enterprise High Availability
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise High Availability

## 1. Problem Statement

[Service Registry](service-registry.md) (ESR, ADR-EAL-004) already tracks instance health; [Scalability](scalability.md) (ADR-EAL-027) already decides how many instances should exist for load; [Deployment](deployment.md) (ADR-EAL-026) already places artifacts and can roll back a bad release. None of them answer: **when an individual instance or failure domain fails — not because of load, not because of bad code, but because a node crashed or an availability zone had a blip — how does the platform detect that and redirect around it fast enough that service isn't interrupted?**

This is deliberately scoped narrower than "Disaster Recovery" (the next roadmap item): High Availability (HA) addresses **individual component/instance/failure-domain failure within an otherwise-operating platform** — the everyday redundancy and failover concern. Recovery from a catastrophic, larger-scale event (an entire region lost, corrupted data requiring restoration from backup) is a different scope with different mechanisms (cross-region replication, formal RTO/RPO targets, a recovery runbook) — this document does not define that; it explicitly names the boundary and leaves Disaster Recovery's content to its own, not-yet-drafted document.

Following the same relationship-mapping discipline just applied to Scalability:

**Uses** (HA actively drives these to do its work):
- **Service Registry (ESR)** — HA's failure detection reads ESR's existing health signals; it does not build a second health-detection mechanism.
- **Workflow Engine** — a failover recovery sequence (detect → deregister failed instance → trigger replacement capacity → notify) is an ordinary workflow definition, continuing the sole-orchestrator principle.
- **Event Bus** — failover events publish as ordinary events for any interested subscriber.

**Consumes** (HA reads from/triggers these without owning them):
- **Scalability** — replacement capacity after a failure is requested via Scalability's existing scale-up mechanism, not a second capacity-decision system.
- **Deployment** — a replacement instance is placed via Deployment's unchanged `deploy()`.
- **Multi Tenancy** — the tenant isolation guarantee must hold through a failover exactly as it does in steady state; HA does not redefine isolation.

**Does NOT own** (explicit boundaries):
- **Health/metrics detection** — HA reads ESR's, PLM's, and EOA's existing health signals; it owns no health-collection mechanism of its own.
- **Scaling policy** — capacity-count decisions remain entirely Scalability's, even when triggered by a failure rather than load.
- **Deployment mechanics** — placing an artifact on a new instance remains entirely Deployment's.
- **Disaster Recovery** — cross-region/catastrophic-loss recovery is an explicitly separate, larger-scoped concern left to its own future document; this document's redundancy/failover guarantees apply within a single, otherwise-operating deployment topology.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Detecting a failed instance | Service Registry (ADR-EAL-004) | Reads ESR's existing Health Check Aggregator output — no new health mechanism. |
| Detecting a degraded plugin | Plugin Lifecycle Management (ADR-EAL-001) | Reads PLM's existing DEGRADED/QUARANTINED state signals. |
| Executing a recovery sequence | Workflow Engine (ADR-EAL-013) | Ordinary workflow definition — detect, deregister, request replacement, notify. |
| Replacing lost capacity | Scalability (ADR-EAL-027) | Calls Scalability's existing scale-up mechanism; HA does not decide capacity itself. |
| Placing the replacement instance | Deployment (ADR-EAL-026) | Calls Deployment's unchanged `deploy()`. |
| Announcing a failover | Event Bus (ADR-EAL-014) | Ordinary `publish()`. |
| Preserving tenant isolation during failover | Multi Tenancy (ADR-EAL-021) | Unchanged isolation guarantee continues to apply; HA introduces no exception. |
| Failure classification | Error Handling Framework (ADR-EAL-009) | Existing taxonomy, new `err.availability.*` codes. |

**Scope boundary:** this document does not modify any of the twenty-seven prior documents. It is explicitly narrower than "all failure" — it covers component/instance/failure-domain redundancy and failover, not catastrophic/cross-region recovery, which remains Disaster Recovery's separate, future scope.

## 2. Goals

| Goal | Description |
|---|---|
| **Redundancy placement across failure domains** | A capability's instances (per Scalability's existing count policy) are spread across independent failure domains, not concentrated in one. |
| **Fast, automated failover** | A failed instance's traffic is redirected without manual intervention, using ESR's existing health signals. |
| **Replacement capacity via existing mechanisms** | Lost capacity is replaced by calling Scalability's and Deployment's unchanged interfaces — never a duplicate capacity or placement mechanism. |
| **Isolation preserved through failure** | Multi Tenancy's guarantees hold during and after a failover, not just in steady state. |
| **A named, explicit boundary with Disaster Recovery** | This document is scoped to component/instance/failure-domain failure; catastrophic/cross-region loss is explicitly deferred to a separate, future document. |

**Non-goals**: HA does not define cross-region replication, backup/restore, or formal RTO/RPO targets — those belong to Disaster Recovery; it does not implement health detection, scaling policy, or deployment mechanics — each remains owned by its respective, unchanged document.

## 3. Architecture

```
   ┌───────────────────────────┐        ┌───────────────────────────┐
   │   Failure Detector (new)       │◄──────┤ Service Registry (ESR) +      │
   │                                 │        │ PLM health signals (unchanged)│
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │ failure detected
   ┌─────────────▼─────────────┐
   │   Redundancy Placement          │  ← new: per-capability failure-
   │   Policy (new)                  │    domain spread constraint
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Failover Recovery Workflow    │──────►│ Workflow Engine (unchanged)  │
   │   (new definition, not a new    │        │ → Scalability scale-up        │
   │    engine)                      │        │ → Deployment.deploy()         │
   └─────────────┬─────────────┘        │ → ESR registration (unchanged)│
                 │                       └───────────────────────────┘
   ┌─────────────▼─────────────┐
   │   Event Bus (unchanged)         │
   │   publish("availability.*")     │
   └───────────────────────────┘

   Explicitly out of scope: cross-region replication, backup/restore,
   catastrophic recovery — deferred to Disaster Recovery (future document).
```

## 4. Components

- **Redundancy Placement Policy** *(new)* — declares, per capability, a minimum spread across independent failure domains (e.g., "at least 2 of N instances in different availability zones"), read alongside (never overriding) Scalability's existing instance-count policy.
- **Failure Detector** *(new)* — consumes ESR's and PLM's existing health signals to identify a failed or unhealthy instance requiring failover; performs no health collection of its own.
- **Failover Recovery Workflow** *(new workflow definition, not a new engine)* — the concrete recovery sequence: deregister the failed instance (via ESR's existing mechanism), request replacement capacity (via Scalability's unchanged scale-up interface), place it (via Deployment's unchanged `deploy()`), and publish the outcome (via the unchanged Event Bus).

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineRedundancyPolicy(capabilityId, minFailureDomainSpread)` | Policy owner → Redundancy Placement Policy | Declares a failure-domain spread requirement, read alongside Scalability's count policy. |
| `detectFailure(instanceRef)` | Failure Detector (internal, reading ESR/PLM signals) | Identifies an instance requiring failover. |
| `executeFailover(capabilityId, failedInstanceRef)` | Failure Detector → Workflow Engine (`startWorkflow()`, unchanged) | Starts the Failover Recovery Workflow. |

## 6. Data Flow

1. A Redundancy Placement Policy is defined per capability, declaring a minimum failure-domain spread — consulted whenever Scalability's own scale-up/down logic places or removes instances, without HA modifying Scalability's own decision process.
2. The Failure Detector continuously consumes ESR's and PLM's existing health signals (unchanged); on detecting a failed or unhealthy instance, it calls `executeFailover()`.
3. The Failover Recovery Workflow (an ordinary Workflow Engine definition) deregisters the failed instance from ESR, requests replacement capacity via Scalability's unchanged scale-up mechanism, places the replacement via Deployment's unchanged `deploy()`, and confirms the replacement satisfies the Redundancy Placement Policy's failure-domain spread.
4. Multi Tenancy's isolation guarantee is not re-verified by HA as a separate step — it continues to hold because the replacement instance is provisioned through the same unchanged mechanisms (Scalability, Deployment) that already respect it.
5. The workflow publishes `availability.failover.detected` and `availability.failover.completed` events on the unchanged Event Bus.
6. Any failure within the recovery workflow itself classifies via EEHF's existing taxonomy with a new `err.availability.*` code.

## 7. Design Patterns

- **Detection reused, response orchestrated, capacity/placement delegated** — HA's own value is entirely in *reacting correctly* to failure; every actual mechanism it invokes (health signals, capacity, placement) is reused unchanged, continuing the same discipline just established in Scalability (ADR-EAL-027).
- **Failure-triggered capacity request, not a second capacity-decision system** — a failover's "replace lost capacity" step is the same scale-up mechanism Scalability already owns for load-driven reasons; HA merely triggers it under a different condition (failure, not load).
- **Explicit scope narrowing against a not-yet-drafted sibling** — naming the HA/Disaster-Recovery boundary now, before Disaster Recovery is drafted, follows the same discipline as EDM's deferred migration question and Multi Tenancy's deferred retention-vs-deletion question: name the boundary, don't guess at the undrafted document's content.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Fail-Closed Validation** (ESA catalog) applies to the Failure Detector — an ambiguous health signal should not trigger an unnecessary failover, but a genuinely failed instance must not be left serving traffic by default either; thresholds should favor safety over false negatives.
- **Failover must not create a tenant-isolation gap** — a hastily-provisioned replacement instance must satisfy Multi Tenancy's unchanged isolation guarantee before it's considered a valid replacement, not after.
- **Recovery workflow actions carry the same authorization requirements as their underlying calls** — deregistration, scale-up, and deployment each remain gated by Identity & Access's unchanged `checkPermission()` exactly as they would outside a failover context.

## 9. Scalability

*(Cross-reference, not a restatement.)* HA's own failure-detection and recovery-workflow-triggering load is proportional to failure rate, not steady-state traffic — a fundamentally different, and typically much lower, volume than Scalability's own load-driven evaluation frequency (Scalability §9).

## 10. Best Practices

- Always define a Redundancy Placement Policy for any capability with an availability requirement — never rely on Scalability's count policy alone to imply failure-domain spread.
- Let the Failure Detector consume existing health signals exclusively — never build a parallel health-check mechanism "to be sure."
- Route every recovery action through the Failover Recovery Workflow — never let an operator or automated trigger call Scalability's or Deployment's interfaces directly outside the workflow, for the same reasons Scalability itself established.
- Keep the HA/Disaster-Recovery boundary explicit in any future extension — a "small" cross-region failover shortcut here would quietly encroach on Disaster Recovery's future scope.

## 11. Common Pitfalls

- **Building a second health-detection mechanism instead of reading ESR's/PLM's existing signals** — repeats the exact duplication this library has avoided since EDM.
- **Treating a failure-triggered scale-up as different from an ordinary one** — it should be the same Scalability mechanism, just triggered by a different condition; a parallel "emergency capacity" system would fragment capacity decisions across two owners.
- **Assuming HA also covers region-level or catastrophic failure** — the single most important scope boundary in this document; that remains explicitly Disaster Recovery's future, separate concern.
- **Skipping the Redundancy Placement Policy check on a replacement instance** — a replacement that lands in the same failure domain as its predecessor doesn't actually restore the intended redundancy.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **A dedicated HA health-monitoring system separate from ESR/PLM** | Build independent failure detection rather than reading existing signals. | Duplicates already-solved health-detection capability, violating "reuse before creating." |
| **A separate "emergency" capacity mechanism distinct from Scalability** | Bypass Scalability's normal scale-up path for failure-triggered replacement. | Fragments capacity decision-making across two owners for no structural reason; Scalability's mechanism works identically regardless of why capacity is needed. |
| **Fold Disaster Recovery's full scope into this document** | Address catastrophic/cross-region recovery here as well. | Premature and over-broad; DR has distinct mechanisms (replication, RTO/RPO, formal recovery plans) deserving its own dedicated document, consistent with the roadmap's own sequencing. |
| **Manual-only failover, no automation** | Rely on operators to notice and respond to instance failures. | Fails the fast-failover goal outright; the entire point of HA is bounding the time-to-recovery below what manual response can achieve. |

## 13. Migration Strategy

1. **Define Redundancy Placement Policies for the highest-availability-requirement capabilities first**, alongside their existing Scalability count policies.
2. **Wire the Failure Detector against ESR's and PLM's existing health signals**, validating detection accuracy before any automated response is enabled.
3. **Implement the Failover Recovery Workflow as an ordinary Workflow Engine definition**, validating end-to-end that a simulated instance failure results in a correctly-placed, correctly-spread replacement.
4. **Explicitly defer any cross-region or catastrophic-failure scenario** to the future Disaster Recovery document rather than extending this one to cover it.

## 14. Success Criteria

- Every availability-critical capability has a defined Redundancy Placement Policy.
- A simulated instance failure results in automated detection and a correctly-placed replacement within an agreed time bound.
- Zero parallel health-detection or capacity-decision mechanisms introduced — confirmed reuse of ESR/PLM signals and Scalability's scale-up path.
- Zero scope overlap with Disaster Recovery once that document exists — confirmed by review at that time.
- Multi Tenancy's isolation guarantee is verified to hold on at least one simulated failover.

## 15. Decision Matrix

| Criterion (weight) | Reused detection + policy-driven placement + Workflow-Engine-based recovery (recommended) | Dedicated HA health monitoring | Separate emergency capacity mechanism | Fold Disaster Recovery in here | Manual-only failover |
|---|---|---|---|---|---|
| Reuse of existing health/capacity/placement mechanisms (High) | 5 | 1 | 2 | 3 | 4 |
| Fast, automated failover (High) | 5 | 4 | 4 | 4 | 1 |
| Clean boundary with Disaster Recovery (High) | 5 | 4 | 4 | 1 | 4 |
| Redundancy/spread guarantee (Medium) | 5 | 3 | 3 | 3 | 2 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 2 | 2 | 1 | 5 |
| **Weighted outcome** | **Best overall fit** | Fails reuse principle | Fragments capacity ownership | Over-broad, premature | Fails fast-failover goal |

**Conclusion**: reused detection signals, a policy-driven redundancy placement constraint, and a Workflow-Engine-based recovery sequence — with catastrophic/cross-region recovery explicitly deferred to Disaster Recovery — is recommended.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-028: Enterprise High Availability as Reused-Signal Failover, Explicitly Scoped Narrower Than Disaster Recovery**

- **Status**: Accepted
- **Context**: No prior document addresses redundancy/failover for individual component or failure-domain loss; this is distinct from Scalability (load-driven capacity) and from the not-yet-drafted Disaster Recovery (catastrophic/cross-region loss).
- **Decision**: Introduce a Redundancy Placement Policy, Failure Detector (reading ESR's/PLM's existing health signals), and Failover Recovery Workflow (an ordinary Workflow Engine definition calling Scalability's and Deployment's unchanged interfaces). **Confirmed at approval: High Availability addresses redundancy and failover within normal failure domains; Disaster Recovery remains the sole authority for catastrophic recovery** — this boundary is permanent and binding on both documents. **Confirmed relationship map**: Uses = Service Registry, Workflow Engine, Event Bus. Consumes = Scalability, Deployment, Multi Tenancy. Does NOT own = health/metrics detection, scaling policy, deployment mechanics, Disaster Recovery. **No modification to any of the twenty-seven prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option achieving fast, automated failover while fully reusing existing detection/capacity/placement mechanisms and preserving a clean, explicit boundary with the not-yet-drafted Disaster Recovery document.
- **Consequences**:
  - *Positive*: failover is fast, automated, and reuses every applicable existing mechanism; redundancy placement is policy-driven and explicit; the HA/DR boundary is named before DR is even drafted, reducing the risk of future scope drift.
  - *Negative*: HA's own recovery quality depends entirely on the accuracy of health signals it doesn't own; a false negative in ESR/PLM's detection would go undetected by HA as well.
  - *Neutral*: this document says nothing about cross-region or catastrophic scenarios — that gap is deliberate and named, not an oversight.
- **Alternatives rejected**: dedicated HA health monitoring, a separate emergency capacity mechanism, folding Disaster Recovery in here, manual-only failover — see §12 and §15.
- **Reversibility**: Fully reversible — the Redundancy Placement Policy, Failure Detector, and Recovery Workflow can be decommissioned without affecting ESR, PLM, Scalability, or Deployment; failover would revert to manual operator response.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Redundancy Placement Policy, Failure Detector, and Failover Recovery Workflow are specified at architecture level. |
| **Confirmed relationship map honored** | Confirmed | Uses/Consumes/Does-NOT-own following the same discipline established with Scalability. |
| **Boundary with Disaster Recovery** | Confirmed explicit, pending that document's own drafting | Named now specifically so DR's future scope isn't accidentally absorbed here. |
| **Sole-orchestrator principle preserved** | Confirmed | Recovery executes exclusively as a Workflow Engine definition. |
| **Technology-agnostic validation** | Ready | No binding to a specific cloud provider's failure-domain model (AZ, rack, host). |
| **HA/DR boundary** | Confirmed at approval | HA = redundancy/failover within normal failure domains. Disaster Recovery = sole authority for catastrophic recovery. Binding on both documents. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Disaster Recovery document itself** — the next roadmap item; this document's explicit boundary naming is intended to make that document's own scope-setting easier, not to predetermine its content.
- **Chaos-engineering validation** — periodically injecting simulated failures to continuously validate the Failure Detector and Recovery Workflow, rather than relying solely on real incidents to prove them out.
- **Cross-capability redundancy coordination** — if one capability's failover implies a related capacity need in a dependency (via EDM's existing graph), a future refinement could surface that, without HA taking ownership of EDM's model.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-028.
