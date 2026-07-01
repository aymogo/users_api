import secrets
from datetime import datetime, timedelta, timezone

from core.config import settings
from core.logging import logger
from models.user import User


class VerificationService:
    """Generates and 'delivers' email/SMS verification codes.

    NOTE (simplification): in dev/test we just log the code to the console
    instead of sending a real email/SMS. In production this would be
    replaced with a real provider integration (e.g. SendGrid, SES, Twilio)
    dispatched via a Celery task so the request/response cycle is never
    blocked on an external API call.
    """

    CODE_LENGTH = 6

    def generate_code(self) -> str:
        return "".join(secrets.choice("0123456789") for _ in range(self.CODE_LENGTH))

    def issue_code(self, user: User) -> str:
        code = self.generate_code()
        user.verification_code = code
        user.verification_code_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES
        )
        self._deliver(user.email, code)
        return code

    def _deliver(self, email: str, code: str) -> None:
        # Simplification: print/log instead of a real email/SMS provider call.
        logger.info("Verification code for %s: %s (dev-mode, not actually sent)", email, code)

    def is_code_valid(self, user: User, code: str) -> bool:
        if not user.verification_code or not user.verification_code_expires_at:
            return False
        if user.verification_code != code:
            return False
        expires_at = user.verification_code_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) <= expires_at