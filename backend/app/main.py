"""FastAPI application factory.

Wires cross-cutting concerns (logging, correlation, error handling, CORS) and mounts routers.
Business logic lives in application services, not here.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import CorrelationLoggingMiddleware
from app.api.routers import auth, health, projects
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
)
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger("startup")
    logger.info(
        "app_start",
        env=settings.app_env,
        model_provider=settings.model_provider,
        connector_mode=settings.connector_mode,
        write_actions=settings.feature_write_actions_enabled,
    )
    yield
    get_logger("shutdown").info("app_stop")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI-native multi-agent Software Delivery Intelligence Platform.",
        lifespan=lifespan,
    )

    app.add_middleware(CorrelationLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(projects.router)

    return app


app = create_app()
