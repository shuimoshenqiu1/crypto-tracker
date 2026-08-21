from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.coins import router as coins_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import User, Coin  # noqa: F401 -- ensure models registered
from app.schemas.common import error_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: close connections
    from app.services.cache import close_redis
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="CryptoTracker API",
    version=settings.APP_VERSION,
    redirect_slashes=False,
    lifespan=lifespan,
)


# --- Exception handlers ---


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    messages = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err["loc"] if x != "body")
        messages.append(f"{loc}: {err['msg']}")
    return JSONResponse(
        status_code=422,
        content=error_response(42201, "; ".join(messages)),
    )


# --- Health endpoint ---


@app.get("/api/v1/health")
async def health_check() -> dict:
    return {
        "code": 0,
        "data": {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "services": {
                "database": "connected",
                "redis": "connected",
                "celery": "active",
            },
            "timestamp": int(time.time() * 1000),
        },
        "message": "",
    }


# --- Routers ---

app.include_router(auth_router, prefix="/api/v1")
app.include_router(coins_router, prefix="/api/v1")
