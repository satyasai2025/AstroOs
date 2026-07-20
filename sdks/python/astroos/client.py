"""AstroOS API client — v2.2.0.

Covers chart computation, dashas, divisional charts, events, AI, yoga,
transit, timeline, reports, export, knowledge, knowledge-graph, research,
and benchmark endpoints.
"""

from __future__ import annotations

import time
from typing import Any, Optional
from urllib.parse import urljoin

from .config import SdkConfig


# ── Internal helpers ───────────────────────────────────────────────────────────

class _APIBase:
    """Base class for API method groups."""

    def __init__(self, client: "AstroOSClient") -> None:
        self._client = client


def _ensure_base_url_trailing_slash(url: str) -> str:
    """Return *url* with exactly one trailing slash so ``urljoin`` works."""
    return url.rstrip("/") + "/"


def _url(base_url: str, path: str) -> str:
    """Join *path* (e.g. ``/horoscope/d1``) onto the *base_url*."""
    return urljoin(base_url, path.lstrip("/"))


# ── API method groups ──────────────────────────────────────────────────────────

class _AuthAPI(_APIBase):
    def register(self, email: str, password: str, display_name: str) -> dict[str, Any]:
        return self._client._post("/auth/register", json={
            "email": email, "password": password, "display_name": display_name,
        })

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._client._post("/auth/login", json={
            "email": email, "password": password,
        })

    def me(self) -> dict[str, Any]:
        return self._client._get("/auth/me")


class _ChartAPI(_APIBase):
    def compute(
        self, birth_datetime_utc: str, latitude: float, longitude: float,
        ayanamsa: str = "lahiri", house_system: str = "W",
    ) -> dict[str, Any]:
        return self._client._post("/horoscope/d1", json={
            "birth_datetime_utc": birth_datetime_utc,
            "latitude": latitude, "longitude": longitude,
            "ayanamsa": ayanamsa, "house_system": house_system,
        })


class _DivisionalAPI(_APIBase):
    def compute(
        self, varga: str, birth_datetime_utc: str, latitude: float,
        longitude: float, ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> dict[str, Any]:
        return self._client._post(f"/divisional/{varga}", json={
            "birth_datetime_utc": birth_datetime_utc,
            "latitude": latitude, "longitude": longitude,
            "ayanamsa": ayanamsa, "house_system": house_system,
        })

    def compute_all(
        self, birth_datetime_utc: str, latitude: float,
        longitude: float, ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> dict[str, Any]:
        return self._client._post("/divisional/all", json={
            "birth_datetime_utc": birth_datetime_utc,
            "latitude": latitude, "longitude": longitude,
            "ayanamsa": ayanamsa, "house_system": house_system,
        })


class _DashaAPI(_APIBase):
    def compute(
        self, system: str, birth_datetime_utc: str, latitude: float,
        longitude: float, ayanamsa: str = "lahiri",
        house_system: str = "W", max_depth: int = 3,
    ) -> dict[str, Any]:
        return self._client._post(f"/dasha/{system}", json={
            "birth_datetime_utc": birth_datetime_utc,
            "latitude": latitude, "longitude": longitude,
            "ayanamsa": ayanamsa, "house_system": house_system,
            "max_depth": max_depth,
        })


class _EventsAPI(_APIBase):
    def list(self, chart_id: str, category: Optional[str] = None) -> dict[str, Any]:
        params: dict[str, Any] = {"chart_id": chart_id}
        if category:
            params["category"] = category
        return self._client._get("/events", params=params)

    def create(self, chart_id: str, event_date: str, title: str, **kw: Any) -> dict[str, Any]:
        return self._client._post("/events", json={
            "chart_id": chart_id, "event_date": event_date, "title": title, **kw,
        })

    def get(self, event_id: str) -> dict[str, Any]:
        return self._client._get(f"/events/{event_id}")

    def update(self, event_id: str, **kw: Any) -> dict[str, Any]:
        return self._client._patch(f"/events/{event_id}", json=kw)

    def delete(self, event_id: str) -> None:
        self._client._delete(f"/events/{event_id}")


class _AIAPI(_APIBase):
    def chart_summary(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ai/chart-summary", json=birth_data)

    def explain_yoga(self, yoga_id: str, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post(f"/ai/explain-yoga/{yoga_id}", json=birth_data)

    def interpret_dasha(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ai/interpret-dasha", json=birth_data)

    def read_transit(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ai/read-transit", json=birth_data)

    def answer_question(self, question: str, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ai/answer-question", json={
            "question": question, **birth_data,
        })

    def enhanced_qa(self, question: str, chart_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ai/enhanced-qa", json={
            "question": question, **chart_data,
        })

    def compare_charts(self, chart_a: dict[str, Any], chart_b: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ai/compare-charts", json={
            "chart_a": chart_a, "chart_b": chart_b,
        })

    def research_query(self, query: str, domains: Optional[list[str]] = None) -> dict[str, Any]:
        return self._client._post("/ai/research-query", json={
            "query": query, "domains": domains or [],
        })

    def generate_hypotheses(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ai/generate-hypotheses", json=birth_data)


class _YogaAPI(_APIBase):
    def catalog(self) -> dict[str, Any]:
        return self._client._get("/yoga/catalog")

    def evaluate(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/yoga/evaluate", json=birth_data)

    def evaluate_with_strength(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/yoga/evaluate/with-strength", json=birth_data)

    def evaluate_timeline(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/yoga/evaluate/timeline", json=birth_data)


class _TransitAPI(_APIBase):
    def compute(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/transit", json=birth_data)


class _TimelineAPI(_APIBase):
    def compute(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/timeline", json=birth_data)


class _ShadbalaAPI(_APIBase):
    def compute(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/shadbala", json=birth_data)


class _AshtakavargaAPI(_APIBase):
    def compute(self, birth_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ashtakavarga", json=birth_data)


class _ReportsAPI(_APIBase):
    def generate_chart(self, **data: Any) -> dict[str, Any]:
        return self._client._post("/report/chart", json=data)

    def generate_pdf(self, **data: Any) -> bytes:
        return self._client._download("/report/chart/pdf", json=data, accept="application/pdf")

    def generate_csv(self, **data: Any) -> str:
        return self._client._download("/report/chart/csv", json=data, accept="text/csv")

    def list_templates(self) -> list[str]:
        return self._client._get("/report/templates")


class _ExportAPI(_APIBase):
    def export_project(
        self, project_id: str, fmt: str = "json",
    ) -> dict[str, Any]:
        return self._client._post(f"/research/export/{project_id}", json={"format": fmt})


class _KnowledgeAPI(_APIBase):
    def search(self, query: str, domain: Optional[str] = None) -> dict[str, Any]:
        return self._client._get("/knowledge/search", params={
            "q": query, "domain": domain,
        })

    def get_book(self, book_id: str) -> dict[str, Any]:
        return self._client._get(f"/knowledge/books/{book_id}")


class _KnowledgeGraphAPI(_APIBase):
    def get_entity(self, entity_id: str) -> dict[str, Any]:
        return self._client._get(f"/knowledge-graph/entity/{entity_id}")

    def relationships(self, **params: Any) -> dict[str, Any]:
        return self._client._get("/knowledge-graph/relationships", params=params if params else None)


class _ResearchAPI(_APIBase):
    def list_projects(self) -> dict[str, Any]:
        return self._client._get("/research/projects")

    def create_project(self, name: str, description: str = "") -> dict[str, Any]:
        return self._client._post("/research/projects", json={
            "name": name, "description": description,
        })

    def get_project(self, project_id: str) -> dict[str, Any]:
        return self._client._get(f"/research/projects/{project_id}")


class _BatchAPI(_APIBase):
    def submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/batch/chart-reports", json=payload)

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._client._get(f"/jobs/{job_id}")

    def list_jobs(self) -> dict[str, Any]:
        return self._client._get("/jobs")

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        return self._client._post(f"/jobs/{job_id}/cancel")


# ── Main client ────────────────────────────────────────────────────────────────

class AstroOSClient:
    """
    Client for the AstroOS v2 API.

    Usage::

        client = AstroOSClient(api_key="...")
        chart = client.chart.compute(
            birth_datetime_utc="1986-06-15T10:30:00+00:00",
            latitude=28.6139, longitude=77.2090,
        )
        yogas = client.yoga.evaluate_with_strength(chart)
        pdf = client.reports.generate_pdf(**chart)

    See the full API reference at ``docs/api-reference.md``.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        config: Optional[SdkConfig] = None,
    ) -> None:
        self._config = config or SdkConfig(
            api_key=api_key, access_token=access_token,
        )
        self._session: Any = None

        # API method groups.
        self.auth = _AuthAPI(self)
        self.chart = _ChartAPI(self)
        self.divisional = _DivisionalAPI(self)
        self.dasha = _DashaAPI(self)
        self.events = _EventsAPI(self)
        self.ai = _AIAPI(self)
        self.yoga = _YogaAPI(self)
        self.transit = _TransitAPI(self)
        self.timeline = _TimelineAPI(self)
        self.shadbala = _ShadbalaAPI(self)
        self.ashtakavarga = _AshtakavargaAPI(self)
        self.reports = _ReportsAPI(self)
        self.export = _ExportAPI(self)
        self.knowledge = _KnowledgeAPI(self)
        self.knowledge_graph = _KnowledgeGraphAPI(self)
        self.research = _ResearchAPI(self)
        self.batch = _BatchAPI(self)

    @property
    def base_url(self) -> str:
        return self._config.base_url

    # -- low-level request helpers ------------------------------------------------

    def _request(
        self, method: str, path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Any:
        """Make an HTTP request with retry logic."""
        url = _url(self.base_url, path)
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._config.api_key:
            headers["x-api-key"] = self._config.api_key
        if self._config.access_token:
            headers["Authorization"] = f"Bearer {self._config.access_token}"

        last_error: Optional[Exception] = None
        for attempt in range(self._config.retry_count):
            try:
                import httpx
                with httpx.Client(timeout=self._config.timeout) as client:
                    response = client.request(
                        method, url, json=json, params=params, headers=headers,
                    )
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data = response.json()
                        if isinstance(data, dict) and "success" in data:
                            return data
                        return {"success": True, "data": data}
                    return {"success": True, "data": response.text}
            except Exception as e:
                last_error = e
                if attempt < self._config.retry_count - 1:
                    time.sleep(self._config.retry_backoff ** attempt)
        raise last_error  # type: ignore[union-attr]

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, json: Optional[dict] = None) -> Any:
        return self._request("POST", path, json=json)

    def _patch(self, path: str, json: Optional[dict] = None) -> Any:
        return self._request("PATCH", path, json=json)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def _download(self, path: str, json: Optional[dict] = None, accept: str = "application/pdf") -> bytes:
        """Download binary content."""
        import httpx
        url = _url(self.base_url, path)
        headers: dict[str, str] = {"Accept": accept}
        if self._config.api_key:
            headers["x-api-key"] = self._config.api_key
        with httpx.Client(timeout=self._config.timeout) as client:
            response = client.request("POST", url, json=json, headers=headers)
            response.raise_for_status()
            return response.content
