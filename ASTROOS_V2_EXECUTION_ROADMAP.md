# AstroOS v2.0 Release Engineering Roadmap

**Date:** 2026-07-19  
**Author:** Chief Solutions Architect (Release Engineering)  
**Status:** Proposed — GA-Critical Path

---

## Current State

✅ All 8 phases (A–H) are FROZEN  
✅ Milestone M1 is COMPLETE (all 10 criteria achieved)  
🎯 **Target:** v2.0.0 General Availability release

---

## GA-Critical Release Blockers

| Blocker | Requirement | Status |
|---------|-------------|--------|
| **RB-1** | SDK publication (PyPI + npm) | ❌ Not done |
| **RB-2** | Production cluster deployed and validated | ❌ Not done |
| **RB-3** | Observability stack verified | ❌ Not done |
| **RB-4** | Health endpoints (`/live`, `/ready`) verified in prod | ❌ Not done |

---

## Non-GA (Post-Release) Items

- Missing report templates (Dasha.html, Research.html) - 7 of 9 exist
- Geocoding production provider - dev OK with Nominatim
- Report export UI buttons - backend endpoints exist
- Additional SDK documentation

---

## GA-Focused Milestones

### M2 — Release Candidate Preparation (Week 1-2)
**Goal:** Package and validate release candidate

| Exit Criteria | Work Required | Status |
|---------------|---------------|--------|
| `astroos-sdk` installable via pip | Publish to PyPI | ❌ |
| `@astroos/sdk` installable via npm | Publish to npm | ❌ |
| All code tagged and verified | Repository ready | ❌ |

### M3 — Production Validation RC (Week 2-3)
**Goal:** Deploy RC to production environment

| Exit Criteria | Work Required | Status |
|---------------|---------------|--------|
| EKS/GKE cluster running | One environment live | ❌ |
| `/metrics` endpoint verified | Prometheus scraping | ❌ |
| Health checks verified | `/live`, `/ready` in prod | ❌ |
| Trivy scan clean | No HIGH/CRITICAL vulns | ❌ |

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

Week 2: Production Cluster Bootstrap
  ├─ Create cluster
  ├─ Deploy Docker image
  ├─ Verify health endpoints
  └─ Configure monitoring

Week 3: RC Validation
  ├─ Run Trivy scan
  ├─ Verify observability
  ├─ Tag v2.0.0-rc.1
  └─ GA Go/No-Go decision
```

---

## Dependencies (Critical Path)

| Dependency | Owner | Acquisition Needed |
|------------|-------|-------------------|
| PyPI credentials | Release Team | Before Week 1 |
| npm credentials | Release Team | Before Week 1 |
| Cloud account (AWS/GCP) | SRE | Before Week 2 |
| Domain + SSL certs | Operations | Before Week 2 |

---

## Exit Criteria Summary

**M2 Exit:** SDKs installable, code tagged  
**M3 Exit:** Cluster live, observability verified, security scan clean  
**M4 Exit (RC):** All above + Go/No-Go for GA  

**GA Exit (M5):** RC approved, `v2.0.0` tag cut, CHANGELOG updated

---

## Project Timeline

| Stage | Duration | Buffer | Total |
|-------|----------|--------|-------|
| SDK Publication | 1 week | 1 week | 2 weeks |
| Production Validation | 2 weeks | 1 week | 3 weeks |
| RC + GA Release | 1 week | 1 week | 2 weeks |
| **Total to v2.0.0 GA** | **4 weeks** | **3 weeks** | **7 weeks** |

---

## Immediate Actions

1. **Day 1:** Atlas to register `astroos-sdk` on PyPI and `@astroos/sdk` on npm
2. **Day 1:** SRE to request cloud provider account
3. **Day 3:** Publish SDK test releases
4. **Week 2:** Deploy RC to test cluster