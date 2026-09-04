"""
AstroOS — Auth Router

HTTP adapter layer. Delegates all logic to AuthService.
No business logic lives here — only request parsing, DTO→schema conversion,
and HTTP error mapping.

Fix log (post code-review):
  - Converts service DTOs → Pydantic response schemas (no schema leak to service).
  - Catches AuthError and PermissionError uniformly (no uncaught 500s).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from apps.api.dependencies import (
    get_auth_service,
    get_current_user_from_bearer,
)
from apps.api.domain.user import User
from apps.api.middleware.rate_limit import limiter
from apps.api.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPairResponse,
    UpdateProfileRequest,
    UserResponse,
)
from apps.api.services.auth_service import (
    AuthError,
    AuthService,
    RegistrationError,
    _user_dto,
)
from apps.api.services.dtos import AuthResultDTO, AuthTokensDTO, UserDTO

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── DTO → Schema converters (router's responsibility, not service's) ──────────


def _dto_to_user_response(dto: UserDTO) -> UserResponse:
    return UserResponse(
        id=dto.id,
        email=dto.email,
        display_name=dto.display_name,
        role=dto.role,
        status=dto.status,
        created_at=dto.created_at,
        last_login_at=dto.last_login_at,
        timezone=dto.timezone,
    )


def _dto_to_token_response(dto: AuthTokensDTO) -> TokenPairResponse:
    return TokenPairResponse(
        access_token=dto.access_token,
        refresh_token=dto.refresh_token,
        expires_in=dto.expires_in,
    )


def _dto_to_auth_response(dto: AuthResultDTO) -> AuthResponse:
    return AuthResponse(
        user=_dto_to_user_response(dto.user),
        tokens=_dto_to_token_response(dto.tokens),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def _handle_auth_error(exc: AuthError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account.",
)
async def register(
    body: RegisterRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        dto = await auth_service.register(
            email=body.email,
            display_name=body.display_name,
            password=body.password,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return _dto_to_auth_response(dto)
    except (AuthError, RegistrationError) as exc:
        raise _handle_auth_error(exc) from exc


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Exchange credentials for tokens.",
)
async def login(
    body: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        dto = await auth_service.login(
            email=body.email,
            password=body.password,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return _dto_to_auth_response(dto)
    except AuthError as exc:
        raise _handle_auth_error(exc) from exc


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    summary="Rotate refresh token.",
)
async def refresh(
    body: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenPairResponse:
    try:
        dto = await auth_service.refresh_tokens(body.refresh_token)
        return _dto_to_token_response(dto)
    except AuthError as exc:
        raise _handle_auth_error(exc) from exc


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the current access token.",
)
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    if token:
        await auth_service.logout(token)
    return MessageResponse(message="Logged out successfully.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password-reset email.",
)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.request_password_reset(body.email)
    # Always the same response, whether or not the account exists —
    # prevents using this endpoint to enumerate registered emails.
    return MessageResponse(
        message="If an account exists for that email, a reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Complete a password reset with a token from the email link.",
)
async def reset_password(
    body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth_service.reset_password(body.token, body.new_password)
    except AuthError as exc:
        raise _handle_auth_error(exc) from exc
    return MessageResponse(message="Password has been reset. Please sign in.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the authenticated user's profile.",
)
async def me(
    current_user: User = Depends(get_current_user_from_bearer),
) -> UserResponse:
    return UserResponse(
        id=current_user.id.value,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role.value,
        status=current_user.status.value,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
        timezone=current_user.timezone,
    )


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update the authenticated user's own profile.",
)
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        updated = await auth_service.update_profile(
            current_user,
            display_name=body.display_name,
            email=str(body.email) if body.email else None,
            timezone=body.timezone,
        )
    except AuthError as exc:
        raise _handle_auth_error(exc) from exc
    return _dto_to_user_response(_user_dto(updated))


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    summary="Change the authenticated user's password.",
)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth_service.change_password(
            current_user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except AuthError as exc:
        raise _handle_auth_error(exc) from exc
    return MessageResponse(
        message="Password updated. Please sign in again with your new password."
    )


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete the authenticated user's account.",
)
async def delete_me(
    current_user: User = Depends(get_current_user_from_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth_service.delete_account(current_user)
    except AuthError as exc:
        raise _handle_auth_error(exc) from exc
    return MessageResponse(message="Account deleted successfully.")

