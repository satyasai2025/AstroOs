---
title: Enterprise Scheduling
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Scheduling

## 1. Problem Statement

Three prior documents each answer "how is something invoked" once triggered: the standard Capability → ECR → Module/Plugin → ESR chain for a single call, the [Workflow Engine](workflow-engine.md) (EWE, ADR-EAL-013) for a multi-step orchestrated execution once started, and the [Event Bus](event-bus.md) (EEB, ADR-EAL-014) for decoupled dispatch once a business event occurs. None of them answer a different, prior question: **what causes something to happen at a specific time, on a recurring interval, or after a defined delay, with no external business event or human action triggering it?**

This is a genuinely distinct concern — clock-driven triggering — and this document is careful not to re-solve execution itself:

- **Scheduling decides *when*; it never decides *how* the triggered work executes.** A fired schedule always hands off to one of the three existing dispatch mechanisms — a direct capability invocation, a workflow instance start (`startWorkflow()`, EWE unchanged), or an event published on the Bus (`publish()`, EEB unchanged) — never a fourth, bespoke execution path.
- **The Timer/Trigger Engine's own reliability is the load-bearing new concern.** A missed fire (scheduler down at the due time), a misconfigured timezone, or an ambiguous catch-up policy after downtime are failure modes no existing document addresses, because none of them involves a clock as the triggering condition.
- **Schedule definitions themselves need governance** — a cron expression or interval is a versioned artifact whose meaning must be precise and auditable, analogous to how the Workflow Engine treats a step sequence as a versioned artifact (EWE §2), but for a fundamentally different kind of trigger condition (time, not data flow).

The Enterprise Scheduling document defines schedule definitions, a durable timer engine, and a dispatch router that always hands off to an existing invocation mechanism — never a new one.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Direct scheduled invocation of a single capability | [Capability Registry](capability-registry.md) (ADR-EAL-003) + [Service Registry](service-registry.md) (ADR-EAL-004) | A fired schedule targeting a capability calls it through the unchanged standard chain — identical to any other caller. |
| Scheduled start of a multi-step process | [Workflow Engine](workflow-engine.md) (ADR-EAL-013) | A fired schedule targeting a workflow calls `startWorkflow()` unchanged; Scheduling never re-implements step sequencing. |
| Scheduled publication of an event for decoupled subscribers | [Event Bus](event-bus.md) (ADR-EAL-014) | A fired schedule targeting a topic calls `publish()` unchanged, using EOA's Common Event Envelope exactly as any other publisher. |
| Schedule parameters (cron expression, catch-up policy, timezone) | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Layered exactly per ADR-EAL-005; no separate schedule-config mechanism. |
| Schedule definition versioning and breaking-change classification | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | A schedule's timing/target contract change is classified via EVCS before being considered a compatible evolution. |
| Gradual rollout of a schedule change | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Shifting a subset of scheduled instances to a revised timing/catch-up policy reuses EFF's rollout/kill switch. |
| Scheduler worker instance tracking | [Service Registry](service-registry.md) (ADR-EAL-004) | The Timer/Trigger Engine's own running instance(s) register with ESR like any other service instance. |
| Classifying a missed fire or dispatch failure | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Maps into EEHF's existing closed taxonomy with new `err.scheduling.*` codes — no new top-level class. |
| Tracing a fired schedule through to its dispatch target | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) | A fresh correlation ID (EEHF's, unchanged) is generated at fire time and propagated to whichever dispatch target is invoked. |

**Scope boundary:** this document does not modify any of the fifteen prior documents. New components are scoped strictly to schedule definition, durable timing, misfire/catch-up handling, and dispatch routing to an existing invocation mechanism.

**Confirmed foundational principle (at approval): Scheduling determines when execution occurs, never how execution is performed.** Every component in this document — the Schedule Definition Registry, Timer/Trigger Engine, Misfire/Catch-Up Handler, and Dispatch Router — exists solely to answer the timing question. The moment a schedule fires, all execution semantics (retries, compensation, step sequencing, subscriber fan-out, capability invocation) belong entirely to whichever existing mechanism (capability chain, EWE, or EEB) the Dispatch Router hands off to. This is a hard boundary: any future proposal for Scheduling to itself perform retries, branching, or multi-step logic would require superseding this ADR, not an incremental extension.

## 2. Goals

| Goal | Description |
|---|---|
| **Versioned, precise schedule definitions** | A schedule's timing (cron/interval/one-off), timezone, and target are a versioned artifact classified via EVCS on change. |
| **Durable, restart-safe timing** | The next-fire time for every schedule is persisted, not held only in an engine process's memory, so a restart does not lose or duplicate fires. |
| **Defined misfire/catch-up behavior** | Every schedule states explicitly what happens if a fire was missed (skip, fire once immediately, fire once per missed occurrence) rather than leaving this undefined. |
| **Dispatch only to existing invocation mechanisms** | A fired schedule always resolves to a direct capability call, a workflow start, or an event publish — never a bespoke fourth execution path. |
| **Full reuse of Foundation/Platform mechanisms for everything except timing itself** | No parallel config, versioning, rollout, error, or tracing system for scheduling specifically. |

**Non-goals**: Scheduling is not a workflow engine (it never sequences multiple steps itself — a workflow target's own steps remain EWE's responsibility); it is not an event bus (a topic target's own subscriber fan-out remains EEB's responsibility); and it does not perform the invoked capability's own retry/compensation logic beyond the misfire policy for the schedule itself.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Schedule Definition          │  ← new: versioned timing +
   │   Registry (new)               │    target + catch-up policy
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Timer/Trigger Engine         │  ← new: durable next-fire-time
   │   (new)                        │    tracking, survives restarts
   └─────────────┬─────────────┘
                 │ fires at due time
   ┌─────────────▼─────────────┐
   │   Misfire/Catch-Up Handler     │  ← new: applies the schedule's
   │   (new)                        │    declared missed-fire policy
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Dispatch Router (new)        │  ← routes to exactly one of:
   └──────┬──────────┬──────────┘
          │          │          │
┌─────────▼──┐ ┌──────▼─────┐ ┌──▼──────────────┐
│ Capability   │ │ Workflow     │ │ Event Bus          │
│ Registry/ESR │ │ Engine        │ │ (publish, unchanged)│
│ (unchanged)   │ │ (startWorkflow,│ │                     │
│               │ │  unchanged)    │ │                     │
└─────────────┘ └────────────┘ └───────────────────┘
```

## 4. Components

- **Schedule Definition Registry** *(new)* — stores versioned schedule definitions: timing expression (cron, fixed interval, or one-off future timestamp), timezone, dispatch target (capability ID, workflow ID, or topic ID) and target type, and the declared misfire/catch-up policy. Changes are classified via EVCS before a revision is considered a compatible evolution of an existing schedule.
- **Timer/Trigger Engine** *(new)* — the durable clock: persists each schedule's next-fire time so that a process restart neither loses a due fire nor duplicates one; this durability guarantee is this document's single most load-bearing new component.
- **Misfire/Catch-Up Handler** *(new)* — when the Timer/Trigger Engine detects a schedule's due time has passed without firing (e.g., due to downtime), applies the schedule's declared policy: skip entirely, fire once immediately, or fire once per missed occurrence.
- **Dispatch Router** *(new)* — on a fire (whether on-time or catch-up), resolves the schedule's declared target type and calls exactly one of the three existing invocation mechanisms — never a bespoke path.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineSchedule(timing, timezone, targetType, targetId, misfirePolicy)` | Schedule owner → Schedule Definition Registry | Declares a new, versioned schedule. |
| `onDue(scheduleId, firedAt)` | Timer/Trigger Engine → Misfire/Catch-Up Handler | Internal signal that a schedule's due time has arrived (on-time or, if detected late, as a catch-up case). |
| `dispatch(scheduleId, targetType, targetId, correlationId)` | Misfire/Catch-Up Handler → Dispatch Router | Hands off a fire (after misfire policy is applied) to be routed to its target. |
| `getScheduleState(scheduleId)` | Operator/tooling → Schedule Definition Registry / Timer Engine | Read-only query of a schedule's next-fire time, last-fired time, and current definition version. |
| `pauseSchedule(scheduleId)` / `resumeSchedule(scheduleId)` | Operator → Timer/Trigger Engine | Explicit, auditable suspension/resumption of a schedule, distinct from an unintentional missed fire. |

## 6. Data Flow

1. A schedule owner calls `defineSchedule()`; the Schedule Definition Registry persists the timing, timezone, target, and misfire policy, applying EVCS classification to any change against a prior version.
2. The Timer/Trigger Engine computes and durably persists the schedule's next-fire time; this persistence is what allows the engine to restart without losing track of pending fires.
3. When the due time arrives, the Engine raises `onDue()`; the Misfire/Catch-Up Handler checks whether this is an on-time fire or a detected-late fire (e.g., the engine was down through the due time) and applies the schedule's declared policy accordingly.
4. The Dispatch Router receives the (possibly policy-adjusted) fire and calls exactly one of: the standard Capability Registry/ESR invocation chain, EWE's `startWorkflow()`, or EEB's `publish()` — generating a fresh correlation ID (EEHF's standard, unchanged) for this specific firing.
5. Any failure in the dispatch call itself (target unreachable, target rejected the call) is classified via EEHF's existing taxonomy with an `err.scheduling.*` code — distinct from a misfire, which is a timing condition, not a call failure.
6. An operator can query `getScheduleState()` at any time, and explicitly `pauseSchedule()`/`resumeSchedule()` a schedule as a deliberate, auditable action distinct from an unintentional gap in firing.

## 7. Design Patterns

- **Durable timer / persisted next-fire-time** — the standard pattern for restart-safe scheduling, directly analogous to the Workflow Engine's Execution State Store (EWE §4) durability discipline, applied here to a schedule's timing state rather than a workflow instance's step progress.
- **Dispatch-only, never re-executing** — the Dispatch Router's sole job is routing to an existing mechanism; this mirrors the Event Bus's own restraint in staying a dispatch layer rather than absorbing subscriber business logic (EEB §7), applied here to keep Scheduling from absorbing either EWE's or EEB's actual execution responsibilities.
- **Explicit misfire policy, not implicit best-effort** — declaring skip/fire-once/fire-per-occurrence explicitly avoids the ambiguity of an undocumented "whatever the engine happens to do" behavior after downtime.
- **Full reuse over parallel construction** — continuing the discipline established since EDM: a schedule's target is always one of three already-existing invocation mechanisms, never a new one built specifically for scheduled contexts.

## 8. Security Considerations

- **Schedule definitions can trigger privileged operations, so defining one should require the same authorization as invoking its target directly** — a schedule targeting a capability should not grant any elevated privilege beyond what a direct, authorized caller of that capability would have, mirroring the Workflow Engine's equivalent principle (EWE §8).
- **Pause/resume as a governance-relevant action** — `pauseSchedule()`/`resumeSchedule()` should be authorized distinctly from routine schedule definition, since silently pausing a security-relevant recurring job (e.g., a periodic credential-rotation trigger) has real operational consequences.
- **No secrets in schedule definitions** — consistent with every manifest/schema pattern in this library, a schedule's timing and target reference are metadata only.
- **Catch-up storms as an availability risk, not just a correctness one** — a "fire once per missed occurrence" policy after extended downtime could produce a burst of dispatch calls; this is a security-adjacent availability concern the Dispatch Router and its targets must be resilient to, not merely a scheduling nicety.

## 9. Scalability

- **Timer/Trigger Engine must scale with total schedule count, not fire frequency alone** — persisting and evaluating next-fire times for a large number of schedules is a different scaling axis than the actual dispatch rate, and both should be considered independently.
- **Dispatch fan-out inherits the scalability profile of its target** — a schedule dispatching to EEB inherits the Bus's own fan-out scaling (EEB §9); a schedule starting a workflow inherits EWE's own instance-scaling profile (EWE §9); Scheduling does not need to re-solve either.
- **Catch-up bursts require deliberate rate-limiting** — per §8's availability concern, the Misfire/Catch-Up Handler should be able to pace fire-per-occurrence catch-up dispatch rather than issuing all missed fires simultaneously.

## 10. Best Practices

- Always declare an explicit misfire policy at schedule-definition time — never leave this to undocumented engine default behavior.
- Version a schedule definition on any timing, timezone, or target change, and classify it via EVCS before assuming continuity with the prior definition's history.
- Treat `pauseSchedule()` as a deliberate, logged operational action, distinct from an unplanned gap in firing that the Misfire/Catch-Up Handler would otherwise need to reconcile.
- Rate-limit catch-up dispatch bursts rather than assuming downstream targets can absorb every missed occurrence simultaneously.

## 11. Common Pitfalls

- **Building a bespoke execution path for scheduled work "since it's already special"** — the single most important pitfall to avoid; a scheduled capability call, workflow start, or event publish must use the exact same mechanism as any other trigger of that same target. 
- **In-memory-only next-fire-time tracking** — reintroduces the exact durability failure the Timer/Trigger Engine exists to prevent; a restart must never lose track of pending fires.
- **No declared misfire policy, relying on implicit engine behavior** — leaves operators unable to predict what happens after downtime, and risks either silently skipped critical work or an unexpected catch-up burst.
- **Conflating a misfire (timing condition) with a dispatch failure (call failure)** — these are different failure classes with different remediation; collapsing them loses the ability to distinguish "the schedule didn't fire on time" from "the schedule fired but its target rejected the call."

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **A bespoke scheduled-execution runtime, separate from the standard invocation chain** | Build a dedicated execution path just for scheduled triggers, rather than dispatching to the existing capability/workflow/event-bus mechanisms. | Directly violates "reuse before creating"; would duplicate invocation, error-classification, and tracing logic that already exists and works, the exact pattern this library has avoided since EDM. |
| **In-memory-only timer, no durable persistence** | Simpler implementation, holding next-fire times only in the running engine process. | Fails the durable, restart-safe timing goal outright; any process restart would lose or duplicate pending fires. |
| **No misfire policy; always skip missed fires silently** | Simplify by never attempting catch-up. | Acceptable for some schedules but not a universal default — critical recurring jobs (e.g., a periodic security-relevant action) may need guaranteed catch-up; making this a per-schedule declared choice rather than a fixed global behavior better serves both cases. |
| **Model scheduling as a special-case Event Bus topic with a built-in timer publisher** | Fold scheduling entirely into EEB, treating every schedule fire as just another topic dispatch. | Would work for event-publish targets but doesn't naturally cover direct capability invocation or workflow start as dispatch targets without EEB absorbing responsibilities outside its own defined scope (EEB §2 non-goals); kept as a separate, thin dispatch layer that *uses* EEB for one of its three target types instead. |

## 13. Migration Strategy

1. **Stand up the Schedule Definition Registry, Timer/Trigger Engine, Misfire/Catch-Up Handler, and Dispatch Router** as new, independently-operable components.
2. **Define the first schedule with a direct capability-invocation target**, the simplest dispatch case, to validate durable timing and misfire handling before adding workflow-start or event-publish targets.
3. **Explicitly test the restart-safety guarantee** (stop and restart the Timer/Trigger Engine mid-cycle) before relying on it for any schedule with real operational consequences.
4. **Add workflow-start and event-publish dispatch targets incrementally**, each validated independently against the same Dispatch Router interface.
5. **Establish catch-up rate-limiting before enabling any "fire once per missed occurrence" policy in production**, per the availability concern in §8/§9.

## 14. Success Criteria

- 100% of schedule dispatches resolve to one of the three existing invocation mechanisms — zero bespoke execution paths.
- A Timer/Trigger Engine restart during a pending fire window results in neither a lost fire nor a duplicate fire, verified by test.
- Every schedule has an explicitly declared misfire policy; zero schedules rely on undocumented default behavior.
- Zero new top-level EEHF error classes introduced; all dispatch failures classify into existing classes with `err.scheduling.*` codes, distinct from misfire conditions.
- At least one scheduled fire is traceable end-to-end via a single correlation ID through its dispatch target, using EOA's Unified Query Interface.

## 15. Decision Matrix

| Criterion (weight) | Durable timer + dispatch-only router to existing mechanisms (recommended) | Bespoke scheduled-execution runtime | In-memory-only timer | No misfire policy (always skip) | Fold entirely into Event Bus |
|---|---|---|---|---|---|
| Reuse of existing invocation mechanisms (High) | 5 | 1 | 4 | 4 | 3 |
| Durable, restart-safe timing (High) | 5 | 3 | 1 | 4 | 3 |
| Defined misfire/catch-up behavior (High) | 5 | 3 | 3 | 2 | 3 |
| Covers all three dispatch target types (Medium) | 5 | 5 | 4 | 4 | 2 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 2 | 4 | 4 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails reuse principle | Fails durability goal | Fails misfire-flexibility goal | Fails target-coverage goal |

**Conclusion**: a durable Timer/Trigger Engine paired with a Dispatch Router that only ever routes to the three existing invocation mechanisms is recommended. It is the only option meeting the durability and misfire-policy goals while fully preserving "reuse before creating" for actual execution.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-016: Enterprise Scheduling as a Durable Timer with Dispatch-Only Routing**

- **Status**: Accepted
- **Context**: No prior document addresses clock-driven triggering — the Workflow Engine drives execution once started, the Event Bus dispatches on a business event, but nothing decides "start this at a specific time or interval with no external trigger."
- **Decision**: Introduce a Schedule Definition Registry, durable Timer/Trigger Engine, Misfire/Catch-Up Handler, and Dispatch Router. Every fired schedule dispatches to exactly one of the three existing invocation mechanisms — direct capability call, `startWorkflow()`, or EEB `publish()` — never a new execution path. **Confirmed at approval: Scheduling determines when execution occurs, never how execution is performed** — this is the document's central, permanent boundary. Schedule versioning reuses EVCS; rollout reuses EFF; dispatch failures classify via EEHF's existing taxonomy with new `err.scheduling.*` codes; a fresh correlation ID is generated per fire using EEHF's unchanged standard. **No modification to any of the fifteen prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option meeting durability and misfire-policy goals while fully reusing existing invocation, error-classification, and tracing mechanisms rather than duplicating them for scheduled contexts specifically. Confirming the when-not-how boundary at approval protects EWE's and EEB's own execution semantics from ever being silently duplicated or overridden by a scheduling-specific shortcut.
- **Consequences**:
  - *Positive*: clock-driven work gets restart-safe timing and explicit, auditable misfire behavior; every dispatch target's own execution semantics (workflow durability, event fan-out, capability invocation) remain exactly as already specified, with zero duplication; the when/how boundary is now an explicit, confirmed decision, not an implicit convention.
  - *Negative*: introduces four new components; schedule owners must explicitly declare a misfire policy rather than relying on an assumed default.
  - *Neutral*: catch-up bursts require deliberate rate-limiting consideration by whoever operates the Timer/Trigger Engine.
- **Alternatives rejected**: bespoke scheduled-execution runtime, in-memory-only timer, no misfire policy, folding entirely into the Event Bus — see §12 and §15.
- **Reversibility**: Fully reversible — the new components can be decommissioned without affecting the Workflow Engine, Event Bus, or any capability's own invocation path; schedules would simply need an alternative triggering mechanism if Scheduling were removed.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Schedule Definition Registry, Timer/Trigger Engine, Misfire/Catch-Up Handler, and Dispatch Router are specified at architecture level. |
| **Full reuse validation** | Confirmed | §1's reuse map traces every dispatch target type to one of the three already-existing invocation mechanisms; no new execution path introduced. |
| **Boundary with Workflow Engine and Event Bus** | Confirmed explicit | §1, §7, §12 directly address why Scheduling dispatches to, rather than absorbs, both systems' responsibilities. |
| **Technology-agnostic validation** | Ready | No binding to a specific cron implementation, job scheduler, or timer technology. |
| **Security model maturity** | Ready for design review | Privilege parity with direct invocation and pause/resume governance are addressed (§8); no formal threat model performed. |
| **Catch-up burst mitigation** | Needs decision | Concrete rate-limiting parameters for "fire once per missed occurrence" policies are flagged for implementation planning, not fixed here. |
| **When-vs-how boundary** | Confirmed at approval | Scheduling determines when execution occurs, never how execution is performed (ADR-EAL-016). Any future proposal to change this requires a superseding ADR. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Dependent schedule ordering** — for cases where one schedule's dispatch should only occur after another's most recent fire completed successfully, a future extension could declare this via EDM's existing dependency graph (schedule → schedule edge) rather than a new ordering mechanism.
- **Adaptive misfire policy based on downtime duration** — a future refinement could vary catch-up behavior based on how long the Timer/Trigger Engine was unavailable, rather than a single fixed policy per schedule.
- **Schedule-level cost awareness for AI-backed targets** — where a schedule dispatches to an AI-backed capability, integrating with the AI Platform's Cost & Usage Meter (AI Platform §4) to inform scheduling frequency decisions, echoing the cost-aware scheduling idea already flagged as future evolution in the AI Platform Architecture (§18) and the Workflow Engine (§18).
- **Calendar-aware scheduling (business days, holidays)** — extending beyond raw cron/interval expressions to calendar-aware timing rules, as a refinement of the Schedule Definition Registry's timing expression rather than a new component.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-016.
