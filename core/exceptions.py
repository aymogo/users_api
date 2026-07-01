class AppError(Exception):
    """Base class for domain-level errors, translated to HTTPException in routers."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class EmailAlreadyExistsError(AppError):
    pass


class InvalidCredentialsError(AppError):
    pass


class UserNotFoundError(AppError):
    pass


class InvalidTokenError(AppError):
    pass


class InvalidVerificationCodeError(AppError):
    pass


class AlreadyVerifiedError(AppError):
    pass