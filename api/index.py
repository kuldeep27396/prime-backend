"""
Vercel serverless function entry point for PRIME API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import minimal configuration and core components
from app.core.config import settings

# Create a lightweight FastAPI app for Vercel
app = FastAPI(
    title="PRIME API",
    description="Predictive Recruitment & Interview Machine - Serverless API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import only essential routers that don't require heavy dependencies
try:
    from app.api.v1 import auth
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
except ImportError:
    pass

try:
    from app.api.v1 import jobs
    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
except ImportError:
    pass

try:
    from app.api.v1 import candidates
    app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["candidates"])
except ImportError:
    pass

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PRIME API - Serverless Version",
        "version": "1.0.0",
        "status": "operational",
        "platform": "Vercel"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "environment": os.getenv("ENVIRONMENT", "production"),
        "platform": "vercel"
    }

# Export the app for Vercel
handler = app
