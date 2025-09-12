"""
Dependency injection utilities for FastAPI
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid

from app.core.database import SessionLocal
from app.core.security import verify_token
from app.models.company import User
from app.services.auth_service import AuthService

# Security scheme
security = HTTPBearer()


def get_db() -> Generator:
    """Database dependency"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service"""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = auth_service.get_user_by_id(uuid.UUID(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
    """Dependency factory for role-based access control"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        role_hierarchy = {
            "admin": ["admin"],
            "recruiter": ["admin", "recruiter"],
            "interviewer": ["admin", "recruiter", "interviewer"]
        }
        
        allowed_roles = role_hierarchy.get(required_role, [])
        
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role or higher"
            )
        
        return current_user
    
    return role_checker


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_recruiter_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require recruiter or admin role"""
    if current_user.role not in ["admin", "recruiter"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter or admin access required"
        )
    return current_user


def require_same_company(current_user: User = Depends(get_current_active_user)):
    """Dependency factory to ensure users can only access their company's data"""
    def company_checker(company_id: uuid.UUID) -> User:
        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: different company"
            )
        return current_user
    
    return company_checker


# Optional authentication for public endpoints
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, auth_service)
    except HTTPException:
        return None