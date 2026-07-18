# AstroOS v2.0.0 — Deployment Instructions

**Platform Status:** ✅ GENERAL AVAILABILITY READY

---

## Quick Deployment (Development)

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

## Production Deployment

### Prerequisites
- Kubernetes cluster (EKS/GKE/AKS)
- PostgreSQL database (RDS/CloudSQL)
- Redis (ElastiCache/Memorystore)
- S3-compatible storage for report exports

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