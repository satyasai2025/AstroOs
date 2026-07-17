---
title: Enterprise Autonomous Systems
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Autonomous Systems

## 1. Problem Statement

This is the final item on the entire roadmap, and it is deliberately the smallest conceptual step of the whole library: [Agent Platform](agent-platform.md) (ADR-EAL-033) already defined a safe propose → translate → execute cycle, with an agent as a planner, never an executor, and zero gate exemptions. The only thing Agent Platform does not address is **running that cycle repeatedly, on its own trigger, without a human re-initiating each one** — true autonomy over a sustained duration rather than one-shot planning.

This document adds exactly that, and nothing else: a **triggering and bounding layer** around Agent Platform's unchanged pipeline. It introduces no new execution model, no elevated authority, and no exemption from anything already established. Removing the human-re-initiates-each-cycle step raises the stakes enough that this document's one genuinely new obligation is an explicit, always-available **kill-switch** — and rather than build a new one, it reuses the Feature Flag Framework's existing kill-switch mechanism literally: autonomous operation is gated by an ordinary feature flag, and disabling that flag halts all future cycles immediately.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Every individual planning/execution cycle | [Agent Platform](agent-platform.md) (ADR-EAL-033) | Unchanged in full — propose (AI), validate/translate (deterministic), execute (Workflow Engine), zero gate exemptions. Autonomous Systems adds no new execution model. |
| Triggering the next cycle | [Scheduling](scheduling.md) (ADR-EAL-016) | An ordinary Scheduling-dispatched trigger calls Agent Platform's existing `proposePlan()`/`translateAndExecute()` pipeline once per cycle — Scheduling still only decides *when*, never *how*, per its own permanent principle. |
| The kill-switch | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Autonomous operation is literally gated by an ordinary feature flag; disabling it (via EFF's existing kill-switch mechanism, unchanged) halts all future cycle triggering immediately — no new kill-switch component built. |
| Resource/cost bounding across cycles | [AI Platform Architecture](ai-platform-architecture.md) (ADR-EAL-011) | The unchanged Cost & Usage Meter caps total spend across a run of cycles. |
| Tier-based extent limits | [Licensing](licensing.md) (ADR-EAL-022) | Unchanged entitlement query caps how much autonomous operation a tenant's plan permits. |
| Authorization for each cycle's actions | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | Fully unchanged — no elevated authority for autonomous operation versus a single agent invocation. |
| Autonomous-cycle audit candidacy | [Audit Framework](audit-framework.md) (ADR-EAL-019) | Recommended, not unilaterally designated, following the established pattern. |

**Scope boundary:** this document does not modify any of the thirty-three prior documents, including Agent Platform's own execution model. It adds a bounding/triggering layer only. Approval of this document completes the entire roadmap (34/34).

## 2. Goals

| Goal | Description |
|---|---|
| **Repeated cycles via Scheduling, not a new loop** | Each cycle is triggered by the existing Scheduling mechanism, dispatching to Agent Platform's unchanged pipeline. |
| **An always-available kill-switch, reusing EFF literally** | Disabling an ordinary feature flag halts all future cycles — no new kill-switch mechanism. |
| **Explicit, pre-declared autonomy bounds** | Maximum cycle count, cost cap, and time window are declared up front, not discovered mid-run. |
| **Zero new execution authority** | Every cycle's actions remain exactly as gated as a single Agent Platform invocation — no exemption for being "autonomous." |
| **Completes the roadmap** | This is the final planned document; any future expansion requires the same amendment discipline (a new roadmap item, its own ADR, explicit approval) established throughout this session. |

**Non-goals**: this document does not grant an autonomous system any capability scope beyond what its underlying Agent Definition already declares (Agent Platform §4); it does not remove or weaken any gate in the confirmed evaluation order; and it does not build a new orchestration, scheduling, or kill-switch mechanism where an existing one already serves.

## 3. Architecture

```
   ┌───────────────────────────┐        ┌───────────────────────────┐
   │   Autonomy Boundary Registry    │◄──────┤ AI Platform Cost & Usage      │
   │   (new) — max cycles, cost cap,  │        │ Meter (unchanged) + Licensing  │
   │   time window                    │        │ (unchanged) — extent caps       │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Kill-switch flag              │◄──────┤ Feature Flag Framework        │
   │   ("autonomous_operation_        │        │ (unchanged) — ordinary flag,   │
   │    enabled") — checked every      │        │  ordinary kill-switch           │
   │    cycle before triggering         │        └───────────────────────────┘
   └─────────────┬─────────────┘
                 │ (if enabled and within bounds)
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Scheduling (unchanged)        │──────►│ Agent Platform (unchanged) —  │
   │   dispatches the next cycle       │        │ propose → translate → execute,│
   │                                 │        │ zero gate exemptions            │
   └───────────────────────────┘        └───────────────────────────┘
```

## 4. Components

- **Autonomy Boundary Registry** *(new)* — declares, per autonomous run, a maximum cycle count, a cost cap (checked against the unchanged AI Platform Cost & Usage Meter), and a time window; a run that would exceed any bound does not trigger a further cycle.
- **Kill-switch flag** *(reused, not new)* — an ordinary Feature Flag Framework flag (e.g., `autonomous_operation_enabled`) checked before each cycle's trigger; disabling it via EFF's existing, unchanged kill-switch mechanism halts all future cycles immediately. No new kill-switch component is built.
- **(Reused, not owned) Scheduling trigger and Agent Platform pipeline** — every cycle is dispatched by Scheduling and executed by Agent Platform's unchanged propose/translate/execute model; this document owns neither.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineAutonomousRun(runId, agentId, maxCycles, costCap, timeWindow)` | Governance action → Autonomy Boundary Registry | Declares the bounds for a run of repeated cycles against an existing Agent Definition (Agent Platform §5, unchanged). |
| `checkBounds(runId)` | Scheduling-dispatched trigger (internal, before each cycle) → Autonomy Boundary Registry + kill-switch flag | Confirms the run is within its declared bounds and the kill-switch flag is still enabled before triggering the next cycle. |
| (Unchanged) `proposePlan()` / `translateAndExecute()` | Scheduling-dispatched trigger → Agent Platform (unchanged) | Each cycle's actual planning and execution — identical to a single, manually-initiated agent invocation. |

## 6. Data Flow

1. A governance action calls `defineAutonomousRun()`, declaring bounds against an already-existing Agent Definition (Agent Platform §4, unchanged) — an autonomous run never expands an agent's declared capability scope.
2. Scheduling (unchanged) dispatches a trigger at its configured interval; before calling Agent Platform's pipeline, `checkBounds()` confirms the run hasn't exceeded its cycle count, cost cap, or time window, and that the kill-switch flag remains enabled.
3. If bounds are satisfied and the flag is enabled, the trigger calls Agent Platform's unchanged `proposePlan()` and `translateAndExecute()` — the cycle proceeds exactly as any single agent invocation would, subject to the full, unmodified evaluation order (Authentication → Authorization → Licensing → Feature Flags → Capability Execution).
4. If the kill-switch flag is disabled at any point, `checkBounds()` fails on the next scheduled check and no further cycle is triggered — the run halts without requiring any other action.
5. Cost accrued by each cycle is read from the unchanged AI Platform Cost & Usage Meter and checked against the run's declared cap before the next cycle is permitted.
6. Autonomous-cycle events are recommended, not unilaterally designated, as Mandatory Audit Event Catalog candidates.

## 7. Design Patterns

- **A bounding/triggering layer, not a new execution model — the tenth consecutive confirmation of the sole-orchestrator principle** — Autonomous Systems adds zero new orchestration; Scheduling triggers, Agent Platform executes, exactly as both were already designed to.
- **Kill-switch by literal reuse, not by pattern-reapplication** — unlike Integration Framework's circuit-breaker (which reapplied PLM's *pattern* without reusing PLM's actual component, since the concerns differed), this document reuses EFF's actual kill-switch mechanism directly, because the concern — "immediately and reliably disable a specific behavior" — is exactly what EFF's kill-switch already does.
- **Bounds declared up front, checked every cycle, never discovered mid-run** — consistent with the fail-closed discipline applied throughout this library: an unbounded or ambiguous check halts rather than proceeding optimistically.
- **Completing the roadmap with the smallest possible new surface** — the final document in this session adds the least new architecture of any of the thirty-four, by design: the discipline built up across the entire library (reuse before creating, sole orchestrator, AI orchestration-only, no gate exemptions) means the "hard part" of autonomy was already solved by Agent Platform; this document only had to add bounding and a kill-switch.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Fail-Closed Validation** (ESA catalog) applies to `checkBounds()` — an unresolvable bounds check (e.g., the Cost & Usage Meter is unreachable) must halt the run, never proceed on an assumed-safe default.
- **Principle: Least-Privilege** (ESA catalog) is preserved by construction — an autonomous run never expands its underlying Agent Definition's declared capability scope; bounding is additive restriction, never a grant of new authority.
- **Kill-switch authorization should be at least as narrow as Agent Definition governance** (Agent Platform §8) — disabling autonomous operation is a significant action and should be available to, and restricted to, an appropriately authorized set of identities.
- **Every cycle's actions remain fully attributable** through the unchanged Identity & Access and Audit Framework mechanisms — autonomy does not reduce traceability.

## 9. Scalability

Not a meaningful new concern — cycle-triggering load is bounded by Scheduling's own dispatch model (Scheduling §9), and each cycle's actual execution load is Agent Platform's (Agent Platform §9). This document introduces no new scaling axis.

## 10. Best Practices

- Always declare explicit cycle-count, cost, and time bounds before enabling an autonomous run — never let it operate unboundedly "until something goes wrong."
- Treat the kill-switch flag with the same operational seriousness as any production kill-switch — test that disabling it actually halts future cycles before relying on it during an incident.
- Never expand an agent's declared capability scope specifically to enable autonomous operation — if broader scope seems necessary, that is a separate, deliberate Agent Platform decision, not a side effect of this document.

## 11. Common Pitfalls

- **Treating "autonomous" as license to relax any gate** — the single most important discipline to carry forward from Agent Platform; nothing about running repeated cycles justifies any exemption from the confirmed evaluation order.
- **Building a new kill-switch instead of reusing EFF's** — would duplicate an already-solved capability for no reason.
- **Discovering bounds violations after the fact instead of checking before each cycle** — `checkBounds()` must run before triggering, not as a post-hoc audit.
- **Letting bounds be adjusted upward mid-run without the same governance rigor as the initial declaration** — a bound that can be silently loosened isn't actually a bound.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **A dedicated autonomous-execution engine, separate from Agent Platform** | Build new orchestration specifically for repeated-cycle autonomy. | Directly duplicates Agent Platform's already-safe propose/translate/execute model; the only genuinely new need is triggering and bounding, not execution. |
| **A bespoke kill-switch mechanism** | Build a new, autonomy-specific disable mechanism instead of reusing EFF's. | Duplicates a capability EFF already provides and has already been validated for exactly this purpose (immediate, reliable behavior disablement). |
| **Unbounded autonomous operation** | No declared cycle/cost/time limits. | Fails the core risk-management goal of this document; unbounded autonomous resource consumption is precisely the scenario a bounding layer exists to prevent. |
| **Expanded capability scope for autonomous agents** | Grant autonomous runs broader access than a single manual invocation. | Violates least-privilege for no structural reason; an agent's declared scope should not depend on how it happens to be triggered. |

## 13. Migration Strategy

1. **Define the kill-switch flag first**, and test that disabling it halts cycle triggering before any autonomous run is ever enabled.
2. **Declare a narrow Autonomy Boundary (low cycle count, low cost cap, short time window) for the first autonomous run**, validating the full bounded-cycle pipeline before expanding.
3. **Confirm no capability scope expansion occurs** by comparing an autonomous run's actual capability access against its underlying Agent Definition's declared scope.
4. **Propose autonomous-cycle events to the Audit Framework's Mandatory Audit Event Catalog** through that document's own governance process.

## 14. Success Criteria

- Every autonomous run has explicit, declared cycle-count, cost, and time bounds — zero unbounded runs.
- Disabling the kill-switch flag is demonstrated halting all future cycle triggering within one Scheduling interval.
- Zero capability scope expansion for any autonomous run relative to its underlying Agent Definition.
- Every cycle within an autonomous run passes the full, unmodified evaluation order — zero exemptions.
- This document's approval is confirmed as completing the full roadmap (34/34 documents).

## 15. Decision Matrix

| Criterion (weight) | Bounding/triggering layer reusing Scheduling + Agent Platform + EFF's kill-switch (recommended) | Dedicated autonomous-execution engine | Bespoke kill-switch | Unbounded operation | Expanded capability scope |
|---|---|---|---|---|---|
| Reuse of Agent Platform's safe execution model (High) | 5 | 1 | 4 | 4 | 3 |
| Reliable, reused kill-switch (High) | 5 | 3 | 3 | 1 | 3 |
| Bounded risk (High) | 5 | 3 | 3 | 1 | 3 |
| Preserves least-privilege scope (High) | 5 | 3 | 4 | 4 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 2 | 3 | 5 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails reuse principle | Duplicates existing capability | Fails bounded-risk goal | Fails least-privilege goal |

**Conclusion**: a thin bounding/triggering layer — Scheduling dispatches, Agent Platform executes unchanged, EFF's existing kill-switch governs — is recommended, completing the roadmap with the smallest new surface consistent with genuine, safe autonomy.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-034: Enterprise Autonomous Systems as a Bounded Triggering Layer Over Agent Platform, Reusing Scheduling and Feature Flags**

- **Status**: Accepted
- **Context**: Agent Platform (ADR-EAL-033) defined a safe single-cycle propose/translate/execute model but did not address repeated, self-triggered cycles; removing per-cycle human re-initiation raises the stakes enough to require an explicit, reliable kill-switch and pre-declared bounds.
- **Decision**: Introduce an Autonomy Boundary Registry (cycle count, cost cap via the unchanged AI Platform Cost & Usage Meter, time window) and reuse the Feature Flag Framework's existing kill-switch mechanism literally (an ordinary flag gates whether the next cycle triggers). Each cycle is dispatched by Scheduling's unchanged mechanism and executed by Agent Platform's unchanged pipeline, with zero new execution authority and zero capability-scope expansion. **Confirmed at approval: autonomous systems remain bounded by declared scope, declared duration, declared cost, declared capabilities, and ordinary platform governance. Autonomous operation remains strictly a composition of existing platform capabilities — no autonomous path bypasses authentication, authorization, licensing, feature flags, workflows, or deterministic execution.** **No modification to any of the thirty-three prior documents. This document's approval completes the roadmap (34/34).**
- **Rationale**: The Decision Matrix (§15) shows this is the only option that achieves genuine, bounded autonomy while fully reusing Agent Platform's already-validated safety model, Scheduling's when-not-how principle, and EFF's already-proven kill-switch mechanism — introducing the minimum new architecture consistent with the risk of unattended, repeated operation.
- **Consequences**:
  - *Positive*: autonomous operation is possible without any new execution risk beyond what Agent Platform already accepted; the kill-switch is proven, not novel; bounds prevent runaway cost or duration.
  - *Negative*: an autonomous run is only as safe as its underlying Agent Definition's scope — this document does not, and should not, compensate for a poorly-scoped agent.
  - *Neutral*: this is the final roadmap item; any future expansion of scope requires a new roadmap entry and its own ADR, per the Roadmap Rules established at the start of this process.
- **Alternatives rejected**: a dedicated autonomous-execution engine, a bespoke kill-switch, unbounded operation, expanded capability scope — see §12 and §15.
- **Reversibility**: Fully reversible — the Autonomy Boundary Registry and kill-switch flag can be removed without affecting Agent Platform, Scheduling, or the Feature Flag Framework; autonomous runs would simply stop being triggerable.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Autonomy Boundary Registry and kill-switch reuse are specified at architecture level. |
| **Zero new execution authority** | Confirmed | Every cycle is an unchanged Agent Platform invocation. |
| **Kill-switch reliability** | Confirmed by design, reusing EFF's proven mechanism | Not a novel, unvalidated component. |
| **Least-privilege preserved** | Confirmed | No capability scope expansion for autonomous runs. |
| **FUTURE-phase caveat** | Explicitly noted | As with the other FUTURE-phase documents, practical value depends on deployment-specific risk tolerance for unattended operation. |
| **Bounding principle** | Confirmed at approval | Bounded by declared scope, duration, cost, capabilities, and ordinary platform governance — a composition of existing capabilities, never a bypass of authentication, authorization, licensing, feature flags, workflows, or deterministic execution. |
| **Roadmap completion** | Confirmed | This was the final planned document; this freeze completes 34/34 across all four phases. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Any further capability beyond this document requires a new roadmap entry and its own ADR** — consistent with the Roadmap Rules established at the outset (ROADMAP.md: "Do not add roadmap items without approval... New roadmap items require an ADR or explicit approval"); this document does not presume what, if anything, comes next.
- **Adaptive bounds based on observed cycle outcomes** — a future refinement could adjust cost/cycle caps based on a run's own track record, still gated by the same governance discipline as the initial declaration.
- **Multi-agent autonomous coordination** — if multiple autonomous runs need to coordinate, a future document could address that using the Event Bus and Knowledge Graph, unchanged, rather than a new coordination mechanism.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-034. This freeze completes the entire roadmap (34/34 across Foundation, Platform, Enterprise, and Future phases).
