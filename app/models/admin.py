"""
Enterprise admin models for multi-tenant architecture and advanced features
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum

from app.core.database import Base


class PermissionType(str, Enum):
    """Permission types for granular access control"""
    # Job management
    JOB_CREATE = "job:create"
    JOB_READ = "job:read"
    JOB_UPDATE = "job:update"
    JOB_DELETE = "job:delete"
    
    # Candidate management
    CANDIDATE_CREATE = "candidate:create"
    CANDIDATE_READ = "candidate:read"
    CANDIDATE_UPDATE = "candidate:update"
    CANDIDATE_DELETE = "candidate:delete"
    CANDIDATE_EXPORT = "candidate:export"
    
    # Interview management
    INTERVIEW_CREATE = "interview:create"
    INTERVIEW_READ = "interview:read"
    INTERVIEW_UPDATE = "interview:update"
    INTERVIEW_DELETE = "interview:delete"
    INTERVIEW_CONDUCT = "interview:conduct"
    
    # Assessment management
    ASSESSMENT_CREATE = "assessment:create"
    ASSESSMENT_READ = "assessment:read"
    ASSESSMENT_UPDATE = "assessment:update"
    ASSESSMENT_DELETE = "assessment:delete"
    ASSESSMENT_GRADE = "assessment:grade"
    
    # Analytics and reporting
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    REPORTS_GENERATE = "reports:generate"
    
    # Admin functions
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_INTEGRATIONS = "admin:integrations"
    ADMIN_TEMPLATES = "admin:templates"
    ADMIN_BRANDING = "admin:branding"
    
    # System functions
    SYSTEM_AUDIT = "system:audit"
    SYSTEM_BACKUP = "system:backup"


class Role(Base):
    """Role model for granular permission management"""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(ARRAY(String), default=[])  # List of permission strings
    is_system_role = Column(Boolean, default=False)  # System roles cannot be deleted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions

    def add_permission(self, permission: str):
        """Add permission to role"""
        if permission not in self.permissions:
            self.permissions = self.permissions + [permission]

    def remove_permission(self, permission: str):
        """Remove permission from role"""
        if permission in self.permissions:
            self.permissions = [p for p in self.permissions if p != permission]


class UserRole(Base):
    """User-Role association with optional resource-level permissions"""
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String, nullable=True)  # Optional: job, department, etc.
    resource_id = Column(String, nullable=True)  # Optional: specific resource ID
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    granted_by_user = relationship("User", foreign_keys=[granted_by])

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if role assignment is expired"""
        if not self.expires_at:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at


class CompanyBranding(Base):
    """Company branding and white-label configuration"""
    __tablename__ = "company_branding"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Branding assets
    logo_url = Column(String, nullable=True)
    favicon_url = Column(String, nullable=True)
    primary_color = Column(String, nullable=True)  # Hex color code
    secondary_color = Column(String, nullable=True)
    accent_color = Column(String, nullable=True)
    
    # Custom domain
    custom_domain = Column(String, nullable=True, unique=True)
    domain_verified = Column(Boolean, default=False)
    
    # Email branding
    email_header_logo = Column(String, nullable=True)
    email_footer_text = Column(Text, nullable=True)
    
    # Custom CSS
    custom_css = Column(Text, nullable=True)
    
    # Feature toggles
    features = Column(JSONB, default={})  # Custom feature configurations
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="branding")

    def __repr__(self):
        return f"<CompanyBranding(company_id={self.company_id}, custom_domain='{self.custom_domain}')>"


class Template(Base):
    """Template library for interviews, assessments, and communications"""
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)  # Null for global templates
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)  # interview, assessment, email, sms
    category = Column(String, nullable=True)  # technical, behavioral, etc.
    
    # Template content
    content = Column(JSONB, nullable=False)  # Template structure and content
    template_metadata = Column(JSONB, default={})  # Additional metadata
    
    # Template properties
    is_public = Column(Boolean, default=False)  # Available to all companies
    is_featured = Column(Boolean, default=False)  # Featured in template library
    usage_count = Column(Integer, default=0)  # Track template usage
    rating = Column(Integer, nullable=True)  # Average rating (1-5)
    
    # Versioning
    version = Column(String, default="1.0")
    parent_template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="templates")
    created_by_user = relationship("User")
    child_templates = relationship("Template", remote_side=[parent_template_id])

    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}', type='{self.type}')>"


class ReviewComment(Base):
    """Collaborative review comments for candidates and interviews"""
    __tablename__ = "review_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # What is being reviewed
    resource_type = Column(String, nullable=False)  # candidate, interview, assessment
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Comment details
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # Optional 1-5 rating
    tags = Column(ARRAY(String), default=[])  # Tags for categorization
    
    # Threading support
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("review_comments.id"), nullable=True)
    thread_id = Column(UUID(as_uuid=True), nullable=True)  # Root comment ID for threading
    
    # Metadata
    is_private = Column(Boolean, default=False)  # Private to author only
    is_resolved = Column(Boolean, default=False)  # For action items
    
    # Author and timestamps
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    author = relationship("User")
    parent_comment = relationship("ReviewComment", remote_side=[id])
    replies = relationship("ReviewComment", remote_side=[parent_comment_id], overlaps="parent_comment")

    def __repr__(self):
        return f"<ReviewComment(id={self.id}, resource_type='{self.resource_type}', author_id={self.author_id})>"


class DataExportRequest(Base):
    """Track data export requests for compliance and analytics"""
    __tablename__ = "data_export_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    # Export details
    export_type = Column(String, nullable=False)  # candidates, interviews, analytics, full_backup
    format = Column(String, nullable=False)  # csv, json, xlsx, pdf
    filters = Column(JSONB, default={})  # Export filters and parameters
    
    # Status tracking
    status = Column(String, default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # Progress percentage
    file_url = Column(String, nullable=True)  # URL to download file
    file_size = Column(Integer, nullable=True)  # File size in bytes
    expires_at = Column(DateTime(timezone=True), nullable=True)  # File expiration
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Request metadata
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    company = relationship("Company")
    requested_by_user = relationship("User")

    def __repr__(self):
        return f"<DataExportRequest(id={self.id}, export_type='{self.export_type}', status='{self.status}')>"