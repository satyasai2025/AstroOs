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

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.models.user import UserModel, UserSessionModel


def _model_to_domain(model: UserModel) -> User:
    """Convert ORM row → domain User. Explicit, not magic."""
    return User(
        id=UserId(model.id),
        email=model.email,
        display_name=model.display_name,
        hashed_password=model.hashed_password,
        role=UserRole(model.role),
        status=UserStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_login_at=model.last_login_at,
        deleted_at=model.deleted_at,
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
            display_name=display_name.strip(),
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
