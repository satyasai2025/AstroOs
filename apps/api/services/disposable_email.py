"""
AstroOS — Disposable Email Detection

Blocks registration with throwaway/temporary email addresses (Mailinator,
10minutemail, etc.) using a local, offline blocklist — no third-party
verification API, no network call, no per-check cost.

EXTRA_BLOCKED_DOMAINS covers anything the upstream package hasn't picked up
yet; add to it directly rather than waiting on a package release.
"""

from disposable_email_domains import blocklist

EXTRA_BLOCKED_DOMAINS: frozenset[str] = frozenset({
    "aghism.com",
})


def is_disposable_email(email: str) -> bool:
    """Return True if *email*'s domain is a known disposable-email provider."""
    if "@" not in email:
        return False
    domain = email.rsplit("@", 1)[1].strip().lower()
    return domain in blocklist or domain in EXTRA_BLOCKED_DOMAINS
