"""Celery application and periodic tasks.

Provides a Celery Beat scheduled task that automatically deletes users who have
not completed email verification within the configured TTL (default: 2 days).
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import settings
from models.user import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Celery application
# ---------------------------------------------------------------------------

celery_app = Celery(
    "users_api",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Schedule: run the cleanup task once a day at 03:00 UTC.
celery_app.conf.beat_schedule = {
    "cleanup-unverified-users-daily": {
        "task": "tasks.cleanup_unverified_users",
        "schedule": crontab(hour=3, minute=0),
    },
}


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

async def _run_cleanup(cutoff: datetime) -> int:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(
            delete(User).where(
                User.is_verified == False,  # noqa: E712
                User.created_at < cutoff,
            )
        )
        deleted_count = result.rowcount
    await engine.dispose()
    return deleted_count


@celery_app.task(name="tasks.cleanup_unverified_users")
def cleanup_unverified_users() -> dict:
    """Delete users who have not verified their account within the allowed TTL.

    Default TTL is 2 days (configured via UNVERIFIED_USER_TTL_DAYS).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.UNVERIFIED_USER_TTL_DAYS)

    deleted_count = asyncio.run(_run_cleanup(cutoff))

    logger.info("Cleanup: deleted %d unverified user(s) older than %s.", deleted_count, cutoff)
    return {"deleted": deleted_count, "cutoff": cutoff.isoformat()}
