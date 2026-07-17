---
title: Enterprise Agent Platform
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Agent Platform

## 1. Problem Statement

This is the most direct test yet of two principles this library has upheld without exception since the AI Platform Architecture: **AI is an orchestration layer over deterministic engines, never a replacement for them** (ADR-EAL-011), and **the Workflow Engine is the only orchestration mechanism in the library** (reconfirmed through Marketplace, Deployment, Scalability, High Availability, Disaster Recovery, and Digital Twin). An "agent" — an AI-backed capability that plans and invokes a sequence of tools autonomously — is architecturally exactly the shape of thing that could violate both principles at once: an agent loop that both decides *and executes* its own plan, bypassing the standard invocation chain and inventing a second orchestrator in the same stroke.

This document resolves that risk by drawing one precise, structural line: **an AI-backed capability may propose a plan — a sequence of capability invocations — but it never executes that plan itself.** Execution is handed to a deterministic **Plan-to-Workflow Translator**, which converts the proposed plan into an ordinary Workflow Engine definition. Every step within that workflow is an ordinary capability invocation through the unchanged Capability Registry → ECR → Module/Plugin → ESR chain, subject to the full, unmodified request evaluation order confirmed at Licensing's approval: **Authentication → Authorization → Licensing → Feature Flags → Capability Execution.** An agent receives no exemption from any of these gates — it acts as whatever identity it has been granted (per Identity & Access, unchanged), and every tool call it initiates is checked exactly as if a human had made the same call directly.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| The agent's planning/reasoning capability itself | [AI Platform Architecture](ai-platform-architecture.md) (ADR-EAL-011) | An ordinary AI-backed capability through the unchanged Model Gateway — no new AI infrastructure. |
| Executing a proposed plan | [Workflow Engine](workflow-engine.md) (ADR-EAL-013) | The Plan-to-Workflow Translator converts a proposed plan into an ordinary workflow definition; execution is the Workflow Engine's, unchanged, in full. |
| Each individual tool/capability invocation | [Capability Registry](capability-registry.md) (ADR-EAL-003) + [Service Registry](service-registry.md) (ADR-EAL-004) | Every step is an ordinary call through the unchanged standard chain — no agent-specific invocation path. |
| Agent identity and per-call authorization | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | An agent acts as an existing identity type (typically System Identity, or "on behalf of" a Human/Provider identity) — no new identity type, no elevated privilege, no exemption from `checkPermission()`. |
| Licensing and feature-flag gating on agent-initiated calls | [Licensing](licensing.md) (ADR-EAL-022) / [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | The confirmed evaluation order (Authentication → Authorization → Licensing → Feature Flags → Capability Execution) applies to every agent-initiated call exactly as to any other — no bypass. |
| Informing the agent's plan with existing relationships | [Knowledge Graph](knowledge-graph.md) (ADR-EAL-032) | Read-only `queryRelationships()` — the agent's plan may be informed by the graph, never write to it directly (it can still `suggestRelationship()` like any other AI-backed capability, unchanged). |
| Informing the agent's plan with relevant capabilities/content | [Semantic Search](semantic-search.md) (ADR-EAL-031) | Read-only `search()` — no new discovery mechanism. |
| Tool-call and planning-failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Existing taxonomy, new `err.agentplatform.*` codes. |
| Agent action audit candidacy | [Audit Framework](audit-framework.md) (ADR-EAL-019) | Recommended, not unilaterally designated, following the pattern established by Licensing and Deployment. |

**Scope boundary:** this document does not modify any of the thirty-two prior documents. An agent is a planning capability plus a deterministic translation step — it introduces no new execution path, no new identity type, and no exemption from any existing gate.

## 2. Goals

| Goal | Description |
|---|---|
| **AI proposes, never executes** | An agent's planning output is a proposed plan; a deterministic translator, not the AI itself, converts it into an executable workflow. |
| **No second orchestrator** | Plan execution is the Workflow Engine's, unchanged — the ninth consecutive confirmation of the sole-orchestrator principle. |
| **No exemption from any gate** | Every agent-initiated tool call passes through the full, unmodified evaluation order — authentication, authorization, licensing, and feature flags apply exactly as to a direct human call. |
| **Least-privilege agent scoping** | An agent's allowed capability scope is explicitly declared, not implicitly "whatever it can reach." |
| **Read-only use of Knowledge Graph and Semantic Search for planning** | An agent may consult, never directly assert into, either. |

**Non-goals**: this document does not let an agent's plan bypass any existing authorization, licensing, or flag gate; it does not introduce a second orchestration mechanism for plan execution; and it does not grant an agent implicit access to any capability beyond what it is explicitly scoped to.

## 3. Architecture

```
   ┌───────────────────────────┐        ┌───────────────────────────┐
   │   Agent Definition Registry     │        │ Knowledge Graph / Semantic    │
   │   (new) — declares allowed        │        │ Search (unchanged) — read-     │
   │   capability scope                │        │ only planning input             │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Planning Capability          │◄──────┤ AI Platform Model Gateway     │
   │   (ordinary AI-backed             │        │ (unchanged)                    │
   │    capability, per ADR-EAL-011)   │        └───────────────────────────┘
   └─────────────┬─────────────┘
                 │ proposed plan (not yet executable)
   ┌─────────────▼─────────────┐
   │   Plan-to-Workflow Translator   │  ← new: deterministic, not AI —
   │   (new)                        │    converts a plan into a workflow
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Workflow Engine (unchanged)   │──────►│ Every step: Capability Registry│
   │   executes the translated        │        │ → ESR chain, full Auth→AuthZ→ │
   │   plan as an ordinary instance    │        │ Licensing→Flags→Execution      │
   └───────────────────────────┘        │ gating (unchanged, per step)   │
                                        └───────────────────────────┘
```

## 4. Components

- **Agent Definition Registry** *(new)* — declares an agent's identity (per Identity & Access, unchanged) and its explicitly scoped set of allowed capabilities — an agent may only plan around capabilities it is declared to have access to, a least-privilege boundary enforced structurally, not left to the planning capability's own discretion.
- **Planning Capability** *(ordinary AI-backed capability, not new AI infrastructure)* — reads the current context, optionally consulting Knowledge Graph and Semantic Search read-only, and proposes a plan: an ordered (or partially-ordered) sequence of capability invocations with parameters. This proposal is data, not an execution path.
- **Plan-to-Workflow Translator** *(new, explicitly deterministic — not AI)* — validates a proposed plan against the Agent Definition Registry's declared scope and converts it into an ordinary Workflow Engine definition; a plan referencing a capability outside the agent's declared scope is rejected here, before any execution begins.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineAgent(agentId, identityRef, allowedCapabilityIds)` | Governance action → Agent Definition Registry | Declares an agent's identity and scoped capability access. |
| `proposePlan(agentId, goal, context)` | Caller → Planning Capability (ordinary AI-backed capability) | Produces a proposed plan — data, not an execution path. |
| `translateAndExecute(agentId, proposedPlan)` | Plan-to-Workflow Translator → Workflow Engine (`startWorkflow()`, unchanged) | Validates scope, converts the plan to a workflow definition, and starts it — every step subject to the full, unchanged gating pipeline. |

## 6. Data Flow

1. An agent is declared via `defineAgent()`, with an explicit, least-privilege set of allowed capabilities — never implicit or open-ended.
2. `proposePlan()` invokes the Planning Capability (an ordinary AI-backed capability, per the unchanged AI Platform), optionally reading Knowledge Graph relationships and Semantic Search results read-only; it returns a proposed plan as data.
3. `translateAndExecute()` validates the proposed plan against the Agent Definition Registry's declared scope — any step referencing a capability outside that scope is rejected here, before execution, not discovered mid-run.
4. The Plan-to-Workflow Translator converts the validated plan into an ordinary Workflow Engine definition and starts it via the unchanged `startWorkflow()`.
5. Each step in the resulting workflow instance invokes its target capability through the unchanged standard chain, subject to the full, unmodified evaluation order (Authentication → Authorization → Licensing → Feature Flags → Capability Execution) — an agent-initiated call receives no exemption at any stage.
6. Any planning or execution failure classifies via EEHF's existing taxonomy with a new `err.agentplatform.*` code.

## 7. Design Patterns

- **AI proposes, determinism translates, the Workflow Engine executes — the sharpest application yet of "AI orchestrates, never replaces"** — the Plan-to-Workflow Translator is the structural enforcement point: a proposed plan is inert data until a deterministic process (not the AI) turns it into something executable, and even then, execution is entirely the Workflow Engine's, not a new agent-specific runtime.
- **Least-privilege agent scoping, enforced at translation time, not at each step's discretion** — mirrors PLM's own least-privilege capability-grant model (PLM §2, §8), applied here to what an agent may even propose to do.
- **No gate exemption for agent-initiated calls** — every step an agent's translated workflow takes is indistinguishable, from the gating pipeline's perspective, from a directly-initiated human call; this is what prevents "it's just an agent" from becoming an informal bypass path.
- **Read-only consultation of Knowledge Graph and Semantic Search** — an agent's planning may be informed by both, exactly as any other AI-backed capability may consult them, with no special write access granted for being "agentic."

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Least-Privilege** (ESA catalog) is the central concern of the Agent Definition Registry — an agent's declared capability scope should be the narrowest set that satisfies its actual purpose, reviewed as carefully as any human role's permission grant.
- **Principle: Fail-Closed Validation** (ESA catalog) applies to the Plan-to-Workflow Translator — a plan step referencing an out-of-scope capability must be rejected outright, never executed with a warning.
- **An agent's identity must be attributable** — whether acting as a System Identity or "on behalf of" a Human/Provider identity, every action it takes must be traceable to that identity through the unchanged Identity & Access and Audit Framework mechanisms, exactly as any other caller's actions are.
- **Agent-initiated actions are a natural candidate for the Mandatory Audit Event Catalog** — consistent with the recommend-don't-mandate pattern already established (Licensing §18, Deployment §18).

## 9. Scalability

Planning-capability load is bounded by the AI Platform's own Model Gateway characteristics (AI Platform §9); translated workflow execution inherits the Workflow Engine's own scaling profile (Workflow Engine §9). This document introduces no new scaling axis beyond the composition of two already-addressed ones.

## 10. Best Practices

- Declare an agent's capability scope as narrowly as its actual purpose requires — never grant broad access "in case the agent needs it later."
- Treat a proposed plan as untrusted data until the Plan-to-Workflow Translator validates it against declared scope — never execute a plan directly from the Planning Capability's output.
- Recommend, rather than assume, agent-action inclusion in the Audit Framework's Mandatory Audit Event Catalog.

## 11. Common Pitfalls

- **Building an "agent loop" that both plans and executes** — the single most important pitfall this entire document exists to prevent; collapsing planning and execution into one AI-driven loop violates both the AI orchestration-only principle and the sole-orchestrator principle simultaneously.
- **Granting an agent implicit or broad capability access "for flexibility"** — inverts least-privilege and makes the Agent Definition Registry's scoping meaningless.
- **Letting an agent's identity be untraceable or shared across many agents** — undermines attribution and the Audit Framework's ability to record what actually happened.
- **Skipping scope validation at translation time and relying on per-step gating alone to catch an out-of-scope call** — per-step gating (Identity & Access, Licensing, Feature Flags) is still the actual enforcement, but validating scope at translation time catches a malformed plan before any workflow instance is even started, failing faster and more legibly.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **A monolithic agent loop that plans and executes in one AI-driven process** | The common "agent framework" pattern — an LLM decides and immediately acts, iteratively. | Violates both the AI orchestration-only principle and the sole-orchestrator principle at once; this library's entire discipline since ADR-EAL-011 exists specifically to prevent this pattern from being adopted uncritically. |
| **Grant agents broad, implicit capability access** | Skip explicit scoping, let an agent call whatever it can discover. | Inverts least-privilege catastrophically for an autonomous, AI-driven caller — exactly the case where explicit scoping matters most. |
| **Exempt agent-initiated calls from Licensing/Feature-Flag gating "since they're internal automation"** | Treat agent calls as a privileged internal path. | Directly violates the confirmed, permanent request evaluation order (ADR-EAL-022); an agent is a caller like any other and must be gated identically. |
| **Let the Planning Capability write directly into Knowledge Graph or execute plans itself** | Skip the translation/validation step for efficiency. | Removes the one structural safeguard (deterministic translation and scope validation) that prevents an agent's proposed plan from becoming an unreviewed execution path. |

## 13. Migration Strategy

1. **Define the first agent with a deliberately narrow capability scope**, validating the full propose → translate → execute pipeline end-to-end before expanding scope.
2. **Implement the Plan-to-Workflow Translator's scope validation first**, testing that an out-of-scope plan step is rejected before any execution attempt.
3. **Confirm no gate exemption exists** by testing an agent-initiated call against Licensing and Feature Flags exactly as a direct human call would be tested.
4. **Propose agent-action inclusion in the Audit Framework's Mandatory Audit Event Catalog** through that document's own governance process.

## 14. Success Criteria

- Every agent has an explicit, narrowly-scoped Agent Definition Registry entry — zero agents with implicit or unbounded capability access.
- 100% of agent-initiated capability invocations pass through the full, unmodified evaluation order — zero gate exemptions.
- A malformed or out-of-scope proposed plan is demonstrably rejected at translation time, before any workflow execution begins.
- Zero instances of the Planning Capability executing a plan directly — confirmed structural separation from the Plan-to-Workflow Translator and Workflow Engine.
- Agent action audit-inclusion is formally proposed to the Audit Framework's governance process.

## 15. Decision Matrix

| Criterion (weight) | AI proposes + deterministic translation + Workflow Engine execution, scoped access (recommended) | Monolithic agent loop | Broad implicit agent access | Gate-exempt agent calls | Planning Capability executes directly |
|---|---|---|---|---|---|
| Preserves AI orchestration-only principle (High) | 5 | 1 | 4 | 3 | 1 |
| Preserves sole-orchestrator principle (High) | 5 | 1 | 4 | 4 | 1 |
| Least-privilege agent scoping (High) | 5 | 3 | 1 | 3 | 3 |
| No gate exemption for agent calls (High) | 5 | 3 | 3 | 1 | 3 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 4 | 2 | 3 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails both core principles | Fails least-privilege goal | Fails gate-exemption goal | Fails structural-separation goal |

**Conclusion**: an agent architecture where AI only proposes, a deterministic translator validates and converts, and the unchanged Workflow Engine executes with zero gate exemptions is recommended — the only option preserving both non-negotiable, library-wide principles simultaneously under the most direct test either has faced.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-033: Enterprise Agent Platform as Propose-Translate-Execute, With No Gate Exemptions**

- **Status**: Accepted
- **Context**: An "agent" is architecturally the shape of thing most likely to violate the AI orchestration-only principle and the sole-orchestrator principle simultaneously, if built as the common monolithic plan-and-execute loop.
- **Decision**: Introduce an Agent Definition Registry (least-privilege capability scoping), a Planning Capability (an ordinary AI-backed capability producing proposed plans as data), and a Plan-to-Workflow Translator (deterministic, validates scope, converts to an ordinary Workflow Engine definition). **Confirmed at approval, stated precisely: an agent is a planner, never an executor. The Planning Capability produces a proposed plan only. The Plan-to-Workflow Translator validates the plan and converts it into an ordinary Workflow Engine definition. Every workflow step must pass the complete evaluation chain — Authentication → Authorization → Licensing → Feature Flags → Capability Execution. Agents receive no privileged execution path or elevated authority.** **No modification to any of the thirty-two prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option preserving both non-negotiable principles under direct pressure from a pattern (the monolithic agent loop) that is common practice elsewhere but incompatible with this library's foundational discipline.
- **Consequences**:
  - *Positive*: agents gain real autonomy (proposing multi-step plans) without any erosion of authorization, licensing, or orchestration guarantees; least-privilege scoping is structurally enforced, not left to the AI's own judgment.
  - *Negative*: every agent action incurs the full gating pipeline's latency, exactly as any other call would — no fast path is offered for agent-initiated traffic.
  - *Neutral*: an agent's usefulness is bounded by its declared scope, which must be maintained deliberately as its purpose evolves.
- **Alternatives rejected**: monolithic agent loop, broad implicit access, gate-exempt agent calls, direct execution by the Planning Capability — see §12 and §15.
- **Reversibility**: Fully reversible — Agent Definitions, the Planning Capability, and the Translator can be decommissioned without affecting the Workflow Engine, Identity & Access, Licensing, or any capability an agent was scoped to call.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Agent Definition Registry, Planning Capability, and Plan-to-Workflow Translator are specified at architecture level. |
| **Preserves AI orchestration-only and sole-orchestrator principles under direct pressure** | Confirmed | The propose/translate/execute separation is the explicit structural safeguard. |
| **No gate exemption for agent calls** | Confirmed | Every step passes the full, unmodified evaluation order. |
| **FUTURE-phase caveat** | Explicitly noted | As with prior FUTURE-phase documents, practical agent usefulness depends on planning-model quality and the richness of declared capability scopes in a given deployment. |
| **Technology-agnostic validation** | Ready | No binding to a specific agent framework or planning-model architecture. |
| **Planner-not-executor boundary** | Confirmed at approval | Agent = planner only; Translator validates/converts; every step passes the complete evaluation chain; no privileged execution path or elevated authority. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Human-in-the-loop plan approval** — for especially consequential plans, routing translated workflows through an explicit human-approval step before execution, building on the Workflow Engine's existing halt/`resumeInstance()` mechanism rather than a new approval system.
- **Cross-reference with Autonomous Systems** — the final FUTURE-phase item may extend agent concepts further; this document does not anticipate that design.
- **Agent scope refinement via Knowledge Graph** — using declared relationships to inform which capabilities an agent's scope should reasonably include, as a design-time aid, never an automatic scope expansion at runtime.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-033.
