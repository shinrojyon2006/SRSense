"""
FastAPI Application Factory — SRSense AI Feature-Based Entry Point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    global_exception_handler,
    http_exception_handler,
)
from app.core.logging import logger
from app.database.session import engine
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.security_middleware import SecurityHeadersMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.modules.health.router import router as health_router
from app.modules.system.router import router as system_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.projects import router as projects_router
from app.api.requirements import router as requirements_router
from app.api.ai import router as ai_router
from app.api.documents import router as documents_router
from app.api.extraction import router as extraction_router
from app.api.graph import router as graph_router
from app.api.intelligence import router as intelligence_router
from app.api.impact import router as impact_router
from app.api.verification import router as verification_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan for startup/shutdown events."""
    logger.info("Initializing %s v%s", settings.APP_NAME, settings.APP_VERSION)
    yield
    await engine.dispose()
    logger.info("Application shutdown complete.")


def create_app() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Software Requirements Engineering Platform Foundation",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # Module Routers Plug-in
    api_prefix = "/api"
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(system_router, prefix=api_prefix)
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(users_router, prefix=api_prefix)
    app.include_router(projects_router, prefix=api_prefix)
    app.include_router(requirements_router, prefix=api_prefix)
    app.include_router(ai_router, prefix=api_prefix)
    app.include_router(documents_router, prefix=api_prefix)
    app.include_router(extraction_router, prefix=api_prefix)
    app.include_router(graph_router, prefix=api_prefix)
    app.include_router(intelligence_router, prefix=api_prefix)
    app.include_router(impact_router, prefix=api_prefix)
    app.include_router(verification_router, prefix=api_prefix)

    return app


app = create_app()
