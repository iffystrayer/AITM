"""
AITM - AI-Powered Threat Modeler
Main FastAPI application entry point
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.auth import validate_production_config
from app.api.v1.router import api_router
from app.services.mitre_service import MitreAttackService

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AITM application...")
    
    # Validate production configuration
    try:
        validate_production_config()
    except RuntimeError as e:
        logger.critical(f"Configuration validation failed: {e}")
        raise
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize MITRE ATT&CK data
    mitre_service = MitreAttackService()
    await mitre_service.initialize()
    logger.info("MITRE ATT&CK data initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AITM application...")


# Create FastAPI app
app = FastAPI(
    title="AITM - AI-Powered Threat Modeler",
    description="Automated threat modeling using AI agents and MITRE ATT&CK framework",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS - permissive for development
if settings.environment == "development":
    cors_origins = ["*"]  # Allow all origins in development
else:
    cors_origins = settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AITM - AI-Powered Threat Modeler",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("BACKEND_PORT", 38527))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
