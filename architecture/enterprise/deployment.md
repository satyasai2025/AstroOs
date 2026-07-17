---
title: Enterprise Deployment
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Deployment

## 1. Problem Statement

Several prior documents assume an artifact is already running somewhere, without ever defining how it got there:

- [Plugin Lifecycle Management](plugin-lifecycle-management.md) (PLM, ADR-EAL-001) governs a plugin's activation state starting from **REGISTERED** — but registration itself assumes a built artifact already exists to register. PLM even references "automatic rollback to its last known-good version" (PLM §10) without defining what makes a prior version available to roll back *to*.
- [Service Registry](service-registry.md) (ESR, ADR-EAL-004) tracks a running instance once it registers itself — but never addresses how that instance came to be built, packaged, and started in the first place.
- [Configuration Framework](configuration-framework.md) (ECF, ADR-EAL-005) has "Environment" as a layer in its precedence hierarchy (Platform Default → **Environment** → Tenant → Instance) — dev/staging/prod-style environments are assumed to exist, without any document defining how an artifact actually gets promoted from one to the next.

Enterprise Deployment (ED) is that missing layer: a build/package pipeline, an environment promotion mechanism (gated by EVCS's existing breaking-change classification), and a rollback mechanism — the thing that actually makes an artifact available for PLM to register, ESR to track once running, and ECF's Environment layer to mean something concrete.

### Boundary clarifications with two easily-confused prior documents

- **vs. Feature Flags (EFF, ADR-EAL-006)**: Deployment controls *which artifact/binary is running where*; Feature Flags control *which already-deployed behavior a given request/user sees*. A capability can be fully deployed everywhere and still flag-disabled for most traffic; the reverse (flag-enabled but not deployed) is structurally impossible. A deployment-level canary (running a new artifact version on a subset of *instances*) and a flag-level rollout (showing new *behavior* to a subset of *traffic*) can look similar but operate at different layers — this document's canary mechanism governs instances, never traffic-targeting, which remains EFF's exclusive domain.
- **vs. Scheduling (ADR-EAL-016)**: A deployment can be scheduled for a specific maintenance window, but per Scheduling's own confirmed, permanent principle — "Scheduling determines when execution occurs, never how execution is performed" — Scheduling would dispatch to a Deployment capability at the right time; it does not, and must not, contain any deployment mechanics itself.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Gating promotion of a breaking change to a stricter environment | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | An artifact version's classification (MAJOR/MINOR/PATCH, per EVCS's rules) determines whether promotion to production requires the deprecation-window/compatibility discipline EVCS already defines. |
| What "Environment" means as a deployment target | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Deployment promotes an artifact through the exact Environment values ECF's Tenant-layer hierarchy already assumes — no second environment concept. |
| Registering the resulting running instance | [Service Registry](service-registry.md) (ADR-EAL-004) | A successfully deployed, started artifact registers with ESR exactly like any other instance — Deployment does not duplicate instance tracking. |
| Activating the deployed artifact as a live plugin/module | [Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) / [Module Registry](module-registry.md) (ADR-EAL-002) | Once deployed and registered, the artifact's activation follows PLM's or the Module Registry's own unchanged lifecycle — Deployment's responsibility ends at "built, packaged, running, registered." |
| Instance-level canary vs. traffic-level rollout | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Explicitly distinct layers (§1); Deployment's canary never substitutes for, or is substituted by, EFF's targeting. |
| Scheduled deployment windows | [Scheduling](scheduling.md) (ADR-EAL-016) | A scheduled deployment dispatches to an ordinary Deployment capability at the scheduled time — Scheduling owns no deployment mechanics. |
| Deployment-failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Classifies via EEHF's existing taxonomy with new `err.deployment.*` codes. |
| Whether deployment events should be mandatory-audit-class | [Audit Framework](audit-framework.md) (ADR-EAL-019) | Recommended, not automatically designated, following the same pattern Licensing already used for its own audit-inclusion proposal (Licensing §18). |

**Scope boundary:** this document does not modify any of the twenty-five prior documents. It fills the gap between "an artifact exists as source code" and "PLM/the Module Registry can register and activate it."

## 2. Goals

| Goal | Description |
|---|---|
| **A defined build/package pipeline** | Source becomes a versioned, deployable artifact through a repeatable process, classified via EVCS. |
| **Environment promotion gated by breaking-change classification** | Promoting a MAJOR-classified artifact version to a stricter environment (especially production) follows EVCS's compatibility/deprecation discipline; PATCH/MINOR changes may promote more freely. |
| **A defined rollback mechanism** | Reverting to a prior artifact version is a first-class, supported operation — the concrete mechanism PLM's own "rollback to last known-good version" language (PLM §10) already assumed existed. |
| **Instance-level canary, kept distinct from traffic-level rollout** | Deployment's own canary mechanism (a subset of instances running a new version) never conflates with or substitutes for EFF's targeting. |
| **Clean handoff to PLM/Module Registry and ESR** | Deployment's responsibility ends at a running, registered instance; activation and ongoing lifecycle remain entirely those documents' domain. |

**Non-goals**: ED does not perform activation decisions (PLM's/Module Registry's role, unchanged); it does not perform traffic-level targeting or rollout (EFF's role, unchanged); it does not decide *when* a deployment occurs on a recurring or scheduled basis (Scheduling's role, unchanged) — it only defines what happens once dispatched.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Source (module/plugin code)  │
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Build/Package Pipeline       │◄──────┤ Version Compatibility        │
   │   (new)                        │        │ Strategy (EVCS) — classifies  │
   └─────────────┬─────────────┘        │  the resulting artifact version│
                 │                       └───────────────────────────┘
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Environment Promotion         │◄──────┤ Configuration Framework       │
   │   Registry (new)               │        │ (ECF) — Environment layer      │
   └─────────────┬─────────────┘        │  targets (dev/staging/prod)   │
                 │                       └───────────────────────────┘
   ┌─────────────▼─────────────┐
   │   Deployment Executor (new)     │  ← places/starts the artifact
   └─────────────┬─────────────┘
                 │ on success                          │ on failure
   ┌─────────────▼─────────────┐        ┌─────────────▼─────────────┐
   │   Service Registry (ESR,        │        │   Rollback Mechanism (new)      │
   │   unchanged) — instance           │        │   — reverts to the prior         │
   │   registers itself                │        │     artifact version              │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   PLM / Module Registry         │  ← activation lifecycle,
   │   (unchanged) — governs           │    entirely unchanged
   │   activation from here on         │
   └───────────────────────────┘
```

## 4. Components

- **Build/Package Pipeline** *(new)* — turns source into a versioned, deployable artifact; the resulting version is classified via EVCS's rules before promotion decisions are made.
- **Environment Promotion Registry** *(new)* — tracks which artifact version is promoted to which ECF Environment-layer value, gating promotion to a stricter environment (especially production) by the artifact's EVCS classification — a MAJOR (breaking) version may require the deprecation-window discipline EVCS already defines before production promotion; PATCH/MINOR changes may follow a lighter path.
- **Deployment Executor** *(new)* — places and starts a promoted artifact version in the target environment; a successfully started instance registers with ESR exactly as any other instance would (ESR §6, unchanged).
- **Rollback Mechanism** *(new)* — reverts a target environment to a prior, previously-promoted artifact version; this is the concrete mechanism PLM's own reference to "automatic rollback to its last known-good version" (PLM §10) already assumed existed, without PLM itself needing to define it.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `buildArtifact(sourceRef)` | Build trigger (manual, CI, or a Scheduling-dispatched capability) → Build/Package Pipeline | Produces a versioned artifact, classified via EVCS. |
| `promoteArtifact(artifactVersion, targetEnvironment)` | Deployment operator/pipeline → Environment Promotion Registry | Promotes a classified artifact version to an ECF Environment-layer target, gated by its EVCS classification. |
| `deploy(artifactVersion, targetEnvironment, canaryPercentage)` | Deployment operator/pipeline → Deployment Executor | Places and starts the artifact; an optional canary percentage limits the deployment to a subset of instances — an instance-level concept, never a traffic-targeting one. |
| `rollback(targetEnvironment, toArtifactVersion)` | Operator (or an automated trigger, e.g. from PLM's health signals) → Rollback Mechanism | Reverts a target environment to a specified prior artifact version. |

## 6. Data Flow

1. Source is built into a versioned artifact via `buildArtifact()`; the Build/Package Pipeline classifies the resulting version via EVCS's rules (MAJOR/MINOR/PATCH).
2. `promoteArtifact()` moves the classified artifact toward a stricter ECF Environment-layer target; a MAJOR-classified version promoting to production is gated by EVCS's compatibility/deprecation discipline (EVCS §4), while PATCH/MINOR changes may proceed with a lighter check.
3. `deploy()` places and starts the promoted artifact in the target environment, optionally limited to a canary percentage of instances — an instance-level concern, distinct from and never substituting for EFF's traffic-level rollout.
4. A successfully started instance registers with ESR (unchanged, ESR §6); from that point, PLM's or the Module Registry's own unchanged activation lifecycle governs whether and how it begins serving as an active plugin/module.
5. On a deployment failure — classified via EEHF's existing taxonomy with an `err.deployment.*` code — or on a health signal indicating the newly-deployed version is unhealthy, `rollback()` reverts the target environment to a specified prior artifact version, the concrete realization of PLM's own "last known-good version" language (PLM §10).
6. Deployment events (build, promotion, deployment, rollback) are candidates this document recommends — not unilaterally designates — for the Audit Framework's Mandatory Audit Event Catalog, following the same pattern established by Licensing (Licensing §18).

## 7. Design Patterns

- **Build/promote/deploy/rollback as a distinct pipeline stage, not conflated with activation** — the clean handoff to PLM/Module Registry (§2, §6) mirrors the same discipline that kept EDM's dependency graph distinct from PLM's activation state machine; "is this artifact running" and "is this plugin active" are different questions answered by different documents.
- **Environment promotion gated by existing version-compatibility classification** — directly reuses EVCS's breaking-change discipline (EVCS §4) rather than inventing a second notion of what makes a change "safe to promote."
- **Instance-level canary, explicitly distinct from traffic-level flag rollout** — the clearest instance yet of two similar-looking mechanisms (both "gradual rollout") operating at genuinely different layers, following the same discipline that kept Licensing's entitlement gate distinct from EFF's rollout gate (Licensing §7).
- **Deployment provides the substrate PLM's own language already assumed** — PLM's "rollback to last known-good version" (PLM §10) is realized concretely by this document's Rollback Mechanism, without PLM itself needing to define it — a "complete, don't redesign" relationship analogous to how Identity & Access completed PLM's Security Gate (Identity & Access §1).

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Fail-Closed Validation** (ESA catalog) applies to environment promotion — an artifact whose EVCS classification can't be determined, or whose required deprecation-window discipline hasn't been satisfied, must not promote to a stricter environment by default.
- **Principle: Audit-Trail Integrity** (ESA catalog) is the direct motivation for recommending deployment events to the Audit Framework's catalog (§6) — who deployed what, to which environment, and when is exactly the kind of record that catalog exists to protect.
- **Promotion and rollback are high-impact operations** — should be gated by a specific, narrowly-granted Identity & Access permission, consistent with how Multi Tenancy and Licensing each gate their own high-impact lifecycle transitions.
- **Build/package pipeline integrity** — the resulting artifact's provenance (what source produced it) should be verifiable, consistent with the integrity-verification principle PLM already established for plugin artifacts (PLM §8) — Deployment is what produces the artifact PLM later verifies.

## 9. Scalability

- **Build/package operations are infrequent relative to instance count** — the now-familiar asymmetry established throughout this library; the Build/Package Pipeline's own throughput requirements are modest compared to, say, ESR's instance-registration volume.
- **Canary deployment volume scales with instance count, not build frequency** — a canary rollout across many instances is a distinct scaling concern from how often new artifact versions are built.
- **Rollback must be fast under incident pressure** — unlike routine promotion, a rollback is often invoked during an active incident; its execution path should be optimized for speed and reliability over the more deliberative checks routine promotion can afford.

## 10. Best Practices

- Always classify a new artifact version via EVCS before any promotion decision — never promote based on an assumed or undetermined classification.
- Treat canary deployment (instance-level) and flag-based rollout (traffic-level) as complementary, not interchangeable — a careful rollout typically uses both, in the correct order (deploy the artifact to a canary instance set, then use EFF to control how much traffic reaches it).
- Keep the Rollback Mechanism's execution path simple and fast — complexity here works directly against its purpose during an actual incident.
- Recommend, rather than assume, deployment-event inclusion in the Audit Framework's Mandatory Audit Event Catalog, respecting that document's own governance process.

## 11. Common Pitfalls

- **Conflating deployment-level canary with flag-level rollout** — the single most tempting and most damaging confusion this document exists to prevent, given how similar the two "gradual rollout" concepts look on the surface.
- **Letting Scheduling contain deployment mechanics "for convenience"** — directly violates Scheduling's own confirmed, permanent principle (ADR-EAL-016); a scheduled deployment must dispatch to this document's capabilities, never duplicate them.
- **Promoting a MAJOR-classified artifact to production without EVCS's compatibility/deprecation discipline** — undermines the entire reason environment promotion is gated by classification in the first place.
- **Treating deployment success as equivalent to activation success** — a successfully deployed, running, registered instance is not yet necessarily an active one; that remains PLM's or the Module Registry's own, unchanged determination.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **No formal deployment layer; assume artifacts appear "somehow"** | Leave build/promote/deploy/rollback entirely undefined, as the status quo across the twenty-five prior documents. | This is precisely the unaddressed gap identified in §1 — PLM's own rollback language and ECF's Environment layer both assume a mechanism that has never been defined. |
| **Fold deployment mechanics into Scheduling** | Let Scheduling itself perform build/promote/deploy actions on a timer. | Directly violates Scheduling's own confirmed, permanent when-not-how principle (ADR-EAL-016); Scheduling must dispatch to Deployment, never contain its mechanics. |
| **Use Feature Flags for environment promotion/canary** | Model a canary deployment as an EFF flag rollout instead of an instance-level Deployment mechanism. | Conflates two genuinely different layers (which binary is running where vs. which traffic sees which behavior); the two mechanisms serve complementary but distinct purposes, as clarified in §1. |
| **Promote artifacts to production without classification gating** | Skip EVCS-based gating and promote based on manual judgment alone. | Removes the fail-closed, systematic protection EVCS's breaking-change classification already provides elsewhere in this library; manual judgment alone reintroduces the inconsistency EVCS was built to prevent. |

## 13. Migration Strategy

1. **Stand up the Build/Package Pipeline and classify existing artifact versions retroactively via EVCS** where feasible, establishing a baseline.
2. **Introduce the Environment Promotion Registry and require classification-gated promotion for all new artifact versions** going forward, without necessarily retrofitting historical promotions.
3. **Implement the Deployment Executor and validate the full pipeline** (build → classify → promote → deploy → ESR registration → PLM/Module Registry activation) against one low-risk artifact first.
4. **Implement and test the Rollback Mechanism deliberately**, including a rehearsed rollback under simulated incident conditions, before relying on it operationally.
5. **Propose deployment events to the Audit Framework's Mandatory Audit Event Catalog** through that document's own governance process, rather than assuming inclusion.

## 14. Success Criteria

- Every artifact version is classified via EVCS before any promotion decision is made.
- Zero MAJOR-classified artifact versions promoted to production without satisfying EVCS's compatibility/deprecation discipline.
- A rollback to a prior artifact version is demonstrated end-to-end, restoring a target environment's running instances to the previous version.
- Zero instances of Scheduling containing deployment mechanics directly — all scheduled deployments dispatch to this document's unchanged interfaces.
- Deployment-event inclusion is formally proposed to the Audit Framework's governance process, with the outcome recorded regardless of direction.

## 15. Decision Matrix

| Criterion (weight) | Dedicated deployment pipeline, classification-gated promotion, clean handoff to PLM/ESR (recommended) | No formal deployment layer | Fold into Scheduling | Use Feature Flags for canary/promotion | Promote without classification gating |
|---|---|---|---|---|---|
| Closes the "artifacts appear somehow" gap (High) | 5 | 1 | 3 | 3 | 4 |
| Respects Scheduling's when-not-how principle (High) | 5 | 5 | 1 | 5 | 5 |
| Clean boundary from Feature Flags (High) | 5 | 4 | 4 | 1 | 4 |
| Classification-gated promotion safety (High) | 5 | 1 | 3 | 3 | 1 |
| Clean handoff to PLM/ESR (Medium) | 5 | 3 | 3 | 3 | 4 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 5 | 3 | 3 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails core goal | Fails Scheduling boundary | Fails EFF boundary | Fails promotion-safety goal |

**Conclusion**: a dedicated Deployment pipeline — build, classification-gated promotion, execution, and rollback — with a clean handoff to PLM/the Module Registry and ESR, is recommended. It is the only option closing the artifact-provenance gap while fully preserving Scheduling's and Feature Flags' already-established boundaries.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-026: Enterprise Deployment as a Classification-Gated Build/Promote/Deploy/Rollback Pipeline**

- **Status**: Accepted
- **Context**: PLM's rollback language, ESR's instance registration, and ECF's Environment layer all assume an artifact-provisioning mechanism this library never defined.
- **Decision**: Introduce a Build/Package Pipeline, Environment Promotion Registry (gated by EVCS's existing breaking-change classification), Deployment Executor (handing off to ESR's unchanged instance registration), and Rollback Mechanism. Canary deployment operates strictly at the instance level, distinct from and never substituting for Feature Flags' traffic-level rollout. Scheduled deployments dispatch to this document's interfaces per Scheduling's unchanged when-not-how principle. Deployment events are recommended, not automatically designated, for the Audit Framework's catalog. **No modification to any of the twenty-five prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option that closes the artifact-provisioning gap while fully preserving the boundaries Scheduling and Feature Flags have already established, and while reusing EVCS's classification discipline rather than inventing a second promotion-safety mechanism.
- **Consequences**:
  - *Positive*: PLM's rollback language and ECF's Environment layer now have a concrete mechanism behind them; environment promotion is systematically gated by breaking-change classification; instance-level canary and traffic-level rollout remain cleanly separated.
  - *Negative*: introduces a fourth new component set; teams must understand the distinction between deployment-level canary and flag-level rollout, which look superficially similar.
  - *Neutral*: activation decisions remain entirely PLM's/the Module Registry's; this document's responsibility ends at a running, registered instance.
- **Alternatives rejected**: no formal deployment layer, folding into Scheduling, using Feature Flags for canary/promotion, promoting without classification gating — see §12 and §15.
- **Reversibility**: Moderate — the pipeline and registry could be decommissioned, but any in-flight promotions or the Rollback Mechanism's historical version record would need individual handling; comparable in cost to reversing ESR adoption rather than EDM's low-cost case.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Build/Package Pipeline, Environment Promotion Registry, Deployment Executor, and Rollback Mechanism are specified at architecture level. |
| **Boundary with Scheduling** | Confirmed explicit | §1 directly reaffirms Scheduling's when-not-how principle; deployment mechanics never move into Scheduling. |
| **Boundary with Feature Flags** | Confirmed explicit | §1, §7, §11 directly address the instance-level-canary vs. traffic-level-rollout distinction. |
| **Clean handoff to PLM/Module Registry/ESR** | Confirmed | Deployment's responsibility explicitly ends at a running, registered instance. |
| **Technology-agnostic validation** | Ready | No binding to a specific CI/CD platform, container runtime, or deployment topology. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Propose deployment events to the Audit Framework's Mandatory Audit Event Catalog** — the concrete near-term follow-up, through that document's own governance process (§6, §18).
- **Automated rollback triggers from health signals** — integrating with PLM's Health & Telemetry Monitor or EEHF's error signals to automatically invoke `rollback()` under defined conditions, rather than requiring manual initiation, as a future, separately-approved enhancement.
- **Blue-green deployment as a Deployment Executor refinement** — a future variant of the instance-level canary model, still kept distinct from EFF's traffic-targeting layer.
- **Deployment cost integration with the AI Platform's Cost & Usage Meter** — for AI-backed capabilities specifically, echoing the cost-aware scheduling/routing ideas already flagged as future evolution elsewhere (AI Platform §18, Workflow Engine §18, Scheduling §18).

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-026.
