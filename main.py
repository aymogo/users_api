from fastapi import FastAPI

from api.routers import auth, users
from core.config import settings
from core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="Authentication & user-management service (FastAPI + JWT + roles).",
    version="1.0.0",
)
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health", tags=["health"], summary="Health check")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}