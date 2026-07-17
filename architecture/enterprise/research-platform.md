---
title: Enterprise Research Platform
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Research Platform

## 1. Problem Statement

The second Platform-phase document, following the pattern established by [Enterprise AI Platform Architecture](ai-platform-architecture.md) (ADR-EAL-011): identify what a research capability genuinely needs beyond the ten Foundation frameworks, and reuse everything else.

A research capability in this platform is fundamentally different from an ordinary deterministic module in one respect: its purpose is to **formulate a hypothesis, run a structured, repeatable statistical study against a defined dataset, and produce a versioned, falsifiable finding** — not to serve a single deterministic calculation on demand. None of the ten Foundation documents, nor the AI Platform Architecture, address:

- **Hypothesis/study definition as a first-class, versioned artifact** — a research question and its methodology need to be recorded precisely enough that the study is reproducible, distinct from a module's interface (Module Registry) or a prompt template (AI Platform §4).
- **Dataset reference and provenance** — a study must declare exactly what data it ran against (scope, time range, source), so a finding can be traced back to the data that produced it — no existing document models "dataset" as an identity.
- **Deterministic statistical execution, kept separate from AI interpretation** — the actual statistical computation (correlation, significance testing, aggregation) must be a deterministic engine, consistent with the orchestration-only principle just confirmed in ADR-EAL-011; AI's role, if any, is limited to narrating or summarizing a finding that a deterministic engine already produced — never computing the statistic itself.
- **A findings lifecycle distinct from a capability's lifecycle** — a research finding progresses from hypothesis to tested to (if validated) published, and only afterward might inform a new or updated deterministic capability (e.g., a validated statistical pattern becoming the basis for a new rule-evaluation capability) — this is a different progression from the Capability Registry's Proposed→Stable maturity lifecycle (Capability Registry, Appendix B), which tracks a capability's *implementation* maturity, not a *research question's* evidentiary status.

The Enterprise Research Platform (ERP) defines these residual, research-specific needs while reusing every applicable Foundation and AI Platform mechanism, exactly as the AI Platform Architecture did relative to the Foundation phase.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Research capability identity & discovery | [Capability Registry](capability-registry.md) (ADR-EAL-003) | A research capability (e.g., a study-execution endpoint) is registered as an ordinary module/plugin and indexed under a `cap.research.*` domain, following the same convention as `cap.ai.*`. |
| Study execution instance tracking | [Service Registry](service-registry.md) (ADR-EAL-004) | A long-running study-execution job's worker instance registers with ESR like any other service instance. |
| Study parameters, dataset scope per environment/tenant | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Study-level parameters (sample window, significance threshold) are ECF configuration keys, layered exactly per ADR-EAL-005. |
| Gradual exposure of a new/updated study methodology | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Rolling out a revised statistical methodology to a subset of study runs before full adoption reuses EFF's rollout/kill-switch mechanism. |
| Study dependencies on datasets/modules | [Dependency Management](dependency-management.md) (ADR-EAL-007) | A study's declared dependency on a dataset reference or an upstream deterministic module is an edge in EDM's shared graph — extending EDM's existing cross-provider model rather than a new graph. |
| What counts as a breaking change to a study's methodology/output contract | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | A methodology revision is classified via EVCS's rules before a new study version is considered comparable to prior runs. |
| Classifying a failed study run (dataset unavailable, execution timeout) | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Maps into EEHF's existing closed taxonomy with new `err.research.*` codes — no new top-level class, exactly as the AI Platform did with `err.ai.*`. |
| Tracing a study execution across dataset access, statistical computation, and (optional) AI narration | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) | Reuses EEHF's correlation ID; no new tracing identifier. |
| AI-assisted narration/summarization of a finding | [AI Platform Architecture](ai-platform-architecture.md) (ADR-EAL-011) | Where a finding is narrated in natural language, that narration is an ordinary AI-backed capability under ADR-EAL-011 — **it summarizes a finding the Statistical Execution Engine already computed deterministically; it never computes the statistic itself**, per that document's confirmed orchestration-only principle. |

**Scope boundary:** this document does not modify any of the eleven prior documents. New components are scoped strictly to hypothesis/study definition, dataset reference, deterministic study execution, and findings lifecycle.

## 2. Goals

| Goal | Description |
|---|---|
| **Versioned, reproducible study definitions** | A hypothesis and its methodology are recorded precisely enough that re-running the same study version against the same dataset scope is reproducible. |
| **Dataset provenance** | Every study declares exactly what data (scope, source, time range) it ran against, and a finding is always traceable back to that declaration. |
| **Deterministic statistical execution** | The actual computation (correlation, significance testing, aggregation) is performed by a deterministic engine, registered like any other module — never by a model. |
| **AI limited to narration, never computation** | Any AI involvement in presenting a finding is strictly summarization/narration of an already-computed deterministic result, consistent with ADR-EAL-011. |
| **A distinct findings lifecycle** | Findings progress Hypothesis → Tested → Published/Refuted independently of any capability's own implementation-maturity lifecycle. |
| **Full reuse of Foundation and AI Platform mechanisms** | No parallel identity, config, flag, dependency, versioning, error, or tracing system is introduced for research specifically. |

**Non-goals**: ERP does not build a general-purpose data science notebook/experimentation IDE; it does not perform the actual statistical computation itself as a "component" separate from an ordinary deterministic module (a Statistical Execution Engine is simply a module, governed by PLM/Module Registry, not a new registry); and it must never let an AI-backed capability substitute a generated statistic for the Statistical Execution Engine's computed result.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Capability Registry (ECR)  │  ← research capabilities registered
   │   cap.research.* domain       │    under cap.research.*
   └─────────────┬─────────────┘
                 │ resolves to
   ┌─────────────▼─────────────┐
   │   Study/Hypothesis Registry  │  ← new: versioned study definitions
   │   (new)                       │    (hypothesis, methodology, params)
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Dataset Reference Layer     │◄──────┤ Dependency Management (EDM)  │
   │   (new)                       │        │ dataset/module dependency    │
   └─────────────┬─────────────┘        │ edges                        │
                 │                       └───────────────────────────┘
   ┌─────────────▼─────────────┐
   │   Statistical Execution        │  ← an ordinary deterministic
   │   Engine (module, per PLM/     │    module — no new registry
   │   Module Registry, unchanged)  │
   └─────────────┬─────────────┘
                 │ produces
   ┌─────────────▼─────────────┐
   │   Findings & Publication       │  ← new: Hypothesis → Tested →
   │   Repository (new)             │    Published/Refuted lifecycle
   └─────────────┬─────────────┘
                 │ optionally narrated by
   ┌─────────────▼─────────────┐
   │   AI-backed narration           │  ← ordinary AI capability per
   │   capability (per ADR-EAL-011)  │    ADR-EAL-011 — summarizes only,
   │                                 │    never computes the statistic
   └───────────────────────────┘
```

## 4. Components

Only the following are genuinely new; the Statistical Execution Engine is explicitly *not* a new registry-level component — it is an ordinary deterministic module:

- **Study/Hypothesis Registry** *(new)* — stores versioned study definitions: the hypothesis statement, methodology (which statistical method, parameters, significance threshold), and a reference to the Statistical Execution Engine module version that will run it. Changes to methodology are classified via EVCS before a new study version is considered comparable to prior runs.
- **Dataset Reference Layer** *(new)* — records what a study's data dependency actually is (scope, source, time range) as a declared identity a study can depend on via EDM's existing dependency graph (extending EDM's model, not replacing it) — enabling impact analysis ("which studies depend on this dataset") using EDM's existing `getDependents()`.
- **Findings & Publication Repository** *(new)* — tracks each study run's result through its own lifecycle (§6): Hypothesis → Tested → Published or Refuted, independent of the Capability Registry's implementation-maturity lifecycle, since a finding's evidentiary status and a capability's implementation readiness are genuinely different questions.
- **Statistical Execution Engine** *(reused pattern, not new)* — an ordinary deterministic module, registered and lifecycle-managed exactly like any other module under PLM/Module Registry; it performs the actual computation. Its determinism is the load-bearing guarantee this entire document is structured to protect.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineStudy(hypothesis, methodology, engineModuleId, datasetRef)` | Researcher/owner → Study/Hypothesis Registry | Declares a new, versioned study definition. |
| `declareDatasetDependency(studyId, datasetRef, versionRange)` | Study owner → Dataset Reference Layer (via EDM) | Records the study's data dependency as an EDM graph edge, enabling impact analysis if the dataset changes. |
| `runStudy(studyId, studyVersion)` | Operator/scheduler → Statistical Execution Engine | Executes the deterministic computation; the engine's own module interface (per PLM/Module Registry) governs how this is actually invoked. |
| `recordFinding(studyId, studyVersion, result, evidenceStrength)` | Statistical Execution Engine → Findings & Publication Repository | Records a study run's deterministic result and advances the finding through its lifecycle (§6). |
| `narrateFinding(findingId)` | Caller → AI-backed narration capability (per ADR-EAL-011) | Optionally produces a natural-language summary of an already-recorded, already-computed finding — never recomputes or overrides the underlying statistic. |

## 6. Findings Lifecycle

Distinct from the Capability Registry's Proposed→Stable maturity lifecycle (Capability Registry, Appendix B) and PLM's plugin activation lifecycle, a research finding progresses through its own evidentiary lifecycle:

```
 HYPOTHESIS
     │
     ▼
  TESTED
     │
     ├──► PUBLISHED
     │
     └──► REFUTED
```

- **HYPOTHESIS** — a study is defined (Study/Hypothesis Registry) but has not yet been executed; the hypothesis and methodology are recorded, no result exists.
- **TESTED** — the Statistical Execution Engine has produced a deterministic result for at least one study run; the finding carries that result and its evidence strength, but has not yet been reviewed for publication.
- **PUBLISHED** — the finding has been reviewed and accepted as a validated result, available for downstream use (e.g., as the evidentiary basis for later proposing a new or updated deterministic capability via the ordinary Module Registry/Capability Registry process — a separate, later decision, not automatic).
- **REFUTED** — the finding did not hold up (failed significance threshold, contradicted by a subsequent run, or invalidated by a dataset correction); retained in the repository for provenance rather than deleted, so the negative result remains discoverable and a hypothesis is not silently re-tested without awareness of prior refutation.

**Governance notes:**

- A finding never moves directly from HYPOTHESIS to PUBLISHED — it must pass through TESTED, i.e., an actual deterministic execution must occur; this is the enforcement point for the "AI never computes the statistic" principle, since only the Statistical Execution Engine's output can advance a finding out of HYPOTHESIS.
- Advancing TESTED → PUBLISHED is a deliberate governance action (a review step), not automatic on execution success, allowing for methodological review before a finding is treated as validated.
- REFUTED is a legitimate, permanent terminal state, not an error — a well-run study that disproves its hypothesis is a valid research outcome and must remain queryable.

## 7. Design Patterns

- **Versioned artifact for hypotheses/methodology** — the same discipline this library applies to every other interface (module, plugin, capability, prompt template) applied here to a study's methodology.
- **Deterministic-computation boundary, enforced structurally** — the Findings & Publication Repository only accepts a `recordFinding()` call from the Statistical Execution Engine (a deterministic module), and the AI narration capability only ever *reads* a finding, never writes one — the orchestration-only principle from ADR-EAL-011 is enforced by which components have write access, not merely by convention.
- **Distinct lifecycle for evidentiary status vs. implementation maturity** — deliberately keeps the Findings Lifecycle (§6) separate from the Capability Registry's maturity lifecycle (Capability Registry, Appendix B), since conflating "is this hypothesis validated" with "is this capability's code stable" would confuse two genuinely different questions, echoing the same reasoning that kept the Feature Flag lifecycle distinct from the Capability Lifecycle (Feature Flag Framework §6).
- **Full reuse over parallel construction** — continuing the discipline established since EDM: dataset dependencies extend EDM's graph rather than inventing a data-lineage system, and study errors extend EEHF's taxonomy via namespaced codes rather than a new class.

## 8. Security Considerations

- **Dataset access governance** — the Dataset Reference Layer must enforce that a study can only declare a dependency on a dataset it is actually authorized to access; this is an access-control concern layered on top of, not replacing, whatever access control already governs the underlying data source.
- **No secrets in study definitions** — consistent with every manifest/schema pattern in this library, a study's methodology and dataset reference are metadata only, never a place for credentials.
- **Finding integrity** — because `recordFinding()` is the sole write path into the Findings Repository and is restricted to the Statistical Execution Engine, unauthorized or fabricated findings are structurally prevented, not merely policy-discouraged.
- **AI narration must not alter the underlying finding** — the narration capability (§4) has read-only access to a finding's recorded result; enforcing this at the interface level (§5, `narrateFinding()` has no write parameter) prevents an AI-generated narrative from ever becoming a substitute source of truth for the statistic itself.

## 9. Scalability

- **Study execution is likely long-running and asynchronous** — unlike most request-path capabilities elsewhere in this library, a statistical study may run for extended periods; `runStudy()` should be treated as an asynchronous operation with the resulting instance tracked in ESR for the duration of execution, not a synchronous request/response call.
- **Dataset reference queries scale with impact-analysis need, not study volume** — `getDependents()` queries against a dataset (via EDM) are comparatively infrequent relative to study executions themselves, mirroring the read/write asymmetry already established elsewhere in this library.
- **Findings Repository is read-heavy for published results, write-light for new findings** — published findings will be queried far more often (by downstream capability-design work, by narration calls) than new findings are recorded, another instance of the now-familiar read/write split (Module Registry §9, Capability Registry §9, ECF §9).

## 10. Best Practices

- Always version a study's methodology explicitly and classify changes via EVCS before treating a re-run as comparable to a prior run — an unversioned methodology change silently invalidates comparability across runs.
- Never grant the AI narration capability write access to the Findings Repository — read-only access is what makes the orchestration-only boundary enforceable rather than aspirational.
- Record REFUTED findings with the same rigor as PUBLISHED ones — a discoverable negative result prevents future re-litigation of an already-tested hypothesis.
- Declare dataset dependencies through EDM from the start, even for a study's first version, so impact analysis is available before it's needed during an incident (e.g., "which studies are affected if this dataset's source changes").

## 11. Common Pitfalls

- **Letting an AI-backed capability "help" by generating a plausible-sounding statistic instead of waiting for the deterministic engine** — the single most important pitfall this document is structured to prevent; the write-access restriction in §7/§8 is the structural safeguard against this occurring even inadvertently.
- **Conflating a finding's evidentiary lifecycle with a capability's implementation-maturity lifecycle** — treating "published finding" as equivalent to "production-ready capability" skips the separate, deliberate decision to actually build a capability based on that finding.
- **Silent methodology drift across study re-runs** — re-running a study with an unversioned tweak to its parameters and treating the result as directly comparable to prior runs, undermining reproducibility.
- **Deleting refuted findings** — losing the negative result risks a future researcher re-testing an already-disproven hypothesis without knowing it was already tried.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Let AI directly compute and report statistics, skipping a deterministic engine** | Have an LLM perform the statistical analysis and report results directly. | Directly violates the confirmed ADR-EAL-011 principle that AI is an orchestration layer over deterministic engines, never a replacement for them; would also make findings non-reproducible and unauditable in the way a deterministic computation is. |
| **No dedicated research platform; ad hoc scripts per study** | Researchers run independent, unversioned scripts with no shared registry or lifecycle. | Fails reproducibility, dataset provenance, and findings-lifecycle goals outright; the status quo this document replaces. |
| **Fold study definitions into the Module Registry** | Treat a study as just another module, with no separate Study/Hypothesis Registry. | A study's versioning concerns (methodology, comparability across runs, evidentiary lifecycle) are different in kind from a module's implementation-versioning concerns (Module Registry §1); forcing them together would conflate "is this code stable" with "is this hypothesis validated," the same distinction problem this document's Findings Lifecycle avoids (§7). |
| **Merge the Findings Lifecycle into the Capability Registry's maturity lifecycle** | Reuse Proposed→Stable directly for findings instead of a separate Hypothesis→Published/Refuted lifecycle. | These lifecycles answer different questions (evidentiary status vs. implementation maturity) and can be out of step with each other (a well-validated finding may never become a capability; a stable capability may not be based on any formal finding at all); collapsing them would lose that distinction. |

## 13. Migration Strategy

1. **Stand up the Study/Hypothesis Registry, Dataset Reference Layer, and Findings & Publication Repository** as new, independently-operable components.
2. **Register the first Statistical Execution Engine as an ordinary module** under the existing, unmodified PLM/Module Registry process — no special-casing.
3. **Declare dataset dependencies via EDM from the first study onward**, rather than retrofitting dependency declarations later.
4. **Introduce AI narration only after the deterministic path is fully operational** — narration is additive and read-only; there is no correctness reason to sequence it earlier.
5. **Establish the review step for TESTED → PUBLISHED** (who approves, what criteria) before the first study reaches TESTED, so publication governance isn't improvised under time pressure.

## 14. Success Criteria

- Every study definition is versioned, with methodology changes classified via EVCS before a re-run is treated as comparable.
- 100% of recorded findings originate from a `recordFinding()` call made by the Statistical Execution Engine — zero findings written by any AI-backed capability.
- Every study's dataset dependency is declared via EDM and queryable via `getDependents()` for impact analysis.
- At least one REFUTED finding is retained and discoverable, demonstrating the negative-result-preservation goal in practice.
- Zero new top-level EEHF error classes introduced; all study-execution failures classify into existing classes with `err.research.*` codes.

## 15. Decision Matrix

| Criterion (weight) | Dedicated research components + deterministic engine, full reuse (recommended) | AI computes statistics directly | Ad hoc scripts, no platform | Fold into Module Registry | Merge findings lifecycle into Capability maturity |
|---|---|---|---|---|---|
| Reproducibility / versioned methodology (High) | 5 | 2 | 1 | 3 | 3 |
| Deterministic computation guarantee (High) | 5 | 1 | 3 | 4 | 4 |
| Respects ADR-EAL-011 orchestration-only principle (High) | 5 | 1 | 4 | 4 | 4 |
| Dataset provenance / impact analysis (Medium) | 5 | 2 | 1 | 2 | 3 |
| Distinct evidentiary lifecycle (Medium) | 5 | 3 | 1 | 2 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 4 | 5 | 3 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails ADR-EAL-011 | Fails core goals | Conflates two concerns | Conflates two concerns |

**Conclusion**: dedicated Study/Hypothesis Registry, Dataset Reference Layer, and Findings Repository, paired with an ordinary deterministic Statistical Execution Engine module and full reuse of the Foundation/AI Platform frameworks, is recommended. It is the only option that upholds the orchestration-only principle while meeting the reproducibility and provenance goals specific to research.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-012: Enterprise Research Platform with Deterministic Execution and AI Limited to Narration**

- **Status**: Accepted
- **Context**: Research capabilities require versioned hypothesis/methodology definitions, dataset provenance, and a distinct evidentiary findings lifecycle, none of which the eleven prior documents address; research is also the first domain where the ADR-EAL-011 orchestration-only principle must be structurally enforced rather than merely stated.
- **Decision**: Introduce a Study/Hypothesis Registry, Dataset Reference Layer, and Findings & Publication Repository, with all actual statistical computation performed by an ordinary deterministic module (Statistical Execution Engine, governed unmodified by PLM/Module Registry). AI involvement is limited to a read-only narration capability under ADR-EAL-011, structurally prevented from writing findings. Dataset dependencies extend EDM's existing graph; study errors extend EEHF's taxonomy via namespaced `err.research.*` codes; no new top-level error class, tracing identifier, or parallel registry is introduced.
- **Rationale**: The Decision Matrix (§15) shows this is the only option that both meets research-specific goals (reproducibility, provenance, evidentiary lifecycle) and structurally — not just procedurally — upholds the confirmed ADR-EAL-011 principle that AI never replaces a deterministic engine.
- **Consequences**:
  - *Positive*: findings are reproducible, auditable, and traceable to their data; the orchestration-only boundary is enforced by write-access design, not convention alone; full reuse keeps the research platform's operational surface consistent with the rest of the library.
  - *Negative*: introduces three new components in addition to the eleven prior documents' worth of infrastructure a research capability must integrate with.
  - *Neutral*: a validated, PUBLISHED finding does not automatically become a new deterministic capability — that remains a separate, deliberate decision via the ordinary Module Registry/Capability Registry process.
- **Alternatives rejected**: AI computing statistics directly, ad hoc scripts, folding into the Module Registry, merging the findings lifecycle into capability maturity — see §12 and §15.
- **Reversibility**: Fully reversible for the new components (Study Registry, Dataset Layer, Findings Repository can be decommissioned without affecting any prior document); the Statistical Execution Engine, being an ordinary module, follows PLM/Module Registry's own reversibility profile.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Study/Hypothesis Registry, Dataset Reference Layer, Findings Repository, and the Findings Lifecycle are specified at architecture level. |
| **Full reuse validation** | Confirmed | §1's reuse map traces every research-specific need to either an existing framework or one of the three genuinely new components. |
| **Enforcement of ADR-EAL-011's orchestration-only principle** | Confirmed structurally | `recordFinding()` is restricted to the Statistical Execution Engine; the AI narration capability has no write path (§7, §8). |
| **Technology-agnostic validation** | Ready | No binding to a specific statistical library, data warehouse, or execution runtime. |
| **Security model maturity** | Ready for design review | Dataset access governance and finding-integrity enforcement are addressed (§8); no formal threat model performed. |
| **Publication governance process** | Needs decision | Who reviews and approves a TESTED → PUBLISHED transition is flagged for implementation planning, not fixed here. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Automated promotion path from PUBLISHED finding to capability proposal** — a future, separately-approved mechanism could formalize (without automating) the step from a validated finding to a proposed new deterministic capability, keeping the decision deliberate per §16's consequences.
- **Cross-study meta-analysis** — combining multiple related PUBLISHED findings into a higher-confidence aggregate result, extending the Findings Repository's model without changing its core lifecycle.
- **Dataset versioning integration with EVCS** — applying EVCS's breaking-change classification to dataset schema changes themselves, not just study methodology, if dataset schemas prove to change in ways that affect study comparability.
- **AI-assisted hypothesis generation (still orchestration-only)** — AI could eventually help *propose* candidate hypotheses for a researcher to formally define in the Study/Hypothesis Registry, provided this remains a suggestion into the HYPOTHESIS stage rather than any path that bypasses deterministic execution before TESTED.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-012.
