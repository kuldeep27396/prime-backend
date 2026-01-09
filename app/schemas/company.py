"""
Company & Job Pydantic Schemas
For B2B client management and job posting
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


# ==========================================
# ENUMS
# ==========================================

class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"
    PAY_PER_USE = "pay_per_use"


class JobStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class JobType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    REMOTE = "remote"
    HYBRID = "hybrid"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ==========================================
# COMPANY SCHEMAS
# ==========================================

class CompanyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, example="Acme Corp")
    email: EmailStr = Field(..., example="hr@acme.com")
    website: Optional[str] = Field(None, example="https://acme.com")
    industry: Optional[str] = Field(None, example="Technology")
    company_size: Optional[str] = Field(None, example="51-200")
    description: Optional[str] = Field(None, example="Leading tech company...")
    headquarters: Optional[str] = Field(None, example="San Francisco, CA")


class CompanyCreate(CompanyBase):
    """Schema for creating a new company"""
    billing_email: Optional[EmailStr] = None


class CompanyUpdate(BaseModel):
    """Schema for updating company details"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    description: Optional[str] = None
    headquarters: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    logo_url: Optional[str] = None


class CompanyResponse(CompanyBase):
    """Company response schema"""
    id: str
    logo_url: Optional[str] = None
    plan_type: str = "free"
    credits_remaining: int = 2
    credits_used: int = 0
    is_active: bool = True
    onboarding_completed: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyStats(BaseModel):
    """Company statistics summary"""
    total_jobs: int = 0
    active_jobs: int = 0
    total_candidates: int = 0
    total_interviews: int = 0
    total_shortlisted: int = 0
    credits_remaining: int = 0
    credits_used: int = 0


class CompanyWithStats(CompanyResponse):
    """Company response with statistics"""
    stats: CompanyStats


# ==========================================
# JOB SCHEMAS
# ==========================================

class AIQuestionConfig(BaseModel):
    """Configuration for AI interview questions"""
    question: str = Field(..., example="Tell me about your experience with React")
    category: Optional[str] = Field(None, example="technical")
    weight: Optional[int] = Field(1, ge=1, le=10, description="Question importance weight")


class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, example="Senior Software Engineer")
    description: Optional[str] = Field(None, example="We are looking for...")
    requirements: Optional[List[str]] = Field(None, example=["5+ years experience", "React expertise"])
    skills_required: Optional[List[str]] = Field(None, example=["Python", "JavaScript", "AWS"])
    experience_min: Optional[int] = Field(0, ge=0, le=50)
    experience_max: Optional[int] = Field(20, ge=0, le=50)
    location: Optional[str] = Field(None, example="San Francisco, CA or Remote")
    job_type: Optional[JobType] = Field(None, example="full-time")
    department: Optional[str] = Field(None, example="Engineering")
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)


class JobCreate(JobBase):
    """Schema for creating a new job"""
    # AI Interview Configuration
    ai_questions: Optional[List[AIQuestionConfig]] = Field(
        None, 
        description="Custom AI interview questions"
    )
    question_count: int = Field(5, ge=3, le=15, description="Number of AI questions")
    interview_duration: int = Field(15, ge=5, le=60, description="Duration in minutes")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.MEDIUM)
    passing_score: int = Field(60, ge=0, le=100, description="Minimum score to shortlist")
    
    # Status
    status: JobStatus = Field(JobStatus.ACTIVE)
    is_public: bool = Field(True, description="Allow public applications")
    application_deadline: Optional[datetime] = None


class JobUpdate(BaseModel):
    """Schema for updating job details"""
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    experience_min: Optional[int] = Field(None, ge=0, le=50)
    experience_max: Optional[int] = Field(None, ge=0, le=50)
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    department: Optional[str] = None
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    
    # AI Config
    ai_questions: Optional[List[AIQuestionConfig]] = None
    question_count: Optional[int] = Field(None, ge=3, le=15)
    interview_duration: Optional[int] = Field(None, ge=5, le=60)
    difficulty_level: Optional[DifficultyLevel] = None
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    
    # Status
    status: Optional[JobStatus] = None
    is_public: Optional[bool] = None
    application_deadline: Optional[datetime] = None


class JobResponse(JobBase):
    """Job response schema"""
    id: str
    company_id: str
    
    # AI Config
    ai_questions: Optional[List[Dict[str, Any]]] = None
    question_count: int = 5
    interview_duration: int = 15
    difficulty_level: str = "medium"
    passing_score: int = 60
    
    # Status
    status: str = "active"
    is_public: bool = True
    application_deadline: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobStats(BaseModel):
    """Job statistics"""
    total_candidates: int = 0
    pending_candidates: int = 0
    interviewed_candidates: int = 0
    shortlisted_candidates: int = 0
    rejected_candidates: int = 0


class JobWithStats(JobResponse):
    """Job response with statistics"""
    stats: JobStats
    company_name: Optional[str] = None
    company_logo: Optional[str] = None


class JobListResponse(BaseModel):
    """Paginated job list response"""
    jobs: List[JobWithStats]
    total: int
    page: int
    limit: int
    total_pages: int


class JobPublicResponse(BaseModel):
    """Public job response (for apply page)"""
    id: str
    title: str
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    department: Optional[str] = None
    
    # Company info
    company_name: str
    company_logo: Optional[str] = None
    company_website: Optional[str] = None
    
    application_deadline: Optional[datetime] = None


# ==========================================
# SUCCESS RESPONSES
# ==========================================

class CompanyCreateResponse(BaseModel):
    """Response for company creation"""
    success: bool = True
    message: str = "Company registered successfully"
    company: CompanyResponse


class JobCreateResponse(BaseModel):
    """Response for job creation"""
    success: bool = True
    message: str = "Job created successfully"
    job: JobResponse


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
