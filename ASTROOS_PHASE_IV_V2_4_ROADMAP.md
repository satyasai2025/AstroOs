# AstroOS Phase IV / v2.4.0 Roadmap

**Version:** v2.4.0 — Phase IV  
**Codename:** "Ganesha" (Removing Obstacles — SaaS, AI, Scale)  
**Date:** 2026-07-19  
**Status:** PLANNING  
**Predecessor:** v2.3.0 Phase III ("Lakshmi") complete  
**Author:** `[rtk:astroos-governance]`

---

## Theme

**From Multi-Channel Ecosystem to Cloud-Native SaaS Platform.** Phase IV delivers AstroOS as a turnkey SaaS offering (self-hosted or managed). Multi-tenant architecture, transformer-level AI models, GPU-accelerated batch processing, and third-party partnerships make AstroOS the profession-grade tool astrology research organizations worldwide depend on.

---

## Operating Model (unchanged)

| Office | Owns | Does NOT own |
|---|---|---|
| **Engineering (CEO-ENG)** | Backend, frontend, mobile, SaaS platform, multi-tenancy, GPU infrastructure, CI/CD, testing, performance, security, DevOps | Architecture decisions, astrology knowledge, benchmarks, research datasets |
| **Architecture (CAO)** | System architecture, ADRs, RFCs, module boundaries, dependency rules, SaaS design patterns | Implementation |
| **Knowledge (CKO)** | Ontology, classical texts, catalogues, glossary, cross-references, conflicts, Knowledge Graph, model training data curation | Calculations |
| **Benchmark (CBO)** | Benchmark specs, gold-standard datasets, accuracy metrics, validation methodology, LLM eval, GPU benchmark profiles | Algorithm implementation |
| **Research Data (CRDO)** | Research datasets, metadata, data standards, import pipelines, dataset quality/versioning, multi-tenant data partitioning | Benchmark rules, software implementation |

---

## Phase Breakdown

### Phase IV.1 — Multi-Tenant SaaS Architecture (3-4 weeks)

**Goal:** AstroOS as a cloud service. Multiple organizations (tenants) on a single deployment, each isolated with their own data, users, configurations.

**Engineering (CEO-ENG):**
- Database multi-tenancy (row-level security, tenant isolation queries)
- Tenant provisioning API (self-serve signup, org creation, admin assignment)
- Subscription management (per-tenant billing, feature flags per plan: Free/Pro/Enterprise)
- Authentication: OAuth (Google, GitHub) + SAML for enterprise SSO
- Static analysis and integration into FastAPI (tenant context middleware)
- Per-tenant metrics/quota enforcement (storage, compute, API calls)

**Architecture (CAO):**
- ADR: Multi-tenancy model (shared DB with RLS vs separate schemas vs separate DBs)
- ADR: Tenant isolation boundaries (more than just data — also compute queues)
- ADR: Billing and payment integration (Stripe Connect for marketplace if retained)
- Design: Data retention policies per tenant (GDPR right to erasure)

**Governance (GOV):**
- SaaS terms of service, privacy policy
- SOC 2 compliance (if targeting enterprise)
- Data residency per tenant (EU data stays in EU, etc.)

**Quality (QA):**
- Tenant isolation test: Tenant A cannot access Tenant B's data (even with crafted queries)
- Tenant provisioning: automated signup → chart creation → data stored correctly

---

### Phase IV.2 — GPU Acceleration & Batch Processing (3 weeks)

**Goal:** Massively parallel chart computation. Use GPU for yoga detection, transit calculations, and batch operations serving research institutions.

**Engineering (CEO-ENG):**
- CUDA kernel for ephemeris lookups (Planet positions computed on GPU)
- CUDA kernel for yoga detection (vectorized planetary position checks)
- CUDA kernel for transit checks (parallel transit computations)
- Batch API: submit 10,000-birth payload, job processed on GPU cluster
- Result streaming (progressive results as computations complete)
- Fallback: graceful CPU execution if GPU unavailable

**Benchmark (CBO):**
- GPU vs CPU latency: measure at 1/100/10,000 birth scales
- GPU accuracy: verify GPU outputs match CPU outputs exactly (bit-exact)

**Architecture (CAO):**
- ADR: GPU resource allocation per tenant (Shared vs dedicated)
- ADR: Cost modeling for GPU compute (billing tenant for GPU minutes)

**Quality (QA):**
- Bit-exactness: GPU computation results must be bit-identical to CPU for same inputs
- Failure recovery: GPU node failure → job requeues to another node

---

### Phase IV.3 — LLM-Powered Research Copilot (4 weeks)

**Goal:** Advanced AI assistant that can reason over large astrological datasets, generate research hypotheses, write analysis reports, and answer natural-language questions.

**Engineering (CEO-ENG):**
- Fine-tuned transformer model for astrology (causal LM trained on astrological texts)
- RAG pipeline: query → retrieve relevant Knowledge Graph entries → generate answer
- Research assistant agent (multi-step: propose → gather → analyze → conclude)
- Multi-chart comparison: natural language query "What do charts X and Y share?"
- Report writer: generate full PDF report from natural language query

**Benchmark (CBO):**
- Model benchmarks: accuracy on yoga detection, chart comparison, factual knowledge
- Hallucination rate: measure against gold-standard datasets (target < 5%)
- Comparison to human domain experts: does better than random, closer to expert than一般人?

**Knowledge (CKO):**
- Fine-tuning dataset: classical texts, modern astrological journals, expert annotations
- RAG corpus: curated Knowledge Graph with embeddings for semantic search

**Governance (GOV):**
- AI transparency: document training data sources, model limitations, potential biases
- AI review process: human-in-the-loop for research outputs before submission

---

### Phase IV.4 — Partner Integrations & Ecosystem (2 weeks)

**Goal:** Connect AstroOS to the wider astrological software ecosystem. Consolidate data, enable migration, and extend reach.

**Engineering (CEO-ENG):**
- Data import from other platforms (Solar Fire, Janus, Morinus, Parashari)
- Chart export formats (Jigsaw, ZET, Swiss Ephemeris `.se1`)
- iCalendar integration: send Dasha events to Google Calendar / Apple Calendar
- Webhook triggers on transits / Dasha events
- Astrological data APIs (Ptolemy, Astro.com, NASA JPL ephemeris integration)

**Architecture (CAO):**
- ADR: Third-party API licensing (frictionless use vs attribution compliance)
- ADR: Forgetting/right to delete (EU user wants to delete from partner integrations too)

**Quality (QA):**
- Import round-trip: export from tool X → import to AstroOS → export from AstroOS → diff must match (within floating-point tolerance)

---

### Phase IV.5 — Advanced Subscription & Marketplace (2 weeks)

**Goal:** Monetization layer. Paid tiers for individual and organizational users. Marketplace for researchers to publish/relicense their datasets.

**Engineering (CEO-ENG):**
- Plan tiers: Free (limited), Pro (full), Enterprise (SSO, support, custom integrations)
- Usage-based pricing API (per chart computation, per batch job, per GPU hour)
- Researcher marketplace: publish a dataset, commission per download
- Revenue-sharing with Knowledge contributors (classical texts, annotations)

**Governance (GOV):**
- Compliance: VAT handling, refund policy, platform liability
- Terms of service per product category (software, data, services)

---

### Phase IV.6 — Cloud Infrastructure & Deployment Automation (2-3 weeks)

**Goal:** One-command deployment of a full AstroOS cloud instance. Managed Kubernetes or serverless.

**Engineering (CEO-ENG):**
- AWS/GCP/Azure Terraform modules (infrastructure as code)
- Managed Kubernetes (EKS/GKE) with Pulumi for per-tenant upgrades
-managed PostgreSQL + Redis (AWS RDS/ElastiCache or K8s-deployed)
-managed monitoring (Grafana Cloud, DataDog, or self-hosted)
- Backup and disaster recovery (point-in-time restore, cross-region replication)

**Architecture (CAO):**
- ADR: Cloud deployment strategy (managed vs self-hosted)
- ADR: Disaster recovery RTO/RPO (RTO < 1 hour, RPO < 5 minutes)

---

## Success Criteria (M4 Definition)

1. **SaaS live** — Registered tenants (10+ orgs), multi-tenant isolation verified
2. **GPU acceleration** — 10,000-birth batch in <5 minutes (vs 30+ min CPU)
3. **LLM accuracy** — Research Copilot passes domain expert benchmark (>80% agreement)
4. **Integrations** — Import/export round-trip with 3+ external platforms verified
5. **Revenue** — 10+ paying customers (Pro or Enterprise), first month revenue >$1000
6. **Infrastructure** — Terraform IaC, managed K8s, DR tested with simulated failure

---

## Out of Scope (for now)

- AI for temple/sect prediction (requires ethics review)
- Automatic chart interpretation for counseling applications (requires clinical validation)
- Web assembly client-side compute (willing to wait for browser standards to mature)
- AR/VR visualization (emerging tech, too early)

---

*Last updated: 2026-07-19*