"""
PRIME (Predictive Recruitment & Interview Machine) - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, create_tables
from app.api.v1 import auth, jobs, candidates, interviews, assessments, applications, chatbot, video_analysis, scoring, integrations, admin, websocket, security

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting PRIME application...")
    await create_tables()
    logger.info("Database tables created/verified")
    yield
    # Shutdown
    logger.info("Shutting down PRIME application...")


# Create FastAPI application
app = FastAPI(
    title="PRIME API",
    description="Predictive Recruitment & Interview Machine - AI-powered recruitment platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Disable TrustedHostMiddleware for development/testing
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["candidates"])
app.include_router(interviews.router, prefix="/api/v1/interviews", tags=["interviews"])
app.include_router(assessments.router, prefix="/api/v1/assessments", tags=["assessments"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["chatbot"])
app.include_router(video_analysis.router, prefix="/api/v1/video-analysis", tags=["video-analysis"])
app.include_router(scoring.router, prefix="/api/v1/scoring", tags=["scoring"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])
app.include_router(security.router, prefix="/api/v1/security", tags=["security"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PRIME API - Predictive Recruitment & Interview Machine",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )