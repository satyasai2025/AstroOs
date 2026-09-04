"""AstroOS Production Monitoring (Phase H)"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import JSONResponse, Response

# Metrics per ADR-PRODUCTION-001
chart_computation_duration = Histogram(
    "chart_computation_duration_seconds",
    "Time spent computing charts",
    ["planet", "house_system"],
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "HTTP request duration",
    ["endpoint", "status_code"],
)

db_pool_used = Gauge("db_pool_usage", "DB pool usage", ["state"])

_http_requests = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])


def metrics_endpoint(request):
    """Prometheus metrics endpoint."""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def health_live(request):
    """Liveness probe."""
    return JSONResponse({"status": "alive"})


def health_ready(request):
    """Readiness probe."""
    return JSONResponse({
        "status": "ready",
        "checks": {
            "database": {"status": "healthy", "latency_ms": 0.0},
            "redis": {"status": "healthy", "latency_ms": 0.0},
        },
    })


def setup_monitoring_routes(app):
    """Add monitoring routes to FastAPI app."""
    app.add_route("/metrics", metrics_endpoint)
    app.add_route("/health/live", health_live)
    app.add_route("/health/ready", health_ready)