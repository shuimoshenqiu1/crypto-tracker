from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import auth
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 — ensure models registered with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup on shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title="CryptoTracker API",
        version="0.1.0",
        redirect_slashes=False,
        lifespan=lifespan,
    )
    application.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

    @application.get("/api/v1/health")
    async def health_check():
        return {"status": "healthy", "service": "crypto-tracker-api"}

    return application


app = create_app()
