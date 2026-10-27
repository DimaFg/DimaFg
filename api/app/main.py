from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

import app.models  # noqa: F401 — регистрирует все модели (внешние ключи между модулями)
from app.core.config import get_settings
from app.core.db import engine
from app.core.errors import ErrorResponse, install_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.modules.leads.router import router as leads_router
from app.modules.portfolio.router import router as portfolio_router
from app.modules.services.router import router as services_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    is_prod = settings.environment == "production"

    app = FastAPI(
        title="Photo portfolio API",
        version="1.0.0",
        docs_url=None if is_prod else "/api/docs",
        redoc_url=None,
        openapi_url=None if is_prod else "/api/openapi.json",
        responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    install_error_handlers(app)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
        )
    app.add_middleware(RequestContextMiddleware, max_body_bytes=settings.max_body_bytes)

    health = APIRouter(prefix="/api/health", tags=["health"])

    @health.get("/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @health.get("/ready")
    def ready():
        try:
            with engine.connect() as conn:
                conn.execute(text("select 1"))
        except Exception:
            return JSONResponse({"status": "unavailable", "database": "error"}, status_code=503)
        return {"status": "ok", "database": "ok"}

    v1 = APIRouter(prefix="/api/v1")
    v1.include_router(services_router)
    v1.include_router(portfolio_router)
    v1.include_router(leads_router)

    app.include_router(health)
    app.include_router(v1)
    return app


app = create_app()
