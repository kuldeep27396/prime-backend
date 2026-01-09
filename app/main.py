from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError, BaseModel, EmailStr, Field
from typing import Optional
import os
from dotenv import load_dotenv

# Import routers
from app.routers import users, sessions
from app.routers import users_extended, content, analytics, integrations
from app.routers import companies, jobs, candidates, ai_interviews
from app.schemas.common import ErrorResponse, ErrorCodes

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Prime Interviews API",
    description="""
    **Prime Interviews API** - AI-powered interview platform for B2B candidate screening and mock practice.

    ## Features

    * **B2B Screening**: Companies onboard, post jobs, receive applications, AI screens candidates
    * **AI Interviews**: Automated video/audio interviews with AI that asks recruiter-style questions
    * **Shortlisting**: AI-powered candidate ranking with detailed reasoning
    * **Mock Practice**: AI interview practice for IT/software professionals
    * **Analytics**: Comprehensive dashboard analytics and progress tracking
    * **Email Notifications**: Automated notifications for interviews and results

    ## Authentication

    This API uses Clerk.js for authentication. Include your Clerk JWT token in the Authorization header:
    ```
    Authorization: Bearer <your_clerk_jwt_token>
    ```

    ## Pricing Tiers

    - **Free**: 2 AI interviews
    - **Starter (1-100)**: Flat monthly price
    - **Growth (100-1000)**: Flat monthly price
    - **Enterprise (1000+)**: Custom pricing
    - **Pay-per-interview**: Per interview cost option
    """,
    version="3.0.0",
    contact={
        "name": "Prime Interviews Team",
        "email": "support@prime-interviews.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers - Core
app.include_router(users.router)
app.include_router(users_extended.router)
app.include_router(sessions.router)
app.include_router(content.router)
app.include_router(analytics.router)
app.include_router(integrations.router)

# Include routers - B2B Company Management
app.include_router(companies.router)
app.include_router(jobs.router)
app.include_router(candidates.router)

# Include routers - AI Interviews
app.include_router(ai_interviews.router)

# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle validation errors"""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join([str(loc) for loc in error["loc"]]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": ErrorCodes.VALIDATION_ERROR,
                "message": "Request validation failed",
                "details": error_details
            }
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle value errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": ErrorCodes.VALIDATION_ERROR,
                "message": str(exc)
            }
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Handle internal server errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": ErrorCodes.INTERNAL_ERROR,
                "message": "Internal server error occurred"
            }
        }
    )

# Health endpoints
@app.get("/",
         summary="Root endpoint",
         description="Returns basic API information and operational status",
         tags=["Health"])
def read_root():
    """Root endpoint - API status"""
    return {
        "message": "Prime Interviews API v2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health",
         summary="Health check",
         description="Returns the health status of the API service",
         tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "2.0.0",
        "database": "connected",
        "email_service": "configured" if os.getenv("SMTP_HOST") else "not_configured"
    }

@app.get("/api/debug/email-config",
         summary="Debug email configuration",
         description="Returns current email configuration status",
         tags=["Debug"])
def debug_email_config():
    """Debug email configuration endpoint"""
    return {
        "brevo_api_key": "***" if os.getenv("BREVO_API_KEY") else None,
        "from_email": os.getenv("SMTP_FROM_EMAIL"),
        "from_name": os.getenv("SMTP_FROM_NAME"),
        **email_service.get_configuration_status()
    }

# Keep the old endpoint for backward compatibility
@app.get("/api/debug/smtp-config",
         summary="Debug email configuration (legacy)",
         description="Returns current email configuration status",
         tags=["Debug"])
def debug_smtp_config():
    """Debug email configuration endpoint"""
    return debug_email_config()

# Keep the original email endpoint from the existing API
from app.email_service import email_service

class EmailRequest(BaseModel):
    """Email request model for sending emails via SMTP"""
    to: EmailStr = Field(..., description="Recipient email address", example="user@example.com")
    toName: Optional[str] = Field(None, description="Recipient name (optional)", example="John Doe")
    subject: str = Field(..., description="Email subject line", example="Welcome to Prime Interviews")
    html: str = Field(..., description="HTML content of the email", example="<h1>Hello World!</h1><p>This is a test email.</p>")

class EmailResponse(BaseModel):
    """Response model for email sending operations"""
    success: bool = Field(..., description="Whether the email was sent successfully")
    message: str = Field(..., description="Status message describing the result")

@app.post("/api/send-email",
          response_model=EmailResponse,
          status_code=status.HTTP_200_OK,
          summary="Send email via Brevo API",
          description="Send transactional emails using the configured Brevo API service",
          tags=["Email"])
async def send_email(email_request: EmailRequest):
    """Send email via Brevo API"""
    try:
        # Check if email service is configured
        if not email_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service is not properly configured. Please check Brevo API environment variables."
            )

        # Send the email
        success = await email_service.send_email(
            to_email=email_request.to,
            to_name=email_request.toName,
            subject=email_request.subject,
            html_content=email_request.html
        )

        if success:
            return EmailResponse(
                success=True,
                message="Email sent successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please check Brevo API configuration and try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while sending email: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
