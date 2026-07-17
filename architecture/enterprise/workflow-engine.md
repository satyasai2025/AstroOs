---
title: Enterprise Workflow Engine
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Workflow Engine

## 1. Problem Statement

Every prior document assumes a capability is invoked once, in isolation, resolved through the standard **Capability → ECR → Module/Plugin → ESR** chain (ADR-EAL-004). None of them address a **multi-step, stateful sequence of capability invocations** that must execute in a defined order, survive partial failure, and potentially span a long duration (minutes to days) — a workflow.

This is a distinct problem from anything already covered:

- **[Dependency Management](dependency-management.md)** (EDM, ADR-EAL-007) models a *static, declared* dependency graph between providers (module/plugin identities) — it answers "what does this provider require to exist and be compatible," evaluated once at validation/activation time. A workflow's step ordering is a *runtime execution* concern for one specific workflow instance's data flow — a fundamentally different graph, evaluated per execution, not per provider registration. **This document does not extend or reuse EDM's graph for step ordering; it introduces a separate, execution-scoped ordering model (§4), and is explicit about that boundary to avoid the two being conflated.**
- No document addresses **partial-failure recovery across multiple steps** — EEHF classifies a single call's failure, but nothing defines what happens to the three already-completed steps of a five-step workflow when the fourth fails (retry the whole workflow? compensate the completed steps? resume from the failure point?).
- No document addresses **durable execution state** — a workflow that pauses for an external event (e.g., awaiting a downstream system) needs its state persisted somewhere between steps, which no Foundation document's "capability invocation" model anticipates.

The Enterprise Workflow Engine (EWE) defines a workflow as a versioned, ordered sequence of capability invocations with durable execution state and defined partial-failure behavior, reusing every applicable Foundation and Platform mechanism for everything that isn't specific to multi-step orchestration itself.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Invoking each individual step | [Capability Registry](capability-registry.md) (ADR-EAL-003) + [Service Registry](service-registry.md) (ADR-EAL-004) | Every workflow step invokes an existing Capability ID through the unchanged Capability → ECR → Module/Plugin → ESR chain — a step is never a bespoke call path. |
| Step-level timeouts, retry counts, concurrency limits | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Layered exactly per ADR-EAL-005; no separate workflow-config mechanism. |
| Gradual rollout of a revised workflow definition version | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Shifting a percentage of new workflow instances to a revised definition reuses EFF's sticky rollout and kill switch. |
| Classifying a failed step | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Maps into EEHF's existing closed taxonomy with new `err.workflow.*` codes — no new top-level class. |
| What counts as a breaking change to a workflow definition | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | A workflow definition revision is classified via EVCS before in-flight instances are considered eligible for migration to it. |
| Tracing a workflow execution across all its steps | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) | A single correlation ID (EEHF, reused unchanged) is generated once per workflow instance and propagated through every step's invocation. |
| AI-backed steps within a workflow | [AI Platform Architecture](ai-platform-architecture.md) (ADR-EAL-011) | An AI step is an ordinary AI-backed capability invocation; the orchestration-only principle applies unchanged — an AI step may narrate, summarize, or suggest a routing choice for confirmation, but must never stand in for a deterministic step whose correctness the workflow depends on. |
| Research-study steps within a workflow | [Research Platform](research-platform.md) (ADR-EAL-012) | A workflow step that triggers a study execution invokes the Statistical Execution Engine capability exactly as any other caller would — the workflow does not gain any special write path into the Findings Repository. |

**Scope boundary:** this document does not modify any of the twelve prior documents. It introduces new components strictly for step ordering, durable execution state, and partial-failure/compensation behavior.

## 2. Goals

| Goal | Description |
|---|---|
| **Versioned workflow definitions** | A workflow's step sequence/graph is a versioned artifact, classified via EVCS on change, not implicit in scattered orchestration code. |
| **Durable execution state** | A workflow instance's progress survives process restarts and long pauses between steps. |
| **Defined partial-failure behavior** | Every workflow definition specifies, per step, what happens on failure: retry (per EEHF's retryable hint), compensate (undo prior steps), or halt for manual intervention. |
| **Reuse of the standard capability-invocation path** | Every step invokes an existing Capability ID through the unchanged ADR-EAL-004 chain; the Workflow Engine is never a second way to reach a provider. |
| **Clear boundary from EDM's dependency graph** | Step ordering within one workflow execution is never conflated with the static, declared provider-dependency graph EDM already owns. |
| **AI orchestration-only principle preserved within workflows** | An AI-backed step follows ADR-EAL-011 unchanged — narration/suggestion only, never a substitute for a deterministic step. |

**Non-goals**: EWE is not a general-purpose programming runtime (workflow definitions describe orchestration, not arbitrary computation); it does not replace EDM's provider-dependency graph; and it does not grant any step type privileged write access to another document's data store (e.g., a workflow step calling the Research Platform's study capability has no more access to the Findings Repository than any other caller, per ADR-EAL-012 §8).

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Workflow Definition         │  ← new: versioned step sequence/graph,
   │   Registry (new)              │    each step referencing a Capability ID
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Workflow Execution Engine   │──────►│ Capability Registry → ESR    │
   │   (new)                       │        │ (unchanged chain, per step)  │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Execution State Store       │  ← new: durable per-instance state,
   │   (new)                       │    keyed by workflow instance ID
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Failure & Compensation      │──────►│ Error Handling Framework     │
   │   Handler (new)               │        │ (EEHF) — step error          │
   │                                │        │ classification, retry hints   │
   └───────────────────────────┘        └───────────────────────────┘

   One correlation ID (EEHF, reused) is generated per workflow instance and
   propagated to every step's capability invocation, traced end-to-end via EOA.
```

## 4. Components

- **Workflow Definition Registry** *(new)* — stores versioned workflow definitions: an ordered sequence or DAG of steps, each step referencing a Capability ID, its input/output mapping, and its per-step failure behavior (retry/compensate/halt). Definition changes are classified via EVCS before being considered comparable to the prior version.
- **Workflow Execution Engine** *(new)* — drives a workflow instance through its defined steps, invoking each step's Capability ID through the unchanged Capability Registry → ESR chain, and generating one correlation ID (per EEHF's existing standard) at instance start, propagated to every step.
- **Execution State Store** *(new)* — durable, per-instance record of which step a workflow instance has reached, what data has flowed between steps, and whether it is currently running, paused, halted, or completed — the mechanism that lets a long-running or paused workflow survive a process restart.
- **Failure & Compensation Handler** *(new)* — consumes EEHF's classified error/retryable signal for a failed step and applies the step's declared failure behavior: retry (respecting EEHF's backoff hint), compensate (execute a declared undo action for already-completed steps), or halt (pause the instance for manual intervention, recorded in the Execution State Store).

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineWorkflow(steps, failureBehaviorPerStep)` | Workflow owner → Workflow Definition Registry | Declares a new, versioned workflow definition. |
| `startWorkflow(workflowId, workflowVersion, input)` | Caller → Workflow Execution Engine | Begins a new instance; generates the instance's correlation ID (per EEHF). |
| `invokeStep(capabilityId, input, correlationId)` | Workflow Execution Engine → Capability Registry/ESR chain (unchanged) | The only path by which a step's underlying capability is ever reached — no bespoke invocation path. |
| `getInstanceState(instanceId)` | Operator/tooling → Execution State Store | Read-only query of a workflow instance's current step, status, and history. |
| `resumeInstance(instanceId)` | Operator → Workflow Execution Engine | Resumes a paused/halted instance, e.g., after a manual intervention resolves a halt condition. |

## 6. Data Flow

1. A caller invokes `startWorkflow()`; the Workflow Execution Engine generates one correlation ID for the entire instance (reusing EEHF's standard, not a new identifier) and records the instance's initial state in the Execution State Store.
2. For each step in the defined sequence/graph, the Engine calls `invokeStep()`, which resolves and calls the step's Capability ID through the unchanged Capability Registry → ECR → Module/Plugin → ESR chain, propagating the instance's correlation ID.
3. On step success, the Execution State Store is updated with the step's output and the instance advances to the next step per the definition.
4. On step failure, EEHF's `classifyError()` (unchanged) produces a classified result including a retryable hint; the Failure & Compensation Handler applies the step's declared behavior — retry (with EEHF's backoff hint), compensate (invoking each completed step's declared undo action in reverse order), or halt (instance paused, state persisted, awaiting `resumeInstance()`).
5. Every step invocation and state transition is, where the workflow owner opts in, wrapped in EOA's Common Event Envelope and ingested into the Telemetry Pipeline, letting an operator trace an entire multi-step, multi-provider execution under one correlation ID via EOA's Unified Query Interface.
6. If a step is AI-backed, its invocation follows the exact same `invokeStep()` path as any deterministic step; nothing in the Workflow Engine grants an AI step a different invocation mechanism, write privilege, or authority than the ADR-EAL-011 orchestration-only model already allows it outside a workflow context.

## 7. Design Patterns

- **Orchestration-style workflow (not choreography)** — a central Workflow Execution Engine explicitly drives step sequencing, rather than steps independently reacting to each other's events; this keeps execution state centrally queryable (§4, Execution State Store) rather than implicitly distributed.
- **Saga pattern for partial-failure compensation** — the Failure & Compensation Handler's compensate behavior is the standard saga pattern: undo already-completed steps via their own declared compensating actions when a later step fails, rather than leaving a workflow instance in an inconsistent partial state.
- **Durable state machine per instance** — each workflow instance's progress is itself a persisted state machine (running/paused/halted/completed/compensating), a smaller-scoped analog of PLM's plugin lifecycle state machine (PLM §3) applied to one workflow execution rather than a provider's whole lifecycle.
- **Full reuse over parallel construction** — every step's actual invocation, error classification, and tracing identifier are unchanged from the standard Foundation/Platform mechanisms; the only new surface is sequencing, durable state, and compensation.

## 8. Security Considerations

- **A workflow step carries no elevated privilege over a direct caller** — invoking a capability as a workflow step must be authorized exactly as a direct invocation would be; the Workflow Engine is not a privilege-escalation path.
- **Compensating actions are themselves ordinary capability invocations** — an undo action declared for a step must be authorized and classified exactly like any other invocation, not treated as an implicitly-trusted internal operation.
- **Execution state may contain sensitive step input/output** — the Execution State Store should apply access control at least as strict as the most sensitive capability invoked within the workflow, consistent with EOA's "strictest-applicable-source-policy" principle (EOA §8).
- **Halted instances awaiting manual intervention are a governance-relevant state** — `resumeInstance()` should be authorized distinctly from routine step execution, since resuming a halted workflow is a deliberate operational decision, not a routine automated step.

## 9. Scalability

- **Execution state read/write is per-instance, not global** — the Execution State Store's access pattern is naturally partitioned by instance ID, avoiding the read/write contention concerns seen in shared registries elsewhere in this library.
- **Long-running instances must not hold engine-level resources for their full duration** — a paused workflow (awaiting a step, awaiting manual resume) should be fully durable in the Execution State Store with no in-memory engine resource held during the pause, so instance count is bounded by storage, not by concurrent engine capacity.
- **Step invocation inherits the scalability profile of whatever it calls** — a step invoking an AI-backed capability inherits the Model Gateway's own latency/availability profile (AI Platform §9); a step invoking a Research Platform study inherits that document's asynchronous execution model (Research Platform §9) — the Workflow Engine does not need to solve these again, only to wait on them correctly.

## 10. Best Practices

- Declare a compensating action for every step that has a side effect, even if compensation is rarely triggered — an undeclared compensation path means a saga cannot safely unwind on later failure.
- Treat step retries as governed by EEHF's retryable hint, never a blanket "retry everything" or "retry nothing" policy at the workflow level.
- Keep step-to-step data passed through the Execution State Store explicit and minimal — avoid smuggling large or sensitive payloads through workflow state when a capability could instead be re-queried for current data.
- Version a workflow definition on every step-sequence or failure-behavior change, and classify it via EVCS before assuming in-flight instances can safely migrate to it.

## 11. Common Pitfalls

- **Conflating workflow step ordering with EDM's provider-dependency graph** — the single most important distinction in this document (§1); a workflow instance's runtime data flow is not a declaration that one provider depends on another, and treating them as the same graph would corrupt both models.
- **Letting an AI-backed step make an authoritative decision a deterministic step should make** — directly violates ADR-EAL-011's orchestration-only principle, now applicable inside workflows exactly as outside them.
- **No declared compensation for a step with real side effects** — leaves a saga unable to safely unwind, resulting in a halted instance with no defined recovery path.
- **Treating a paused/long-running instance as requiring held engine resources** — undermines the scalability goal in §9; pause state must be fully durable, not dependent on an engine process staying alive.
- **A workflow step bypassing the standard Capability Registry/ESR chain "for efficiency"** — reintroduces a second invocation path this document explicitly avoids (§2), undermining every reuse benefit this library has built up.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Choreography (event-driven, no central engine)** | Steps react to each other's published events with no central orchestrator. | Makes execution state implicit and harder to query centrally (no single Execution State Store to inspect); a valid pattern for some systems, but this document's durable, queryable per-instance state goal (§2) is better served by explicit orchestration. |
| **Reuse EDM's dependency graph for step ordering** | Model a workflow's step sequence as EDM dependency edges between the same providers. | Conflates a static, provider-level declaration (EDM's actual scope, evaluated once) with a per-execution, runtime ordering concern (evaluated per workflow instance) — the exact confusion §1 is structured to avoid. |
| **No compensation; retry-only failure handling** | Only support retrying a failed step, with no saga-style undo of completed steps. | Leaves a workflow with real side effects (e.g., a step that already committed a change) unable to safely unwind on a later, unrecoverable failure — fails the defined partial-failure-behavior goal for any workflow with more than trivial side effects. |
| **In-memory-only execution state (no durable store)** | Keep workflow instance progress only in the engine process's memory. | Fails the durable-execution-state goal outright; any process restart or long pause between steps would lose all progress. |

## 13. Migration Strategy

1. **Stand up the Workflow Definition Registry, Workflow Execution Engine, and Execution State Store** as new, independently-operable components, with no change required to any of the twelve prior documents.
2. **Define the first workflow using only steps that invoke already-existing Capability IDs** through the unchanged standard chain, validating that no bespoke invocation path is needed.
3. **Require a declared compensating action for every side-effecting step from the first workflow definition onward**, rather than retrofitting compensation after an incident demonstrates its absence.
4. **Use EFF for rolling out a revised workflow definition version** to a subset of new instances before full cutover, consistent with the reuse map (§1).
5. **Introduce AI-backed steps only after the deterministic step path is validated**, applying ADR-EAL-011's orchestration-only principle from the first AI step onward, not as an afterthought.

## 14. Success Criteria

- 100% of workflow steps invoke an existing Capability ID through the unchanged Capability Registry → ESR chain — zero bespoke invocation paths.
- Every workflow instance's progress is queryable via `getInstanceState()` at any point, including across a process restart.
- Every side-effecting step in an active workflow definition has a declared, tested compensating action.
- Zero new top-level EEHF error classes introduced; all step failures classify into existing classes with `err.workflow.*` codes.
- At least one workflow instance's full multi-step execution is traceable end-to-end via a single correlation ID through EOA's Unified Query Interface.
- Zero AI-backed steps observed making an authoritative decision in place of a declared deterministic step.

## 15. Decision Matrix

| Criterion (weight) | Dedicated orchestration engine, full reuse of standard invocation path (recommended) | Choreography (event-driven) | Reuse EDM's graph for step ordering | Retry-only, no compensation | In-memory-only state |
|---|---|---|---|---|---|
| Durable, queryable execution state (High) | 5 | 2 | 3 | 3 | 1 |
| Defined partial-failure/compensation behavior (High) | 5 | 3 | 3 | 1 | 3 |
| Clean boundary from EDM (High) | 5 | 4 | 1 | 4 | 4 |
| Reuse of standard invocation/error/tracing mechanisms (High) | 5 | 3 | 2 | 4 | 4 |
| Survives process restart / long pauses (Medium) | 5 | 3 | 3 | 3 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 3 | 4 | 4 | 5 |
| **Weighted outcome** | **Best overall fit** | Weaker central visibility | Fails EDM-boundary goal | Fails compensation goal | Fails durability goal |

**Conclusion**: a dedicated orchestration engine with durable execution state, saga-style compensation, and full reuse of the standard capability-invocation, error-classification, and tracing mechanisms is recommended. It is the only option that meets the durability and compensation goals while keeping a clean, explicit boundary from EDM's distinct dependency-graph concern.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-013: Enterprise Workflow Engine as an Orchestration Layer with Durable State and Saga-Style Compensation**

- **Status**: Accepted
- **Context**: No prior document addresses multi-step, stateful sequences of capability invocations with durable execution state and defined partial-failure behavior; this is distinct from EDM's static provider-dependency graph, a distinction this document is explicit about to prevent conflation.
- **Decision**: Introduce a Workflow Definition Registry, Workflow Execution Engine, Execution State Store, and Failure & Compensation Handler. Every step invokes an existing Capability ID through the unchanged Capability Registry → ECR → Module/Plugin → ESR chain; step failures classify via EEHF's unchanged taxonomy with new `err.workflow.*` codes; one correlation ID per instance reuses EEHF's standard unchanged; workflow definition versioning reuses EVCS; rollout reuses EFF. AI-backed steps remain subject to ADR-EAL-011's orchestration-only principle without exception. **No modification to any of the twelve prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option meeting the durability, compensation, and EDM-boundary goals simultaneously, while the reuse map (§1) confirms every applicable Foundation/Platform mechanism is reused rather than duplicated.
- **Consequences**:
  - *Positive*: workflows gain durable, queryable execution state and safe partial-failure recovery; the standard invocation/error/tracing path remains the only path, keeping the library's reuse discipline intact; the AI orchestration-only principle extends into multi-step contexts without any special-casing.
  - *Negative*: introduces four new components; workflow authors must explicitly declare compensating actions, an authoring discipline beyond simply defining the happy-path step sequence.
  - *Neutral*: choreography-style, fully event-driven orchestration remains a valid pattern for other contexts but is not adopted here, in favor of centrally queryable state.
- **Alternatives rejected**: choreography, reusing EDM's graph for step ordering, retry-only failure handling, in-memory-only state — see §12 and §15.
- **Reversibility**: Fully reversible for the new components; any workflow definition could, in principle, be re-expressed as direct sequential caller-side code if the Workflow Engine were decommissioned, though durability and compensation guarantees would be lost in that reversal.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Definition Registry, Execution Engine, State Store, and Compensation Handler are specified at architecture level. |
| **Full reuse validation** | Confirmed | §1's reuse map traces every non-orchestration-specific need to an existing Foundation/Platform mechanism. |
| **Boundary with EDM** | Confirmed explicit | §1 and §11 both call out the static-dependency-graph vs. runtime-step-ordering distinction directly. |
| **Preservation of ADR-EAL-011's orchestration-only principle** | Confirmed | AI-backed steps use the unchanged `invokeStep()` path with no elevated privilege (§6, §8). |
| **Technology-agnostic validation** | Ready | No binding to a specific workflow runtime, state store technology, or orchestration framework. |
| **Security model maturity** | Ready for design review | Step privilege parity and execution-state access control are addressed (§8); no formal threat model performed. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Human-in-the-loop wait steps** — a formalized step type that pauses an instance awaiting explicit human input, building on the existing halt/`resumeInstance()` mechanism rather than a separate approval system.
- **Cross-workflow composition** — a workflow step that itself starts a child workflow instance, with the parent's correlation ID propagated to the child, extending the existing tracing model rather than introducing a second one.
- **Compensation dry-run / simulation** — validating a workflow definition's compensating actions against a test scenario before production use, reducing the risk of an untested undo path being exercised for the first time during a real failure.
- **Cost-aware step scheduling** — for workflows containing AI-backed steps, using the AI Platform's Cost & Usage Meter (AI Platform §4) to inform scheduling/retry decisions, echoing the cost-aware routing idea already flagged as future evolution in the AI Platform Architecture (§18).

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-013.
