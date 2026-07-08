"""
AstroOS — Password Hashing

Direct bcrypt wrapper — no passlib layer.
passlib < 1.8 has a hard incompatibility with bcrypt >= 4.0 (its internal
`detect_wrap_bug` probe sends a 73-byte password that bcrypt 4+ rejects).

Using bcrypt directly:
- hash_password  : one-way bcrypt hash with configurable cost factor.
- verify_password: constant-time comparison.

Both raise no exceptions for normal inputs; callers should treat
verify_password returning False as the failure signal.
"""

import bcrypt

from apps.api.config import get_settings

_settings = get_settings()


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain* at the configured cost factor."""
    cost = _settings.BCRYPT_ROUNDS
    salt = bcrypt.gensalt(rounds=cost)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Return True iff *plain* matches *hashed*.

    bcrypt.checkpw performs constant-time comparison.
    Returns False (never raises) for any mismatch, including malformed hashes.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        # Malformed hash stored in DB, legacy algorithm, encoding error, etc.
        # Always return False — never expose internal error details.
        return False
