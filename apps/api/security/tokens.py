"""
AstroOS — Opaque Token Generation

For secrets that are compared by exact match rather than decoded (password
reset links), not JWTs. secrets.token_urlsafe already carries 256 bits of
entropy, so hashing it with bcrypt's deliberately-slow KDF would add
latency with no security benefit — SHA-256 is the correct primitive here.
"""

import hashlib
import secrets


def generate_reset_token() -> str:
    """Return a new URL-safe, single-use password-reset token."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Return the SHA-256 hex digest of *token*, for storage/lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
