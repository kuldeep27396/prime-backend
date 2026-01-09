"""
Candidate Pydantic Schemas
For job applications and candidate management
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


# ==========================================
# ENUMS
# ==========================================

class CandidateStatus(str, Enum):
    APPLIED = "applied"
    INVITED = "invited"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"


class AIRecommendation(str, Enum):
    STRONGLY_RECOMMEND = "strongly_recommend"
    RECOMMEND = "recommend"
    NEUTRAL = "neutral"
    NOT_RECOMMEND = "not_recommend"


# ==========================================
# RESUME SCHEMAS
# ==========================================

class ParsedResume(BaseModel):
    """Parsed resume data (ATS-style)"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    
    # Experience
    years_of_experience: Optional[int] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    work_history: Optional[List[Dict[str, Any]]] = None
    
    # Skills
    skills: Optional[List[str]] = None
    programming_languages: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    
    # Education
    education: Optional[List[Dict[str, Any]]] = None
    highest_degree: Optional[str] = None
    
    # Additional
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


# ==========================================
# CANDIDATE SCHEMAS
# ==========================================

class CandidateBase(BaseModel):
    email: EmailStr = Field(..., example="candidate@example.com")
    name: str = Field(..., min_length=2, max_length=255, example="John Doe")
    phone: Optional[str] = Field(None, max_length=50, example="+1-555-123-4567")
    linkedin_url: Optional[str] = Field(None, example="https://linkedin.com/in/johndoe")


class CandidateApply(CandidateBase):
    """Schema for candidate job application (public)"""
    # Resume will be uploaded separately via multipart form
    cover_letter: Optional[str] = Field(None, max_length=5000)
    
    class Config:
        from_attributes = True


class CandidateCreate(CandidateBase):
    """Schema for creating candidate (internal/bulk upload)"""
    job_id: str
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None


class CandidateBulkUpload(BaseModel):
    """Schema for bulk candidate upload"""
    candidates: List[CandidateCreate]


class CandidateUpdate(BaseModel):
    """Schema for updating candidate"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = None
    status: Optional[CandidateStatus] = None


class CandidateStatusUpdate(BaseModel):
    """Schema for updating candidate status"""
    status: CandidateStatus
    notes: Optional[str] = None


# ==========================================
# AI EVALUATION SCHEMAS
# ==========================================

class AIEvaluation(BaseModel):
    """AI evaluation summary for a candidate"""
    overall_score: int = Field(..., ge=0, le=100)
    technical_score: Optional[int] = Field(None, ge=0, le=100)
    communication_score: Optional[int] = Field(None, ge=0, le=100)
    problem_solving_score: Optional[int] = Field(None, ge=0, le=100)
    
    summary: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendation: AIRecommendation
    recommendation_reason: str


# ==========================================
# CANDIDATE RESPONSE SCHEMAS
# ==========================================

class CandidateResponse(CandidateBase):
    """Candidate response schema"""
    id: str
    job_id: str
    
    # Resume
    resume_url: Optional[str] = None
    resume_parsed: Optional[ParsedResume] = None
    
    # Status
    status: str = "applied"
    
    # AI Evaluation
    ai_score: Optional[int] = None
    ai_summary: Optional[str] = None
    ai_strengths: Optional[List[str]] = None
    ai_weaknesses: Optional[List[str]] = None
    ai_recommendation: Optional[str] = None
    shortlisted: bool = False
    shortlist_reason: Optional[str] = None
    
    # Interview
    interview_link: Optional[str] = None
    interview_sent_at: Optional[datetime] = None
    interview_expires_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CandidateWithJobResponse(CandidateResponse):
    """Candidate with job details"""
    job_title: str
    company_name: str


class CandidateListResponse(BaseModel):
    """Paginated candidate list response"""
    candidates: List[CandidateResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    
    # Summary stats
    status_counts: Dict[str, int] = {}


class CandidateDetailResponse(CandidateResponse):
    """Detailed candidate view with interview history"""
    job_title: str
    company_name: str
    interview_sessions: List[Dict[str, Any]] = []


# ==========================================
# SHORTLISTING SCHEMAS
# ==========================================

class ShortlistRequest(BaseModel):
    """Request to run AI shortlisting"""
    threshold: Optional[int] = Field(None, ge=0, le=100, description="Override default passing score")
    limit: Optional[int] = Field(None, ge=1, le=100, description="Max candidates to shortlist")
    auto_send_invites: bool = Field(False, description="Automatically send interview invites")


class ShortlistCandidate(BaseModel):
    """Candidate in shortlist result"""
    id: str
    name: str
    email: str
    ai_score: int
    ai_recommendation: str
    shortlist_reason: str
    interview_link: Optional[str] = None


class ShortlistResponse(BaseModel):
    """Response for shortlisting operation"""
    success: bool = True
    message: str
    job_id: str
    total_candidates: int
    shortlisted_count: int
    shortlisted_candidates: List[ShortlistCandidate]
    rejected_count: int


class CandidateReportResponse(BaseModel):
    """Detailed AI report for a candidate"""
    candidate: CandidateResponse
    job_title: str
    company_name: str
    
    # Detailed evaluation
    evaluation: AIEvaluation
    
    # Per-question analysis (if interview completed)
    question_responses: Optional[List[Dict[str, Any]]] = None
    
    # Comparison with other candidates
    percentile: Optional[int] = None  # How candidate ranks vs others


# ==========================================
# SUCCESS RESPONSES
# ==========================================

class ApplicationResponse(BaseModel):
    """Response for job application"""
    success: bool = True
    message: str = "Application submitted successfully"
    candidate_id: str
    interview_link: Optional[str] = None
    interview_scheduled: bool = False


class BulkUploadResponse(BaseModel):
    """Response for bulk candidate upload"""
    success: bool = True
    message: str
    total_uploaded: int
    successful: int
    failed: int
    errors: List[Dict[str, str]] = []


class SendInviteResponse(BaseModel):
    """Response for sending interview invite"""
    success: bool = True
    message: str
    candidate_id: str
    interview_link: str
    expires_at: datetime
