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
    participants = relationship("RoomParticipant", back_populates="video_room")

class RoomParticipant(Base):
    __tablename__ = "room_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(String(255), ForeignKey("video_rooms.room_id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    participant_type = Column(String(50), nullable=False, index=True)  # 'participant', 'mentor', 'observer'
    joined_at = Column(DateTime, default=func.now(), index=True)
    left_at = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    video_room = relationship("VideoRoom", back_populates="participants")
    user = relationship("User")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    target_companies = Column(JSONB)  # Array of target companies
    focus_areas = Column(JSONB)  # Array of focus areas
    preferred_interview_types = Column(JSONB)  # Array of preferred interview types
    years_of_experience = Column(Integer)
    current_role = Column(String(255))
    current_company = Column(String(255))
    location = Column(String(255))
    linkedin_url = Column(Text)
    github_url = Column(Text)
    portfolio_url = Column(Text)
    resume_url = Column(Text)
    bio = Column(Text)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User", uselist=False)

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    logo_url = Column(Text)
    website = Column(Text)
    industry = Column(String(255), index=True)
    size = Column(String(100))  # Company size category
    description = Column(Text)
    headquarters = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    job_postings = relationship("JobPosting", back_populates="company")
    company_mentors = relationship("CompanyMentor", back_populates="company")

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(255))
    location = Column(String(255))
    job_type = Column(String(100))  # Full-time, Part-time, Contract
    experience_level = Column(String(100))  # Entry, Mid, Senior
    salary_min = Column(Numeric(10, 2))
    salary_max = Column(Numeric(10, 2))
    description = Column(Text)
    requirements = Column(JSONB)  # Array of requirements
    skills_required = Column(JSONB)  # Array of required skills
    is_active = Column(Boolean, default=True, index=True)
    posted_at = Column(DateTime, default=func.now(), index=True)
    expires_at = Column(DateTime)

    # Relationships
    company = relationship("Company", back_populates="job_postings")

class CompanyMentor(Base):
    __tablename__ = "company_mentors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("mentors.id"), nullable=False, index=True)
    position = Column(String(255))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_current = Column(Boolean, default=True, index=True)

    # Relationships
    company = relationship("Company", back_populates="company_mentors")
    mentor = relationship("Mentor")

class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    content_type = Column(String(100), nullable=False, index=True)  # article, video, course, book
    url = Column(Text)
    thumbnail_url = Column(Text)
    difficulty_level = Column(String(50), index=True)  # beginner, intermediate, advanced
    duration_minutes = Column(Integer)
    skills_covered = Column(JSONB)  # Array of skills
    tags = Column(JSONB)  # Array of tags
    is_premium = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=0)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user_progress = relationship("UserProgress", back_populates="resource")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    question_type = Column(String(100), nullable=False, index=True)  # technical, behavioral, system_design
    difficulty = Column(String(50), index=True)  # easy, medium, hard
    category = Column(String(255), index=True)
    skills_tested = Column(JSONB)  # Array of skills
    expected_answer = Column(Text)
    follow_up_questions = Column(JSONB)  # Array of follow-up questions
    companies_asked_at = Column(JSONB)  # Array of company names
    time_limit_minutes = Column(Integer)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user_responses = relationship("UserResponse", back_populates="question")

class InterviewTemplate(Base):
    __tablename__ = "interview_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    interview_type = Column(String(100), nullable=False, index=True)  # technical, behavioral, system_design
    duration_minutes = Column(Integer, nullable=False)
    questions = Column(JSONB)  # Array of question IDs
    companies = Column(JSONB)  # Array of company names
    difficulty = Column(String(50), index=True)
    is_public = Column(Boolean, default=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    creator = relationship("User")

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("learning_resources.id"), nullable=False, index=True)
    status = Column(String(50), default='not_started', index=True)  # not_started, in_progress, completed
    progress_percentage = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    time_spent_minutes = Column(Integer, default=0)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'))
    notes = Column(Text)

    # Relationships
    user = relationship("User")
    resource = relationship("LearningResource", back_populates="user_progress")

class UserResponse(Base):
    __tablename__ = "user_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("interview_questions.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    response = Column(Text)
    is_correct = Column(Boolean)
    time_taken_seconds = Column(Integer)
    feedback = Column(Text)
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    user = relationship("User")
    question = relationship("InterviewQuestion", back_populates="user_responses")
    session = relationship("Session")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)  # session_reminder, mentor_review, system
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    is_email_sent = Column(Boolean, default=False)
    is_sms_sent = Column(Boolean, default=False)
    scheduled_at = Column(DateTime, index=True)
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    user = relationship("User")

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    subject = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    template_type = Column(String(100), nullable=False, index=True)  # session_booking, reminder, review_request
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

class UserAnalytics(Base):
    __tablename__ = "user_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    total_sessions = Column(Integer, default=0)
    completed_sessions = Column(Integer, default=0)
    average_rating = Column(Numeric(3, 2), default=0)
    total_time_spent_minutes = Column(Integer, default=0)
    skills_improved = Column(JSONB)  # Array of skills with improvement data
    companies_interviewed_with = Column(JSONB)  # Array of company names
    session_history = Column(JSONB)  # Detailed session performance data
    streak_days = Column(Integer, default=0)
    last_activity_at = Column(DateTime, default=func.now(), index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User", uselist=False)

class SessionAnalytics(Base):
    __tablename__ = "session_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("mentors.id"), nullable=False, index=True)
    performance_score = Column(Integer, CheckConstraint('performance_score >= 0 AND performance_score <= 100'))
    technical_score = Column(Integer, CheckConstraint('technical_score >= 0 AND technical_score <= 100'))
    communication_score = Column(Integer, CheckConstraint('communication_score >= 0 AND communication_score <= 100'))
    problem_solving_score = Column(Integer, CheckConstraint('problem_solving_score >= 0 AND problem_solving_score <= 100'))
    feedback_summary = Column(Text)
    key_improvements = Column(JSONB)  # Array of improvement areas
    strengths = Column(JSONB)  # Array of strengths
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    session = relationship("Session")
    user = relationship("User")
    mentor = relationship("Mentor")

class SkillProgression(Base):
    __tablename__ = "skill_progression"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    skill = Column(String(255), nullable=False, index=True)
    initial_score = Column(Integer, CheckConstraint('initial_score >= 0 AND initial_score <= 100'))
    current_score = Column(Integer, CheckConstraint('current_score >= 0 AND current_score <= 100'))
    improvement_percentage = Column(Numeric(5, 2))
    assessments_count = Column(Integer, default=0)
    last_assessed_at = Column(DateTime, default=func.now(), index=True)
    next_recommended_assessment = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User")

class MentorAvailability(Base):
    __tablename__ = "mentor_availability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("mentors.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False, index=True)  # 0-6 (Sunday-Saturday)
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)  # HH:MM format
    timezone = Column(String(100), nullable=False)
    is_available = Column(Boolean, default=True, index=True)
    recurring = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    mentor = relationship("Mentor")