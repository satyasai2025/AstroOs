# AstroOS API Reference (v2.x)

AstroOS ships a self-documenting OpenAPI schema. With `DEBUG=true` (development default in `.env`):

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/docs` | Swagger UI (interactive, try requests in the browser) |
| `http://localhost:8000/api/redoc` | ReDoc |
| `http://localhost:8000/api/openapi.json` | Raw OpenAPI 3 schema |
| `http://localhost:8000/api/healthz` | Health check (no auth) |

This document is a curated overview with copy-paste examples. The OpenAPI docs are the authoritative, always-current reference.

---

## Conventions

- All endpoints are prefixed `/api/v1` unless noted.
- All request/response bodies are JSON.
- Datetimes are UTC ISO-8601 (e.g. `1986-06-15T10:30:00+00:00`).
- Everything except `/auth/*`, `/knowledge*` (read), and `/api/healthz` requires a Bearer token.

### Common birth-data payload

Most calculation endpoints accept this shape:

```json
{
  "birth_datetime_utc": "1986-06-15T10:30:00+00:00",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "ayanamsa": "lahiri",
  "house_system": "W"
}
```

- `ayanamsa`: `lahiri | kp | raman | yukteshwar | fagan_bradley | true_chitra`
- `house_system`: `W` (Whole Sign) · `P` (Placidus) · `K` (Koch) · `E` (Equal)

---

## Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | — | Create a user account |
| POST | `/auth/login` | — | Get access + refresh tokens |
| POST | `/auth/refresh` | — | Rotate tokens using a refresh token |
| POST | `/auth/logout` | Bearer | Revoke tokens (requires Redis; no-op without it) |

Example:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","display_name":"Me","password":"changeme123"}'

curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"changeme123"}'
# → { "user": {...}, "tokens": { "access_token": "...", "refresh_token": "..." } }
```

Use the token on subsequent requests:

```bash
TOKEN="<access_token>"
curl -s http://localhost:8000/api/v1/horoscope/d1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"birth_datetime_utc":"1986-06-15T10:30:00+00:00","latitude":28.6139,"longitude":77.2090,"ayanamsa":"lahiri","house_system":"W"}'
```

---

## Calculation Endpoints (Bearer required)

### Horoscope

- `POST /horoscope/d1` — D1 birth chart: ascendant, planet positions, houses, aspects, strengths, Panchanga.

### Divisional charts

- `POST /divisional/{varga}` — single varga (e.g. `/divisional/D9`).
- `POST /divisional/all` — all 15 vargas in one call.

Supported vargas: `D2 D3 D4 D7 D9 D10 D12 D16 D20 D24 D27 D30 D40 D45 D60`.

### Dasha

- `POST /dasha/{system}` — `vimshottari | yogini | ashtottari | kalachakra | chara | narayana`.
- Body: common birth payload plus `max_depth` (1 = Mahadasha … 5 = Prana).

### Strength & tabular systems

- `POST /shadbala/...` — six-fold planetary strength.
- `POST /ashtakavarga/...` — bindu / Sarvashtakavarga.
- `POST /yoga/...` — yoga detection (Panch Mahapurusha, Raja, Dhana, Chandra, Nabhasa, Arishta, ...).
- `POST /transit/...` — current transit positions vs natal chart.
- `POST /timeline/...` — Dasha timeline with events.

### Utilities

- `POST /geocode/search` — place name → coordinates.
- `POST /geocode/timezone` — coordinates → timezone (for converting local birth time to UTC).

---

## Analysis, Research & Reporting

| Prefix | Role required | Purpose |
|--------|---------------|---------|
| `/workflow` | authenticated | One-shot full analysis (`POST /workflow/analyze`) |
| `/ai` | authenticated | Chart summaries, yoga explanations, Q&A (cited) |
| `/report` | authenticated | Chart / research / comparison reports |
| `/export` | authenticated | CSV/JSON export of charts and research data |
| `/visualization` | authenticated | Chart wheel and statistical visualization payloads |
| `/events` | authenticated | Life-event records tied to charts |
| `/benchmark` | authenticated | Accuracy validation against gold-standard data |
| `/research`, `/statistics` | researcher | Projects, experiments, snapshots, distributions |
| `/knowledge`, `/knowledge-graph` | read: public · write: researcher/admin | Classical texts, verses, rules, karakatvas, graph |
| `/admin` | admin | System status, module registry, user management |
| `/api/v1/datasets` | authenticated | Dataset registry and import pipeline |

Roles are assigned per-user (`user` → `researcher` → `admin`). In a local single-user install you typically promote your own account once via the admin bootstrap.

---

## Errors

Errors follow FastAPI conventions:

```json
{ "detail": "Human-readable message" }
```

| Status | Meaning |
|--------|---------|
| 401 | Missing/expired/invalid token |
| 403 | Insufficient role |
| 404 | Not found (or soft-deleted) |
| 409 | Conflict (e.g. email already registered) |
| 422 | Validation error (`detail` is a list of field errors) |

---

## Health check

```bash
curl http://localhost:8000/api/healthz
```

```json
{
  "status": "ok",
  "version": "2.0.0",
  "environment": "development",
  "ephemeris": { "mode": "moshier", "official_data": false }
}
```

`ephemeris.mode` is `swiss` when `.se1` data files are present in `data/ephemeris/`, otherwise `moshier` (built-in approximation, ~1 arc-minute).
