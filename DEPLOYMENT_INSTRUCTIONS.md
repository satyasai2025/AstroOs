# AstroOS v2.0.0 — Deployment Instructions

**Platform Status:** ✅ GENERAL AVAILABILITY READY

AstroOS is a **Local-First** Vedic Astrology Research Platform. The primary deployment target is a single local machine (personal computer). These instructions cover both local setup (required) and optional production deployment patterns.

---

## Local Setup (Primary)

```bash
# Clone and enter the repository
cd AstroOS

# Copy environment template
cp .env.example .env
# Edit .env with your database URL and secrets

# Start development services
docker-compose up -d

# API available at: http://localhost:8000
# Metrics at: http://localhost:8000/metrics
# Health at: http://localhost:8000/health/live
# Docs at: http://localhost:8000/api/docs
```

---

## Optional Production Deployment

For users who wish to deploy AstroOS as a multi-user service or make it available over a network, production deployment patterns are provided. These are **optional** — AstroOS is designed to run entirely on a local machine without any external services.

### Prerequisites
- Kubernetes cluster (EKS/GKE/AKS) or a single VM
- PostgreSQL database (RDS/CloudSQL or local)
- Redis (optional — for JWT denylist in multi-user scenarios)
- S3-compatible storage for report exports (optional)

### Steps

1. **Build production image:**
```bash
docker build -f Dockerfile.prod -t astroos/api:v2.0.0 .
```

2. **Deploy to Kubernetes:**
```bash
# Manifests would be in deploy/k8s/ (future Phase I)
kubectl apply -f deploy/k8s/
```

3. **Configure external secrets:**
- Set DATABASE_URL, REDIS_URL in Kubernetes Secrets
- Configure WeasyPrint system dependencies in container

### Health Checks
- Liveness: `http://api:8000/health/live`
- Readiness: `http://api:8000/health/ready`
- Metrics: `http://api:8000/metrics`

---

## SDK Publication

```bash
# Python SDK to TestPyPI
cd sdks/python
python -m build
twine upload --repository testpypi dist/*

# TypeScript SDK to npm
cd sdks/typescript
npm publish --access public
```

---

## Deployment Status

| Component | Status | Path |
|-----------|--------|------|
| Production Dockerfile | ✅ Ready | Dockerfile.prod |
| Docker Compose | ✅ Ready | docker-compose.yml |
| CI/CD Pipeline | ✅ Ready | .github/workflows/ci.yml |
| Prometheus Config | ✅ Ready | prometheus/prometheus.yml |
| Production Guide | ✅ Ready | docs/production/configuration.md |