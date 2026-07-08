---
name: AstroOS refresh token replay guard
description: Atomic single-use enforcement for refresh tokens via conditional UPDATE WHERE revoked_at IS NULL + RETURNING.
---

## Rule
`UserRepository.revoke_session_by_jti()` must use a conditional UPDATE (`WHERE revoked_at IS NULL`) with `RETURNING` to atomically claim the revocation. Callers check the bool return value before issuing new tokens.

## Why
Without an atomic guard, two concurrent requests with the same refresh token can both read `revoked_at IS NULL`, both revoke, and both receive new valid tokens — a refresh replay attack. The conditional UPDATE is serialized by PostgreSQL row-level locking, ensuring only one caller gets `True`.

## How to apply
```python
async def revoke_session_by_jti(self, jti: str) -> bool:
    now = datetime.now(timezone.utc)
    stmt = (
        update(UserSessionModel)
        .where(UserSessionModel.refresh_token_jti == jti)
        .where(UserSessionModel.revoked_at.is_(None))  # atomic guard
        .values(revoked_at=now)
        .returning(UserSessionModel.id)
    )
    result = await self._session.execute(stmt)
    return result.scalar_one_or_none() is not None
```

In `AuthService.refresh_tokens()`:
```python
revoked = await self._user_repo.revoke_session_by_jti(jti)
if not revoked:
    raise AuthError("Refresh token is invalid or has already been used.")
```
Always check the return value. Never proceed to issue new tokens if `revoked` is `False`.
