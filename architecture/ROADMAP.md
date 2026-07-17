# Enterprise Architecture Library — Roadmap

**STATUS: v1.0 COMPLETE — 34/34 documents frozen across all four phases (2026-07-15).** [COMPLETION_REPORT.md](COMPLETION_REPORT.md) reviewed and approved 2026-07-15.

**GOVERNANCE MODE.** No v2.0 roadmap is active. The library accepts changes only via: a new ADR, an approved RFC, or a governance decision. No document is added, drafted, or modified outside those three triggers until further instruction.

Tracks the full planned scope of the Enterprise Architecture Library across four phases. See [STATUS.md](STATUS.md) for per-document lifecycle detail and [INDEX.md](INDEX.md) for the master table of contents.

Legend: ✅ Frozen/Accepted · 🔶 Drafted, awaiting approval · ⬜ Not started

## FOUNDATION

| | Document | ADR |
|---|---|---|
| ✅ | Plugin Lifecycle | ADR-EAL-001 |
| ✅ | Module Registry | ADR-EAL-002 |
| ✅ | Capability Registry | ADR-EAL-003 |
| ✅ | Service Registry | ADR-EAL-004 |
| ✅ | Configuration Framework | ADR-EAL-005 |
| ✅ | Feature Flags | ADR-EAL-006 |
| ✅ | Dependency Management | ADR-EAL-007 |
| ✅ | Version Compatibility | ADR-EAL-008 |
| ✅ | Error Handling | ADR-EAL-009 |
| ✅ | Observability | ADR-EAL-010 |

## PLATFORM

| | Document | ADR |
|---|---|---|
| ✅ | AI Platform | ADR-EAL-011 |
| ✅ | Research Platform | ADR-EAL-012 |
| ✅ | Workflow Engine | ADR-EAL-013 |
| ✅ | Event Bus | ADR-EAL-014 |
| ✅ | Notification Framework | ADR-EAL-015 |
| ✅ | Scheduling | ADR-EAL-016 |
| ✅ | Security Architecture | ADR-EAL-017 |
| ✅ | Identity & Access | ADR-EAL-018 |
| ✅ | Audit Framework | ADR-EAL-019 |
| ✅ | API Gateway | ADR-EAL-020 |

## ENTERPRISE

| | Document | ADR |
|---|---|---|
| ✅ | Multi Tenancy | ADR-EAL-021 |
| ✅ | Licensing | ADR-EAL-022 |
| ✅ | Marketplace | ADR-EAL-023 |
| ✅ | SDK | ADR-EAL-024 |
| ✅ | Integration Framework | ADR-EAL-025 |
| ✅ | Deployment | ADR-EAL-026 |
| ✅ | Scalability | ADR-EAL-027 |
| ✅ | High Availability | ADR-EAL-028 |
| ✅ | Disaster Recovery | ADR-EAL-029 |

## FUTURE

| | Document | ADR |
|---|---|---|
| ✅ | Digital Twin | ADR-EAL-030 |
| ✅ | Semantic Search | ADR-EAL-031 |
| ✅ | Knowledge Graph | ADR-EAL-032 |
| ✅ | Agent Platform | ADR-EAL-033 |
| ✅ | Autonomous Systems | ADR-EAL-034 |

## Status

**ROADMAP.md is the authoritative backlog.** After each document is approved: freeze it, update this file, update STATUS.md, update INDEX.md, then scan the tables above for the first ⬜/🔶 entry in phase order and continue with that item automatically — never by naming or recalling a specific document ahead of the scan. Progress pauses only if a roadmap dependency blocks the next item, an architectural decision needs the principal's approval, or the roadmap is complete.

**Confirmed principle (ADR-EAL-011):** AI remains an orchestration layer over deterministic engines, never a replacement for them. This applies to every Platform-phase document going forward wherever AI/model-backed components interact with deterministic capabilities.

**Confirmed principle (ADR-EAL-016):** Scheduling determines when execution occurs, never how execution is performed. Any future document that triggers time-based execution must dispatch to an existing invocation mechanism (capability chain, Workflow Engine, or Event Bus) rather than duplicating execution logic.

**Confirmed principle (ADR-EAL-034):** Autonomous Systems remain bounded by declared scope, declared duration, declared cost, declared capabilities, and ordinary platform governance. Autonomous operation is strictly a composition of existing platform capabilities — no autonomous path bypasses authentication, authorization, licensing, feature flags, workflows, or deterministic execution. This document's freeze completes the roadmap (34/34).

**Confirmed principle (ADR-EAL-033):** An agent is a planner, never an executor. The Planning Capability produces a proposed plan only; the Plan-to-Workflow Translator validates and converts it into an ordinary Workflow Engine definition. Every workflow step must pass the complete evaluation chain (Authentication → Authorization → Licensing → Feature Flags → Capability Execution). Agents receive no privileged execution path or elevated authority.

**Confirmed principle (ADR-EAL-028):** High Availability addresses redundancy and failover within normal failure domains only. Disaster Recovery remains the sole authority for catastrophic/cross-region recovery. This boundary is binding on both documents.

**Open governance question (ADR-EAL-021):** Multi Tenancy names, but does not resolve, a tension between tenant data-deletion requests and the Audit Framework's mandatory retention floor (ADR-EAL-019). **Tracked as a Governance Decision requiring a separate, dedicated ADR filed under the Audit & Compliance category** (not yet drafted) — not resolved informally, not defaulted either direction. See multi-tenancy.md §16.

**Confirmed principle (ADR-EAL-022):** Canonical request evaluation order — **Authentication → Authorization → Licensing → Feature Flags → Capability Execution** — short-circuiting on failure at any stage. This is the binding pipeline sequence for every gated capability invocation going forward.

**Reconfirmed (not altered) at ADR-EAL-022's approval:**
- Identity & Access (ADR-EAL-018) is the sole authoritative source for authentication, authorization, and identity — no other document, including Licensing, implements its own identity or permission model.
- API Gateway (ADR-EAL-020) remains strictly a translation and enforcement layer — no business logic, not an orchestration engine.
- Multi Tenancy (ADR-EAL-021): Tenant is a platform construct/attribute, never a new identity type.

**Confirmed principle (ADR-EAL-023):** Marketplace reuses existing platform capabilities throughout (PLM registration, Licensing entitlement, Identity & Access identity+attributes). The Workflow Engine remains the *only* orchestration mechanism in the library — no document may introduce a second orchestrator without superseding ADR-EAL-013. Payment processing stays outside the Marketplace boundary entirely.

## Roadmap Rules

- **ROADMAP.md is the only source of sequencing.** No other document, memory of prior conversation, or restated plan determines what's next — this file, read fresh at the time of the decision, is authoritative.
- **Never reference document names in workflow decisions.** "What's next" is derived by scanning this file's tables for the first ⬜/🔶 entry in phase order, not by naming or recalling a specific document ahead of time.
- **Always select the next unfinished roadmap item dynamically.** Re-read this file at each transition point rather than carrying forward a previously stated "next" item.
- **Work sequentially, unless priorities change.** Default order is top-to-bottom within a phase, phases in the order listed (Foundation → Platform → Enterprise → Future).
- **Do not skip items unless dependencies require it.** A skip must be justified by an actual dependency or blocking condition, not convenience, and should be called out explicitly when it happens.
- **Do not add roadmap items without approval.** This roadmap is a closed list until the principal adds to it.
- **New roadmap items require an ADR or explicit approval.** Either a dedicated ADR proposing the addition, or an explicit approval instruction in chat — never inferred or added unilaterally.

*(Supersedes the earlier note that item order "does not imply a mandatory sequence" — sequential order is now the default per these rules.)*

## Notes

- Foundation phase is horizontal/cross-cutting (identity, lifecycle, capability mapping, runtime instances, configuration, flags, dependencies, versioning, errors, observability) and is complete.
- Platform phase is vertical (specific capability domains). AI Platform is the first entry and establishes the working pattern: reuse every applicable Foundation framework, introduce new components only for the residual gap, never redesign a frozen document.
- Each document, regardless of phase, follows the Standard Workflow (Audit → Research → Requirements → Architecture → Design → Review → Wait for Approval → Freeze → Update STATUS.md → Update INDEX.md) and produces the same 18-section Document Standard.
