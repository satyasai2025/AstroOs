# AstroOS v2.0 Release Engineering Roadmap

**Date:** 2026-07-19  
**Author:** Chief Solutions Architect (Release Engineering)  
**Status:** Proposed — GA-Critical Path

---

## Current State

✅ All 8 phases (A–H) are FROZEN  
✅ Milestone M1 is COMPLETE (all 10 criteria achieved)  
✅ **Architecture:** Local-First (Next.js → FastAPI → PostgreSQL → Swiss Ephemeris)  
🎯 **Target:** v2.0.0 General Availability release

> **Local-First Principle:** AstroOS runs entirely on a single local machine. No cloud deployment, Kubernetes cluster, or external services are required for GA. Production deployment patterns are optional enhancements for users who wish to deploy AstroOS as a service.

---

## GA-Critical Release Blockers

| Blocker | Requirement | Status |
|---------|-------------|--------|
| **RB-1** | SDK publication (PyPI + npm) | ❌ Not done |
| **RB-2** | Local installation validated | ❌ Not done |
| **RB-3** | All tests passing against local PostgreSQL | ❌ Not done |
| **RB-4** | Version consistency across all manifests | ❌ Not done |

---

## Non-GA (Post-Release) Items

- Missing report templates (Dasha.html, Research.html) - 7 of 9 exist
- Geocoding provider evaluation (dev OK with Nominatim)
- Report export UI buttons - backend endpoints exist
- Additional SDK documentation
- Optional: Kubernetes deployment manifests
- Optional: Helm charts for enterprise deployment

---

## GA-Focused Milestones

### M2 — Release Candidate Preparation (Week 1-2)
**Goal:** Package and validate release candidate for local-first deployment

| Exit Criteria | Work Required | Status |
|---------------|---------------|--------|
| `astroos-sdk` installable via pip | Publish to PyPI | ❌ |
| `@astroos/sdk` installable via npm | Publish to npm | ❌ |
| Local installation tested | Verify setup on clean machine | ❌ |
| All code tagged and verified | Repository ready | ❌ |

### M3 — Local Validation RC (Week 2-3)
**Goal:** Validate RC runs correctly on local machine

| Exit Criteria | Work Required | Status |
|---------------|---------------|--------|
| Local PostgreSQL setup verified | Test on clean install | ❌ |
| `/metrics` endpoint verified | Prometheus scraping locally | ❌ |
| Health checks verified | `/health/live`, `/health/ready` locally | ❌ |
| Test suite passes | Full pytest run | ❌ |

### M4 — v2.0.0 Release Candidate (Week 3)
**Goal:** RC ready for GA validation

| Exit Criteria | Work Required | Status |
|---------------|---------------|--------|
| All blockers resolved | M2 + M3 complete | ❌ |
| RC tag `v2.0.0-rc.1` cut | Repository Owner action | ❌ |

---

## Execution Sequence (Optimized)

```
Week 1: SDK Publication
  ├─ Register PyPI package
  ├─ Publish Test release
  └─ Publish public release

Week 2: Local Validation
  ├─ Test local installation on clean machine
  ├─ Verify health endpoints locally
  ├─ Run full test suite
  └─ Validate Docker image builds

Week 3: RC Validation
  ├─ Run Trivy scan
  ├─ Verify observability stack
  ├─ Tag v2.0.0-rc.1
  └─ GA Go/No-Go decision

> Note: Production deployment (Kubernetes, cloud) is optional and not required for GA.
```

---

## Dependencies (Critical Path)

| Dependency | Owner | Acquisition Needed |
|------------|-------|-------------------|
| PyPI credentials | Release Team | Before Week 1 |
| npm credentials | Release Team | Before Week 1 |
| Test machine (local) | Release Team | Before Week 2 |
| Trivy binary | Release Team | Before Week 3 |

> **Note:** Cloud account (AWS/GCP) and Domain/SSL certs are **optional** — only needed for users deploying AstroOS as a service, not for GA of the local-first platform.

---

## Exit Criteria Summary

**M2 Exit:** SDKs installable, code tagged  
**M3 Exit:** Local installation validated, observability verified, security scan clean  
**M4 Exit (RC):** All above + Go/No-Go for GA  

**GA Exit (M5):** RC approved, `v2.0.0` tag cut, CHANGELOG updated

---

## Project Timeline

| Stage | Duration | Buffer | Total |
|-------|----------|--------|-------|
| SDK Publication | 1 week | 1 week | 2 weeks |
| Local Validation | 1 week | 1 week | 2 weeks |
| RC + GA Release | 1 week | 1 week | 2 weeks |
| **Total to v2.0.0 GA** | **3 weeks** | **3 weeks** | **6 weeks** |

> **Note:** Timeline assumes local-first validation only. Optional production deployment activities (Kubernetes, cloud) are not on the critical path and would extend the timeline.

---

## Immediate Actions

1. **Day 1:** Atlas to register `astroos-sdk` on PyPI and `@astroos/sdk` on npm
2. **Day 1:** Verify local installation on clean test machine
3. **Day 3:** Publish SDK test releases
4. **Week 2:** Validate local Docker image and health endpoints
