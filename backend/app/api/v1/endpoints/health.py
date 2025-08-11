"""
Health check endpoint for monitoring and E2E tests.
"""

from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint that returns the service status.
    Used by monitoring systems and E2E tests to verify the service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "service": "AITM API",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check that includes more system information.
    """
    try:
        # Test database connection
        from app.core.database import async_session
        async with async_session() as db:
            await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "service": "AITM API",
        "version": "1.0.0",
        "components": {
            "database": db_status,
            "auth": "healthy",
            "permissions": "healthy"
        }
    }