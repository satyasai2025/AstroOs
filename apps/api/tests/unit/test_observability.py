"""Unit tests for apps/api/observability.py (Phase II.2 — local-first)."""

import json
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.observability import (
    CORRELATION_HEADER,
    TRACEPARENT_HEADER,
    JsonLogFormatter,
    correlation_id_var,
    make_traceparent,
    new_correlation_id,
    observability_middleware,
    parse_traceparent,
    start_span,
)


# ── traceparent ──────────────────────────────────────────────────────────────

def test_parse_traceparent_valid():
    tp = "00-" + "ab" * 16 + "-" + "cd" * 8 + "-01"
    parsed = parse_traceparent(tp)
    assert parsed == ("ab" * 16, "cd" * 8)


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "garbage",
        "00-short-cdcdcdcdcdcdcdcd-01",
        "00-" + "0" * 32 + "-" + "cd" * 8 + "-01",  # all-zero trace id
        "00-" + "ab" * 16 + "-" + "0" * 16 + "-01",  # all-zero span id
        "00-" + "zz" * 16 + "-" + "cd" * 8 + "-01",  # non-hex
    ],
)
def test_parse_traceparent_invalid(bad):
    assert parse_traceparent(bad) is None


def test_make_traceparent_roundtrip():
    trace_id, span_id = "ab" * 16, "cd" * 8
    assert parse_traceparent(make_traceparent(trace_id, span_id)) == (
        trace_id,
        span_id,
    )


# ── JSON formatter ───────────────────────────────────────────────────────────

def test_json_formatter_includes_extras_and_correlation():
    token = correlation_id_var.set("test-cid-123")
    try:
        record = logging.LogRecord(
            "astroos.test", logging.INFO, __file__, 1, "hello %s", ("world",), None
        )
        record.custom_field = 42
        out = json.loads(JsonLogFormatter().format(record))
    finally:
        correlation_id_var.reset(token)
    assert out["message"] == "hello world"
    assert out["level"] == "INFO"
    assert out["correlation_id"] == "test-cid-123"
    assert out["custom_field"] == 42
    assert "ts" in out


def test_json_formatter_is_single_line():
    record = logging.LogRecord(
        "astroos.test", logging.WARNING, __file__, 1, "multi\nline", (), None
    )
    assert "\n" not in JsonLogFormatter().format(record)


# ── spans ────────────────────────────────────────────────────────────────────

def test_start_span_nesting_and_logging(caplog):
    with caplog.at_level(logging.INFO, logger="apps.api.observability"):
        with start_span("outer") as outer:
            with start_span("inner", engine="yoga") as inner:
                assert inner.trace_id == outer.trace_id
                assert inner.parent_span_id == outer.span_id
    span_logs = [r for r in caplog.records if r.getMessage() == "span"]
    assert len(span_logs) == 2
    inner_rec = next(r for r in span_logs if r.span_name == "inner")
    assert inner_rec.span_status == "ok"
    assert inner_rec.attr_engine == "yoga"
    assert inner_rec.duration_ms >= 0


def test_start_span_records_error_status(caplog):
    with caplog.at_level(logging.INFO, logger="apps.api.observability"):
        with pytest.raises(ValueError):
            with start_span("failing"):
                raise ValueError("boom")
    rec = next(r for r in caplog.records if r.getMessage() == "span")
    assert rec.span_status == "error"


# ── middleware ───────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    app = FastAPI()
    app.middleware("http")(observability_middleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True, "cid": correlation_id_var.get()}

    return TestClient(app)


def test_middleware_generates_correlation_id(client):
    resp = client.get("/ping")
    assert resp.status_code == 200
    cid = resp.headers[CORRELATION_HEADER]
    assert len(cid) == 16
    assert resp.json()["cid"] == cid  # visible inside the request context


def test_middleware_echoes_provided_correlation_id(client):
    resp = client.get("/ping", headers={CORRELATION_HEADER: "my-id-42"})
    assert resp.headers[CORRELATION_HEADER] == "my-id-42"


def test_middleware_continues_incoming_trace(client):
    trace_id = "ab" * 16
    resp = client.get(
        "/ping",
        headers={TRACEPARENT_HEADER: make_traceparent(trace_id, "cd" * 8)},
    )
    parsed = parse_traceparent(resp.headers[TRACEPARENT_HEADER])
    assert parsed is not None
    assert parsed[0] == trace_id  # same trace continued
    assert parsed[1] != "cd" * 8  # new span for this request


def test_middleware_records_metrics(client):
    from prometheus_client import REGISTRY

    before = (
        REGISTRY.get_sample_value(
            "http_requests_total", {"method": "GET", "endpoint": "/ping"}
        )
        or 0
    )
    client.get("/ping")
    after = REGISTRY.get_sample_value(
        "http_requests_total", {"method": "GET", "endpoint": "/ping"}
    )
    assert after == before + 1


def test_new_correlation_id_unique():
    assert new_correlation_id() != new_correlation_id()
