"""
Pydantic schemas for enterprise admin features
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid


# Role Management Schemas
class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(..., min_items=1)

    @validator('permissions')
    def validate_permissions(cls, v):
        from app.models.admin import PermissionType
        valid_permissions = [p.value for p in PermissionType]
        invalid = [p for p in v if p not in valid_permissions]
        if invalid:
            raise ValueError(f"Invalid permissions: {invalid}")
        return v


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = None

    @validator('permissions')
    def validate_permissions(cls, v):
        if v is not None:
            from app.models.admin import PermissionType
            valid_permissions = [p.value for p in PermissionType]
            invalid = [p for p in v if p not in valid_permissions]
            if invalid:
                raise ValueError(f"Invalid permissions: {invalid}")
        return v


class RoleResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    description: Optional[str]
    permissions: List[str]
    is_system_role: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserRoleAssignment(BaseModel):
    role_id: uuid.UUID
    expires_at: Optional[datetime] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None


# Company Branding Schemas
class CompanyBrandingUpdate(BaseModel):
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    custom_domain: Optional[str] = None
    email_header_logo: Optional[str] = None
    email_footer_text: Optional[str] = None
    custom_css: Optional[str] = None
    features: Optional[Dict[str, Any]] = None


class CompanyBrandingResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    company_id: uuid.UUID
    logo_url: Optional[str]
    favicon_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    accent_color: Optional[str]
    custom_domain: Optional[str]
    domain_verified: bool
    email_header_logo: Optional[str]
    email_footer_text: Optional[str]
    custom_css: Optional[str]
    features: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Template Library Schemas
class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    type: str = Field(..., pattern=r'^(interview|assessment|email|sms)$')
    category: Optional[str] = None
    content: Dict[str, Any] = Field(..., min_items=1)
    is_public: bool = False


class TemplateResponse(BaseModel):
    id: uuid.UUID
    company_id: Optional[uuid.UUID]
    name: str
    description: Optional[str]
    type: str
    category: Optional[str]
    content: Dict[str, Any]
    template_metadata: Dict[str, Any]
    is_public: bool
    is_featured: bool
    usage_count: int
    rating: Optional[int]
    version: str
    parent_template_id: Optional[uuid.UUID]
    created_by: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateClone(BaseModel):
    new_name: Optional[str] = None


# Collaborative Review Schemas
class ReviewCommentCreate(BaseModel):
    resource_type: str = Field(..., pattern=r'^(candidate|interview|assessment)$')
    resource_id: uuid.UUID
    content: str = Field(..., min_length=1, max_length=2000)
    parent_comment_id: Optional[uuid.UUID] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = None
    is_private: bool = False


class ReviewCommentResponse(BaseModel):
    id: uuid.UUID
    resource_type: str
    resource_id: uuid.UUID
    content: str
    rating: Optional[int]
    tags: List[str]
    parent_comment_id: Optional[uuid.UUID]
    thread_id: Optional[uuid.UUID]
    is_private: bool
    is_resolved: bool
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Data Export Schemas
class DataExportCreate(BaseModel):
    export_type: str = Field(..., pattern=r'^(candidates|interviews|analytics|full_backup)$')
    format: str = Field(..., pattern=r'^(csv|json|xlsx|pdf)$')
    filters: Dict[str, Any] = Field(default_factory=dict)


class DataExportResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    export_type: str
    format: str
    filters: Dict[str, Any]
    status: str
    progress: int
    file_url: Optional[str]
    file_size: Optional[int]
    expires_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    requested_by: uuid.UUID
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Analytics Schemas
class OverviewMetrics(BaseModel):
    total_jobs: int
    total_candidates: int
    total_interviews: int
    hire_rate: float


class FunnelMetrics(BaseModel):
    applications: int
    screening: int
    interviews: int
    offers: int
    hires: int


class PerformanceMetrics(BaseModel):
    avg_time_to_hire: int  # days
    interview_completion_rate: float
    candidate_satisfaction: float
    cost_per_hire: int


class TrendMetrics(BaseModel):
    applications_trend: List[int]
    hire_rate_trend: List[float]


class CompanyAnalyticsResponse(BaseModel):
    overview: OverviewMetrics
    funnel: FunnelMetrics
    performance: PerformanceMetrics
    trends: TrendMetrics


# Permission Management Schemas
class PermissionInfo(BaseModel):
    name: str
    description: str
    category: str


class PermissionListResponse(BaseModel):
    permissions: List[PermissionInfo]


# User Management Schemas
class UserWithRoles(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    last_login: Optional[datetime]
    assigned_roles: List[RoleResponse]
    permissions: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# System Configuration Schemas
class SystemSettings(BaseModel):
    max_file_size: int = Field(default=10485760)  # 10MB
    allowed_file_types: List[str] = Field(default=['pdf', 'doc', 'docx', 'txt'])
    session_timeout: int = Field(default=3600)  # 1 hour
    max_concurrent_interviews: int = Field(default=10)
    enable_proctoring: bool = Field(default=True)
    enable_ai_scoring: bool = Field(default=True)


class CompanySettingsUpdate(BaseModel):
    settings: SystemSettings


class CompanySettingsResponse(BaseModel):
    company_id: uuid.UUID
    settings: SystemSettings
    updated_at: datetime

    class Config:
        from_attributes = True