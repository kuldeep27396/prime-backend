"""
Assessment system models
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Assessment(Base):
    """Assessment model for technical and behavioral evaluations"""
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)  # coding, behavioral, cognitive
    questions = Column(JSONB, default=[])  # list of question objects
    responses = Column(JSONB, default=[])  # list of response objects
    auto_grade = Column(JSONB, nullable=True)  # automated grading results
    manual_grade = Column(JSONB, nullable=True)  # manual grading results
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    application = relationship("Application", back_populates="assessments")
    assessment_questions = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan")
    assessment_responses = relationship("AssessmentResponse", back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assessment(id={self.id}, type='{self.type}', application_id={self.application_id})>"


class AssessmentQuestion(Base):
    """Individual assessment question model"""
    __tablename__ = "assessment_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(String, nullable=False)  # coding, multiple_choice, whiteboard, essay
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    test_cases = Column(JSONB, default=[])  # for coding questions
    expected_answer = Column(Text, nullable=True)  # for non-coding questions
    time_limit = Column(Integer, nullable=True)  # time limit in seconds
    difficulty = Column(String, default="medium")  # easy, medium, hard
    points = Column(Integer, default=10)  # points for this question
    question_metadata = Column(JSONB, default={})  # question-specific metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assessment = relationship("Assessment", back_populates="assessment_questions")
    responses = relationship("AssessmentResponse", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AssessmentQuestion(id={self.id}, type='{self.question_type}', title='{self.title}')>"


class AssessmentResponse(Base):
    """Assessment response model for storing candidate answers"""
    __tablename__ = "assessment_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False)
    response_content = Column(Text, nullable=True)  # text response or code
    media_url = Column(String, nullable=True)  # for whiteboard or video responses
    execution_result = Column(JSONB, nullable=True)  # for coding questions
    time_taken = Column(Integer, nullable=True)  # time taken in seconds
    auto_score = Column(Numeric(5, 2), nullable=True)  # automated score (0-100)
    manual_score = Column(Numeric(5, 2), nullable=True)  # manual score (0-100)
    feedback = Column(Text, nullable=True)  # feedback on the response
    response_metadata = Column(JSONB, default={})  # response-specific metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    assessment = relationship("Assessment", back_populates="assessment_responses")
    question = relationship("AssessmentQuestion", back_populates="responses")

    def __repr__(self):
        return f"<AssessmentResponse(id={self.id}, question_id={self.question_id}, auto_score={self.auto_score})>"