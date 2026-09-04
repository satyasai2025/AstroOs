"""
AstroOS — Secrets-at-rest Encryption

Symmetric encryption for values stored in the database that must be
recoverable in plaintext later (unlike passwords, which are one-way
hashed) — currently just per-user AI provider API keys in ai_settings.

Fernet (AES-128-CBC + HMAC-SHA256, from the `cryptography` package) rather
than a hand-rolled scheme: it's authenticated (tampering is detected, not
just decrypted into garbage) and versioned (the token embeds enough info
to reject keys encrypted under a different ENCRYPTION_KEY cleanly).
"""

from cryptography.fernet import Fernet, InvalidToken

from apps.api.config import get_settings

_settings = get_settings()
_fernet = Fernet(_settings.ENCRYPTION_KEY.encode("utf-8"))


class DecryptionError(RuntimeError):
    """Raised when a stored secret can't be decrypted (wrong/rotated key, corrupted data)."""


def encrypt_secret(plaintext: str) -> str:
    """Encrypt *plaintext*, returning an opaque token safe to store as text."""
    return _fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Decrypt a token produced by encrypt_secret. Raises DecryptionError on failure."""
    try:
        return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise DecryptionError("Stored secret could not be decrypted.") from exc
