"""
Audit and security models
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AuditLog(Base):
    """Audit log model for tracking user actions and system events"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # create, update, delete, login, logout, etc.
    resource_type = Column(String, nullable=True)  # job, candidate, interview, etc.
    resource_id = Column(String, nullable=True)  # ID of the affected resource
    details = Column(JSONB, default={})  # additional details about the action
    ip_address = Column(INET, nullable=True)  # IP address of the user
    user_agent = Column(Text, nullable=True)  # browser/client information
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', resource_type='{self.resource_type}')>"


class ProctoringEvent(Base):
    """Proctoring event model for tracking integrity violations during interviews"""
    __tablename__ = "proctoring_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=False)  # face_detection, voice_analysis, suspicious_activity, browser_focus_lost
    severity = Column(String, nullable=False)  # low, medium, high, critical
    details = Column(JSONB, default={})  # event-specific details
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    interview = relationship("Interview", back_populates="proctoring_events")

    def __repr__(self):
        return f"<ProctoringEvent(id={self.id}, event_type='{self.event_type}', severity='{self.severity}')>"

    @property
    def is_critical(self):
        """Check if this is a critical security event"""
        return self.severity == 'critical'

    @property
    def requires_attention(self):
        """Check if this event requires immediate attention"""
        return self.severity in ['high', 'critical']


class DataRetentionPolicy(Base):
    """Data retention policy model for GDPR compliance"""
    __tablename__ = "data_retention_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    data_type = Column(String, nullable=False)  # audit_logs, interviews, candidates, etc.
    retention_days = Column(Integer, nullable=False)  # Number of days to retain data
    auto_delete = Column(Boolean, default=True)  # Whether to automatically delete expired data
    encryption_required = Column(Boolean, default=False)  # Whether data must be encrypted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="data_retention_policies")

    def __repr__(self):
        return f"<DataRetentionPolicy(data_type='{self.data_type}', retention_days={self.retention_days})>"


class SecurityAlert(Base):
    """Security alert model for monitoring and notifications"""
    __tablename__ = "security_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String, nullable=False)  # critical_event, data_breach, suspicious_activity
    severity = Column(String, nullable=False)  # low, medium, high, critical
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    details = Column(JSONB, default={})
    resolved = Column(Boolean, default=False)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="security_alerts")
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<SecurityAlert(alert_type='{self.alert_type}', severity='{self.severity}')>"

    @property
    def is_critical(self):
        """Check if this is a critical alert"""
        return self.severity == 'critical'


class ComplianceLog(Base):
    """Compliance log model for tracking GDPR/CCPA actions"""
    __tablename__ = "compliance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(String, nullable=False)  # User ID or identifier of data subject
    action = Column(String, nullable=False)  # data_export, data_deletion, data_anonymization, consent_withdrawal
    legal_basis = Column(String, nullable=True)  # GDPR Article 6 basis
    details = Column(JSONB, default={})
    requested_by = Column(String, nullable=True)  # Email or identifier of requester
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="compliance_logs")
    processor = relationship("User", foreign_keys=[processed_by])

    def __repr__(self):
        return f"<ComplianceLog(action='{self.action}', subject_id='{self.subject_id}')>"