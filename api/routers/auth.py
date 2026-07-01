from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_auth_service
from core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidVerificationCodeError,
)
from schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenPair,
    VerifyRequest,
)
from schemas.user import UserCreate, UserResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with 'unverified' status and issues a "
                "verification code (logged to console in dev mode).",
)
async def signup(
        data: UserCreate,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    try:
        user = await auth_service.register(data)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail) from exc
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Authenticate and obtain tokens",
    description="Validates credentials and returns a JWT access/refresh token pair.",
)
async def login(
        data: LoginRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPair:
    try:
        return await auth_service.authenticate(data.email, data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.detail) from exc


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description="Exchanges a valid refresh token for a new short-lived access token.",
)
async def refresh(
        data: RefreshRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessTokenResponse:
    try:
        access_token = await auth_service.refresh_access_token(data.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.detail) from exc
    return AccessTokenResponse(access_token=access_token)


@router.post(
    "/verify",
    response_model=UserResponse,
    summary="Verify user email/SMS code",
    description="Confirms the verification code sent at signup and marks the user as verified.",
)
async def verify(
        data: VerifyRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    try:
        user = await auth_service.verify(data.email, data.code)
    except InvalidVerificationCodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    return UserResponse.model_validate(user)
