"""
AstroOS Observability (Phase II.2 — Local-First)

Structured JSON logging with correlation IDs, lightweight request tracing,
and HTTP request metrics. Designed for the local-first architecture:

- No new runtime dependencies (stdlib + existing prometheus_client only).
- Tracing is W3C Trace Context compatible (`traceparent` header) so it can
  be upgraded to full OpenTelemetry later without changing propagation.
- JSON logs are opt-out: set ASTROOS_JSON_LOGS=0 for plain console logs.

Wire-up (see apps/api/main.py):
    setup_structured_logging()
    app.middleware("http")(observability_middleware)
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterator, Optional

from starlette.requests import Request
from starlette.responses import Response

from apps.api.monitoring import _http_requests, api_request_duration

logger = logging.getLogger(__name__)

# ── Context propagation ──────────────────────────────────────────────────────

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
span_id_var: ContextVar[str] = ContextVar("span_id", default="")

CORRELATION_HEADER = "X-Correlation-ID"
TRACEPARENT_HEADER = "traceparent"


def new_correlation_id() -> str:
    """Generate a short, log-friendly correlation ID."""
    return secrets.token_hex(8)


def get_correlation_id() -> str:
    """Current request's correlation ID ('' outside a request)."""
    return correlation_id_var.get()


# ── W3C Trace Context (traceparent) ──────────────────────────────────────────

def parse_traceparent(value: str) -> Optional[tuple[str, str]]:
    """
    Parse a W3C `traceparent` header → (trace_id, parent_span_id), or None.

    Format: version "-" trace-id(32 hex) "-" parent-id(16 hex) "-" flags
    """
    parts = value.strip().split("-")
    if len(parts) != 4:
        return None
    _, trace_id, parent_id, _ = parts
    if len(trace_id) != 32 or len(parent_id) != 16:
        return None
    try:
        int(trace_id, 16)
        int(parent_id, 16)
    except ValueError:
        return None
    if trace_id == "0" * 32 or parent_id == "0" * 16:
        return None
    return trace_id, parent_id


def make_traceparent(trace_id: str, span_id: str) -> str:
    """Render a W3C `traceparent` header (sampled flag set)."""
    return f"00-{trace_id}-{span_id}-01"


# ── Minimal tracer ───────────────────────────────────────────────────────────

@dataclass
class Span:
    """A single timed operation, logged as a structured event on close."""

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str = ""
    started_at: float = field(default_factory=time.perf_counter)
    attributes: dict[str, Any] = field(default_factory=dict)

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def duration_ms(self) -> float:
        return (time.perf_counter() - self.started_at) * 1000.0


@contextmanager
def start_span(name: str, **attributes: Any) -> Iterator[Span]:
    """
    Start a traced span. Nested spans inherit the current trace and parent.

    Emits a structured log record ("span") on exit with duration_ms and
    error status — locally inspectable, OTel-upgradeable later.
    """
    trace_id = trace_id_var.get() or secrets.token_hex(16)
    parent = span_id_var.get()
    span = Span(
        name=name,
        trace_id=trace_id,
        span_id=secrets.token_hex(8),
        parent_span_id=parent,
        attributes=dict(attributes),
    )
    trace_token = trace_id_var.set(trace_id)
    span_token = span_id_var.set(span.span_id)
    error: Optional[BaseException] = None
    try:
        yield span
    except BaseException as exc:  # re-raised; recorded first
        error = exc
        raise
    finally:
        span_id_var.reset(span_token)
        trace_id_var.reset(trace_token)
        logger.info(
            "span",
            extra={
                "span_name": span.name,
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "duration_ms": round(span.duration_ms(), 3),
                "span_status": "error" if error else "ok",
                **{f"attr_{k}": v for k, v in span.attributes.items()},
            },
        )


# ── Structured JSON logging ──────────────────────────────────────────────────

_RESERVED = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
) | {"message", "asctime", "taskName"}


class JsonLogFormatter(logging.Formatter):
    """Format log records as single-line JSON with correlation/trace context."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        cid = correlation_id_var.get()
        if cid:
            payload["correlation_id"] = cid
        tid = trace_id_var.get()
        if tid and "trace_id" not in record.__dict__:
            payload["trace_id"] = tid
        # Merge `extra={...}` fields.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def setup_structured_logging(level: int = logging.INFO) -> None:
    """
    Install the JSON formatter on the root logger.

    Opt-out for plain local development: ASTROOS_JSON_LOGS=0.
    Idempotent — safe to call more than once.
    """
    if os.environ.get("ASTROOS_JSON_LOGS", "1") in ("0", "false", "no"):
        logging.basicConfig(level=level)
        return
    root = logging.getLogger()
    root.setLevel(level)
    for handler in root.handlers:
        if getattr(handler, "_astroos_json", False):
            return  # already installed
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    handler._astroos_json = True  # type: ignore[attr-defined]
    root.handlers = [handler]


# ── HTTP middleware: correlation + metrics + request span ────────────────────

async def observability_middleware(
    request: Request, call_next: Callable
) -> Response:
    """
    Per-request observability:

    - Accepts/creates X-Correlation-ID; echoes it on the response.
    - Accepts/creates W3C traceparent; echoes the request's own span.
    - Records Prometheus request count + duration (existing Phase H metrics).
    - Emits one structured "http_request" log line per request.
    """
    cid = request.headers.get(CORRELATION_HEADER) or new_correlation_id()
    cid_token = correlation_id_var.set(cid)

    incoming = request.headers.get(TRACEPARENT_HEADER, "")
    parsed = parse_traceparent(incoming) if incoming else None
    trace_id = parsed[0] if parsed else secrets.token_hex(16)
    parent_span_id = parsed[1] if parsed else ""
    span_id = secrets.token_hex(8)
    trace_token = trace_id_var.set(trace_id)
    span_token = span_id_var.set(span_id)

    endpoint = request.url.path
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.perf_counter() - started
        _http_requests.labels(method=request.method, endpoint=endpoint).inc()
        api_request_duration.labels(
            endpoint=endpoint, status_code=str(status_code)
        ).observe(duration)
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": endpoint,
                "status_code": status_code,
                "duration_ms": round(duration * 1000.0, 3),
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
                "client": request.client.host if request.client else "",
            },
        )
        span_id_var.reset(span_token)
        trace_id_var.reset(trace_token)
        correlation_id_var.reset(cid_token)
        if "response" in locals():
            response.headers[CORRELATION_HEADER] = cid
            response.headers[TRACEPARENT_HEADER] = make_traceparent(
                trace_id, span_id
            )
