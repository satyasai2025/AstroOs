# API Key Management — AstroOS v2.3.0

## Overview

API keys are the default authentication mechanism for the AstroOS API (local-first).
OAuth 2.0 is available as an optional add-on for users who expose their instance publicly.

## Default: API Keys (Local-First)

```
POST /api/v1/auth/api-key          # Generate a new API key
GET  /api/v1/auth/api-keys         # List active API keys
DELETE /api/v1/auth/api-key/{id}   # Revoke an API key
```

### Usage

```bash
curl -H "x-api-key: <your-key>" http://localhost:8000/api/v1/horoscope/d1 \
  -d '{"birth_datetime_utc":"1986-06-15T10:30:00Z","latitude":28.6139,"longitude":77.2090}'
```

### Key Properties
- 32-byte random hex string
- Scoped to read/write/admin
- Optional expiry date
- Stored as SHA-256 hash (never plaintext)

## Optional: OAuth 2.0

Enable via `ASTROOS_OAUTH_ENABLED=1`. Requires:
- Authorization server config (or built-in minimal provider)
- Redirect URI registration
- Token refresh support

OAuth is disabled by default. Only enable if you expose AstroOS publicly.

## Rate Limiting

- Local-first default: **disabled** (no limit for single-user on localhost)
- Optional: enable via `ASTROOS_RATE_LIMIT=100/hour`
- Algorithm: token bucket with configurable refill rate
