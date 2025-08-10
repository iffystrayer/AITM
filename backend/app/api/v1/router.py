"""
API v1 router
"""

from fastapi import APIRouter

from app.api.v1.endpoints import projects, threat_modeling
from app.api.v1 import analytics, enhanced_ai
from app.api.endpoints import reports, predictions, auth
from app.core.config import get_settings

settings = get_settings()
api_router = APIRouter()

# Health check endpoint for API v1
@api_router.get("/health")
async def health_check():
    """Health check endpoint for API v1"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
        "api_version": "v1"
    }

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(enhanced_ai.router, prefix="/enhanced-ai", tags=["enhanced-ai"])
api_router.include_router(reports.router)
