"""
Integration models for ATS, calendar, and communication services
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Integration(Base):
    """Base integration model"""
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # ats, calendar, communication
    provider = Column(String, nullable=False)  # greenhouse, google, resend, etc.
    enabled = Column(Boolean, default=True)
    credentials = Column(JSONB, default={})  # Encrypted credentials
    settings = Column(JSONB, default={})
    field_mappings = Column(JSONB, default=[])
    status = Column(String, default="pending")  # connected, disconnected, error, pending
    last_sync = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    sync_logs = relationship("SyncLog", back_populates="integration", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Integration(id={self.id}, name='{self.name}', type='{self.type}')>"


class SyncLog(Base):
    """Sync operation log"""
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    operation_type = Column(String, nullable=False)  # sync_candidates, sync_jobs, update_status
    status = Column(String, nullable=False)  # success, error, in_progress
    records_processed = Column(Integer, default=0)
    records_success = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_details = Column(JSONB, default=[])
    sync_metadata = Column(JSONB, default={})
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    integration = relationship("Integration", back_populates="sync_logs")

    def __repr__(self):
        return f"<SyncLog(id={self.id}, operation='{self.operation_type}', status='{self.status}')>"


class EmailTemplate(Base):
    """Email template model"""
    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=False)
    variables = Column(JSONB, default=[])
    category = Column(String, nullable=True)  # interview_invite, rejection, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    campaigns = relationship("Campaign", back_populates="template")

    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, name='{self.name}')>"


class Campaign(Base):
    """Email/SMS campaign model"""
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, default="email")  # email, sms
    status = Column(String, default="draft")  # draft, scheduled, running, completed, failed
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    recipients = Column(JSONB, default=[])
    variables = Column(JSONB, default={})  # per-recipient variables
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    template = relationship("EmailTemplate", back_populates="campaigns")

    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"


class CalendarEvent(Base):
    """Calendar event model"""
    __tablename__ = "calendar_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String, nullable=True)  # ID from calendar provider
    provider = Column(String, nullable=False)  # google, outlook
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String, default="UTC")
    attendees = Column(JSONB, default=[])
    location = Column(String, nullable=True)
    meeting_url = Column(String, nullable=True)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=True)
    status = Column(String, default="scheduled")  # scheduled, confirmed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    interview = relationship("Interview")

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title='{self.title}', start='{self.start_time}')>"