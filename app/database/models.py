from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    profile_image = Column(Text)
    role = Column(String(50), default='candidate', index=True)  # candidate, mentor, admin
    experience = Column(String(100))
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    skill_assessments = relationship("SkillAssessment", back_populates="user")
    reviews = relationship("Review", back_populates="user")

class Mentor(Base):
    __tablename__ = "mentors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    title = Column(String(255))
    current_company = Column(String(255), index=True)
    previous_companies = Column(JSONB)  # Array of companies
    avatar = Column(Text)
    bio = Column(Text)
    specialties = Column(JSONB)  # Array of specialties
    skills = Column(JSONB)  # Array of skills
    languages = Column(JSONB)  # Array of languages
    experience = Column(Integer, index=True)
    rating = Column(Numeric(3, 2), default=0, index=True)
    review_count = Column(Integer, default=0, index=True)
    hourly_rate = Column(Numeric(8, 2))
    response_time = Column(String(50))
    timezone = Column(String(100))
    availability = Column(JSONB)  # Array of available slots
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # Relationships
    user = relationship("User")
    sessions = relationship("Session", back_populates="mentor")
    reviews = relationship("Review", back_populates="mentor")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("mentors.id"), nullable=False, index=True)
    session_type = Column(String(255), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration = Column(Integer, nullable=False, index=True)  # Duration in minutes
    meeting_type = Column(String(50), index=True)  # video, audio, in-person
    meeting_link = Column(Text)
    status = Column(String(50), default='pending', index=True)  # pending, confirmed, completed, cancelled
    record_session = Column(Boolean, default=False)
    special_requests = Column(Text)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'))
    feedback = Column(Text)
    cancellation_reason = Column(Text)
    recording_url = Column(Text)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    mentor = relationship("Mentor", back_populates="sessions")
    reviews = relationship("Review", back_populates="session")
    video_rooms = relationship("VideoRoom", back_populates="session")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    recent_searches = Column(JSONB)  # Array of recent search terms
    favorite_topics = Column(JSONB)  # Array of favorite topics
    favorite_mentors = Column(JSONB)  # Array of mentor IDs
    timezone = Column(String(100))
    notification_settings = Column(JSONB)  # Email, SMS preferences
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="preferences")

class SkillAssessment(Base):
    __tablename__ = "skill_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    skill = Column(String(255), nullable=False, index=True)
    score = Column(Integer, CheckConstraint('score >= 0 AND score <= 100'), nullable=False, index=True)
    assessed_at = Column(DateTime, default=func.now(), index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    
    # Relationships
    user = relationship("User", back_populates="skill_assessments")
    session = relationship("Session")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("mentors.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False, index=True)
    comment = Column(Text)
    is_public = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    session = relationship("Session", back_populates="reviews")
    mentor = relationship("Mentor", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class VideoRoom(Base):
    __tablename__ = "video_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    room_url = Column(Text, nullable=False)
    participant_token = Column(Text)
    mentor_token = Column(Text)
    status = Column(String(50), default='active', index=True)  # active, ended
    recording_url = Column(Text)
    actual_duration = Column(Integer)  # Actual duration in minutes
    created_at = Column(DateTime, default=func.now(), index=True)
    ended_at = Column(DateTime)
    
    # Relationships
    session = relationship("Session", back_populates="video_rooms")