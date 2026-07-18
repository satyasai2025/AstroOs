"""AstroOS API client."""

from __future__ import annotations

import time
from typing import Any, Optional
from urllib.parse import urljoin

from .config import SdkConfig


class _APIBase:
    """Base class for API method groups."""

    def __init__(self, client: "AstroOSClient") -> None:
        self._client = client


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

    def delete(self, event_id: str) -> None:
        self._client._delete(f"/events/{event_id}")


class _AIAPI(_APIBase):
    def explain(self, topic: str, source_data: dict[str, Any]) -> dict[str, Any]:
        return self._client._post("/ai/explain", json={
            "topic": topic, "source_data": source_data,
        })


class _ReportsAPI(_APIBase):
    def generate_chart(self, **data: Any) -> dict[str, Any]:
        return self._client._post("/report/chart", json=data)

    def generate_pdf(self, **data: Any) -> bytes:
        return self._client._download("/report/chart/pdf", json=data)

    def generate_csv(self, **data: Any) -> str:
        return self._client._get("/report/chart/csv", params=data)

    def list_templates(self) -> list[str]:
        return self._client._get("/report/templates")


class AstroOSClient:
    """
    Client for the AstroOS API.

    Usage:
        client = AstroOSClient(api_key="...")
        chart = client.chart.compute(...)
        events = client.events.list(chart_id=...)
        pdf = client.reports.generate_pdf(...)
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
        self.dasha = _DashaAPI(self)
        self.events = _EventsAPI(self)
        self.ai = _AIAPI(self)
        self.reports = _ReportsAPI(self)

    @property
    def base_url(self) -> str:
        return self._config.base_url

    def _request(
        self, method: str, path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Any:
        """Make an HTTP request with retry logic."""
        url = urljoin(self.base_url, path.lstrip("/"))
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
                    data = response.json()
                    if isinstance(data, dict) and "success" in data:
                        return data
                    return {"success": True, "data": data}
            except Exception as e:
                last_error = e
                if attempt < self._config.retry_count - 1:
                    time.sleep(self._config.retry_backoff ** attempt)
        raise last_error  # type: ignore

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, json: Optional[dict] = None) -> Any:
        return self._request("POST", path, json=json)

    def _download(self, path: str, json: Optional[dict] = None) -> bytes:
        """Download binary content."""
        import httpx
        url = urljoin(self.base_url, path.lstrip("/"))
        headers: dict[str, str] = {
            "Accept": "application/pdf",
        }
        if self._config.api_key:
            headers["x-api-key"] = self._config.api_key
        with httpx.Client(timeout=self._config.timeout) as client:
            response = client.request("POST", url, json=json, headers=headers)
            response.raise_for_status()
            return response.content

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)
