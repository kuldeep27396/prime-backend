import os
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timezone
import secrets

# Security
security = HTTPBearer()

class ClerkAuth:
    def __init__(self):
        self.clerk_publishable_key = os.getenv("CLERK_PUBLISHABLE_KEY")
        self.clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
        self.jwt_secret = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
        self.clerk_api_url = "https://api.clerk.dev/v1"
        
        if not self.clerk_publishable_key or not self.clerk_secret_key:
            print("⚠️  Clerk authentication not configured. Set CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY.")

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Clerk JWT token and return user information"""
        try:
            # Verify the token using Clerk's public keys
            headers = {
                "Authorization": f"Bearer {self.clerk_secret_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                # Get Clerk's public keys
                keys_response = await client.get(
                    f"{self.clerk_api_url}/jwks",
                    headers=headers
                )
                keys_response.raise_for_status()
                keys_data = keys_response.json()
                
                # Verify the token
                payload = jwt.decode(
                    token,
                    keys_data["keys"][0]["x5c"][0],
                    algorithms=["RS256"],
                    audience="user",
                    issuer="https://clerk_instance.clerk.accounts.dev"
                )
                
                return payload
                
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to verify token with Clerk: {str(e)}"
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}"
            )

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """Get user information from Clerk token"""
        payload = await self.verify_token(token)
        
        return {
            "sub": payload.get("sub"),  # Clerk user ID
            "email": payload.get("email"),
            "email_verified": payload.get("email_verified", False),
            "first_name": payload.get("first_name"),
            "last_name": payload.get("last_name"),
            "image_url": payload.get("image_url"),
            "iat": payload.get("iat"),
            "exp": payload.get("exp")
        }

    async def authenticate_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Authenticate user using Clerk JWT token"""
        if not self.clerk_publishable_key or not self.clerk_secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service not configured"
            )
        
        try:
            user_info = await self.get_user_info(credentials.credentials)
            return user_info
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Get current authenticated user"""
        return await self.authenticate_user(credentials)

    async def get_current_user_optional(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
        """Get current authenticated user (optional - returns None if not authenticated)"""
        if credentials is None:
            return None
        
        try:
            return await self.authenticate_user(credentials)
        except HTTPException:
            return None

# Create global instance
clerk_auth = ClerkAuth()

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    return await clerk_auth.get_current_user(credentials)

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Dependency to get current authenticated user (optional)"""
    return await clerk_auth.get_current_user_optional(credentials)