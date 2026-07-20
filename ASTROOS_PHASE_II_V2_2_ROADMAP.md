# AstroOS Phase II / v2.2.0 Roadmap

**Version:** v2.2.0 — Phase II  
**Codename:** "Arundhati" (Enterprise-Ready & Scale)  
**Date:** 2026-07-19  
**Status:** PLANNING  
**Predecessor:** v2.1.0 Phase I ("Vistara")  
**Author:** `[rtk:astroos-governance]`

---

## Theme

**From Local-First Baseline to Enterprise-Ready Platform.** Phase I delivered optional K8s/Helm, multi-region design, SDK publication, Celery async, and AI yoga scoring. Phase II operationalizes these: production deployments, container orchestration, cloud-native observability, public SDK distribution, distributed task queues, and calculator-grade AI model integration.

---

## Scope

Phase II picks up where Phase I.5 ends. All enterprise capability must:
- Default to local-first; cloud/offline modes togglable
- Have runbooks, SLIs/SLOs, and rollback procedures
- Be published (K8s Helm chart to OCI, SDKs to PyPI/npm, Docker images to a registry)
- Pass full acceptance (QA) and governance (GOV) gates before release

---

## Out of Scope (for now)

- Kubernetes vendor lock-in (GKE vs EKS vs local kind) — provide portable Helm charts
- Multi-cloud (active-active across providers) — multi-region within one provider first
- Custom mobile apps (React Native / Swift / Kotlin) — SDK-first approach
- SaaS multi-tenant hosting (would require tenant isolation work)
- Plugin marketplace or third-party integrations (webhooks in Phase I were optional, still deferred)

---

## Phase Breakdown

### Phase II.1 — Container Orchestration & Deployment Automation (2-3 weeks)

**Goal:** Make the Helm chart and container images the canonical deployment artifact. Anyone should be able to deploy AstroOS via `helm install` to a cluster, or via `docker compose` locally, with identical behavior.

**Engineering (CEO-ENG):**
- Containerize FastAPI backend with multi-arch builds (amd64, arm64), non-root user, distroless base
- Containerize Next.js frontend with nginx-based prod image
- PostgreSQL container (with initialization scripts for schema migrations)
- Redis container (optional, for async job updates)
- `docker-compose.yml` for single-node dev/staging (all services, health-checked)
- `helm install astroos` with configurable replicas, resources, ingress, TLS, feature flags
- CI pipeline: build image → push to registry → Helm lint → deploy to test namespace → smoke tests

**Architecture (CAO):**
- ADR: Container image publish strategy (registry choice, tag scheme, signing)
- ADR: Helm chart release mechanism (Helm repo vs OCI)
- ADR: Migration strategy for existing local-first users
- Design: Secrets management (env vars → sealed-secrets/external-secrets)

**Quality (QA):**
- Integration tests: deploy to kind/minikube, verify full stack
- Regression: containerized outputs match local-first baseline exactly
- Smoke tests: health endpoints + E2E analysis

**Governance (GOV):**
- Audit CI/CD pipeline (no secrets in logs, image scanning)
- Verify Helm chart defaults to local-first
- Check runbook completeness

---

### Phase II.2 — Cloud-Native Observability & SRE Foundation (2 weeks)

**Goal:** Production-ready monitoring, alerting, and incident response. Same observability stack regardless of deployment.

**Engineering (CEO-ENG):**
- Prometheus metrics (request latency, error rates, job durations)
- Grafana dashboards pre-built (via Helm)
- Alertmanager rules (p95 latency > 5s, Rule Engine OOM, etc.)
- Jaeger/OpenTelemetry tracing (workflow orchestrator, engines, AI services)
- Structured JSON logs with correlation IDs
- SLI/SLO definitions per service

**Architecture (CAO):**
- ADR: Observability stack choice (Prometheus baseline)
- ADR: Log retention policy (local vs centralized)
- ADR: Trace context propagation
- Incident runbook templates

**Benchmark (CBO):**
- Accuracy SLIs for AI models (prediction drift)
- Performance benchmarks at scale (1 vs 1000 births)

**Quality (QA):**
- Chaos engineering: pod restarts, network delays → graceful degradation
- Load testing: concurrent requests, bottleneck identification

---

### Phase II.3 — SDK Public Release & Developer Experience (2 weeks)

**Goal:** Publish SDKs to PyPI and npm, with public docs, versioning, and support policy.

**Engineering (CEO-ENG):**
- Python SDK: PyPI publish, semantic versioning, API stability policy, Jupyter examples
- TypeScript SDK: npm publish, ESM + CommonJS, zero deps, README guides
- Documentation site: `/docs/sdk/*`, auto-generated API refs (Sphinx, TypeDoc)

**Knowledge (CKO):**
- SDK tutorials: Ashtakavarga, yoga detection, knowledge citations
- Verify examples use only public API

**Benchmark (CBO):**
- Benchmark SDK latency vs direct API
- Document performance characteristics

**Quality (QA):**
- Test installs in clean rooms (`pip install --dry-run`, `npm install --dry-run`)
- E2E test: SDK-only script compiles and runs
- API compatibility: SDK matches underlying contracts

---

### Phase II.4 — Distributed Worker Pools & Auto-Scaling (2-3 weeks)

**Goal:** Scale Celery workers for high-volume batch processing. Auto-scale based on queue depth.

**Engineering (CEO-ENG):**
- Celery worker deployments: CPU-heavy, I/O-bound, AI workers (separate pools)
- Redis/RabbitMQ for queues (configurable)
- Horizontal Pod Autoscaler on worker deployments (queue depth metric)
- Celery Flower or alternative for monitoring UI
- Batch job API: submit 1000+ births → single report zip (async, pollable)

**Architecture (CAO):**
- ADR: Worker pool topology (CPU vs I/O vs AI)
- ADR: Message broker choice (Redis vs RabbitMQ)
- ADR: Retry policies, dead-letter queues
- Task priorities: interactive (high) vs bulk (low)

**Research Data (CRDO):**
- Validate batch pipelines: import large datasets, run analysis, export
- Stress test: 1000-birth batch, measure completion time

**Quality (QA):**
- Test worker failure: crash mid-task → task requeues correctly
- Test priority starvation: high-priority not backlogged

---

### Phase II.5 — AI Model Hardening & Calculator Integration (3-4 weeks)

**Goal:** Move AI from experimental to calculator-grade. Yoga scoring, chart comparison, research hypotheses validated against gold standards.

**Engineering (CEO-ENG):**
- LLM-as-Judge for yoga scoring (calibrated against classical texts)
- Model versioning and reproducibility
- Chart comparison: two D1 charts → similarity score + diffs (deterministic, temp=0)
- Research assistant: chart + context → PAI-driven hypotheses (grounded in Knowledge Graph)
- AI fallback: if AI service down → rule-based scoring (graceful degradation)

**Benchmark (CBO):**
- Gold-standard yoga dataset (manually verified)
- AI agreement rate target > 90%
- A/B test: AI scoring vs human domain expert labels

**Knowledge (CKO):**
- Curate yoga definitions from classical texts (BPH, JBP, Saravali, etc.) for training
- Resolve cross-school yoga definition conflicts
- Publish yoga ontology mappings

**Quality (QA):**
- Adversarial testing: edge cases (rare planetary positions) → no hallucinations
- Regression: re-run model on historical charts, ensure output stability

---

### Phase II.6 — Documentation, Developer Tools & Community Readiness (2 weeks)

**Goal:** External developers can install, configure, and contribute without help.

**Engineering (CEO-ENG):**
- Developer onboarding guide ("First Contribution" tutorial, dev-setup script)
- IDE configs: `.vscode/`, `.editorconfig`, pre-commit hooks (black, isort, eslint)
- Changelog + migration guide v2.1→v2.2, deprecation policy

**Knowledge (CKO):**
- Astrology encyclopedia: inline docs for classical terms
- Glossary updates with cross-references

**Benchmark (CBO):**
- Publish performance benchmarks (latency, SLO compliance)

**Governance (GOV):**
- License compliance (MIT/Apache/BSD only, no viral)
- `SECURITY.md`: vulnerability disclosure process

---

### System-Wide Quality Gate (1 week per phase)

After each II.x phase:
- All tests pass (unit, integration, regression)
- Container outputs identical to local-first
- Performance benchmarks meet SLOs
- Security scans pass (Trivy, Bandit)
-Docs: no broken links, code examples verified

---

### Governance Enforcement (1-2 weeks)

Concurrent with II.x phases:
- Local-first compliance (no external services required by default)
- Helm chart security (non-root, read-only root FS)
- SDK API stability policy (breaking changes → major version)
- AI model transparency documented

---

### v2.2.0 Release (1 week)

**Deliverables:**
- Git tag `v2.2.0`
- Helm chart in OCI registry or Helm repo
- Docker images on GHCR/ECR/Quay
- PyPI package `astroos` updated
- npm package `@astroos/sdk` published
- Release notes + migration guide
- Staging/production deployment (if applicable)

---

## Operating Model (unchanged)

| Office | Owns | Does NOT own |
|---|---|---|
| **Engineering (CEO-ENG)** | Backend, frontend, SDKs, API, DB, CI/CD, testing, performance, security, DevOps | Architecture, astrology knowledge, benchmarks, research datasets |
| **Architecture (CAO)** | System architecture, ADRs, RFCs, module boundaries, dependency rules | Implementation |
| **Knowledge (CKO)** | Ontology, classical texts, catalogues, glossary, cross-references, Knowledge Graph | Calculations |
| **Benchmark (CBO)** | Benchmark specs, gold-standard datasets, accuracy metrics, validation methodology | Algorithm implementation |
| **Research Data (CRDO)** | Research datasets, metadata, data standards, import pipelines, dataset quality/versioning | Benchmark rules, software implementation |

---

## Dependencies

Phase II strictly depends on Phase I being complete:
- I.1 (K8s/Helm configs) → II.1 (container orchestration)
- I.2 (multi-region design) → II.2 (observability)
- I.3 (SDK publication) → II.3 (public SDK release)
- I.4 (Celery async) → II.4 (distributed workers)
- I.5 (AI enhancements) → II.5 (AI hardening)

---

## Success Criteria (M2 Definition)

1. **Helm chart deployable** — `helm install astroos` to cluster, services healthy
2. **SDKs published** — `pip install astroos`, `npm install @astroos/sdk` succeed
3. **Observability operational** — Prometheus + Grafana + alerts + traces
4. **Worker pools autoscaling** — HPA scales on queue depth, failure recovery
5. **AI model deterministic & calibrated** — same inputs give identical outputs; accuracy > 90%
6. **Developer onboarding** — <30 minutes to contribute from docs

---

*Last updated: 2026-07-19*