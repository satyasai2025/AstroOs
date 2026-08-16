"""
AstroOS — User Repository

All database I/O for the User aggregate lives here.
Returns domain objects, never ORM models.
Service layer never imports SQLAlchemy directly.

Fix log (post code-review):
  - revoke_session_by_jti now uses an atomic conditional UPDATE
    (WHERE revoked_at IS NULL + RETURNING id) to guard against
    concurrent refresh-token replay attacks.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.models.user import PasswordResetTokenModel, UserModel, UserSessionModel


def _capitalize_name(name: str) -> str:
    """Capitalize each word in a name string."""
    return " ".join(word.capitalize() for word in name.strip().split())


def _model_to_domain(model: UserModel) -> User:
    """Convert ORM row → domain User. Explicit, not magic."""
    return User(
        id=UserId(model.id),
        email=model.email,
        display_name=_capitalize_name(model.display_name),
        hashed_password=model.hashed_password,
        role=UserRole(model.role),
        status=UserStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_login_at=model.last_login_at,
        deleted_at=model.deleted_at,
        timezone=model.timezone,
    )


class UserRepository:
    """
    Data access for the User aggregate.

    Constructor accepts an AsyncSession injected by the DI layer.
    No global state; safe for concurrent requests.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id.value)
            .where(UserModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_domain(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(UserModel)
            .where(UserModel.email == email.lower().strip())
            .where(UserModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_domain(row) if row else None

    async def email_exists(self, email: str) -> bool:
        stmt = select(UserModel.id).where(
            UserModel.email == email.lower().strip()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        email: str,
        display_name: str,
        hashed_password: str,
        role: UserRole = UserRole.RESEARCHER,
    ) -> User:
        model = UserModel(
            email=email.lower().strip(),
            display_name=_capitalize_name(display_name),
            hashed_password=hashed_password,
            role=role,
            status=UserStatus.ACTIVE,
        )
        self._session.add(model)
        await self._session.flush()  # populate id + timestamps from DB
        await self._session.refresh(model)
        return _model_to_domain(model)

    async def update_last_login(self, user_id: UserId, now: datetime) -> None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id.value)
            .values(last_login_at=now)
        )
        await self._session.execute(stmt)

    async def create_session(
        self,
        user_id: UserId,
        refresh_token_jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSessionModel:
        session_model = UserSessionModel(
            user_id=user_id.value,
            refresh_token_jti=refresh_token_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(session_model)
        await self._session.flush()
        await self._session.refresh(session_model)
        return session_model

    async def get_session_by_jti(self, jti: str) -> Optional[UserSessionModel]:
        stmt = select(UserSessionModel).where(
            UserSessionModel.refresh_token_jti == jti
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_session_by_jti(self, jti: str) -> bool:
        """
        Atomically mark a session as revoked.

        Uses a conditional UPDATE (WHERE revoked_at IS NULL) + RETURNING
        so that only one concurrent caller can succeed. The caller that
        performs the update receives True; all others receive False.

        This is the primary guard against refresh-token replay attacks
        under concurrent requests.

        Returns:
            True  — session was active and has now been revoked by this call.
            False — session was already revoked or does not exist.
        """
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

    async def revoke_all_sessions(self, user_id: UserId) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(UserSessionModel)
            .where(UserSessionModel.user_id == user_id.value)
            .where(UserSessionModel.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self._session.execute(stmt)

    # ── Password reset ────────────────────────────────────────────────────────

    async def update_password(self, user_id: UserId, hashed_password: str) -> None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id.value)
            .values(hashed_password=hashed_password)
        )
        await self._session.execute(stmt)

    async def update_profile(
        self,
        user_id: UserId,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update a user's own display_name, email, and/or timezone.

        Only non-None fields are changed. Returns the updated User, or None
        if no matching (non-deleted) user exists.
        """
        values: dict = {}
        if display_name is not None:
            values["display_name"] = _capitalize_name(display_name)
        if email is not None:
            values["email"] = email.lower().strip()
        if timezone is not None:
            values["timezone"] = timezone

        if not values:
            return await self.get_by_id(user_id)

        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id.value)
            .where(UserModel.deleted_at.is_(None))
            .values(**values)
            .returning(UserModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_by_id(user_id)

    async def create_reset_token(
        self,
        user_id: UserId,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetTokenModel:
        model = PasswordResetTokenModel(
            user_id=user_id.value,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def consume_reset_token(self, token_hash: str) -> Optional[uuid.UUID]:
        """
        Atomically mark a reset token as used and return the user_id it
        belonged to, or None if it doesn't exist / is expired / was already
        used.

        Same single-use guard as revoke_session_by_jti: a conditional
        UPDATE (WHERE used_at IS NULL) + RETURNING so only one concurrent
        caller can succeed — prevents the same reset link being replayed.
        Returning user_id from the same atomic statement (rather than a
        separate lookup) avoids a check-then-act race between validating
        the token and consuming it.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.token_hash == token_hash)
            .where(PasswordResetTokenModel.used_at.is_(None))
            .where(PasswordResetTokenModel.expires_at > now)
            .values(used_at=now)
            .returning(PasswordResetTokenModel.user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Admin listing/moderation ──────────────────────────────────────────
    # Moved here from AdminEngine (Phase 10 R3 cleanup, 2026-07-23) — that
    # engine was querying UserModel directly with a raw session, the one
    # place in the codebase that bypassed the repository layer every other
    # engine uses. Behavior is unchanged, just relocated so DB access for
    # the User aggregate lives in exactly one place.

    @staticmethod
    def _filtered_users_stmt(status: Optional[str], role: Optional[str]):
        """Shared status/role filter for list_all/count_all, so a caller's
        pagination total always reflects the exact same WHERE clause as
        the page it's counting."""
        stmt = select(UserModel).where(UserModel.deleted_at.is_(None))
        if status:
            stmt = stmt.where(UserModel.status == status)
        if role:
            stmt = stmt.where(UserModel.role == role)
        return stmt

    async def list_all(
        self,
        *,
        status: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        stmt = (
            self._filtered_users_stmt(status, role)
            .order_by(UserModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_model_to_domain(row) for row in result.scalars().all()]

    async def count_all(
        self,
        *,
        status: Optional[str] = None,
        role: Optional[str] = None,
    ) -> int:
        stmt = self._filtered_users_stmt(status, role)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self._session.execute(count_stmt)
        return result.scalar_one()

    async def set_role(self, user_id: UserId, new_role: UserRole) -> Optional[User]:
        """Atomic role update. Returns the updated User, or None if no
        matching (non-deleted) user exists."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id.value, UserModel.deleted_at.is_(None))
            .values(role=new_role)
            .returning(UserModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_by_id(user_id)

    async def set_status(self, user_id: UserId, new_status: UserStatus) -> bool:
        """Atomic status update (used for suspend/activate). Returns
        whether a matching (non-deleted) user was found and updated."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id.value, UserModel.deleted_at.is_(None))
            .values(status=new_status)
            .returning(UserModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
