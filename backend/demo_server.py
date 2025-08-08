"""
Demo server for AITM Report Generation System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.reports import router as reports_router

# Create FastAPI app
app = FastAPI(
    title="AITM Reports Demo",
    description="Demo server for AITM report generation system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include reports router
app.include_router(reports_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "AITM Reports Demo Server", 
        "docs": "/docs",
        "reports": "/api/v1/reports"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "reports-demo"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "demo_server:app", 
        host="0.0.0.0", 
        port=38527, 
        reload=True,
        log_level="info"
    )
