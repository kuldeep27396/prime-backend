from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import os
from dotenv import load_dotenv

# Import our email service
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.email_service import email_service

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Prime Interviews API",
    description="""
    **Prime Interviews API** - A comprehensive backend service for recruitment and interview management.
    
    ## Features
    
    * **Health Monitoring**: Check API status and health
    * **Email Service**: Send transactional emails via SMTP
    * **CORS Enabled**: Cross-origin resource sharing configured
    
    ## Authentication
    
    Currently, the API is open for development. Authentication will be added in future versions.
    
    ## Rate Limiting
    
    No rate limiting is currently implemented. Please use responsibly.
    """,
    version="1.0.0",
    contact={
        "name": "Prime Interviews Team",
        "email": "support@prime-interviews.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class EmailRequest(BaseModel):
    """Email request model for sending emails via SMTP"""
    to: EmailStr = Field(..., description="Recipient email address", example="user@example.com")
    toName: Optional[str] = Field(None, description="Recipient name (optional)", example="John Doe")
    subject: str = Field(..., description="Email subject line", example="Welcome to Prime Interviews")
    html: str = Field(..., description="HTML content of the email", example="<h1>Hello World!</h1><p>This is a test email.</p>")

    class Config:
        schema_extra = {
            "example": {
                "to": "candidate@example.com",
                "toName": "Jane Smith",
                "subject": "Interview Confirmation - Software Engineer Position",
                "html": "<h2>Interview Confirmation</h2><p>Dear Jane,</p><p>Your interview is scheduled for tomorrow at 2 PM.</p><p>Best regards,<br>Prime Interviews Team</p>"
            }
        }

class EmailResponse(BaseModel):
    """Response model for email sending operations"""
    success: bool = Field(..., description="Whether the email was sent successfully")
    message: str = Field(..., description="Status message describing the result")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Email sent successfully"
            }
        }

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Health status of the API", example="healthy")

class StatusResponse(BaseModel):
    """API status response model"""
    message: str = Field(..., description="API status message")
    status: str = Field(..., description="Operational status")
    version: Optional[str] = Field(None, description="API version")

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message details")

@app.get("/", 
         response_model=StatusResponse,
         summary="Root endpoint",
         description="Returns basic API information and operational status",
         tags=["Health"])
def read_root():
    """
    **Root Endpoint**
    
    Returns basic information about the Prime Interviews API including:
    - API name and status
    - Operational confirmation
    
    This endpoint can be used to verify that the API is running and accessible.
    """
    return {"message": "PRIME API", "status": "operational"}

@app.get("/health", 
         response_model=HealthResponse,
         summary="Health check",
         description="Returns the health status of the API service",
         tags=["Health"])
def health_check():
    """
    **Health Check Endpoint**
    
    Performs a basic health check of the API service.
    
    Returns:
    - `status`: Current health status of the service
    
    This endpoint is typically used by monitoring systems and load balancers
    to determine if the service is healthy and ready to handle requests.
    """
    return {"status": "healthy"}

@app.get("/api/v1/test", 
         response_model=StatusResponse,
         summary="API test endpoint",
         description="Test endpoint to verify API functionality and version",
         tags=["Testing"])
def test_endpoint():
    """
    **API Test Endpoint**
    
    A simple test endpoint that confirms the API is working correctly.
    
    Returns:
    - API working confirmation message
    - Current API version
    
    Useful for:
    - Integration testing
    - API connectivity verification
    - Version checking
    """
    return {"message": "API is working", "status": "operational", "version": "1.0.0"}

@app.post("/api/send-email", 
          response_model=EmailResponse,
          status_code=status.HTTP_200_OK,
          summary="Send email via SMTP",
          description="Send transactional emails using the configured SMTP service",
          tags=["Email"],
          responses={
              200: {
                  "description": "Email sent successfully",
                  "model": EmailResponse,
                  "content": {
                      "application/json": {
                          "example": {
                              "success": True,
                              "message": "Email sent successfully"
                          }
                      }
                  }
              },
              422: {
                  "description": "Validation Error - Invalid email format or missing required fields",
                  "model": ErrorResponse
              },
              500: {
                  "description": "Internal Server Error - SMTP configuration or sending failure",
                  "model": ErrorResponse,
                  "content": {
                      "application/json": {
                          "examples": {
                              "not_configured": {
                                  "summary": "SMTP not configured",
                                  "value": {"detail": "Email service is not properly configured"}
                              },
                              "send_failure": {
                                  "summary": "Email sending failed",
                                  "value": {"detail": "Failed to send email"}
                              }
                          }
                      }
                  }
              }
          })
async def send_email(email_request: EmailRequest):
    """
    **Send Email via SMTP**
    
    Send transactional emails using the configured SMTP service.
    
    ## Requirements
    
    - Valid recipient email address
    - Email subject line
    - HTML content for the email body
    - Properly configured SMTP settings in environment variables
    
    ## SMTP Configuration
    
    The following environment variables must be set:
    - `SMTP_HOST`: SMTP server hostname
    - `SMTP_PORT`: SMTP server port (default: 465)
    - `SMTP_USER`: SMTP username
    - `SMTP_PASSWORD`: SMTP password
    - `SMTP_FROM_EMAIL`: Sender email address
    - `SMTP_FROM_NAME`: Sender name (optional)
    
    ## Usage Examples
    
    - Welcome emails for new users
    - Interview confirmation emails
    - Password reset notifications
    - System alerts and notifications
    
    ## Security Notes
    
    - All emails are sent over encrypted connections (TLS/SSL)
    - Email addresses are validated before sending
    - HTML content is sent as-is (ensure it's sanitized)
    """
    try:
        # Check if email service is configured
        if not email_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service is not properly configured. Please check SMTP environment variables."
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
                detail="Failed to send email. Please check SMTP configuration and try again."
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while sending email: {str(e)}"
        )

@app.get("/api/debug/smtp-config", 
         summary="Debug SMTP configuration",
         description="Check SMTP configuration status (for debugging only)",
         tags=["Debug"])
def debug_smtp_config():
    """
    **Debug SMTP Configuration**
    
    Returns the current SMTP configuration status and loaded environment variables.
    This endpoint helps debug email service configuration issues.
    
    **Note**: This is a debug endpoint and should be removed in production.
    """
    return {
        "smtp_host": email_service.smtp_host,
        "smtp_port": email_service.smtp_port,
        "smtp_user": email_service.smtp_user,
        "smtp_password": "***" if email_service.smtp_password else None,
        "from_email": email_service.from_email,
        "from_name": email_service.from_name,
        "smtp_secure": email_service.smtp_secure,
        "is_configured": email_service.is_configured()
    }
