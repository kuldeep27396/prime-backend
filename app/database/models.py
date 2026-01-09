"""
PRIME Interviews Database Models
Version 3.0 - B2B Screening + AI Mock Interviews

This module defines all SQLAlchemy ORM models for the platform.
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, Numeric, ForeignKey, CheckConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

Base = declarative_base()


# ==========================================
# ENUMS
# ==========================================

class PlanType(str, enum.Enum):
    FREE = "free"  # 2 interviews
    STARTER = "starter"  # 1-100 interviews
    GROWTH = "growth"  # 100-1000 interviews
    ENTERPRISE = "enterprise"  # 1000+ interviews
    PAY_PER_USE = "pay_per_use"  # Per interview cost


class CandidateStatus(str, enum.Enum):
    APPLIED = "applied"
    INVITED = "invited"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"


class InterviewStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class InterviewType(str, enum.Enum):
    SCREENING = "screening"  # B2B candidate screening
    MOCK = "mock"  # Individual practice


class MockCategory(str, enum.Enum):
    DSA = "dsa"  # Data Structures & Algorithms
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"


# ==========================================
# CORE USER MODELS
# ==========================================

class User(Base):
    """Platform users - both B2C mock users and company admins"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)  # Clerk user ID
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    profile_image = Column(Text)
    role = Column(String(50), default='user', index=True)  # user, company_admin, super_admin
    experience = Column(String(100))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)  # For company admins
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    mock_sessions = relationship("AIInterviewSession", back_populates="user", foreign_keys="AIInterviewSession.user_id")
    skill_assessments = relationship("SkillAssessment", back_populates="user")
    company = relationship("Company", back_populates="admins")


class UserPreference(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    recent_searches = Column(JSONB)  # Array of recent search terms
    favorite_topics = Column(JSONB)  # Array of favorite mock topics
    preferred_difficulty = Column(String(50), default='medium')  # easy, medium, hard
    timezone = Column(String(100))
    notification_settings = Column(JSONB)  # Email, SMS preferences
    mock_history_public = Column(Boolean, default=False)  # Share mock progress
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class SkillAssessment(Base):
    """Skill evaluation records from mock interviews"""
    __tablename__ = "skill_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    skill = Column(String(255), nullable=False, index=True)
    score = Column(Integer, CheckConstraint('score >= 0 AND score <= 100'), nullable=False, index=True)
    assessed_at = Column(DateTime, default=func.now(), index=True)
    interview_session_id = Column(UUID(as_uuid=True), ForeignKey("ai_interview_sessions.id"))
    
    # Relationships
    user = relationship("User", back_populates="skill_assessments")
    interview_session = relationship("AIInterviewSession")


class Session(Base):
    """User login sessions (maintained for backwards compatibility)"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_info = Column(Text)
    ip_address = Column(String(45))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_active = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


# ==========================================
# B2B COMPANY MODELS
# ==========================================

class Company(Base):
    """B2B client companies that use screening platform"""
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    logo_url = Column(Text)
    website = Column(Text)
    industry = Column(String(255), index=True)
    company_size = Column(String(50))  # 1-10, 11-50, 51-200, 201-500, 500+
    description = Column(Text)
    headquarters = Column(String(255))
    
    # Billing & Plan
    plan_type = Column(String(50), default=PlanType.FREE.value, index=True)
    credits_remaining = Column(Integer, default=2)  # Free tier = 2 interviews
    credits_used = Column(Integer, default=0)
    billing_email = Column(String(255))
    stripe_customer_id = Column(String(255))  # For future Stripe integration
    
    is_active = Column(Boolean, default=True, index=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    admins = relationship("User", back_populates="company")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class Job(Base):
    """Job postings created by companies"""
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    
    # Job Details
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    requirements = Column(JSONB)  # Array of requirements
    skills_required = Column(JSONB)  # Array of required skills
    experience_min = Column(Integer, default=0)
    experience_max = Column(Integer, default=20)
    location = Column(String(255))
    job_type = Column(String(50), index=True)  # full-time, part-time, contract, remote
    department = Column(String(255))
    salary_min = Column(Numeric(10, 2))
    salary_max = Column(Numeric(10, 2))
    
    # AI Interview Configuration
    ai_questions = Column(JSONB)  # Custom questions for AI to ask
    question_count = Column(Integer, default=5)  # Number of AI questions
    interview_duration = Column(Integer, default=15)  # Duration in minutes
    difficulty_level = Column(String(50), default='medium')  # easy, medium, hard
    passing_score = Column(Integer, default=60)  # Minimum score to shortlist
    
    # Status
    status = Column(String(50), default='active', index=True)  # draft, active, paused, closed
    is_public = Column(Boolean, default=True)  # Public application link
    application_deadline = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    """Candidates who apply to jobs"""
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Candidate Info
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50))
    linkedin_url = Column(Text)
    
    # Resume
    resume_url = Column(Text)  # Stored file URL
    resume_text = Column(Text)  # Extracted text for AI parsing
    resume_parsed = Column(JSONB)  # ATS-style parsed data: skills, experience, education
    
    # Application Status
    status = Column(String(50), default=CandidateStatus.APPLIED.value, index=True)
    
    # AI Evaluation
    ai_score = Column(Integer, CheckConstraint('ai_score >= 0 AND ai_score <= 100'))
    ai_summary = Column(Text)  # AI-generated summary
    ai_strengths = Column(JSONB)  # Array of strengths
    ai_weaknesses = Column(JSONB)  # Array of areas to improve
    ai_recommendation = Column(String(50))  # strongly_recommend, recommend, neutral, not_recommend
    shortlisted = Column(Boolean, default=False, index=True)
    shortlist_reason = Column(Text)  # Why AI shortlisted/rejected
    
    # Interview
    interview_token = Column(String(255), unique=True, index=True)  # Unique token for interview link
    interview_link = Column(Text)  # Full interview URL
    interview_sent_at = Column(DateTime)
    interview_expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    job = relationship("Job", back_populates="candidates")
    interview_sessions = relationship("AIInterviewSession", back_populates="candidate")


# ==========================================
# AI INTERVIEW MODELS
# ==========================================

class AIInterviewSession(Base):
    """AI-powered interview sessions for both B2B screening and mock practice"""
    __tablename__ = "ai_interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Owner - either a candidate (B2B) or user (mock practice)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True, index=True)
    
    # Interview Type
    interview_type = Column(String(50), nullable=False, index=True)  # screening, mock
    mock_category = Column(String(50), index=True)  # For mock: dsa, system_design, behavioral, etc.
    topic = Column(String(255))  # Specific topic being tested
    difficulty = Column(String(50), default='medium')
    
    # Status
    status = Column(String(50), default=InterviewStatus.PENDING.value, index=True)
    
    # Timing
    scheduled_at = Column(DateTime, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_minutes = Column(Integer)
    actual_duration_seconds = Column(Integer)  # Actual time taken
    
    # Questions & Answers (stored as JSONB)
    questions = Column(JSONB)  # [{id, question, expected_answer, category, difficulty}]
    answers = Column(JSONB)  # [{question_id, answer_text, answer_audio_url, timestamp}]
    
    # AI Evaluation
    ai_evaluation = Column(JSONB)  # Per-question scores and feedback
    overall_score = Column(Integer, CheckConstraint('overall_score >= 0 AND overall_score <= 100'))
    technical_score = Column(Integer)
    communication_score = Column(Integer)
    problem_solving_score = Column(Integer)
    ai_feedback = Column(Text)  # Overall AI feedback
    
    # Recording (TODO: implement later with 7-day retention)
    recording_url = Column(Text)
    recording_expires_at = Column(DateTime)
    
    # Metadata
    browser_info = Column(JSONB)  # Device/browser info
    ip_address = Column(String(50))
    
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="interview_sessions")
    user = relationship("User", back_populates="mock_sessions", foreign_keys=[user_id])
    job = relationship("Job")


class InterviewQuestion(Base):
    """Question bank for AI interviews"""
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    question = Column(Text, nullable=False)
    question_type = Column(String(100), nullable=False, index=True)  # technical, behavioral, situational
    category = Column(String(100), nullable=False, index=True)  # dsa, system_design, frontend, etc.
    difficulty = Column(String(50), index=True)  # easy, medium, hard
    
    # Expected answer and evaluation criteria
    expected_answer = Column(Text)
    evaluation_criteria = Column(JSONB)  # What AI should look for
    keywords = Column(JSONB)  # Key terms that should be mentioned
    follow_up_questions = Column(JSONB)  # Potential follow-ups
    
    # Metadata
    skills_tested = Column(JSONB)  # Array of skills
    companies_asked_at = Column(JSONB)  # Companies known to ask this
    time_limit_seconds = Column(Integer, default=180)  # 3 minutes default
    
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)


# ==========================================
# MOCK INTERVIEW SPECIFIC MODELS
# ==========================================

class MockInterviewCategory(Base):
    """Categories for mock interview practice"""
    __tablename__ = "mock_interview_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(50))  # Icon name for UI
    color = Column(String(50))  # Theme color
    
    # Topics within this category
    topics = Column(JSONB)  # [{name, description, difficulty_levels, question_count}]
    
    # Difficulty levels available
    difficulty_levels = Column(JSONB, default=['easy', 'medium', 'hard'])
    
    order_index = Column(Integer, default=0)  # For display ordering
    is_active = Column(Boolean, default=True, index=True)
    is_premium = Column(Boolean, default=False)  # Premium-only category
    
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)


class UserMockProgress(Base):
    """Track user progress in mock interviews"""
    __tablename__ = "user_mock_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    category = Column(String(100), nullable=False, index=True)
    topic = Column(String(255))
    
    # Progress stats
    total_attempts = Column(Integer, default=0)
    best_score = Column(Integer, default=0)
    average_score = Column(Numeric(5, 2), default=0)
    last_attempt_at = Column(DateTime)
    last_score = Column(Integer)
    
    # Time tracking
    total_time_spent_seconds = Column(Integer, default=0)
    
    # Streak
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User")


# ==========================================
# NOTIFICATION & EMAIL MODELS
# ==========================================

class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=True, index=True)
    
    type = Column(String(100), nullable=False, index=True)  # interview_invite, shortlist, mock_complete
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    is_read = Column(Boolean, default=False, index=True)
    is_email_sent = Column(Boolean, default=False)
    
    scheduled_at = Column(DateTime, index=True)
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    user = relationship("User")


class EmailLog(Base):
    """Log of all emails sent"""
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    to_email = Column(String(255), nullable=False, index=True)
    to_name = Column(String(255))
    subject = Column(String(500), nullable=False)
    email_type = Column(String(100), index=True)  # interview_invite, shortlist_notice, etc.
    
    # Related entities
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    
    status = Column(String(50), default='sent', index=True)  # sent, delivered, opened, bounced, failed
    provider_message_id = Column(String(255))  # ID from Brevo/email provider
    
    sent_at = Column(DateTime, default=func.now(), index=True)
    opened_at = Column(DateTime)


# ==========================================
# ANALYTICS MODELS
# ==========================================

class CompanyAnalytics(Base):
    """Analytics for B2B companies"""
    __tablename__ = "company_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, unique=True, index=True)
    
    # Totals
    total_jobs_posted = Column(Integer, default=0)
    total_candidates = Column(Integer, default=0)
    total_interviews_conducted = Column(Integer, default=0)
    total_shortlisted = Column(Integer, default=0)
    total_hired = Column(Integer, default=0)
    
    # Averages
    average_candidate_score = Column(Numeric(5, 2), default=0)
    average_time_to_shortlist_hours = Column(Numeric(10, 2), default=0)
    
    # Monthly data
    monthly_stats = Column(JSONB)  # [{month, candidates, interviews, shortlisted}]
    
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    company = relationship("Company")


class UserAnalytics(Base):
    """Analytics for individual users (mock interviews)"""
    __tablename__ = "user_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Mock interview stats
    total_mock_sessions = Column(Integer, default=0)
    total_time_spent_minutes = Column(Integer, default=0)
    average_score = Column(Numeric(5, 2), default=0)
    best_score = Column(Integer, default=0)
    
    # Category breakdown
    category_stats = Column(JSONB)  # {dsa: {attempts, avg_score}, system_design: {...}}
    
    # Skills
    skills_improved = Column(JSONB)  # Array of skills with improvement data
    weak_areas = Column(JSONB)  # Areas needing improvement
    
    # Streaks
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_activity_at = Column(DateTime, default=func.now(), index=True)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User")


# ==========================================
# LEGACY STUBS (for backwards compatibility)
# ==========================================

class Mentor(Base):
    """Legacy: Stub for backwards compatibility with existing routers"""
    __tablename__ = "mentors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    name = Column(String(255))
    email = Column(String(255))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class VideoRoom(Base):
    """Legacy: Stub for backwards compatibility with existing routers"""
    __tablename__ = "video_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class UserProfile(Base):
    """Legacy: Stub for backwards compatibility"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    bio = Column(Text)
    skills = Column(JSONB)
    created_at = Column(DateTime, default=func.now())


class SkillProgression(Base):
    """Legacy: Stub for backwards compatibility"""
    __tablename__ = "skill_progressions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    skill = Column(String(255))
    level = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class SessionAnalytics(Base):
    """Legacy: Stub for backwards compatibility"""
    __tablename__ = "session_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), index=True)
    data = Column(JSONB)
    created_at = Column(DateTime, default=func.now())


class Review(Base):
    """Legacy: Stub for backwards compatibility"""
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=func.now())


class LearningResource(Base):
    """Legacy: Stub for backwards compatibility"""
    __tablename__ = "learning_resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255))
    content = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime, default=func.now())


class InterviewTemplate(Base):
    """Legacy: Stub for backwards compatibility"""
    __tablename__ = "interview_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    questions = Column(JSONB)
    created_at = Column(DateTime, default=func.now())


class UserProgress(Base):
    """Legacy: Stub for backwards compatibility"""
    __tablename__ = "user_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    progress_data = Column(JSONB)
    created_at = Column(DateTime, default=func.now())


class UserResponse(Base):
    """Legacy: Stub for backwards compatibility"""
    __tablename__ = "user_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    question_id = Column(UUID(as_uuid=True))
    response = Column(Text)
    created_at = Column(DateTime, default=func.now())