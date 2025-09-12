"""
Chatbot pre-screening API endpoints
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.company import User
from app.services.chatbot_service import ChatbotService
from app.schemas.chatbot import (
    ChatbotTemplateCreate, ChatbotTemplateUpdate, ChatbotTemplateResponse,
    ChatbotSessionStart, CandidateResponse, ChatbotInteractionResponse,
    PreScreeningReport, ChatbotListResponse, ChatbotSessionListResponse
)
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()


# Template Management Endpoints
@router.post("/templates", response_model=ChatbotTemplateResponse, status_code=201)
async def create_chatbot_template(
    template_data: ChatbotTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chatbot template"""
    
    if not current_user.is_recruiter:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    service = ChatbotService(db)
    
    try:
        return await service.create_template(
            template_data,
            current_user.company_id,
            current_user.id
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create chatbot template")


@router.get("/templates", response_model=ChatbotListResponse)
async def get_chatbot_templates(
    job_id: Optional[UUID] = Query(None, description="Filter by job ID"),
    active_only: bool = Query(True, description="Show only active templates"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chatbot templates for the current company"""
    
    service = ChatbotService(db)
    
    try:
        templates = await service.get_templates(
            current_user.company_id,
            job_id,
            active_only
        )
        
        # Simple pagination
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_templates = templates[start_idx:end_idx]
        
        return ChatbotListResponse(
            templates=paginated_templates,
            total=len(templates),
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve chatbot templates")


@router.get("/templates/{template_id}", response_model=ChatbotTemplateResponse)
async def get_chatbot_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chatbot template"""
    
    service = ChatbotService(db)
    
    try:
        return await service.get_template(template_id, current_user.company_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Chatbot template not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve chatbot template")


@router.put("/templates/{template_id}", response_model=ChatbotTemplateResponse)
async def update_chatbot_template(
    template_id: UUID,
    template_data: ChatbotTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a chatbot template"""
    
    if not current_user.is_recruiter:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    service = ChatbotService(db)
    
    try:
        return await service.update_template(
            template_id,
            template_data,
            current_user.company_id
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Chatbot template not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update chatbot template")


# Session Management Endpoints
@router.post("/sessions/start", response_model=ChatbotInteractionResponse)
async def start_chatbot_session(
    session_data: ChatbotSessionStart,
    is_trial: bool = Query(False, description="Whether this is a trial session"),
    db: Session = Depends(get_db)
):
    """Start a new chatbot pre-screening session"""
    
    service = ChatbotService(db)
    
    try:
        result = await service.start_session(session_data, is_trial)
        return ChatbotInteractionResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start chatbot session")


@router.post("/sessions/{session_id}/respond", response_model=ChatbotInteractionResponse)
async def respond_to_chatbot(
    session_id: UUID,
    response_data: CandidateResponse,
    is_trial: bool = Query(False, description="Whether this is a trial session"),
    db: Session = Depends(get_db)
):
    """Submit candidate response to chatbot"""
    
    service = ChatbotService(db)
    
    try:
        return await service.process_candidate_response(
            session_id,
            response_data,
            is_trial
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Chatbot session not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process response")


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Get current status of a chatbot session"""
    
    service = ChatbotService(db)
    
    try:
        return await service.get_session_status(session_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Chatbot session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve session status")


@router.get("/sessions/{session_id}/report", response_model=PreScreeningReport)
async def get_pre_screening_report(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate pre-screening report for completed session"""
    
    if not current_user.is_recruiter:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    service = ChatbotService(db)
    
    try:
        return await service.generate_pre_screening_report(session_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Chatbot session not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate report")


# Candidate-facing endpoints (no authentication required)
@router.get("/public/sessions/{session_id}/status")
async def get_public_session_status(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Get session status for candidates (public endpoint)"""
    
    service = ChatbotService(db)
    
    try:
        status = await service.get_session_status(session_id)
        
        # Return limited information for public access
        return {
            "session_id": status["session_id"],
            "status": status["status"],
            "progress": status["progress"],
            "current_question_index": status["current_question_index"]
        }
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve session status")


@router.post("/public/sessions/{session_id}/respond", response_model=ChatbotInteractionResponse)
async def public_respond_to_chatbot(
    session_id: UUID,
    response_data: CandidateResponse,
    is_trial: bool = Query(False, description="Whether this is a trial session"),
    db: Session = Depends(get_db)
):
    """Public endpoint for candidates to respond to chatbot"""
    
    service = ChatbotService(db)
    
    try:
        return await service.process_candidate_response(
            session_id,
            response_data,
            is_trial
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process response")


# Analytics and Management Endpoints
@router.get("/analytics/templates/{template_id}")
async def get_template_analytics(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a chatbot template"""
    
    if not current_user.is_recruiter:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # TODO: Implement template analytics
    # This would include metrics like:
    # - Number of sessions started/completed
    # - Average completion time
    # - Average scores by question
    # - Drop-off rates
    
    return {
        "template_id": template_id,
        "total_sessions": 0,
        "completed_sessions": 0,
        "average_score": 0,
        "average_completion_time": 0,
        "completion_rate": 0
    }


@router.get("/sessions")
async def get_chatbot_sessions(
    template_id: Optional[UUID] = Query(None, description="Filter by template ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chatbot sessions for the current company"""
    
    if not current_user.is_recruiter:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # TODO: Implement session listing with filters
    # This would query sessions based on company, template, status, etc.
    
    return ChatbotSessionListResponse(
        sessions=[],
        total=0,
        page=page,
        size=size
    )