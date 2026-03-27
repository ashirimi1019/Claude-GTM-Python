"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.errors import AppError, error_response
from app.routes import health, skills, offers, campaigns, icp, agents, health_monitor, variants, artifacts, cron
from services.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan — startup and shutdown hooks."""
    # Startup: initialize shared resources
    configure_logging()
    yield
    # Shutdown: cleanup


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="CirrusLabs API",
        version="0.1.0",
        description="Signal-driven outbound campaign automation",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global error handler
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return error_response(exc)

    # Routes
    app.include_router(health.router)
    app.include_router(skills.router, prefix="/api")
    app.include_router(offers.router, prefix="/api")
    app.include_router(campaigns.router, prefix="/api")
    app.include_router(icp.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    app.include_router(health_monitor.router, prefix="/api")
    app.include_router(variants.router, prefix="/api")
    app.include_router(artifacts.router, prefix="/api")
    app.include_router(cron.router, prefix="/api")

    return app
