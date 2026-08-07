"""
AstroOS — AI Settings Router

HTTP adapter layer. Delegates all logic to AISettingsService.
No business logic lives here — only request parsing, domain→schema
conversion, and HTTP error mapping.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.api.dependencies import get_ai_settings_service, get_current_user_from_bearer
from apps.api.domain.ai_settings import AISettings
from apps.api.domain.user import User
from apps.api.schemas.ai_settings import (
    AISettingsResponse,
    TestAISettingsRequest,
    TestConnectionResponse,
    UpdateAISettingsRequest,
)
from apps.api.services.ai_settings_service import AISettingsError, AISettingsService

router = APIRouter(prefix="/ai/settings", tags=["ai-settings"])


def _handle_ai_settings_error(exc: AISettingsError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


def _to_response(settings: AISettings) -> AISettingsResponse:
    return AISettingsResponse(
        provider=settings.provider,
        has_api_key=settings.has_api_key,
        api_key_last4=settings.api_key_last4,
        model=settings.model,
        base_url=settings.base_url,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )


@router.get("", response_model=AISettingsResponse, summary="Get the current user's AI settings.")
async def get_ai_settings(
    current_user: User = Depends(get_current_user_from_bearer),
    service: AISettingsService = Depends(get_ai_settings_service),
) -> AISettingsResponse:
    settings = await service.get_settings(current_user.id)
    return _to_response(settings)


@router.put("", response_model=AISettingsResponse, summary="Update the current user's AI settings.")
async def update_ai_settings(
    body: UpdateAISettingsRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    service: AISettingsService = Depends(get_ai_settings_service),
) -> AISettingsResponse:
    try:
        settings = await service.update_settings(
            current_user.id,
            provider=body.provider,
            api_key=body.api_key,
            clear_api_key=False,
            model=body.model,
            base_url=body.base_url,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except AISettingsError as exc:
        raise _handle_ai_settings_error(exc) from exc
    return _to_response(settings)


@router.post(
    "/test",
    response_model=TestConnectionResponse,
    summary="Test connectivity to the given (or already-stored) AI provider settings.",
)
async def test_ai_settings(
    body: TestAISettingsRequest,
    request: Request,
    current_user: User = Depends(get_current_user_from_bearer),
    service: AISettingsService = Depends(get_ai_settings_service),
) -> TestConnectionResponse:
    try:
        result = await service.test_connection(
            current_user.id,
            request.app.state.http_client,
            provider=body.provider,
            api_key=body.api_key,
            model=body.model,
            base_url=body.base_url,
        )
    except AISettingsError as exc:
        raise _handle_ai_settings_error(exc) from exc
    return TestConnectionResponse(success=result.success, message=result.message)
