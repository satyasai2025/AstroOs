# Production Environment Configuration

## Required Environment Variables

These variables MUST be set in production. Copy `.env.example` to `.env` and configure:

```bash
# Core
DATABASE_URL=postgresql+asyncpg://astroos:password@postgres:5432/astroos
REDIS_URL=redis://redis:6379/0

# Security
JWT_PRIVATE_KEY_PATH=/app/keys/private.pem
JWT_PUBLIC_KEY_PATH=/app/keys/public.pem
# Generate with: python -c "from cryptography.hazmat.primitives.asymmetric import rsa; from cryptography.hazmat.primitives import serialization; key = rsa.generate_private_key(65537, 2048); open('/app/keys/private.pem','wb').write(key.private_bytes(serialization.PrivateFormat.PEM, serialization.NoEncryption()))"

# Astrology
EPHEMERIS_PATH=/app/data/ephemeris
# Download Official Swiss Ephemeris: wget https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1 -P /app/data/ephemeris/

# Application
APP_NAME="AstroOS Production"
APP_VERSION="2.0.0"
ENVIRONMENT=production
DEBUG=false

# CORS
ALLOWED_ORIGINS=["https://astroos.io","https://app.astroos.io"]

# Performance
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Docker Compose for Production

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://astroos:astroos_password@postgres:5432/astroos
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - DEBUG=false
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./data/ephemeris:/app/data/ephemeris:ro
      - ./keys:/app/keys:ro

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: astroos
      POSTGRES_PASSWORD: astroos_password
      POSTGRES_DB: astroos
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U astroos -d astroos"]
      interval: 10s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    command: redis-server --save 60 1 --loglevel warning
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 10

  prometheus:
    image: prom/prometheus:v2.51.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.console.libraries=/etc/prometheus/console_libraries"
      - "--web.console.templates=/etc/prometheus/consoles"
      - "--web.enable-lifecycle"

volumes:
  postgres_data:
  redis_data:
```

## Kubernetes Deployment

### api-deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: astroos-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: astroos-api
  template:
    metadata:
      labels:
        app: astroos-api
    spec:
      containers:
      - name: api
        image: astroos:2.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: astroos-secrets
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: astroos-api
spec:
  selector:
    app: astroos-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### secrets.yaml
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: astroos-secrets
type: Opaque
data:
  DATABASE_URL: <base64-encoded-connection-string>
  REDIS_URL: <base64-encoded-connection-string>
  JWT_PRIVATE_KEY: <base64-encoded-key>