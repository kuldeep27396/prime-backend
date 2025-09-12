"""
Chatbot pre-screening schemas
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from uuid import UUID


# Question Configuration Schemas
class QuestionConfig(BaseModel):
    """Configuration for a single chatbot question"""
    id: str = Field(..., description="Unique question identifier")
    type: str = Field(..., description="Question type: open_ended, multiple_choice, rating, yes_no")
    text: str = Field(..., description="Question text to display")
    options: Optional[List[str]] = Field(None, description="Options for multiple choice questions")
    required: bool = Field(True, description="Whether this question is required")
    follow_up_rules: Optional[Dict[str, Any]] = Field(None, description="Rules for follow-up questions")
    evaluation_criteria: Optional[Dict[str, Any]] = Field(None, description="Criteria for evaluating responses")


class ChatbotSettings(BaseModel):
    """Chatbot behavior settings"""
    personality: str = Field("professional", description="Chatbot personality: professional, friendly, casual")
    response_time_limit: Optional[int] = Field(300, description="Time limit for responses in seconds")
    max_retries: int = Field(3, description="Maximum retries for unclear responses")
    language: str = Field("en", description="Language code")
    enable_follow_ups: bool = Field(True, description="Enable dynamic follow-up questions")
    scoring_weights: Optional[Dict[str, float]] = Field(None, description="Weights for different evaluation criteria")


# Template Schemas
class ChatbotTemplateCreate(BaseModel):
    """Schema for creating a chatbot template"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    job_id: Optional[UUID] = Field(None, description="Associated job ID")
    question_flow: List[QuestionConfig] = Field(..., min_items=1)
    settings: ChatbotSettings = Field(default_factory=ChatbotSettings)


class ChatbotTemplateUpdate(BaseModel):
    """Schema for updating a chatbot template"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    job_id: Optional[UUID] = None
    question_flow: Optional[List[QuestionConfig]] = None
    settings: Optional[ChatbotSettings] = None
    is_active: Optional[bool] = None


class ChatbotTemplateResponse(BaseModel):
    """Schema for chatbot template response"""
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str]
    job_id: Optional[UUID]
    question_flow: List[QuestionConfig]
    settings: ChatbotSettings
    is_active: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Message Schemas
class ChatbotMessageCreate(BaseModel):
    """Schema for creating a chatbot message"""
    sender: str = Field(..., pattern="^(bot|candidate)$")
    message_type: str = Field("text", pattern="^(text|question|response|system)$")
    content: str = Field(..., min_length=1)
    question_id: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatbotMessageResponse(BaseModel):
    """Schema for chatbot message response"""
    id: UUID
    sender: str
    message_type: str
    content: str
    question_id: Optional[str]
    message_metadata: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True


# Session Schemas
class ChatbotSessionStart(BaseModel):
    """Schema for starting a chatbot session"""
    application_id: UUID
    template_id: UUID


class CandidateResponse(BaseModel):
    """Schema for candidate response to a question"""
    question_id: str
    response: Union[str, List[str], int, bool]
    response_time: Optional[int] = Field(None, description="Response time in seconds")


class ChatbotSessionUpdate(BaseModel):
    """Schema for updating a chatbot session"""
    status: Optional[str] = Field(None, pattern="^(started|in_progress|completed|abandoned)$")
    current_question_index: Optional[int] = None
    responses: Optional[Dict[str, Any]] = None


class EvaluationResult(BaseModel):
    """Schema for question evaluation result"""
    question_id: str
    score: float = Field(..., ge=0, le=100)
    reasoning: str
    keywords_found: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)


class ChatbotSessionResponse(BaseModel):
    """Schema for chatbot session response"""
    id: UUID
    application_id: UUID
    template_id: UUID
    status: str
    current_question_index: int
    conversation_history: List[ChatbotMessageResponse]
    responses: Dict[str, Any]
    evaluation_results: Dict[str, EvaluationResult]
    overall_score: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


# Pre-screening Report Schemas
class QuestionSummary(BaseModel):
    """Summary of a single question's response"""
    question_id: str
    question_text: str
    candidate_response: str
    evaluation: EvaluationResult
    follow_up_questions: List[str] = Field(default_factory=list)


class PreScreeningReport(BaseModel):
    """Complete pre-screening report"""
    session_id: UUID
    candidate_name: str
    candidate_email: str
    job_title: str
    overall_score: int
    completion_rate: float
    total_time_minutes: int
    question_summaries: List[QuestionSummary]
    strengths: List[str]
    concerns: List[str]
    recommendation: str  # "proceed", "reject", "needs_review"
    generated_at: datetime


# API Response Schemas
class ChatbotInteractionResponse(BaseModel):
    """Response for chatbot interaction"""
    message: str
    question_id: Optional[str] = None
    is_final: bool = False
    next_question: Optional[QuestionConfig] = None
    session_status: str
    progress: float = Field(..., ge=0, le=100, description="Completion percentage")


class ChatbotListResponse(BaseModel):
    """Response for listing chatbot templates"""
    templates: List[ChatbotTemplateResponse]
    total: int
    page: int
    size: int


class ChatbotSessionListResponse(BaseModel):
    """Response for listing chatbot sessions"""
    sessions: List[ChatbotSessionResponse]
    total: int
    page: int
    size: int