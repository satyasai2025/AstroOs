"""
AstroOS — AI Settings Repository

All database I/O for the AISettings aggregate lives here.
Returns domain objects, never ORM models, to callers other than
get_decrypted_api_key (see its docstring for why that one is special).
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.ai_settings import AISettings
from apps.api.domain.user import UserId
from apps.api.models.ai_settings import AISettingsModel
from apps.api.security.encryption import decrypt_secret, encrypt_secret


def _model_to_domain(model: AISettingsModel) -> AISettings:
    return AISettings(
        user_id=UserId(model.user_id),
        provider=model.provider,
        has_api_key=model.api_key_encrypted is not None,
        api_key_last4=model.api_key_last4,
        model=model.model,
        base_url=model.base_url,
        temperature=model.temperature,
        max_tokens=model.max_tokens,
    )


class AISettingsRepository:
    """
    Data access for the per-user AI settings aggregate.

    Constructor accepts an AsyncSession injected by the DI layer.
    No global state; safe for concurrent requests.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_model(self, user_id: UserId) -> Optional[AISettingsModel]:
        stmt = select(AISettingsModel).where(AISettingsModel.user_id == user_id.value)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UserId) -> Optional[AISettings]:
        model = await self._get_model(user_id)
        return _model_to_domain(model) if model else None

    async def get_decrypted_api_key(self, user_id: UserId) -> Optional[str]:
        """
        Internal-only accessor for apps.api.services.ai_provider (the
        outbound AI call resolver). Never call this from a router — the
        public surface only ever returns has_api_key / api_key_last4
        (see AISettings), never the plaintext key.
        """
        model = await self._get_model(user_id)
        if model is None or model.api_key_encrypted is None:
            return None
        return decrypt_secret(model.api_key_encrypted)

    async def upsert(
        self,
        user_id: UserId,
        *,
        provider: str,
        api_key: Optional[str],
        clear_api_key: bool,
        model: Optional[str],
        base_url: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AISettings:
        """
        Create or update the single settings row for this user.

        api_key=None with clear_api_key=False leaves any existing stored
        key untouched — the frontend only ever displays a masked key, so
        it can never legitimately re-send the real one. clear_api_key=True
        (or api_key="") removes the stored key.
        """
        existing = await self._get_model(user_id)
        if existing is None:
            existing = AISettingsModel(user_id=user_id.value)
            self._session.add(existing)

        existing.provider = provider
        existing.model = model
        existing.base_url = base_url
        existing.temperature = temperature
        existing.max_tokens = max_tokens

        if clear_api_key or api_key == "":
            existing.api_key_encrypted = None
            existing.api_key_last4 = None
        elif api_key:
            existing.api_key_encrypted = encrypt_secret(api_key)
            existing.api_key_last4 = api_key[-4:]

        await self._session.flush()
        await self._session.refresh(existing)
        return _model_to_domain(existing)
