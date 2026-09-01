# Relocation Studio Frontend Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a research-section page where a user supplies birth data + target location and sees the four relocation technique fixtures (paran_crossings, sun_angular, midpoints_to_angles, harmonic_interpretation) rendered through a new live API endpoint.

**Architecture:** A new FastAPI router `POST /api/v1/relocation/analyze` computes relocation facts via `RelocationEngine`, resolves the four relocation techniques by id, executes them with `TechniqueEngine`, and returns structured JSON. A Next.js client component (`RelocationStudio`) renders a form with presets, calls the endpoint via the existing `api` client, and displays per-technique rule cards. The page lives under the Research section and gets a nav entry.

**Tech Stack:** FastAPI + Pydantic (backend), pyswisseph via `RelocationEngine`, Next.js 15 (App Router), React, existing `@/lib/api` client, Playwright e2e.

## Global Constraints

- Existing technique framework (TechniqueResolver, TechniqueEngine, FactRegistry, domain/technique.py) must NOT be modified.
- The relocation engine and fixtures 09-12 (already committed) must NOT change.
- Auth: route registered under `/api/v1` with `_authenticated = [Depends(require_authenticated)]` (see `apps/api/main.py:341`).
- Frontend API base: use the existing `api.post` client (`apps/web/src/lib/api.ts`), which prepends `/api` and attaches auth.
- Frontend conventions: dark theme inputs `rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-white focus:border-<color>-500 focus:outline-none`; cards `rounded-xl border border-slate-800 bg-slate-900/40 p-5` (see SynastryStudio).
- Nav entries live in `apps/web/src/config/navConfig.ts` Research module; icons must be from `src/components/ui/Icon.tsx` (`compass`, `search`, `bar`, `document`, `grid`, `camera`, `sparkle`, `shield`, etc.).
- Test command (backend): `.venv/bin/python -m pytest`
- Typecheck (frontend): `pnpm --dir apps/web typecheck`
- Commit identity is already set locally (`monkeycode-ai`).
- Working tree: branch `260828-feat-astrocartography` in worktree at `/tmp/opencode/AstroOs/.worktrees/260828-feat-astrocartography`.

---

### Task 1: Relocation schemas (`apps/api/schemas/relocation.py`)

**Files:**
- Create: `apps/api/schemas/relocation.py`
- Test: `apps/api/tests/unit/test_relocation_schemas.py`

**Interfaces:**
- Produces: `RelocationAnalyzeRequest` (fields `birth_utc: datetime`, `birth_lat: float`, `birth_lon: float`, `target_lat: float`, `target_lon: float`, `ayanamsa: str = "lahiri"`, `house_system: str = "P"`), `RelocationAngleSchema`, `RelocationTriggerSchema`, `RelocationTechniqueSchema`, `RelocationAnalyzeResponse`. Used verbatim by Task 2's router and Task 3's tests.

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/unit/test_relocation_schemas.py`:

```python
"""AstroOS — Relocation router schemas unit tests."""

from datetime import datetime, timezone

from apps.api.schemas.relocation import (
    RelocationAnalyzeRequest,
    RelocationAnalyzeResponse,
)


def test_analyze_request_defaults():
    req = RelocationAnalyzeRequest(
        birth_utc=datetime(1936, 8, 19, 3, 2, 0, tzinfo=timezone.utc),
        birth_lat=34.0195,
        birth_lon=-118.4912,
        target_lat=40.2338,
        target_lon=-111.6585,
    )
    assert req.ayanamsa == "lahiri"
    assert req.house_system == "P"


def test_analyze_response_shape():
    resp = RelocationAnalyzeResponse(
        birth={"lat": 34.0195, "lon": -118.4912},
        target={"lat": 40.2338, "lon": -111.6585},
        angles={
            "ascendant": {"degree": 123.45, "sign": "leo", "label": 123.45,
                          "harmonic_family": "seventh"},
            "midheaven": {"degree": 45.67, "sign": "taurus", "label": 45.67,
                          "harmonic_family": "seventh"},
        },
        techniques=[
            {
                "technique_id": "sun_angular",
                "technique_name": "Sun Angular (You Shine)",
                "confidence": 55,
                "confidence_basis": "1/1 primary rules triggered; +0 supporting, -0 opposing; input availability 100%.",
                "is_matched": True,
                "triggers": [
                    {
                        "rule_id": "SUN-001",
                        "rule_name": "Sun Conjunct Asc/MC Shines",
                        "role": "primary",
                        "status": "not_triggered",
                        "provenance": "source_derived",
                        "matched_conditions": [],
                        "failed_conditions": ["relocation.planet.sun.line_in_orb == True"],
                        "missing_facts": [],
                        "explanation": "test",
                    }
                ],
            }
        ],
        facts={"relocation.midpoints.asc.count": 2},
    )
    assert resp.techniques[0]["technique_id"] == "sun_angular"
    assert resp.facts["relocation.midpoints.asc.count"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest apps/api/tests/unit/test_relocation_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.api.schemas.relocation'`

- [ ] **Step 3: Write the schema module**

Create `apps/api/schemas/relocation.py`:

```python
"""
AstroOS — Relocation Analysis API Schemas

DTO boundary for POST /api/v1/relocation/analyze. Converts domain objects
(Fact, TechniqueExecutionResult, RuleTrigger) to/from HTTP in the router
layer; no domain types leak through here. Mirrors the discipline of
schemas/technique.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class RelocationAnalyzeRequest(BaseModel):
    birth_utc: datetime = Field(description="ISO 8601 UTC birth datetime")
    birth_lat: float = Field(ge=-90.0, le=90.0)
    birth_lon: float = Field(ge=-180.0, le=180.0)
    target_lat: float = Field(ge=-90.0, le=90.0)
    target_lon: float = Field(ge=-180.0, le=180.0)
    ayanamsa: str = "lahiri"
    house_system: str = "P"


class RelocationAngleSchema(BaseModel):
    degree: float
    sign: str
    label: float
    harmonic_family: str


class RelocationTriggerSchema(BaseModel):
    rule_id: str
    rule_name: str
    role: str
    status: str
    provenance: str
    matched_conditions: list[str] = Field(default_factory=list)
    failed_conditions: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    explanation: str


class RelocationTechniqueSchema(BaseModel):
    technique_id: str
    technique_name: str
    confidence: int
    confidence_basis: str
    is_matched: bool
    triggers: list[RelocationTriggerSchema] = Field(default_factory=list)


class RelocationAnalyzeResponse(BaseModel):
    birth: dict[str, float]
    target: dict[str, float]
    angles: dict[str, RelocationAngleSchema]
    techniques: list[RelocationTechniqueSchema]
    facts: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest apps/api/tests/unit/test_relocation_schemas.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add apps/api/schemas/relocation.py apps/api/tests/unit/test_relocation_schemas.py
git commit -m "feat(relocation): request/response schemas for analyze endpoint"
```

---

### Task 2: Relocation router (`apps/api/routers/relocation.py`) + registration

**Files:**
- Create: `apps/api/routers/relocation.py`
- Modify: `apps/api/main.py` (import + `include_router`)
- Test: `apps/api/tests/unit/test_relocation_router.py`

**Interfaces:**
- Consumes: `RelocationAnalyzeRequest` / `RelocationAnalyzeResponse` from Task 1; `RelocationEngine` (apps/api/services/relocation_engine.py); `Fact` (apps/api/domain/facts.py); `FactRegistry`; `TechniqueResolver`; `TechniqueEngine`; `technique_registry.get_technique`.
- Produces: endpoint `POST /api/v1/relocation/analyze`. Task 4's frontend calls this path.

- [ ] **Step 1: Write the failing router test**

Create `apps/api/tests/unit/test_relocation_router.py`:

```python
"""AstroOS — Relocation analyze endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.techniques import (  # noqa: F401
    harmonic_interpretation,
    midpoints_to_angles,
    paran_crossings,
    sun_angular,
)

PROVO_BODY = {
    "birth_utc": "1936-08-19T03:02:00Z",
    "birth_lat": 34.0195,
    "birth_lon": -118.4912,
    "target_lat": 40.2338,
    "target_lon": -111.6585,
    "ayanamsa": "tropical",
}


@pytest.fixture(autouse=True)
def ensure_fixtures_and_auth():
    paran_crossings.init_paran_crossings()
    sun_angular.init_sun_angular()
    midpoints_to_angles.init_midpoints_to_angles()
    harmonic_interpretation.init_harmonic_interpretation()
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "test_user"}
    yield
    app.dependency_overrides.clear()


def test_relocation_analyze_happy_path():
    client = TestClient(app)
    response = client.post("/api/v1/relocation/analyze", json=PROVO_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["birth"]["lat"] == 34.0195
    assert data["target"]["lon"] == -111.6585
    tech_ids = {t["technique_id"] for t in data["techniques"]}
    assert {"paran_crossings", "sun_angular", "midpoints_to_angles",
            "harmonic_interpretation"} <= tech_ids
    any_triggered = any(
        t["status"] == "triggered"
        for tech in data["techniques"]
        for t in tech["triggers"]
    )
    assert any_triggered


def test_relocation_analyze_requires_auth():
    client = TestClient(app)
    app.dependency_overrides.clear()
    response = client.post("/api/v1/relocation/analyze", json=PROVO_BODY)
    assert response.status_code in (401, 403)


def test_relocation_analyze_422_on_bad_coords():
    client = TestClient(app)
    bad = dict(PROVO_BODY, target_lat=95.0)
    response = client.post("/api/v1/relocation/analyze", json=bad)
    assert response.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest apps/api/tests/unit/test_relocation_router.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.api.routers.relocation'`

- [ ] **Step 3: Write the router**

Create `apps/api/routers/relocation.py`:

```python
"""
AstroOS — Relocation Analysis Router

Adapter-only HTTP surface for the relocation engine + the four relocation
technique fixtures. Computes facts for a birth->target pair server-side,
executes the four techniques, and maps results to HTTP. No astrology and no
rule logic live here (same discipline as routers/technique.py).
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter

from apps.api.domain.facts import Fact
from apps.api.schemas.relocation import (
    RelocationAnalyzeRequest,
    RelocationAnalyzeResponse,
    RelocationAngleSchema,
    RelocationTechniqueSchema,
    RelocationTriggerSchema,
)
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.relocation_engine import RelocationEngine
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.technique_resolver import TechniqueResolver
# Importing this registers the bundled relocation technique fixtures.
from apps.api.services.techniques import (  # noqa: F401
    harmonic_interpretation,
    midpoints_to_angles,
    paran_crossings,
    sun_angular,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relocation", tags=["relocation"])

_RELOCATION_TECHNIQUE_IDS = (
    "paran_crossings",
    "sun_angular",
    "midpoints_to_angles",
    "harmonic_interpretation",
)


def _to_angle_schema(registry: FactRegistry, name: str) -> RelocationAngleSchema:
    base = f"relocation.{name}"
    return RelocationAngleSchema(
        degree=registry.get_value(f"{base}.degree", 0.0),
        sign=registry.get_value(f"{base}.sign", ""),
        label=registry.get_value(f"{base}.label", 0.0),
        harmonic_family=registry.get_value(f"{base}.harmonic_family", ""),
    )


def _to_trigger_schema(trigger) -> RelocationTriggerSchema:
    return RelocationTriggerSchema(
        rule_id=trigger.rule_id,
        rule_name=trigger.rule_name,
        role=trigger.role.value,
        status=trigger.status.value,
        provenance=trigger.provenance.value,
        matched_conditions=list(trigger.matched_conditions),
        failed_conditions=list(trigger.failed_conditions),
        missing_facts=list(trigger.missing_facts),
        explanation=trigger.explanation,
    )


@router.post("/analyze", response_model=RelocationAnalyzeResponse)
def analyze_relocation(body: RelocationAnalyzeRequest) -> RelocationAnalyzeResponse:
    engine = RelocationEngine(ayanamsa=body.ayanamsa, house_system=body.house_system)
    facts = engine.compute_facts(
        body.birth_utc,
        body.birth_lat,
        body.birth_lon,
        body.target_lat,
        body.target_lon,
    )

    registry = FactRegistry()
    for fact in facts:
        registry.add_fact(fact)

    resolver = TechniqueResolver()
    tech_engine = TechniqueEngine()
    techniques: list[RelocationTechniqueSchema] = []
    for tech_id in _RELOCATION_TECHNIQUE_IDS:
        tech = resolver.resolve_by_id(tech_id, 1)
        if tech is None:
            continue
        result = tech_engine.execute(tech, registry)
        techniques.append(
            RelocationTechniqueSchema(
                technique_id=result.technique_id,
                technique_name=tech.name,
                confidence=result.confidence,
                confidence_basis=result.confidence_basis,
                is_matched=any(
                    t.status.value == "triggered" for t in result.triggers
                ),
                triggers=[_to_trigger_schema(t) for t in result.triggers],
            )
        )

    return RelocationAnalyzeResponse(
        birth={"lat": body.birth_lat, "lon": body.birth_lon},
        target={"lat": body.target_lat, "lon": body.target_lon},
        angles={
            "ascendant": _to_angle_schema(registry, "ascendant"),
            "midheaven": _to_angle_schema(registry, "midheaven"),
        },
        techniques=techniques,
        facts={
            "relocation.midpoints.asc.count": registry.get_value(
                "relocation.midpoints.asc.count", 0
            ),
            "relocation.midpoints.mc.count": registry.get_value(
                "relocation.midpoints.mc.count", 0
            ),
            "relocation.midpoints.asc.double": registry.get_value(
                "relocation.midpoints.asc.double", False
            ),
            "relocation.midpoints.mc.double": registry.get_value(
                "relocation.midpoints.mc.double", False
            ),
            "relocation.paran.count": registry.get_value("relocation.paran.count", 0),
            "relocation.lines.paran.count": registry.get_value(
                "relocation.lines.paran.count", 0
            ),
        },
    )
```

- [ ] **Step 4: Register the router in main.py**

In `apps/api/main.py`, add the import near the other router imports (after line 83 `from apps.api.routers import custom_techniques as custom_techniques_router`):

```python
from apps.api.routers import relocation as relocation_router
```

Then register it right after the `custom_techniques_router` include (after line 431):

```python
    app.include_router(
        relocation_router.router, prefix="/api/v1", dependencies=_authenticated
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest apps/api/tests/unit/test_relocation_router.py -v`
Expected: PASS (3 passed)

Run (regression): `.venv/bin/python -m pytest apps/api/tests/unit/test_relocation_techniques.py apps/api/tests/unit/test_relocation_engine.py -q`
Expected: PASS (45 passed)

- [ ] **Step 6: Commit**

```bash
git add apps/api/routers/relocation.py apps/api/main.py apps/api/tests/unit/test_relocation_router.py
git commit -m "feat(relocation): analyze endpoint computing + executing four relocation techniques"
```

---

### Task 3: Relocation page route (`apps/web/src/app/research/relocation/page.tsx`)

**Files:**
- Create: `apps/web/src/app/research/relocation/page.tsx`

**Interfaces:**
- Consumes: `<RelocationStudio />` (Task 4). No props.
- Produces: route `/research/relocation` that renders the studio inside a `max-w-7xl` container (mirrors `research/synastry/page.tsx`).

- [ ] **Step 1: Write the page**

Create `apps/web/src/app/research/relocation/page.tsx`:

```tsx
import { RelocationStudio } from "@/components/research/RelocationStudio";

export const metadata = {
  title: "Relocation & Astro-Cartography Studio | AstroOS Research",
  description:
    "Evaluate relocation techniques — paran crossings, Sun angularity, midpoints to angles, and harmonic interpretation — for any birth chart and target location.",
};

export default function RelocationPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <RelocationStudio />
    </div>
  );
}
```

- [ ] **Step 2: Verify the route compiles**

Run: `pnpm --dir apps/web typecheck`
Expected: FAIL with `ModuleNotFoundError: Cannot find module '@/components/research/RelocationStudio'` (or similar) — the page references the not-yet-created component. This is the expected failing state; Task 4 resolves it.

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/app/research/relocation/page.tsx
git commit -m "feat(web): add relocation studio route"
```

---

### Task 4: RelocationStudio component (`apps/web/src/components/research/RelocationStudio.tsx`)

**Files:**
- Create: `apps/web/src/components/research/RelocationStudio.tsx`

**Interfaces:**
- Consumes: `api.post("/v1/relocation/analyze", body)` (existing `@/lib/api` client), response type `RelocationAnalyzeResponse` (defined in this file to match Task 1's schema).
- Produces: `<RelocationStudio />` rendered by Task 3's page.

- [ ] **Step 1: Write the component**

Create `apps/web/src/components/research/RelocationStudio.tsx`:

```tsx
"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";

interface Trigger {
  rule_id: string;
  rule_name: string;
  role: string;
  status: "triggered" | "not_triggered" | "insufficient_data";
  provenance: string;
  matched_conditions: string[];
  failed_conditions: string[];
  missing_facts: string[];
  explanation: string;
}

interface TechniqueResult {
  technique_id: string;
  technique_name: string;
  confidence: number;
  confidence_basis: string;
  is_matched: boolean;
  triggers: Trigger[];
}

interface AngleInfo {
  degree: number;
  sign: string;
  label: number;
  harmonic_family: string;
}

interface RelocationAnalyzeResponse {
  birth: { lat: number; lon: number };
  target: { lat: number; lon: number };
  angles: { ascendant: AngleInfo; midheaven: AngleInfo };
  techniques: TechniqueResult[];
  facts: Record<string, unknown>;
}

const HARMONIC_LABELS: Record<string, string> = {
  ninth: "9th harmonic — comfort zone",
  fifth: "5th harmonic — creative / playful",
  seventh: "7th harmonic — discipline / training",
};

const STATUS_STYLES: Record<Trigger["status"], string> = {
  triggered: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  not_triggered: "bg-slate-700/20 text-slate-400 border-slate-600/40",
  insufficient_data: "bg-amber-500/10 text-amber-400 border-amber-500/30",
};

interface Preset {
  name: string;
  birth_utc: string;
  birth_lat: number;
  birth_lon: number;
  target_lat: number;
  target_lon: number;
}

const PRESETS: Preset[] = [
  {
    name: "Robert Redford → Provo, UT",
    birth_utc: "1936-08-19T03:02:00Z",
    birth_lat: 34.0195,
    birth_lon: -118.4912,
    target_lat: 40.2338,
    target_lon: -111.6585,
  },
  {
    name: "Robert Redford → Los Angeles (birth)",
    birth_utc: "1936-08-19T03:02:00Z",
    birth_lat: 34.0195,
    birth_lon: -118.4912,
    target_lat: 34.0195,
    target_lon: -118.4912,
  },
];

const inputCls =
  "mt-1 w-full rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-white focus:border-cyan-500 focus:outline-none";

export function RelocationStudio() {
  const [birthUtc, setBirthUtc] = useState<string>("1936-08-19T03:02:00Z");
  const [birthLat, setBirthLat] = useState<number>(34.0195);
  const [birthLon, setBirthLon] = useState<number>(-118.4912);
  const [targetLat, setTargetLat] = useState<number>(40.2338);
  const [targetLon, setTargetLon] = useState<number>(-111.6585);
  const [ayanamsa, setAyanamsa] = useState<string>("lahiri");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RelocationAnalyzeResponse | null>(null);

  const applyPreset = (p: Preset) => {
    setBirthUtc(p.birth_utc);
    setBirthLat(p.birth_lat);
    setBirthLon(p.birth_lon);
    setTargetLat(p.target_lat);
    setTargetLon(p.target_lon);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.post<RelocationAnalyzeResponse>(
        "/v1/relocation/analyze",
        {
          birth_utc: birthUtc,
          birth_lat: birthLat,
          birth_lon: birthLon,
          target_lat: targetLat,
          target_lon: targetLon,
          ayanamsa,
        },
      );
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-6 backdrop-blur">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Relocation &amp; Astro-Cartography Studio
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          See how the paran crossings, Sun angularity, midpoint-to-angle, and
          harmonic techniques apply to a target location.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {PRESETS.map((p) => (
          <button
            key={p.name}
            onClick={() => applyPreset(p)}
            className="rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:border-cyan-500 hover:text-cyan-400"
          >
            {p.name}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
          <h2 className="text-base font-semibold text-cyan-400">Birth Location</h2>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="text-xs font-medium text-slate-400">
                Birth Date &amp; Time (UTC)
              </label>
              <input
                type="text"
                value={birthUtc}
                onChange={(e) => setBirthUtc(e.target.value)}
                className={inputCls}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">Latitude</label>
              <input
                type="number"
                step="any"
                value={birthLat}
                onChange={(e) => setBirthLat(parseFloat(e.target.value))}
                className={inputCls}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">Longitude</label>
              <input
                type="number"
                step="any"
                value={birthLon}
                onChange={(e) => setBirthLon(parseFloat(e.target.value))}
                className={inputCls}
              />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
          <h2 className="text-base font-semibold text-purple-400">Target Location</h2>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="text-xs font-medium text-slate-400">Latitude</label>
              <input
                type="number"
                step="any"
                value={targetLat}
                onChange={(e) => setTargetLat(parseFloat(e.target.value))}
                className={inputCls}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">Longitude</label>
              <input
                type="number"
                step="any"
                value={targetLon}
                onChange={(e) => setTargetLon(parseFloat(e.target.value))}
                className={inputCls}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="text-xs font-medium text-slate-400">Ayanamsa</label>
              <select
                value={ayanamsa}
                onChange={(e) => setAyanamsa(e.target.value)}
                className={inputCls}
              >
                <option value="lahiri">Lahiri</option>
                <option value="tropical">Tropical (no ayanamsa)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="rounded-lg bg-cyan-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-cyan-500 disabled:opacity-50"
      >
        {loading ? "Analyzing…" : "Run Relocation Analysis"}
      </button>

      {error && (
        <div className="rounded border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
            <h2 className="text-base font-semibold text-white">
              Angles at Target Location
            </h2>
            <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
              {(["ascendant", "midheaven"] as const).map((key) => {
                const angle = result.angles[key];
                return (
                  <div key={key}>
                    <div className="text-xs font-medium text-slate-400 capitalize">
                      {key}
                    </div>
                    <div className="mt-1 text-lg font-semibold text-white">
                      {angle.sign} {angle.degree.toFixed(2)}°
                    </div>
                    <div className="text-xs text-slate-400">
                      {HARMONIC_LABELS[angle.harmonic_family] ?? angle.harmonic_family}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {result.techniques.map((tech) => (
            <div
              key={tech.technique_id}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-white">{tech.technique_name}</h3>
                <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-400">
                  {tech.confidence}% confidence
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">{tech.confidence_basis}</p>
              <div className="mt-3 space-y-2">
                {tech.triggers.map((t) => (
                  <div
                    key={t.rule_id}
                    className="rounded-lg border bg-slate-800/40 p-3"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm font-semibold text-slate-200">
                        {t.rule_name}
                        <span className="ml-2 text-xs font-normal text-slate-500">
                          {t.rule_id}
                        </span>
                      </div>
                      <span
                        className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${STATUS_STYLES[t.status]}`}
                      >
                        {t.status.replace(/_/g, " ")}
                      </span>
                    </div>
                    {t.explanation && (
                      <p className="mt-1 text-xs text-slate-400">{t.explanation}</p>
                    )}
                    {t.missing_facts.length > 0 && (
                      <p className="mt-1 text-xs text-amber-400/80">
                        Missing: {t.missing_facts.join(", ")}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Run typecheck**

Run: `pnpm --dir apps/web typecheck`
Expected: PASS (no errors)

- [ ] **Step 3: Run lint on the new file**

Run: `pnpm --dir apps/web lint`
Expected: no errors for `src/components/research/RelocationStudio.tsx`

- [ ] **Step 4: Add nav entry in `apps/web/src/config/navConfig.ts`**

In the Research module `items` array (after the `research/patterns` line ~243), add:

```ts
          { href: "/research/relocation", label: "Relocation Studio", subtitle: "Astro-cartography techniques", icon: "compass", viewId: "research-relocation" },
```

- [ ] **Step 5: Run typecheck again**

Run: `pnpm --dir apps/web typecheck`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/components/research/RelocationStudio.tsx apps/web/src/config/navConfig.ts
git commit -m "feat(web): RelocationStudio component + nav entry"
```

---

### Task 5: E2E smoke test (`apps/web/e2e/relocation.spec.ts`)

**Files:**
- Create: `apps/web/e2e/relocation.spec.ts`

**Interfaces:**
- Consumes: the rendered page at `/research/relocation` (Tasks 3-4), which calls the live API through the Next.js proxy.
- Produces: Playwright smoke spec. Run manually (requires API + DB), NOT in CI default.

- [ ] **Step 1: Write the spec**

Create `apps/web/e2e/relocation.spec.ts`:

```ts
import { test, expect } from "@playwright/test";

test.describe("Relocation & Astro-Cartography Studio", () => {
  test("loads studio, runs a preset, and renders technique cards", async ({ page }) => {
    await page.goto("/research/relocation");

    await expect(page.locator("h1")).toContainText("Relocation & Astro-Cartography Studio");

    await page.click("button:has-text('Robert Redford → Provo, UT')");
    await page.click("button:has-text('Run Relocation Analysis')");

    await expect(page.locator("text=Angles at Target Location")).toBeVisible({ timeout: 30000 });
    await expect(page.locator("text=Paran Lines (Crossing Lines / X-Marks)")).toBeVisible();
    await expect(page.locator("text=Sun Angular (You Shine)")).toBeVisible();
    await expect(page.locator("text=Midpoints to Angles (Planetary Picture / Isograph)")).toBeVisible();
    await expect(page.locator("text=Harmonic Interpretation (5th / 7th / 9th)")).toBeVisible();
  });
});
```

- [ ] **Step 2: Verify it is collected**

Run: `pnpm --dir apps/web playwright test --list`
Expected: lists `relocation.spec.ts` with 1 test.

Note: executing the e2e test requires the API (`:8000`), Postgres, and the Next.js dev server (`:3000`) running — same prerequisites as every other `e2e/*.spec.ts`. Do not run it in a sandbox without the full stack.

- [ ] **Step 3: Commit**

```bash
git add apps/web/e2e/relocation.spec.ts
git commit -m "test(web): e2e smoke spec for relocation studio"
```

---

## Self-Review Notes

- **Spec coverage:** backend endpoint (Tasks 1-2), frontend page + studio + nav (Tasks 3-4), tests incl. auth-gate + 422 (Task 2), e2e smoke (Task 5), error/loading states (Task 4), presets pre-fill + editable (Task 4), angles + harmonic family shown (Task 4), facts subset exposed (Task 2).
- **Resolver:** the spec originally said `resolve_applicable` with a wildcard objective; the four techniques have distinct objectives, so the plan uses `resolve_by_id` for the explicit four ids (fixed in the spec already).
- **Auth override:** tests use `app.dependency_overrides[require_authenticated] = lambda: {"sub": "test_user"}` matching `test_custom_techniques_api.py`.
- **No placeholders:** every step has concrete code or an exact command.
