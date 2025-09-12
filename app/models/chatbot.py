"""
Chatbot pre-screening models
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class ChatbotTemplate(Base):
    """Chatbot conversation template for pre-screening"""
    __tablename__ = "chatbot_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True)
    question_flow = Column(JSONB, default=[])  # List of question configurations
    settings = Column(JSONB, default={})  # Chatbot behavior settings
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    job = relationship("Job")
    created_by_user = relationship("User")
    sessions = relationship("ChatbotSession", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatbotTemplate(id={self.id}, name='{self.name}')>"


class ChatbotSession(Base):
    """Individual chatbot conversation session with a candidate"""
    __tablename__ = "chatbot_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("chatbot_templates.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="started")  # started, in_progress, completed, abandoned
    current_question_index = Column(Integer, default=0)
    conversation_history = Column(JSONB, default=[])  # List of messages
    responses = Column(JSONB, default={})  # Structured responses by question ID
    evaluation_results = Column(JSONB, default={})  # AI evaluation of responses
    overall_score = Column(Integer, nullable=True)  # 0-100 score
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    application = relationship("Application")
    template = relationship("ChatbotTemplate", back_populates="sessions")

    def __repr__(self):
        return f"<ChatbotSession(id={self.id}, status='{self.status}')>"


class ChatbotMessage(Base):
    """Individual messages in a chatbot conversation"""
    __tablename__ = "chatbot_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chatbot_sessions.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False)  # 'bot' or 'candidate'
    message_type = Column(String, default="text")  # text, question, response, system
    content = Column(Text, nullable=False)
    question_id = Column(String, nullable=True)  # Reference to question in template
    message_metadata = Column(JSONB, default={})  # Additional message data
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatbotSession")

    def __repr__(self):
        return f"<ChatbotMessage(id={self.id}, sender='{self.sender}', type='{self.message_type}')>"