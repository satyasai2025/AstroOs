# AstroOS Phases F, G, H — Architecture Design Summary

**Date:** 2026-07-18  
**Author:** Chief Solutions Architect  
**Status:** Proposed — pending review  

---

## 1. Executive Summary

This document consolidates the architecture decisions for **Phase F (Reporting)**, **Phase G (SDK)**, and **Phase H (Production)** into a single coherent package ready for Atlas to implement after approval.

| Phase | ADR | Status |
|-------|-----|--------|
| F — Reports | `architecture/adr/ADR-REPORT-001-reporting-architecture.md` | Proposed |
| G — SDK | `architecture/adr/ADR-SDK-001-sdk-architecture.md` | Proposed |
| H — Production | `architecture/adr/ADR-PRODUCTION-001-production-architecture.md` | Proposed |

All three ADRs follow the AstroOS workflow: **Audit → Research → Requirements → Architecture → Design → Review**.

---

## 2. Phase Relationships

```
Phase F (Reporting) ─────┐
                         │
Phase G (SDK) ───────────┼──► Phase H (Production)
                         │
Backend API (Phases A-E)─┘
```

- **Phase F** extends the existing backend API with report-generation endpoints (PDF/CSV/JSON).
- **Phase G** consumes the API (including the new reporting endpoints) via typed client SDKs.
- **Phase H** deploys the entire backend + workers + SDKs as a production Kubernetes-native system.

No circular dependencies: H is the deployment target; F and G are independent application-layer enhancements.

---

## 3. Component Architecture

### 3.1 Phase F — Reporting

**Objective:** Professional horoscope reports (9 types) exportable as PDF/JSON/CSV.

**Stack:**
- **Template Engine:** Jinja2 (`apps/api/services/report_template_engine.py` new)
- **PDF Generation:** WeasyPrint (HTML→PDF)
- **Plugin System:** Each report type is a plugin class registered in a registry
- **Export Formats:** JSON canonical, PDF via HTML template, CSV for flat sections

**New Files:**
- `apps/api/services/report_template_engine.py`
- `apps/api/reports/plugins/` (one plugin per report type)
- `templates/reports/` (Jinja2 HTML templates)
- `tests/unit/test_report_template_engine.py`

**Modified Files:**
- `apps/api/routers/report.py` (add PDF/CSV endpoints)
- `apps/api/main.py` (register new routes)

**Interface Contracts:**
- `POST /report/chart/pdf` → Stream PDF
- `POST /report/chart/csv` → Stream CSV

**Dependencies Added:**
- `weasyprint` + system packages (libffi, libpango, libcairo, fontconfig)

**Risk Highlights:**
- WeasyPrint system dependencies in Docker (mitigation: multi-stage Dockerfile with pinned apt packages)
- PDF rendering latency 300-800ms per report (mitigation: async task queue for batch generation)
- Unicode glyphs for Sanskrit terms (mitigation: bundle Noto Sans)

---

### 3.2 Phase G — SDK

**Objective:** Production-ready Python + TypeScript SDKs for external integrators.

**Stack:**
- **Python:** `astroos-sdk` on PyPI, `httpx` (async), `pydantic` models
- **TypeScript:** `@astroos/sdk` on npm, native `fetch` + `AbortController`, `zod` schemas
- **Auth:** API key or JWT; refresh tokens handled transparently
- **Retry:** Exponential backoff with jitter for 429/5xx
- **Error Model:** Typed exceptions with `request_id` propagation

**New Files:**
- `sdks/python/astroos/` (client, models, exceptions, retry)
- `sdks/typescript/astroos/` (client, models, exceptions, retry)
- `docs/sdk/quickstart-python.md`
- `docs/sdk/quickstart-typescript.md`

**Interface Contracts:**
```python
# Python
client = AstroOSClient(base_url="...", api_key="...")
chart = await client.horoscope.create_birth_chart(...)
report = await client.report.generate(chart_id=chart.id, format=ReportFormat.PDF)
```

```typescript
// TypeScript
const client = new AstroOSClient({ baseURL: "...", apiKey: "..." });
const chart = await client.horoscope.createBirthChart(...);
const report = await client.report.generate({ chartId: chart.id, format: "pdf" });
```

**Dependencies Added:**
- Python: `httpx`, `pydantic`, `tenacity` (retry)
- TypeScript: No runtime dependencies beyond Node 18+

**Risk Highlights:**
- SDK drift from API schema (mitigation: contract tests in CI; generate JSON Schema from Pydantic)
- PyPI/npm publish misconfiguration (mitigation: automated CI with dry-run to TestPyPI/npm)

---

### 3.3 Phase H — Production

**Objective:** Deployable, observable, maintainable production system.

**Stack:**
- **Container Runtime:** Docker (multi-stage builds)
- **Orchestration:** Kubernetes (EKS/GKE/AKS)
- **CI/CD:** GitHub Actions or GitLab CI
- **Database:** Managed PostgreSQL (RDS/CloudSQL) + PITR
- **Cache:** Managed Redis (ElastiCache/Memorystore)
- **Object Storage:** S3-compatible (reports, chart images)
- **Secrets:** External Secrets Operator → AWS Secrets Manager / GCP Secret Manager
- **Observability:** Prometheus + Grafana + OpenTelemetry + Loki/ELK
- **Security:** Non-root containers, NetworkPolicies, RBAC, Trivy scanning

**New Files:**
- `Dockerfile` (API, worker)
- `deploy/k8s/base/` (Deployment, Service, HPA, NetworkPolicy)
- `deploy/k8s/overlays/{dev,staging,prod}/` (Kustomize)
- `.github/workflows/ci-cd.yml`
- `monitoring/alertmanager-rules.yml`
- `monitoring/grafana-dashboards/`

**Modified Files:**
- `apps/api/main.py` (add `/health/live`, `/health/ready`, `/metrics`)

**Infrastructure Contracts:**
- All images pinned to digest SHAs in production
- Health checks: liveness (`/health/live`), readiness (`/health/ready`)
- Metrics: `GET /metrics` on port 8001
- Logging: structured JSON to stdout

**Risk Highlights:**
- Kubernetes ops burden (mitigation: managed EKS/GKE; internal GitOps runbooks)
- Observability data volume (mitigation: tiered retention, trace sampling)
- Image supply-chain attacks (mitigation: Sigstore signing, SBOM, Trivy scanning)

---

## 4. Cross-Cutting Concerns

### 4.1 Authentication & Authorization
- **Backend:** JWT (RS256) via `apps/api/security/jwt.py`; RBAC via `dependencies.py`
- **SDK:** Accepts API key or JWT; refresh tokens transparent
- **Production:** Ingress WAF rate-limiting; mTLS optional (service mesh future)

### 4.2 Data Flow
```
Client → SDK (optional) → API Gateway → FastAPI → Engine → PostgreSQL/Redis
                                                  ↓
                                              S3 (PDF/CSV exports)
```

### 4.3 Versioning
- **API:** `v1` (current)
- **SDK:** Tied to `v1`; major version bump for breaking API changes
- **EVCS:** All artifact versions classified before promotion (ADR-EAL-008)

### 4.4 Secrets Management
- **Development:** `.env` (gitignored)
- **Production:** External Secrets Operator → cloud Secrets Manager
- **CI/CD:** Git-crypt or GitHub Environments/secrets

---

## 5. Technology Recommendations

| Layer | Recommendation | Rationale |
|-------|---------------|-----------|
| PDF Rendering | WeasyPrint | HTML-first, CSS support, no browser automation |
| Python HTTP | httpx | Async-first, HTTP/2, well-maintained |
| TypeScript HTTP | fetch + AbortController | Native, zero dependencies |
| Python Models | pydantic | Already in use; JSON Schema generation |
| TypeScript Models | zod | Runtime validation; TypeScript inference |
| Retry (Python) | tenacity | Declarative, well-tested |
| Retry (TypeScript) | Custom exponential backoff | Small surface; native fetch needs AbortController |
| Task Queue | Celery (default), ARQ (future) | Celery mature; ARQ simpler async-native alternative |
| Container Registry | AWS ECR / GCP Artifact Registry | Integrated with secrets; image scanning |
| Kubernetes Distro | EKS / GKE / AKS | Managed control plane; reduced ops burden |
| Observability | OpenTelemetry + Prometheus + Grafana | Vendor-neutral; cloud-agnostic |
| Log Aggregation | Loki or ELK | Loki lighter; ELK more feature-rich |

---

## 6. Implementation Sequencing

```
Week 1: F.1 Template Engine Foundation + G.1 Python SDK Core
Week 2: F.2 PDF Export + G.2 TypeScript SDK Core
Week 3: F.3 Specialized Report Plugins + G.3 Integration Examples
Week 4: F.4 Frontend Integration + H.2 Kubernetes Manifests
Week 5: H.1 Containerization & CI/CD + H.3 Managed Services
Week 6: H.4 Observability Stack + H.5 Hardening
Week 7: H.6 Load Testing & Cutover
```

Parallel tracks:
- **F and G** can proceed concurrently; SDK can consume the new report endpoints as they land.
- **H** depends on F and G being functionally complete but can begin CI/CD pipeline setup immediately.

---

## 7. Risks & Mitigations Summary

| Risk | Phase | Likelihood | Impact | Mitigation |
|------|-------|-----------|--------|-----------|
| WeasyPrint system deps break Docker build | F | Medium | High | Pin apt versions; multi-stage Dockerfile; fail-fast CI |
| SDK drift from API schema | G | Medium | High | Contract tests; generate JSON Schema from Pydantic |
| K8s operational burden | H | Medium | High | Managed K8s; GitOps runbooks; start single-cluster |
| Image supply-chain attack | H | Low | High | Sigstore signing; Trivy scanning; SBOM |
| Secrets sprawl | H | Medium | High | External Secrets Operator; single source of truth |
| PDF rendering timeout | F | Low | Medium | 5s timeout; async task queue for batch |
| Breaking API change forces SDK major | G | Low | Medium | Deprecation headers; 6-month sunset window |

---

## 8. Open Decisions

1. **Multiregion:** Single-region GA; multi-region as Phase I.
2. **Service Mesh:** Not in Phase H; reassess at scale.
3. **GPU Nodes:** Assess based on AI model inference benchmarks.
4. **Batch Jobs vs. Celery:** Use Celery for report generation; K8s Jobs for one-off data imports/benchmarks.
5. **SDK Streaming:** Defer to Phase I; current use cases fit request/response.

---

## 9. Approval Checklist

- [ ] **Phase F (Reporting):** Engineering CAO, UX review of templates
- [ ] **Phase G (SDK):** Engineering CAO, Security review of auth
- [ ] **Phase H (Production):** Engineering CAO, SRE/Ops, Security, Finance
- [ ] **Joint sign-off:** All three phases approved as a coherent program

---

## 10. Next Steps for Atlas

1. Implement Phase F.1: Template Engine Foundation (Week 1)
2. Implement Phase G.1: Python SDK Core (Week 1)
3. Begin Phase H.1: Containerization & CI/CD setup (Week 1)
4. Follow weekly implementation plans in each ADR
5. Surface blockers via AstroOS governance channels

---

*End of Design Summary*