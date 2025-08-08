"""
API v1 router
"""

from fastapi import APIRouter

from app.api.v1.endpoints import projects, threat_modeling

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(threat_modeling.router, prefix="/threat-modeling", tags=["threat-modeling"])
