"""
Interviews API endpoints
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.company import User
from app.services.interview_service import InterviewService
from app.schemas.interview import (
    InterviewTemplateCreate, InterviewTemplateUpdate, InterviewTemplate, InterviewTemplateList,
    InterviewCreate, InterviewUpdate, Interview, InterviewList, InterviewResponse,
    InterviewResponseCreate, InterviewTemplateAnalytics, QuestionBankFilter, 
    CalendarEvent, CalendarIntegration, BatchVideoProcessing,
    LiveAIInterviewStart, LiveAIResponse, LiveAIInterviewComplete, LiveAISessionState
)

router = APIRouter()


# Interview Template endpoints
@router.post("/templates", response_model=InterviewTemplate)
async def create_interview_template(
    template_data: InterviewTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new interview template"""
    service = InterviewService(db)
    return await service.create_template(
        template_data=template_data,
        company_id=current_user.company_id,
        user_id=current_user.id
    )


@router.get("/templates", response_model=InterviewTemplateList)
async def get_interview_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    search: Optional[str] = Query(None, description="Search templates by name"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of interview templates"""
    service = InterviewService(db)
    result = await service.get_templates(
        company_id=current_user.company_id,
        template_type=template_type,
        search=search,
        page=page,
        size=size
    )
    return InterviewTemplateList(**result)


@router.get("/templates/{template_id}", response_model=InterviewTemplate)
async def get_interview_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interview template by ID"""
    service = InterviewService(db)
    return await service.get_template(
        template_id=template_id,
        company_id=current_user.company_id
    )


@router.put("/templates/{template_id}", response_model=InterviewTemplate)
async def update_interview_template(
    template_id: UUID,
    template_data: InterviewTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update interview template"""
    service = InterviewService(db)
    return await service.update_template(
        template_id=template_id,
        template_data=template_data,
        company_id=current_user.company_id,
        user_id=current_user.id
    )


@router.delete("/templates/{template_id}")
async def delete_interview_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete interview template"""
    service = InterviewService(db)
    success = await service.delete_template(
        template_id=template_id,
        company_id=current_user.company_id,
        user_id=current_user.id
    )
    return {"success": success, "message": "Template deleted successfully"}


@router.post("/templates/{template_id}/customize", response_model=InterviewTemplate)
async def customize_template_for_role(
    template_id: UUID,
    role_requirements: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Customize interview template for specific role"""
    service = InterviewService(db)
    return await service.customize_template_for_role(
        template_id=template_id,
        role_requirements=role_requirements,
        company_id=current_user.company_id
    )


@router.get("/templates/{template_id}/analytics", response_model=InterviewTemplateAnalytics)
async def get_template_analytics(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for interview template"""
    service = InterviewService(db)
    return await service.get_template_analytics(
        template_id=template_id,
        company_id=current_user.company_id
    )


# Interview endpoints
@router.post("/", response_model=Interview)
async def create_interview(
    interview_data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new interview"""
    service = InterviewService(db)
    return await service.create_interview(
        interview_data=interview_data,
        company_id=current_user.company_id,
        user_id=current_user.id
    )


@router.get("/", response_model=InterviewList)
async def get_interviews(
    application_id: Optional[UUID] = Query(None, description="Filter by application ID"),
    status: Optional[str] = Query(None, description="Filter by interview status"),
    interview_type: Optional[str] = Query(None, description="Filter by interview type"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of interviews"""
    service = InterviewService(db)
    result = await service.get_interviews(
        company_id=current_user.company_id,
        application_id=application_id,
        status=status,
        interview_type=interview_type,
        page=page,
        size=size
    )
    return InterviewList(**result)


@router.get("/{interview_id}", response_model=Interview)
async def get_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interview by ID"""
    service = InterviewService(db)
    return await service.get_interview(
        interview_id=interview_id,
        company_id=current_user.company_id
    )


@router.put("/{interview_id}", response_model=Interview)
async def update_interview(
    interview_id: UUID,
    interview_data: InterviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update interview"""
    service = InterviewService(db)
    return await service.update_interview(
        interview_id=interview_id,
        interview_data=interview_data,
        company_id=current_user.company_id,
        user_id=current_user.id
    )


@router.post("/{interview_id}/schedule", response_model=dict)
async def schedule_interview_with_calendar(
    interview_id: UUID,
    calendar_event: CalendarEvent,
    calendar_integration: CalendarIntegration,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule interview with calendar integration"""
    service = InterviewService(db)
    success = await service.schedule_interview_with_calendar(
        interview_id=interview_id,
        calendar_event=calendar_event,
        calendar_integration=calendar_integration,
        company_id=current_user.company_id
    )
    return {"success": success, "message": "Interview scheduled successfully"}


# One-way Video Interview endpoints
@router.post("/{interview_id}/start-one-way", response_model=dict)
async def start_one_way_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a one-way video interview session"""
    service = InterviewService(db)
    return await service.start_one_way_interview(
        interview_id=interview_id,
        company_id=current_user.company_id
    )


@router.post("/{interview_id}/complete-one-way", response_model=Interview)
async def complete_one_way_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete a one-way video interview"""
    service = InterviewService(db)
    return await service.complete_one_way_interview(
        interview_id=interview_id,
        company_id=current_user.company_id
    )


@router.get("/{interview_id}/upload-url", response_model=dict)
async def get_video_upload_url(
    interview_id: UUID,
    question_id: str = Query(..., description="Question ID"),
    file_extension: str = Query("webm", description="File extension"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pre-signed URL for video upload"""
    service = InterviewService(db)
    return await service.get_video_upload_url(
        interview_id=interview_id,
        question_id=question_id,
        file_extension=file_extension,
        company_id=current_user.company_id
    )


@router.post("/{interview_id}/responses", response_model=InterviewResponse)
async def create_interview_response(
    interview_id: UUID,
    response_data: InterviewResponseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an interview response"""
    service = InterviewService(db)
    return await service.create_video_response(
        interview_id=interview_id,
        response_data=response_data,
        company_id=current_user.company_id
    )


@router.get("/{interview_id}/responses", response_model=List[InterviewResponse])
async def get_interview_responses(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all responses for an interview"""
    service = InterviewService(db)
    return await service.get_interview_responses(
        interview_id=interview_id,
        company_id=current_user.company_id
    )


@router.post("/batch-process", response_model=dict)
async def process_batch_videos(
    batch_data: BatchVideoProcessing,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process multiple video interviews in batch"""
    service = InterviewService(db)
    return await service.process_batch_videos(
        batch_data=batch_data,
        company_id=current_user.company_id
    )


# Live AI Interview endpoints
@router.post("/{interview_id}/start-live-ai", response_model=LiveAIInterviewStart)
async def start_live_ai_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a live AI interview session"""
    service = InterviewService(db)
    return await service.start_live_ai_interview(
        interview_id=interview_id,
        company_id=current_user.company_id
    )


@router.post("/{interview_id}/live-ai-response", response_model=dict)
async def process_live_ai_response(
    interview_id: UUID,
    response_data: LiveAIResponse,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process candidate response in live AI interview"""
    service = InterviewService(db)
    return await service.process_live_ai_response(
        interview_id=interview_id,
        candidate_response=response_data.candidate_response,
        response_metadata=response_data.response_metadata,
        company_id=current_user.company_id
    )


@router.post("/{interview_id}/complete-live-ai", response_model=LiveAIInterviewComplete)
async def complete_live_ai_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete a live AI interview and generate summary"""
    service = InterviewService(db)
    return await service.complete_live_ai_interview(
        interview_id=interview_id,
        company_id=current_user.company_id
    )


@router.get("/{interview_id}/live-ai-session", response_model=LiveAISessionState)
async def get_live_ai_session_state(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current live AI interview session state"""
    service = InterviewService(db)
    return await service.get_live_ai_session_state(
        interview_id=interview_id,
        company_id=current_user.company_id
    )


# Question Bank endpoints
@router.get("/question-bank", response_model=dict)
async def get_question_bank(
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search questions"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get question bank with filtering"""
    service = InterviewService(db)
    filters = QuestionBankFilter(
        type=question_type,
        category=category,
        difficulty=difficulty,
        tags=tags,
        search=search
    )
    return await service.get_question_bank(
        company_id=current_user.company_id,
        filters=filters
    )