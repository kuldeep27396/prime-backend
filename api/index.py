from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from dotenv import load_dotenv

# Import our email service
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.email_service import email_service

# Load environment variables
load_dotenv()

app = FastAPI(title="Prime Interviews API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class EmailRequest(BaseModel):
    to: EmailStr
    toName: Optional[str] = None
    subject: str
    html: str

class EmailResponse(BaseModel):
    success: bool
    message: str

@app.get("/")
def read_root():
    return {"message": "PRIME API", "status": "operational"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/test")
def test_endpoint():
    return {"message": "API is working", "version": "1.0.0"}

@app.post("/api/send-email", response_model=EmailResponse)
async def send_email(email_request: EmailRequest):
    """Send an email using SMTP"""
    try:
        # Check if email service is configured
        if not email_service.is_configured():
            raise HTTPException(
                status_code=500,
                detail="Email service is not properly configured"
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
                status_code=500,
                detail="Failed to send email"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending email: {str(e)}"
        )
