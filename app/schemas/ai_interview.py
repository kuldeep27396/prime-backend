"""
AI Interview Pydantic Schemas
For both B2B screening and mock practice interviews
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==========================================
# ENUMS
# ==========================================

class InterviewType(str, Enum):
    SCREENING = "screening"  # B2B candidate screening
    MOCK = "mock"  # Individual practice


class InterviewStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class MockCategory(str, Enum):
    DSA = "dsa"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ==========================================
# QUESTION SCHEMAS
# ==========================================

class InterviewQuestion(BaseModel):
    """A single interview question"""
    id: str
    question: str
    category: str
    difficulty: str
    time_limit_seconds: int = 180
    expected_points: Optional[List[str]] = None  # Key points to cover


class QuestionAnswer(BaseModel):
    """Answer submitted for a question"""
    question_id: str
    answer_text: str
    answer_audio_url: Optional[str] = None  # If audio/video recorded
    time_taken_seconds: int


class QuestionEvaluation(BaseModel):
    """AI evaluation of a single answer"""
    question_id: str
    score: int = Field(..., ge=0, le=100)
    feedback: str
    strengths: List[str] = []
    improvements: List[str] = []
    keywords_found: List[str] = []
    keywords_missing: List[str] = []


# ==========================================
# AI INTERVIEW SESSION SCHEMAS
# ==========================================

class AIInterviewCreate(BaseModel):
    """Create a new AI interview session"""
    # For screening interviews
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    
    # For mock interviews
    mock_category: Optional[MockCategory] = None
    topic: Optional[str] = Field(None, example="Arrays & Strings")
    
    # Common settings
    interview_type: InterviewType
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    question_count: int = Field(5, ge=3, le=15)
    duration_minutes: int = Field(15, ge=5, le=60)


class AIInterviewStart(BaseModel):
    """Start an interview session"""
    session_id: str
    browser_info: Optional[Dict[str, Any]] = None


class AIInterviewSubmitAnswer(BaseModel):
    """Submit an answer during interview"""
    question_id: str
    answer_text: str
    answer_audio_url: Optional[str] = None
    time_taken_seconds: int = Field(..., ge=0)


class AIInterviewComplete(BaseModel):
    """Complete an interview session"""
    session_id: str


# ==========================================
# AI INTERVIEW RESPONSE SCHEMAS
# ==========================================

class AIInterviewResponse(BaseModel):
    """AI Interview session response"""
    id: str
    
    # Type info
    interview_type: str
    mock_category: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str = "medium"
    
    # Status
    status: str = "pending"
    
    # Timing
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    actual_duration_seconds: Optional[int] = None
    
    # Questions (only shown when interview starts)
    questions: Optional[List[InterviewQuestion]] = None
    current_question_index: int = 0
    total_questions: int = 0
    
    # Scores (only shown after completion)
    overall_score: Optional[int] = None
    technical_score: Optional[int] = None
    communication_score: Optional[int] = None
    problem_solving_score: Optional[int] = None
    
    created_at: datetime

    class Config:
        from_attributes = True


class AIInterviewStartResponse(BaseModel):
    """Response when starting an interview"""
    success: bool = True
    session_id: str
    message: str = "Interview started"
    
    # First question(s)
    questions: List[InterviewQuestion]
    total_questions: int
    time_limit_minutes: int
    
    # Instructions
    instructions: str = "Answer each question clearly. You can take up to the time limit for each question."


class AIInterviewNextQuestion(BaseModel):
    """Response after answering a question"""
    success: bool = True
    message: str
    
    # Progress
    answered_count: int
    remaining_count: int
    
    # Next question (null if interview complete)
    next_question: Optional[InterviewQuestion] = None
    
    # Preview of current answer evaluation
    preview_feedback: Optional[str] = None


class AIInterviewAnalysis(BaseModel):
    """Complete AI analysis after interview"""
    session_id: str
    interview_type: str
    
    # Overall scores
    overall_score: int
    technical_score: Optional[int] = None
    communication_score: Optional[int] = None
    problem_solving_score: Optional[int] = None
    
    # Detailed feedback
    summary: str
    strengths: List[str]
    areas_to_improve: List[str]
    
    # Per-question breakdown
    question_evaluations: List[QuestionEvaluation]
    
    # Comparison (for mock interviews)
    percentile: Optional[int] = None  # How user ranks vs others who took same interview
    
    # Recommendations
    recommended_topics: List[str] = []
    recommended_resources: List[Dict[str, str]] = []


# ==========================================
# MOCK INTERVIEW SPECIFIC SCHEMAS
# ==========================================

class MockCategoryResponse(BaseModel):
    """Mock interview category"""
    id: str
    name: str
    display_name: str
    description: str
    icon: str
    color: str
    topics: List[Dict[str, Any]]
    difficulty_levels: List[str]
    is_premium: bool = False


class MockCategoryListResponse(BaseModel):
    """List of mock categories"""
    categories: List[MockCategoryResponse]


class MockProgressResponse(BaseModel):
    """User's progress in a mock category"""
    category: str
    topic: Optional[str] = None
    total_attempts: int = 0
    best_score: int = 0
    average_score: float = 0
    last_score: Optional[int] = None
    last_attempt_at: Optional[datetime] = None
    total_time_spent_minutes: int = 0
    current_streak: int = 0


class MockHistoryResponse(BaseModel):
    """User's mock interview history"""
    sessions: List[AIInterviewResponse]
    total: int
    page: int
    limit: int
    
    # Summary stats
    total_sessions: int = 0
    average_score: float = 0
    best_score: int = 0
    total_time_spent_minutes: int = 0


class MockStartRequest(BaseModel):
    """Request to start a mock interview"""
    category: MockCategory
    topic: Optional[str] = None
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    question_count: int = Field(5, ge=3, le=10)


# ==========================================
# SCREENING SPECIFIC SCHEMAS
# ==========================================

class ScreeningInterviewCreate(BaseModel):
    """Create screening interview for a candidate"""
    candidate_id: str
    job_id: str
    send_invite_email: bool = True
    custom_message: Optional[str] = None  # Custom message in invite email
    expires_in_hours: int = Field(72, ge=1, le=168)  # Default 3 days


class ScreeningInviteResponse(BaseModel):
    """Response after creating screening interview"""
    success: bool = True
    message: str
    session_id: str
    candidate_id: str
    interview_link: str
    interview_token: str
    expires_at: datetime
    email_sent: bool = False


class ScreeningValidateToken(BaseModel):
    """Validate interview token (for public access)"""
    token: str


class ScreeningTokenResponse(BaseModel):
    """Response for token validation"""
    valid: bool
    expired: bool = False
    session_id: Optional[str] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    question_count: Optional[int] = None


# ==========================================
# SUCCESS RESPONSES
# ==========================================

class AIInterviewCreateResponse(BaseModel):
    """Response for creating AI interview"""
    success: bool = True
    message: str = "Interview session created"
    session: AIInterviewResponse
    interview_link: Optional[str] = None  # For screening interviews


class AIInterviewCompleteResponse(BaseModel):
    """Response when interview is completed"""
    success: bool = True
    message: str = "Interview completed successfully"
    session_id: str
    overall_score: int
    summary: str
    analysis_ready: bool = True  # Analysis is ready to view
