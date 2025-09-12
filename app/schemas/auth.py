"""
Authentication schemas for request/response validation
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    role: str = "recruiter"
    is_active: bool = True

    @validator("role")
    def validate_role(cls, v):
        allowed_roles = ["admin", "recruiter", "interviewer"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str
    company_id: Optional[uuid.UUID] = None
    profile: Optional[dict] = {}

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for user updates"""
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    profile: Optional[dict] = None

    @validator("role")
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ["admin", "recruiter", "interviewer"]
            if v not in allowed_roles:
                raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class UserResponse(UserBase):
    """Schema for user response"""
    id: uuid.UUID
    company_id: uuid.UUID
    profile: dict
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[str] = None


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class EmailVerification(BaseModel):
    """Schema for email verification"""
    token: str


class CompanyCreate(BaseModel):
    """Schema for company creation"""
    name: str
    domain: Optional[str] = None
    settings: Optional[dict] = {}


class CompanyResponse(BaseModel):
    """Schema for company response"""
    id: uuid.UUID
    name: str
    domain: Optional[str]
    settings: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True