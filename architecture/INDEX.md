# Enterprise Architecture Library — Index

**v1.0 COMPLETE — 34/34 documents frozen across all four phases (2026-07-15).** See [COMPLETION_REPORT.md](COMPLETION_REPORT.md) for the full summary.

Master table of contents for all architecture artifacts. See [STATUS.md](STATUS.md) for lifecycle tracking of each document and [ROADMAP.md](ROADMAP.md) for the full planned scope (Foundation / Platform / Enterprise / Future phases).

## Structure

```
architecture/
├── ROADMAP.md          Full planned scope across all phases
├── STATUS.md            Lifecycle tracker (completed / current / pending)
├── INDEX.md             This file — master table of contents
├── handbook/            Technology handbook reference documents
├── enterprise/           Enterprise Architecture Library documents (this track)
├── adr/                  Architecture Decision Records
├── rfc/                  Request for Comments documents
├── decisions/            Standalone decision records outside the ADR format
├── future/               Future evolution / roadmap notes
└── research/             Research and technology evaluation notes
```

## Enterprise Architecture Library

| # | Document | Status | Path |
|---|---|---|---|
| 1 | Enterprise Plugin Lifecycle Management | Frozen | [enterprise/plugin-lifecycle-management.md](enterprise/plugin-lifecycle-management.md) |
| 2 | Enterprise Module Registry | Frozen | [enterprise/module-registry.md](enterprise/module-registry.md) |
| 3 | Enterprise Capability Registry | Frozen | [enterprise/capability-registry.md](enterprise/capability-registry.md) |
| 4 | Enterprise Service Registry | Frozen | [enterprise/service-registry.md](enterprise/service-registry.md) |
| 5 | Enterprise Configuration Framework | Frozen | [enterprise/configuration-framework.md](enterprise/configuration-framework.md) |
| 6 | Enterprise Feature Flag Framework | Frozen | [enterprise/feature-flag-framework.md](enterprise/feature-flag-framework.md) |
| 7 | Enterprise Dependency Management | Frozen | [enterprise/dependency-management.md](enterprise/dependency-management.md) |
| 8 | Enterprise Version Compatibility Strategy | Frozen | [enterprise/version-compatibility-strategy.md](enterprise/version-compatibility-strategy.md) |
| 9 | Enterprise Error Handling Framework | Frozen | [enterprise/error-handling-framework.md](enterprise/error-handling-framework.md) |
| 10 | Enterprise Observability Architecture | Frozen | [enterprise/observability-architecture.md](enterprise/observability-architecture.md) |
| 11 | Enterprise AI Platform Architecture | Frozen | [enterprise/ai-platform-architecture.md](enterprise/ai-platform-architecture.md) |
| 12 | Enterprise Research Platform | Frozen | [enterprise/research-platform.md](enterprise/research-platform.md) |
| 13 | Enterprise Workflow Engine | Frozen | [enterprise/workflow-engine.md](enterprise/workflow-engine.md) |
| 14 | Enterprise Event Bus | Frozen | [enterprise/event-bus.md](enterprise/event-bus.md) |
| 15 | Enterprise Notification Framework | Frozen | [enterprise/notification-framework.md](enterprise/notification-framework.md) |
| 16 | Enterprise Scheduling | Frozen | [enterprise/scheduling.md](enterprise/scheduling.md) |
| 17 | Enterprise Security Architecture | Frozen | [enterprise/security-architecture.md](enterprise/security-architecture.md) |
| 18 | Enterprise Identity & Access | Frozen | [enterprise/identity-and-access.md](enterprise/identity-and-access.md) |
| 19 | Enterprise Audit Framework | Frozen | [enterprise/audit-framework.md](enterprise/audit-framework.md) |
| 20 | Enterprise API Gateway | Frozen | [enterprise/api-gateway.md](enterprise/api-gateway.md) |
| 21 | Enterprise Multi Tenancy | Frozen | [enterprise/multi-tenancy.md](enterprise/multi-tenancy.md) |
| 22 | Enterprise Licensing | Frozen | [enterprise/licensing.md](enterprise/licensing.md) |
| 23 | Enterprise Marketplace | Frozen | [enterprise/marketplace.md](enterprise/marketplace.md) |
| 24 | Enterprise SDK | Frozen | [enterprise/sdk.md](enterprise/sdk.md) |
| 25 | Enterprise Integration Framework | Frozen | [enterprise/integration-framework.md](enterprise/integration-framework.md) |
| 26 | Enterprise Deployment | Frozen | [enterprise/deployment.md](enterprise/deployment.md) |
| 27 | Enterprise Scalability | Frozen | [enterprise/scalability.md](enterprise/scalability.md) |
| 28 | Enterprise High Availability | Frozen | [enterprise/high-availability.md](enterprise/high-availability.md) |
| 29 | Enterprise Disaster Recovery | Frozen | [enterprise/disaster-recovery.md](enterprise/disaster-recovery.md) |
| 30 | Enterprise Digital Twin | Frozen | [enterprise/digital-twin.md](enterprise/digital-twin.md) |
| 31 | Enterprise Semantic Search | Frozen | [enterprise/semantic-search.md](enterprise/semantic-search.md) |
| 32 | Enterprise Knowledge Graph | Frozen | [enterprise/knowledge-graph.md](enterprise/knowledge-graph.md) |
| 33 | Enterprise Agent Platform | Frozen | [enterprise/agent-platform.md](enterprise/agent-platform.md) |
| 34 | Enterprise Autonomous Systems | Frozen | [enterprise/autonomous-systems.md](enterprise/autonomous-systems.md) |

## ADRs

| ID | Title | Status | Source Document |
|---|---|---|---|
| ADR-EAL-001 | Centralized Plugin Lifecycle Controller with Declarative Manifests | Accepted | [enterprise/plugin-lifecycle-management.md](enterprise/plugin-lifecycle-management.md) |
| ADR-EAL-002 | Centralized Module Registry, Distinct from the Plugin Registry | Accepted | [enterprise/module-registry.md](enterprise/module-registry.md) |
| ADR-EAL-003 | Enterprise Capability Registry as a Read-Only, Event-Synchronized Mapping Layer | Accepted | [enterprise/capability-registry.md](enterprise/capability-registry.md) |
| ADR-EAL-004 | Dedicated Enterprise Service Registry, Layered Under the Design-Time Registries | Accepted | [enterprise/service-registry.md](enterprise/service-registry.md) |
| ADR-EAL-005 | Layered Enterprise Configuration Framework with Schema-First Validation and Secrets-by-Reference | Accepted | [enterprise/configuration-framework.md](enterprise/configuration-framework.md) |
| ADR-EAL-006 | Enterprise Feature Flag Framework as a Dedicated Component Beside the Configuration Framework | Accepted | [enterprise/feature-flag-framework.md](enterprise/feature-flag-framework.md) |
| ADR-EAL-007 | Shared Enterprise Dependency Management Capability, Adopted Additively | Accepted | [enterprise/dependency-management.md](enterprise/dependency-management.md) |
| ADR-EAL-008 | Enterprise Version Compatibility Strategy as a Written Policy Specification, Adopted Voluntarily | Accepted | [enterprise/version-compatibility-strategy.md](enterprise/version-compatibility-strategy.md) |
| ADR-EAL-009 | Enterprise Error Handling Framework as a Shared, Non-Invasive Error Contract | Accepted | [enterprise/error-handling-framework.md](enterprise/error-handling-framework.md) |
| ADR-EAL-010 | Enterprise Observability Architecture as a Common Envelope and Additive Telemetry Pipeline | Accepted | [enterprise/observability-architecture.md](enterprise/observability-architecture.md) |
| ADR-EAL-011 | Enterprise AI Platform Architecture as a Thin Vertical Layer Over the Existing Horizontal Library | Accepted | [enterprise/ai-platform-architecture.md](enterprise/ai-platform-architecture.md) |
| ADR-EAL-012 | Enterprise Research Platform with Deterministic Execution and AI Limited to Narration | Accepted | [enterprise/research-platform.md](enterprise/research-platform.md) |
| ADR-EAL-013 | Enterprise Workflow Engine as an Orchestration Layer with Durable State and Saga-Style Compensation | Accepted | [enterprise/workflow-engine.md](enterprise/workflow-engine.md) |
| ADR-EAL-014 | Enterprise Event Bus as a Decoupled Pub/Sub Layer, Distinct from Observability and Workflow Orchestration | Accepted | [enterprise/event-bus.md](enterprise/event-bus.md) |
| ADR-EAL-015 | Enterprise Notification Framework as an Event-Bus-Subscribing, Preference-Gated Delivery Layer | Accepted | [enterprise/notification-framework.md](enterprise/notification-framework.md) |
| ADR-EAL-016 | Enterprise Scheduling as a Durable Timer with Dispatch-Only Routing | Accepted | [enterprise/scheduling.md](enterprise/scheduling.md) |
| ADR-EAL-017 | Enterprise Security Architecture as a Consolidated Reference Catalog, Not a Runtime Component | Accepted | [enterprise/security-architecture.md](enterprise/security-architecture.md) |
| ADR-EAL-018 | Enterprise Identity & Access as a Shared Authentication/Authorization Substrate Completing Existing Enforcement Points | Accepted | [enterprise/identity-and-access.md](enterprise/identity-and-access.md) |
| ADR-EAL-019 | Enterprise Audit Framework as a Mandatory, Tamper-Evident Subset Layered on Observability's Existing Ingestion | Accepted | [enterprise/audit-framework.md](enterprise/audit-framework.md) |
| ADR-EAL-020 | Enterprise API Gateway as a Single External Ingress Point, Translating Into Existing Internal Mechanisms | Accepted | [enterprise/api-gateway.md](enterprise/api-gateway.md) |
| ADR-EAL-021 | Enterprise Multi Tenancy as a Registry, Identity Attribute, and Capability Classification — with Retention-vs-Deletion Explicitly Unresolved | Accepted | [enterprise/multi-tenancy.md](enterprise/multi-tenancy.md) |
| ADR-EAL-022 | Enterprise Licensing as an Independent Entitlement Layer, with Confirmed Request Evaluation Order | Accepted | [enterprise/licensing.md](enterprise/licensing.md) |
| ADR-EAL-023 | Enterprise Marketplace as a Listing/Publisher Layer with Workflow-Engine-Based Fulfillment | Accepted | [enterprise/marketplace.md](enterprise/marketplace.md) |
| ADR-EAL-024 | Enterprise SDK as a Thin, Contract-Generated Client — No Second Gateway, Auth Mechanism, or Orchestrator | Accepted | [enterprise/sdk.md](enterprise/sdk.md) |
| ADR-EAL-025 | Enterprise Integration Framework as a General Outbound-Connector Pattern, With Webhooks Received Through the Unchanged API Gateway | Accepted | [enterprise/integration-framework.md](enterprise/integration-framework.md) |
| ADR-EAL-026 | Enterprise Deployment as a Classification-Gated Build/Promote/Deploy/Rollback Pipeline | Accepted | [enterprise/deployment.md](enterprise/deployment.md) |
| ADR-EAL-027 | Enterprise Scalability as a Policy/Decision Layer With an Explicit Five-Domain Non-Ownership Boundary | Accepted | [enterprise/scalability.md](enterprise/scalability.md) |
| ADR-EAL-028 | Enterprise High Availability as Reused-Signal Failover, Explicitly Scoped Narrower Than Disaster Recovery | Accepted | [enterprise/high-availability.md](enterprise/high-availability.md) |
| ADR-EAL-029 | Enterprise Disaster Recovery as a Deliberately-Gated, Workflow-Engine-Orchestrated Recovery Authority | Accepted | [enterprise/disaster-recovery.md](enterprise/disaster-recovery.md) |
| ADR-EAL-030 | Enterprise Digital Twin as a One-Directional, Event-Bus-Synchronized Mirror with Deterministic Simulation | Accepted | [enterprise/digital-twin.md](enterprise/digital-twin.md) |
| ADR-EAL-031 | Enterprise Semantic Search as AI-Generated Embeddings with Deterministic Matching | Accepted | [enterprise/semantic-search.md](enterprise/semantic-search.md) |
| ADR-EAL-032 | Enterprise Knowledge Graph as a Reference-Only Relationship Layer, AI-Suggests/Human-Confirms | Accepted | [enterprise/knowledge-graph.md](enterprise/knowledge-graph.md) |
| ADR-EAL-033 | Enterprise Agent Platform as Propose-Translate-Execute, With No Gate Exemptions | Accepted | [enterprise/agent-platform.md](enterprise/agent-platform.md) |
| ADR-EAL-034 | Enterprise Autonomous Systems as a Bounded Triggering Layer Over Agent Platform, Reusing Scheduling and Feature Flags | Accepted | [enterprise/autonomous-systems.md](enterprise/autonomous-systems.md) |

## Decisions (AMPs — Architecture Maintenance Proposals)

Two governance artifact types are used in this library:
- **AMP — Architecture Maintenance Proposal**: proposes a correction to an existing defect/inconsistency (e.g., an audit finding). Filed in this section.
- **AIP — Architecture Improvement Proposal**: proposes a new capability or enhancement beyond fixing a defect. None filed yet.

AMPs 001–007 below were filed from the Architecture Library Validation Audit (2026-07-15, frozen). AMP-008 has a different origin — a cross-office referral from the Engineering Office (ER-002) concerning runtime module dependency structure, not the Enterprise Architecture Library itself; it is filed in the same section because it is the same artifact type (a correction/decision proposal, not a new-capability proposal). Each proposes a correction or decision only; none has been applied — every one requires its own governance approval before any document or code is touched.

| ID | Title | Severity | Status | Path |
|---|---|---|---|---|
| AMP-001 | Disaster Recovery presumes Multi Tenancy's "tenant tier" before it exists | Medium | Proposed | [decisions/AMP-001-disaster-recovery-tenant-tier-forward-reference.md](decisions/AMP-001-disaster-recovery-tenant-tier-forward-reference.md) |
| AMP-002 | Stale contradictory note in STATUS.md | Low | Proposed | [decisions/AMP-002-status-stale-note.md](decisions/AMP-002-status-stale-note.md) |
| AMP-003 | Disaster Recovery internal ordinal inconsistency ("fourth" vs "fifth") | Low | Proposed | [decisions/AMP-003-disaster-recovery-ordinal-inconsistency.md](decisions/AMP-003-disaster-recovery-ordinal-inconsistency.md) |
| AMP-004 | Semantic Search / Knowledge Graph ordinal drift ("seventh"/"eighth") | Low | Proposed | [decisions/AMP-004-semantic-search-ordinal-drift.md](decisions/AMP-004-semantic-search-ordinal-drift.md) |
| AMP-005 | Digital Twin cardinal/ordinal phrasing inconsistency | Low/Informational | Proposed | [decisions/AMP-005-digital-twin-phrasing-inconsistency.md](decisions/AMP-005-digital-twin-phrasing-inconsistency.md) |
| AMP-006 | "Category: enterprise" field does not distinguish roadmap phases | Low | Proposed | [decisions/AMP-006-category-field-phase-ambiguity.md](decisions/AMP-006-category-field-phase-ambiguity.md) |
| AMP-007 | Completion Report undercounts distinct audit-catalog proposals | Informational | Proposed | [decisions/AMP-007-completion-report-proposal-count.md](decisions/AMP-007-completion-report-proposal-count.md) |
| AMP-008 | Ontology Registry (Module 12) has no approved dependency model — contradicts its own docstring, duplicated by AI Engine | Medium | Proposed | [decisions/AMP-008-ontology-registry-dependency-model.md](decisions/AMP-008-ontology-registry-dependency-model.md) |

## RFCs

_None yet._

## Handbook

_Referenced as completed in prior work (Phase 0.5 — 14 documents) but not present in this repository; not indexed here until provided._

## Research

_None yet._

## Future / Roadmap Notes

_None yet — see individual documents' "Future Evolution" sections until a dedicated roadmap artifact is created._
