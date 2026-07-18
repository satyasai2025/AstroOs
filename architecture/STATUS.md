# Enterprise Architecture Library — STATUS

**v1.0 COMPLETE — 34/34 documents frozen across all four phases (2026-07-15).** [COMPLETION_REPORT.md](COMPLETION_REPORT.md) reviewed and approved 2026-07-15.

**GOVERNANCE MODE.** No v2.0 roadmap is active. Changes accepted only via a new ADR, an approved RFC, or a governance decision.

**Architecture Office primary responsibilities (in effect):**
- Architecture reviews
- ADR governance
- AMP reviews
- RFC reviews
- Architecture conformance audits
- Architecture support for implementation

**Architecture Library Validation Audit (2026-07-15): FROZEN.** 7 findings (0 Critical, 0 High, 1 Medium, 4 Low, 2 Informational). One AMP (Architecture Maintenance Proposal) filed per finding in `decisions/` — see [INDEX.md](INDEX.md#decisions-amps--architecture-maintenance-proposals) for the full list. No frozen document has been modified; every AMP awaits its own separate approval.

**Cross-office referral (2026-07-16): AMP-008.** Engineering Office closed ER-002 (investigation of `apps/api/services/ontology_registry.py`'s zero-caller status) without implementing any change, per instruction, and referred the dependency-model decision here instead. AMP-008 asks the Architecture Office to decide (a) whether Module 13 (Rule Engine) should ever consume Module 12 (Ontology) given Module 13's own Facts-only design discipline, and (b) whether Module 24 (AI Engine) should adopt Module 12 as its canonical name source instead of its current hardcoded duplicate. Awaiting approval; see `decisions/AMP-008-ontology-registry-dependency-model.md`. Only once an option is selected should a new Engineering Request be opened to implement it.

**Governance artifact taxonomy:** AMP (Architecture Maintenance Proposal) = correction to an existing defect/inconsistency. AIP (Architecture Improvement Proposal) = new capability or enhancement beyond fixing a defect. (ACP is not used — the principal explicitly deferred/dropped it.)

Tracks the lifecycle of every document in the Enterprise Architecture Library. Updated on every freeze per the Standard Workflow. See [ROADMAP.md](ROADMAP.md) for the full planned scope across all phases (Foundation / Platform / Enterprise / Future).

## Legend

- **Draft** — in Design/Review, not yet approved
- **Approved** — approved by Chief Solutions Architect's principal, pending final freeze
- **Frozen** — approved and frozen; changes require a new ADR superseding the existing one
- **Superseded** — replaced by a later document/ADR

## Completed (Frozen)

| Document | Category | Version | Frozen Date | Path |
|---|---|---|---|---|
| Enterprise Plugin Lifecycle Management | enterprise | 1.1 | 2026-07-15 | [architecture/enterprise/plugin-lifecycle-management.md](enterprise/plugin-lifecycle-management.md) |
| Enterprise Module Registry | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/module-registry.md](enterprise/module-registry.md) |
| Enterprise Capability Registry | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/capability-registry.md](enterprise/capability-registry.md) |
| Enterprise Service Registry | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/service-registry.md](enterprise/service-registry.md) |
| Enterprise Configuration Framework | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/configuration-framework.md](enterprise/configuration-framework.md) |
| Enterprise Feature Flag Framework | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/feature-flag-framework.md](enterprise/feature-flag-framework.md) |
| Enterprise Dependency Management | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/dependency-management.md](enterprise/dependency-management.md) |
| Enterprise Version Compatibility Strategy | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/version-compatibility-strategy.md](enterprise/version-compatibility-strategy.md) |
| Enterprise Error Handling Framework | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/error-handling-framework.md](enterprise/error-handling-framework.md) |
| Enterprise Observability Architecture | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/observability-architecture.md](enterprise/observability-architecture.md) |
| Enterprise AI Platform Architecture | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/ai-platform-architecture.md](enterprise/ai-platform-architecture.md) |
| Enterprise Research Platform | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/research-platform.md](enterprise/research-platform.md) |
| Enterprise Workflow Engine | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/workflow-engine.md](enterprise/workflow-engine.md) |
| Enterprise Event Bus | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/event-bus.md](enterprise/event-bus.md) |
| Enterprise Notification Framework | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/notification-framework.md](enterprise/notification-framework.md) |
| Enterprise Scheduling | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/scheduling.md](enterprise/scheduling.md) |
| Enterprise Security Architecture | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/security-architecture.md](enterprise/security-architecture.md) |
| Enterprise Identity & Access | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/identity-and-access.md](enterprise/identity-and-access.md) |
| Enterprise Audit Framework | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/audit-framework.md](enterprise/audit-framework.md) |
| Enterprise API Gateway | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/api-gateway.md](enterprise/api-gateway.md) |
| Enterprise Multi Tenancy | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/multi-tenancy.md](enterprise/multi-tenancy.md) |
| Enterprise Licensing | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/licensing.md](enterprise/licensing.md) |
| Enterprise Marketplace | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/marketplace.md](enterprise/marketplace.md) |
| Enterprise SDK | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/sdk.md](enterprise/sdk.md) |
| Enterprise Integration Framework | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/integration-framework.md](enterprise/integration-framework.md) |
| Enterprise Deployment | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/deployment.md](enterprise/deployment.md) |
| Enterprise Scalability | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/scalability.md](enterprise/scalability.md) |
| Enterprise High Availability | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/high-availability.md](enterprise/high-availability.md) |
| Enterprise Disaster Recovery | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/disaster-recovery.md](enterprise/disaster-recovery.md) |
| Enterprise Digital Twin | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/digital-twin.md](enterprise/digital-twin.md) |
| Enterprise Semantic Search | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/semantic-search.md](enterprise/semantic-search.md) |
| Enterprise Knowledge Graph | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/knowledge-graph.md](enterprise/knowledge-graph.md) |
| Enterprise Agent Platform | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/agent-platform.md](enterprise/agent-platform.md) |
| Enterprise Autonomous Systems | enterprise | 1.0 | 2026-07-15 | [architecture/enterprise/autonomous-systems.md](enterprise/autonomous-systems.md) |

## Current (In Progress)

_None. All 34 planned documents are frozen. Roadmap complete._

_(PLATFORM phase complete — 10/10. ENTERPRISE phase in progress.)_

## Open Governance Questions

- **Retention vs. deletion (Multi Tenancy, ADR-EAL-021 §16):** Tenant data-deletion requests may conflict with the Audit Framework's mandatory retention floor (ADR-EAL-019). Tracked as a Governance Decision requiring a separate, dedicated ADR filed under the **Audit & Compliance** category — not yet drafted, not resolved informally.

## Canonical Cross-Cutting Rules

- **Request evaluation order (ADR-EAL-022):** Authentication → Authorization → Licensing → Feature Flags → Capability Execution, short-circuiting on failure at any stage.
- **Identity & Access (ADR-EAL-018)** is the sole authoritative source for authentication, authorization, and identity — no other document implements its own identity or permission model.
- **API Gateway (ADR-EAL-020)** remains strictly a translation/enforcement layer — no business logic, not an orchestration engine.
- **Tenant (ADR-EAL-021)** is a platform construct/attribute, never a new identity type.
- **AI (ADR-EAL-011)** is an orchestration layer over deterministic engines, never a replacement for them.
- **Scheduling (ADR-EAL-016)** determines when execution occurs, never how it is performed.
- **Marketplace (ADR-EAL-023)** reuses existing platform capabilities throughout. **Workflow Engine (ADR-EAL-013) is the only orchestration mechanism in the library** — no second orchestrator without superseding that ADR. Payment processing stays outside the Marketplace boundary.
- **SDK (ADR-EAL-024)** is a thin, contract-generated client wrapping the API Gateway only — not a second gateway, not a second auth mechanism (no client-side credential verification), and not a second orchestrator (single-call retry only, per EEHF's hint).
- **Integration Framework (ADR-EAL-025)** generalizes outbound external-system calls (connector registry, circuit breaker) and inbound webhook receipt (via the unchanged API Gateway). Recognizes, but does not migrate or redefine, the Notification Framework's existing Delivery Channel Adapter Layer. Reapplies PLM's circuit-breaker *pattern* (not its component) for outbound-call reliability. Fills the "external payment step" gap Licensing and Marketplace both deferred.
- **Deployment (ADR-EAL-026)** is a classification-gated (via EVCS) build/promote/deploy/rollback pipeline, handing off cleanly to ESR (instance registration) and PLM/Module Registry (activation). Instance-level canary is kept strictly distinct from Feature Flags' traffic-level rollout. Scheduled deployments dispatch to Deployment per Scheduling's unchanged when-not-how principle.
- **Scalability (ADR-EAL-027)** uses Capability Registry/Workflow Engine/Event Bus; consumes Identity & Access/Licensing/Configuration; explicitly does NOT own Identity, Scheduling, Observability, Error Handling, or Deployment. Scale actions execute exclusively as Workflow Engine definitions.
- **High Availability (ADR-EAL-028)** addresses redundancy/failover within normal failure domains only (reused ESR/PLM health signals, Scalability's scale-up, Deployment's `deploy()`). **Disaster Recovery is the sole authority for catastrophic/cross-region recovery** — binding on both documents.
- **Disaster Recovery (ADR-EAL-029)** is deliberately gated (`declareDisaster()`), never automatic, unlike HA's automated failover. Per-store replication/RPO policy; recovery executes as an ordinary Workflow Engine definition — the fifth consecutive confirmation of the sole-orchestrator principle.
- **Digital Twin (ADR-EAL-030)**, first FUTURE-phase item: a one-directional Event Bus subscriber (no write-back to its source entity); simulation is deterministic-only with optional read-only AI narration — the sixth consecutive confirmation of both the AI orchestration-only and sole-orchestrator principles.
- **Semantic Search (ADR-EAL-031)** fulfills the Capability Registry's own flagged future evolution (§18) generally, without modifying ECR. AI generates embeddings only; matching/ranking is deterministic. Full corpus reindex is a Workflow Engine definition; single-item updates are direct calls, not workflows — a deliberate right-sizing of the sole-orchestrator principle.
- **Knowledge Graph (ADR-EAL-032)** is a reference-only typed relationship layer; nodes always reference existing entity IDs. EDM's dependency edges and Semantic Search's similarity results are mirrored read-only, never redefined. AI-backed capabilities may only `suggestRelationship()` into a pending queue — never assert directly into the graph — the eighth extension of the AI orchestration-only principle.
- **Agent Platform (ADR-EAL-033):** an agent is a planner, never an executor. Planning Capability produces a proposed plan only; the Plan-to-Workflow Translator (deterministic) validates and converts it into an ordinary Workflow Engine definition. Every step passes the complete evaluation chain (Authentication → Authorization → Licensing → Feature Flags → Capability Execution) — agents receive no privileged execution path or elevated authority.
- **Autonomous Systems (ADR-EAL-034):** bounded by declared scope, duration, cost, and capabilities plus ordinary platform governance. A composition of existing capabilities only — no bypass of authentication, authorization, licensing, feature flags, workflows, or deterministic execution. Kill-switch reuses EFF's existing mechanism literally. **This freeze completes the roadmap: 34/34.**

_(Determined by scanning ROADMAP.md's tables for the first ⬜/🔶 entry at the time of this update — not carried forward from prior conversation.)_

## Pending (Not Started)

Per ROADMAP.md, the sole authoritative backlog. Sequential order is the default per Roadmap Rules — do not skip without a stated dependency reason.

**ENTERPRISE**: Multi Tenancy · Licensing · Marketplace · SDK · Integration Framework · Deployment · Scalability · High Availability · Disaster Recovery

**FUTURE**: Digital Twin · Semantic Search · Knowledge Graph · Agent Platform · Autonomous Systems

## Notes

- AstroOS v1.0 is treated as an immutable architectural baseline per the active Operating Policy. No document in this library inspects or references the AstroOS repository/source code.
- "Audit" phase for every document in this library means auditing approved baseline documents, business requirements, feature/technology proposals, prior Enterprise Architecture documents, ADRs, and RFCs — never the repository.
- Module Registry and Plugin Registry are permanently separate components (ADR-EAL-002, Accepted). They are not to be merged. The Enterprise Capability Registry (ADR-EAL-003, Accepted) is the mechanism for cross-cutting capability discovery across both, without changing either registry's ownership.
- Every capability has a globally unique, stable Capability ID (`cap.<domain>.<action>`, e.g. `cap.chart.compute`) and its own maturity lifecycle (Proposed → Experimental → Stable → Deprecated → Removed), independent of its current provider's own lifecycle state. See capability-registry.md Appendices A & B.
- The Enterprise Service Registry (ADR-EAL-004, Accepted) is the independent runtime registry for live service instances/health. Canonical consumer lookup chain: **Capability → ECR → Module/Plugin → ESR**. ESR does not perform routing/load-balancing itself and does not alter identity/ownership/lifecycle owned by the other three registries.
- The Enterprise Configuration Framework (ADR-EAL-005, Accepted) governs configuration for modules/plugins/instances. Hierarchy: **Platform Default → Environment → Tenant → Instance**. Secrets are reference/handle-only, never inline. Every config key is explicitly classified **Live Reconfigurable** or **Restart Required** — no unclassified keys.
- The Enterprise Feature Flag Framework (ADR-EAL-006, Accepted) is deliberately separate from ECF: flags own per-request/per-user targeting, sticky rollout percentage, and kill-switch semantics; ECF owns provider/instance-level layered config. Flags have their own lifecycle (Planned → Rolling Out → Fully Rolled Out → Cleanup-Pending → Retired) distinct from the Capability Lifecycle.
- Enterprise Dependency Management (EDM, ADR-EAL-007, Accepted) is a shared, additive dependency-graph capability (construction, cycle detection, version-range validation, impact analysis) supporting cross-provider (module↔plugin) edges. **PLM and the Module Registry are NOT modified or migrated** — their existing internal dependency components remain exactly as frozen. Migration to EDM, if ever pursued, requires its own future ADR against ADR-EAL-001/002.
- Enterprise Version Compatibility Strategy (EVCS, ADR-EAL-008, Accepted) is a **written policy specification only** (semver rules, breaking-change classification, deprecation window standard, compatibility declaration format) — not a runtime component. PLM's Compatibility Checker and EDM's Version-Range Validator are unchanged; future conformance by either is optional and requires its own separate ADR.
- Enterprise Error Handling Framework (EEHF, ADR-EAL-009, Accepted) is a shared error taxonomy + `err.<domain>.<condition>` code namespace + correlation-ID propagation standard, operating at per-call granularity. PLM and ESR may optionally consume its error signals but **retain exclusive ownership** of health/recovery decisions (DEGRADED/QUARANTINED, healthy/unhealthy) — EEHF does not modify either frozen document.
- Enterprise Observability Architecture (EOA, ADR-EAL-010, Accepted) is a Common Event Envelope + Telemetry Pipeline (logs/metrics/traces + unified query) that any of the nine prior emitters may optionally adopt. **EEHF's Correlation ID is the single, library-wide tracing identifier** — no second scheme. No frozen document is modified.
- Enterprise AI Platform Architecture (ADR-EAL-011, Accepted) is the first *vertical* document — reuses all ten Foundation frameworks via an explicit map, adding only Model Gateway/Router, Prompt & Context Template Registry, Safety & Guardrail Layer, and Cost & Usage Meter for the residual gap. **Confirmed foundational principle: AI is an orchestration layer over deterministic engines, never a replacement for them** — applies to all future Platform-phase AI-adjacent work.
- Per ROADMAP.md Roadmap Rules: work proceeds sequentially through the backlog; new roadmap items require an ADR or explicit approval; after each freeze, the next unfinished item is drafted automatically and presented for approval (Wait-for-Approval gate is unchanged — only the "ask what's next" step is removed).
