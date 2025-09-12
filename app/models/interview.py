"""
Interview system models
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class InterviewTemplate(Base):
    """Interview template model for reusable interview configurations"""
    __tablename__ = "interview_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # template description
    type = Column(String, nullable=False)  # one_way, live_ai, technical
    questions = Column(JSONB, default=[])  # list of question objects
    settings = Column(JSONB, default={})  # template-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="interview_templates")
    interviews = relationship("Interview", back_populates="template")

    def __repr__(self):
        return f"<InterviewTemplate(id={self.id}, name='{self.name}', type='{self.type}')>"


class Interview(Base):
    """Interview instance model"""
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("interview_templates.id"), nullable=True)
    type = Column(String, nullable=False)  # one_way, live_ai, technical
    status = Column(String, default="scheduled")  # scheduled, in_progress, completed, cancelled
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    interview_metadata = Column(JSONB, default={})  # interview-specific metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    application = relationship("Application", back_populates="interviews")
    template = relationship("InterviewTemplate", back_populates="interviews")
    responses = relationship("InterviewResponse", back_populates="interview", cascade="all, delete-orphan")
    proctoring_events = relationship("ProctoringEvent", back_populates="interview", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Interview(id={self.id}, type='{self.type}', status='{self.status}')>"


class InterviewResponse(Base):
    """Interview response model for storing candidate responses"""
    __tablename__ = "interview_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String, nullable=False)  # reference to question in template or dynamic question
    response_type = Column(String, nullable=False)  # video, audio, text, code
    content = Column(Text, nullable=True)  # text content or transcript
    media_url = Column(String, nullable=True)  # URL to stored media file
    duration = Column(Integer, nullable=True)  # duration in seconds for media responses
    response_metadata = Column(JSONB, default={})  # response-specific metadata (sentiment, confidence, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    interview = relationship("Interview", back_populates="responses")

    def __repr__(self):
        return f"<InterviewResponse(id={self.id}, interview_id={self.interview_id}, response_type='{self.response_type}')>"