"""
Health check endpoints for Kubernetes probes and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.core.database import get_db

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the service is up.
    """
    return {"status": "healthy", "service": "uems-backend"}


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.
    Returns 200 if the application process is running.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes readiness probe.
    Returns 200 if the application can serve traffic (DB is connected).
    """
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(
            "Readiness check failed - database connection error",
            extra={'event': 'readiness_check_failed', 'error': str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=503,
            detail="Service not ready - database connection failed"
        )
