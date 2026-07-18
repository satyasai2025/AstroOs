"""AstroOS API - Rate Limiting Middleware (Phase M3)"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI

# Global limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour", "10/minute"],
)


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting middleware on FastAPI app."""
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)


def get_limiter() -> Limiter:
    """Retrieve the global limiter instance."""
    return limiter