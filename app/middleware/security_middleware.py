"""
Security middleware for automatic audit logging and monitoring
"""

import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.security_service import security_service
from app.api.deps import get_current_user_optional

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic security monitoring and audit logging"""
    
    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", "/",
            "/api/v1/security/audit-log"  # Avoid recursive logging
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with security monitoring"""
        start_time = time.time()
        
        # Skip monitoring for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Extract request information
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        user_agent = request.headers.get("user-agent")
        ip_address = self._get_client_ip(request)
        
        # Get user context if available
        user_id = None
        try:
            # Try to get current user without raising exceptions
            db = next(get_db())
            user = await get_current_user_optional(request, db)
            if user:
                user_id = str(user.id)
        except Exception:
            # User not authenticated or error occurred
            pass
        
        # Process request
        response = None
        error = None
        
        try:
            response = await call_next(request)
        except Exception as e:
            error = str(e)
            logger.error(f"Request error: {error}")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log security-relevant actions
        await self._log_security_action(
            request=request,
            response=response,
            user_id=user_id,
            method=method,
            path=path,
            query_params=query_params,
            ip_address=ip_address,
            user_agent=user_agent,
            process_time=process_time,
            error=error
        )
        
        # Monitor for suspicious activity
        await self._monitor_suspicious_activity(
            request=request,
            response=response,
            user_id=user_id,
            ip_address=ip_address,
            process_time=process_time
        )
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP address considering proxies"""
        # Check for forwarded headers (common in production)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    async def _log_security_action(
        self,
        request: Request,
        response: Response,
        user_id: str,
        method: str,
        path: str,
        query_params: str,
        ip_address: str,
        user_agent: str,
        process_time: float,
        error: str = None
    ):
        """Log security-relevant actions"""
        try:
            # Determine if this action should be logged
            should_log = self._should_log_action(method, path, response.status_code if response else 500)
            
            if not should_log:
                return
            
            # Determine action type
            action = self._determine_action_type(method, path)
            
            # Extract resource information
            resource_type, resource_id = self._extract_resource_info(path)
            
            # Prepare audit details
            details = {
                "method": method,
                "path": path,
                "query_params": query_params,
                "status_code": response.status_code if response else 500,
                "process_time": round(process_time, 3),
                "user_agent": user_agent
            }
            
            if error:
                details["error"] = error
            
            # Log to database
            db = next(get_db())
            await security_service.log_user_action(
                db=db,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                request=request
            )
            
        except Exception as e:
            logger.error(f"Failed to log security action: {str(e)}")
    
    def _should_log_action(self, method: str, path: str, status_code: int) -> bool:
        """Determine if action should be logged"""
        # Always log authentication actions
        if "/auth/" in path:
            return True
        
        # Log all write operations
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True
        
        # Log failed requests
        if status_code >= 400:
            return True
        
        # Log access to sensitive endpoints
        sensitive_paths = ["/admin/", "/security/", "/integrations/"]
        if any(sensitive in path for sensitive in sensitive_paths):
            return True
        
        return False
    
    def _determine_action_type(self, method: str, path: str) -> str:
        """Determine action type from method and path"""
        # Authentication actions
        if "/auth/login" in path:
            return "login"
        elif "/auth/logout" in path:
            return "logout"
        elif "/auth/register" in path:
            return "register"
        elif "/auth/" in path:
            return "auth_action"
        
        # CRUD operations
        if method == "POST":
            return "create"
        elif method == "PUT" or method == "PATCH":
            return "update"
        elif method == "DELETE":
            return "delete"
        elif method == "GET":
            return "read"
        
        return "unknown_action"
    
    def _extract_resource_info(self, path: str) -> tuple:
        """Extract resource type and ID from path"""
        path_parts = path.strip("/").split("/")
        
        # Skip api/v1 prefix
        if len(path_parts) >= 2 and path_parts[0] == "api" and path_parts[1] == "v1":
            path_parts = path_parts[2:]
        
        if not path_parts:
            return None, None
        
        resource_type = path_parts[0]
        resource_id = None
        
        # Try to find resource ID (usually UUID or numeric)
        for part in path_parts[1:]:
            if self._looks_like_id(part):
                resource_id = part
                break
        
        return resource_type, resource_id
    
    def _looks_like_id(self, value: str) -> bool:
        """Check if value looks like an ID"""
        # UUID pattern
        if len(value) == 36 and value.count("-") == 4:
            return True
        
        # Numeric ID
        if value.isdigit():
            return True
        
        return False
    
    async def _monitor_suspicious_activity(
        self,
        request: Request,
        response: Response,
        user_id: str,
        ip_address: str,
        process_time: float
    ):
        """Monitor for suspicious activity patterns"""
        try:
            # Monitor for brute force attacks
            if "/auth/login" in request.url.path and response and response.status_code == 401:
                await self._check_brute_force(ip_address, user_id)
            
            # Monitor for unusual response times
            if process_time > 10.0:  # Requests taking more than 10 seconds
                await self._log_slow_request(request, process_time, user_id)
            
            # Monitor for error patterns
            if response and response.status_code >= 500:
                await self._log_server_error(request, response.status_code, user_id)
            
        except Exception as e:
            logger.error(f"Failed to monitor suspicious activity: {str(e)}")
    
    async def _check_brute_force(self, ip_address: str, user_id: str):
        """Check for brute force login attempts"""
        # This would typically check recent failed login attempts
        # For now, just log the attempt
        logger.warning(f"Failed login attempt from IP: {ip_address}, User: {user_id}")
    
    async def _log_slow_request(self, request: Request, process_time: float, user_id: str):
        """Log unusually slow requests"""
        logger.warning(
            f"Slow request detected: {request.method} {request.url.path} "
            f"took {process_time:.2f}s for user {user_id}"
        )
    
    async def _log_server_error(self, request: Request, status_code: int, user_id: str):
        """Log server errors for monitoring"""
        logger.error(
            f"Server error {status_code}: {request.method} {request.url.path} "
            f"for user {user_id}"
        )
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        if not response:
            return
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Add HSTS header for HTTPS (in production)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"