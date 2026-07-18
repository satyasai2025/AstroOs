"""AstroOS Python SDK — Exceptions (Phase G)"""

from __future__ import annotations


class AstroOSError(Exception):
    """Base SDK error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AstroOSAuthError(AstroOSError):
    """Authentication failed."""


class AstroOSValidationError(AstroOSError):
    """Request validation failed."""


class AstroOSRateLimitError(AstroOSError):
    """Rate limit exceeded."""


class AstroOSServerError(AstroOSError):
    """Server error response."""


class AstroOSNotFoundError(AstroOSError):
    """Resource not found."""