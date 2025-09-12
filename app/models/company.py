"""
Company and User models
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Company(Base):
    """Company model for multi-tenant architecture"""
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    settings = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")
    interview_templates = relationship("InterviewTemplate", back_populates="company", cascade="all, delete-orphan")
    
    # Admin relationships
    roles = relationship("Role", back_populates="company", cascade="all, delete-orphan")
    branding = relationship("CompanyBranding", back_populates="company", uselist=False, cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="company", cascade="all, delete-orphan")
    
    # Security and compliance relationships
    data_retention_policies = relationship("DataRetentionPolicy", back_populates="company", cascade="all, delete-orphan")
    security_alerts = relationship("SecurityAlert", back_populates="company", cascade="all, delete-orphan")
    compliance_logs = relationship("ComplianceLog", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"


class User(Base):
    """User model with role-based access control"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin, recruiter, interviewer
    profile = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="users")
    created_jobs = relationship("Job", back_populates="created_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Admin relationships
    user_roles = relationship("UserRole", foreign_keys="UserRole.user_id", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_recruiter(self):
        return self.role in ["admin", "recruiter"]

    @property
    def is_interviewer(self):
        return self.role in ["admin", "recruiter", "interviewer"]

    def update_last_login(self):
        """Update last login timestamp"""
        from datetime import datetime
        self.last_login = datetime.utcnow()

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission through their roles"""
        from datetime import datetime
        current_time = datetime.utcnow()
        
        for user_role in self.user_roles:
            # Skip expired roles
            if user_role.is_expired:
                continue
                
            if user_role.role.has_permission(permission):
                return True
        
        return False

    def get_permissions(self) -> list:
        """Get all permissions for this user"""
        from datetime import datetime
        current_time = datetime.utcnow()
        permissions = set()
        
        for user_role in self.user_roles:
            # Skip expired roles
            if user_role.is_expired:
                continue
                
            permissions.update(user_role.role.permissions)
        
        return list(permissions)