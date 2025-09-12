"""
Job, Candidate, and Application models
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Job(Base):
    """Job posting model"""
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    requirements = Column(JSONB, default={})  # skills, experience, education, location, salary
    status = Column(String, default="active")  # draft, active, paused, closed
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="jobs")
    created_by_user = relationship("User", back_populates="created_jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', status='{self.status}')>"


class Candidate(Base):
    """Candidate model"""
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)
    parsed_data = Column(JSONB, default={})  # skills, experience, education, certifications, languages
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.name}', email='{self.email}')>"


class Application(Base):
    """Job application model linking candidates to jobs"""
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="applied")  # applied, screening, interviewing, assessed, hired, rejected
    cover_letter = Column(Text, nullable=True)
    application_data = Column(JSONB, default={})  # additional application metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="application", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="application", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('job_id', 'candidate_id', name='unique_job_candidate_application'),
    )

    def __repr__(self):
        return f"<Application(id={self.id}, job_id={self.job_id}, candidate_id={self.candidate_id}, status='{self.status}')>"