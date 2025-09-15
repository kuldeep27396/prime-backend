from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

class SuccessResponse(BaseModel):
    """Standard success response schema"""
    success: bool = Field(True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")

class ErrorDetail(BaseModel):
    """Error detail schema"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    success: bool = Field(False, description="Success status")
    error: ErrorDetail = Field(..., description="Error details")

class ValidationErrorResponse(BaseModel):
    """Validation error response schema"""
    success: bool = Field(False, description="Success status")
    error: Dict[str, Any] = Field(..., description="Validation error details")

# Common error codes
class ErrorCodes:
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"