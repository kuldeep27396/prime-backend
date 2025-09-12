"""
Interview schemas for request/response validation
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


# Question schemas
class QuestionBase(BaseModel):
    """Base question schema"""
    id: str = Field(..., description="Unique question identifier")
    type: str = Field(..., description="Question type: behavioral, technical, cultural, situational")
    category: str = Field(..., description="Question category for organization")
    content: str = Field(..., description="Question text")
    expected_duration: Optional[int] = Field(None, description="Expected response duration in seconds")
    difficulty: str = Field(default="medium", description="Question difficulty: easy, medium, hard")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional question metadata")


class QuestionCreate(QuestionBase):
    """Schema for creating questions"""
    pass


class QuestionUpdate(BaseModel):
    """Schema for updating questions"""
    type: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    expected_duration: Optional[int] = None
    difficulty: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class Question(QuestionBase):
    """Complete question schema"""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Interview Template schemas
class InterviewTemplateBase(BaseModel):
    """Base interview template schema"""
    name: str = Field(..., description="Template name")
    type: str = Field(..., description="Interview type: one_way, live_ai, technical")
    description: Optional[str] = Field(None, description="Template description")
    questions: List[QuestionBase] = Field(default_factory=list, description="List of questions")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Template settings")


class InterviewTemplateCreate(InterviewTemplateBase):
    """Schema for creating interview templates"""
    pass


class InterviewTemplateUpdate(BaseModel):
    """Schema for updating interview templates"""
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    questions: Optional[List[QuestionBase]] = None
    settings: Optional[Dict[str, Any]] = None


class InterviewTemplate(InterviewTemplateBase):
    """Complete interview template schema"""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterviewTemplateList(BaseModel):
    """Schema for paginated interview template list"""
    templates: List[InterviewTemplate]
    total: int
    page: int
    size: int
    has_next: bool


# Interview schemas
class InterviewBase(BaseModel):
    """Base interview schema"""
    type: str = Field(..., description="Interview type: one_way, live_ai, technical")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled interview time")
    interview_metadata: Dict[str, Any] = Field(default_factory=dict, description="Interview metadata")


class InterviewCreate(InterviewBase):
    """Schema for creating interviews"""
    application_id: UUID = Field(..., description="Application ID")
    template_id: Optional[UUID] = Field(None, description="Template ID to use")


class InterviewUpdate(BaseModel):
    """Schema for updating interviews"""
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    interview_metadata: Optional[Dict[str, Any]] = None


class Interview(InterviewBase):
    """Complete interview schema"""
    id: UUID
    application_id: UUID
    template_id: Optional[UUID]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterviewList(BaseModel):
    """Schema for paginated interview list"""
    interviews: List[Interview]
    total: int
    page: int
    size: int
    has_next: bool


# Interview Response schemas
class InterviewResponseBase(BaseModel):
    """Base interview response schema"""
    question_id: str = Field(..., description="Question ID")
    response_type: str = Field(..., description="Response type: video, audio, text, code")
    content: Optional[str] = Field(None, description="Text content or transcript")
    media_url: Optional[str] = Field(None, description="Media file URL")
    duration: Optional[int] = Field(None, description="Response duration in seconds")
    response_metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


class VideoResponseCreate(BaseModel):
    """Schema for creating video responses"""
    question_id: str = Field(..., description="Question ID")
    duration: int = Field(..., description="Video duration in seconds")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    video_metadata: Dict[str, Any] = Field(default_factory=dict, description="Video metadata")


class VideoUploadResponse(BaseModel):
    """Schema for video upload response"""
    upload_url: str = Field(..., description="Pre-signed upload URL")
    media_url: str = Field(..., description="Final media URL")
    expires_at: datetime = Field(..., description="Upload URL expiration")


class BatchVideoProcessing(BaseModel):
    """Schema for batch video processing"""
    interview_ids: List[UUID] = Field(..., description="List of interview IDs to process")
    processing_options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")


class InterviewResponseCreate(InterviewResponseBase):
    """Schema for creating interview responses"""
    pass


class InterviewResponse(InterviewResponseBase):
    """Complete interview response schema"""
    id: UUID
    interview_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics schemas
class InterviewTemplateAnalytics(BaseModel):
    """Interview template analytics schema"""
    template_id: UUID
    template_name: str
    total_interviews: int
    completed_interviews: int
    average_completion_rate: float
    average_duration: Optional[float]
    average_score: Optional[float]
    question_analytics: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]


class InterviewAnalytics(BaseModel):
    """Interview analytics schema"""
    interview_id: UUID
    completion_rate: float
    total_duration: Optional[int]
    question_responses: List[Dict[str, Any]]
    candidate_engagement: Dict[str, Any]
    performance_metrics: Dict[str, Any]


# Calendar integration schemas
class CalendarEvent(BaseModel):
    """Calendar event schema"""
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    attendees: List[str]
    location: Optional[str]
    meeting_url: Optional[str]


class CalendarIntegration(BaseModel):
    """Calendar integration schema"""
    provider: str = Field(..., description="Calendar provider: google, outlook")
    access_token: str
    refresh_token: Optional[str]
    calendar_id: Optional[str]


# Question bank schemas
class QuestionBankFilter(BaseModel):
    """Question bank filter schema"""
    type: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None


class QuestionBank(BaseModel):
    """Question bank schema"""
    questions: List[Question]
    categories: List[str]
    types: List[str]
    difficulties: List[str]
    tags: List[str]
    total: int


# Live AI Interview schemas
class LiveAIInterviewStart(BaseModel):
    """Schema for starting live AI interview"""
    interview_id: UUID
    session_id: str
    opening_question: str
    candidate_name: str
    job_title: str
    interview_config: Dict[str, Any]
    started_at: str


class LiveAIResponse(BaseModel):
    """Schema for live AI interview response processing"""
    candidate_response: str = Field(..., description="Candidate's response text")
    response_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")


class LiveAIInterviewComplete(BaseModel):
    """Schema for completed live AI interview"""
    interview_id: UUID
    summary: Dict[str, Any]
    completed_at: str
    status: str


class LiveAISessionState(BaseModel):
    """Schema for live AI interview session state"""
    interview_id: UUID
    session_state: Dict[str, Any]
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]