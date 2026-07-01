from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import TokenType, decode_token
from db.session import get_db
from models.user import User, UserRole
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.user_service import UserService
from services.verification_service import VerificationService

# HTTPBearer shows a simple "Bearer token" input in Swagger UI's Authorize dialog.
bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(session)


def get_verification_service() -> VerificationService:
    return VerificationService()


def get_auth_service(
        repository: Annotated[UserRepository, Depends(get_user_repository)],
        verification_service: Annotated[VerificationService, Depends(get_verification_service)],
) -> AuthService:
    return AuthService(repository, verification_service)


def get_user_service(
        repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository)


async def get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
        repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Resolve and validate the current user from the access token."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_error

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise credentials_error from exc

    if payload.get("type") != TokenType.ACCESS.value:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = await repository.get_by_id(int(user_id))
    if user is None:
        raise credentials_error

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    """Guard dependency restricting an endpoint to Admin role only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires administrator privileges.",
        )
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
