"""
Authentication service for user management and authentication
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import uuid

from app.models.company import User, Company
from app.schemas.auth import UserCreate, UserUpdate, UserLogin, CompanyCreate
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    create_reset_token,
    create_verification_token,
    verify_reset_token,
    verify_verification_token
)
from app.core.config import settings


class AuthService:
    """Authentication service class"""

    def __init__(self, db: Session):
        self.db = db

    def create_company(self, company_data: CompanyCreate) -> Company:
        """Create a new company"""
        try:
            company = Company(
                name=company_data.name,
                domain=company_data.domain,
                settings=company_data.settings or {}
            )
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
            return company
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company with this domain already exists"
            )

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            # Hash the password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user
            user = User(
                email=user_data.email,
                password_hash=hashed_password,
                role=user_data.role,
                company_id=user_data.company_id,
                profile=user_data.profile or {},
                is_active=True  # Will be False until email verification in production
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
            
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive"
            )
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login timestamp
        user.update_last_login()
        self.db.commit()
        
        return user

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> User:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields if provided
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

    def create_access_token_for_user(self, user: User) -> dict:
        """Create access token for user"""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "company_id": str(user.company_id)
        }
        
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(token_data, expires_delta)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }

    def initiate_password_reset(self, email: str) -> str:
        """Initiate password reset process"""
        user = self.get_user_by_email(email)
        if not user:
            # Don't reveal if email exists or not for security
            return "If the email exists, a reset link has been sent"
        
        reset_token = create_reset_token(email)
        
        # TODO: Send email with reset token
        # For now, we'll return the token (in production, this should be sent via email)
        return reset_token

    def reset_password(self, token: str, new_password: str) -> User:
        """Reset user password with token"""
        email = verify_reset_token(token)
        user = self.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def send_verification_email(self, email: str) -> str:
        """Send email verification"""
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        verification_token = create_verification_token(email)
        
        # TODO: Send email with verification token
        # For now, we'll return the token (in production, this should be sent via email)
        return verification_token

    def verify_email(self, token: str) -> User:
        """Verify user email with token"""
        email = verify_verification_token(token)
        user = self.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Activate user account
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def deactivate_user(self, user_id: uuid.UUID) -> User:
        """Deactivate user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def change_password(self, user_id: uuid.UUID, current_password: str, new_password: str) -> User:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        
        return user