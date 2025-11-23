"""
FastAPI Application Entry Point for UEMS (University Education Management System).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import engine, Base
from app.middleware.logging_middleware import LoggingMiddleware

# Import all models to ensure they're registered with SQLAlchemy
from app.models import (
    User, Course, Enrollment, Grade, Attendance, Payment, PaymentHistory
)

# Import API routers
from app.api import health, auth, courses, payments, analytics

# Setup structured JSON logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="University Education Management System - Production-grade full-stack application",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# =============================================================================
# CORS Configuration
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Custom Middleware
# =============================================================================

app.add_middleware(LoggingMiddleware)

# =============================================================================
# Prometheus Instrumentation
# =============================================================================

if settings.ENABLE_METRICS:
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/health/live", "/health/ready"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )

    # Instrument the app and expose metrics endpoint
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    logger.info(
        "Prometheus instrumentation enabled",
        extra={'event': 'metrics_enabled', 'endpoint': '/metrics'}
    )

# =============================================================================
# API Routes
# =============================================================================

# Health checks (no prefix, for Kubernetes probes)
app.include_router(health.router)

# API v1 routes
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(courses.router, prefix=settings.API_V1_PREFIX)
app.include_router(payments.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)

# =============================================================================
# Lifecycle Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks.
    Create database tables if they don't exist.
    """
    logger.info(
        "Application starting up",
        extra={
            'event': 'app_startup',
            'environment': settings.ENVIRONMENT,
            'version': settings.APP_VERSION
        }
    )

    # Create tables (in production, use Alembic migrations instead)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info(
        "Database tables created/verified",
        extra={'event': 'db_tables_ready'}
    )


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown tasks.
    Clean up database connections.
    """
    logger.info(
        "Application shutting down",
        extra={'event': 'app_shutdown'}
    )

    await engine.dispose()

    logger.info(
        "Database connections closed",
        extra={'event': 'db_connections_closed'}
    )


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
