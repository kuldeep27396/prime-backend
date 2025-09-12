"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_auth_service, get_current_active_user, security
from app.schemas.auth import (
    UserCreate, UserResponse, UserLogin, Token, 
    PasswordReset, PasswordResetConfirm, EmailVerification,
    CompanyCreate, CompanyResponse
)
from app.services.auth_service import AuthService
from app.models.company import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        user = auth_service.create_user(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return access token"""
    user = auth_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = auth_service.create_access_token_for_user(user)
    return token_data


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout user (client-side token removal)"""
    # In a stateless JWT system, logout is handled client-side
    # In production, you might want to implement token blacklisting
    return {"message": "Successfully logged out"}


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset"""
    token = auth_service.initiate_password_reset(reset_data.email)
    
    # In production, this would send an email and not return the token
    return {
        "message": "If the email exists, a reset link has been sent",
        "reset_token": token  # Remove this in production
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm password reset with token"""
    try:
        user = auth_service.reset_password(reset_data.token, reset_data.new_password)
        return {"message": "Password successfully reset"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/verify-email")
async def request_email_verification(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request email verification"""
    token = auth_service.send_verification_email(current_user.email)
    
    # In production, this would send an email and not return the token
    return {
        "message": "Verification email sent",
        "verification_token": token  # Remove this in production
    }


@router.post("/verify-email/confirm")
async def confirm_email_verification(
    verification_data: EmailVerification,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm email verification with token"""
    try:
        user = auth_service.verify_email(verification_data.token)
        return {"message": "Email successfully verified"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        auth_service.change_password(current_user.id, current_password, new_password)
        return {"message": "Password successfully changed"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Create a new company (public endpoint for initial setup)"""
    try:
        company = auth_service.create_company(company_data)
        return company
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "authentication"}