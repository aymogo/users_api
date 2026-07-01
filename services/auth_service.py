from jose import JWTError

from core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidVerificationCodeError,
)
from core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.user import User
from repositories.user_repository import UserRepository
from schemas.auth import TokenPair
from schemas.user import UserCreate
from services.verification_service import VerificationService


class AuthService:
    """Coordinates registration, login and token lifecycle."""

    def __init__(self, repository: UserRepository, verification_service: VerificationService) -> None:
        self._repository = repository
        self._verification_service = verification_service

    async def register(self, data: UserCreate) -> User:
        existing = await self._repository.get_by_email(data.email)
        if existing is not None:
            raise EmailAlreadyExistsError(f"User with email '{data.email}' already exists.")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            is_verified=False,
        )
        self._verification_service.issue_code(user)
        return await self._repository.create(user)

    async def authenticate(self, email: str, password: str) -> TokenPair:
        user = await self._repository.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")

        return TokenPair(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh_access_token(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except JWTError as exc:
            raise InvalidTokenError("Invalid or expired refresh token.") from exc

        if payload.get("type") != TokenType.REFRESH.value:
            raise InvalidTokenError("Provided token is not a refresh token.")

        user_id = payload.get("sub")
        user = await self._repository.get_by_id(int(user_id))
        if user is None:
            raise InvalidTokenError("User associated with this token no longer exists.")

        return create_access_token(str(user.id))

    async def verify(self, email: str, code: str) -> User:
        user = await self._repository.get_by_email(email)
        if user is None:
            raise InvalidVerificationCodeError("Invalid email or verification code.")

        if not self._verification_service.is_code_valid(user, code):
            raise InvalidVerificationCodeError("Invalid or expired verification code.")

        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires_at = None
        return await self._repository.save(user)