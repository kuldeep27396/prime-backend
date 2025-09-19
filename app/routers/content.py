from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, or_
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from app.database import get_db
from app.database.models import LearningResource, InterviewQuestion, InterviewTemplate, User, UserProgress, UserResponse
from app.schemas.common import SuccessResponse, ErrorResponse, ErrorCodes
from app.auth.clerk_auth import get_current_user
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["Content & Learning"])

# Pydantic models
class LearningResourceResponse(BaseModel):
    id: str
    title: str
    description: str
    content_type: str
    url: Optional[str]
    thumbnail_url: Optional[str]
    difficulty_level: str
    duration_minutes: Optional[int]
    skills_covered: Optional[List[str]]
    tags: Optional[List[str]]
    is_premium: bool
    view_count: int
    rating: float
    created_at: str

class InterviewQuestionResponse(BaseModel):
    id: str
    question: str
    question_type: str
    difficulty: str
    category: str
    skills_tested: Optional[List[str]]
    companies_asked_at: Optional[List[str]]
    time_limit_minutes: Optional[int]
    created_at: str

class InterviewTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    interview_type: str
    duration_minutes: int
    difficulty: str
    companies: Optional[List[str]]
    is_public: bool
    created_at: str

class UserProgressResponse(BaseModel):
    id: str
    resource_id: str
    status: str
    progress_percentage: int
    started_at: Optional[str]
    completed_at: Optional[str]
    time_spent_minutes: int
    rating: Optional[int]
    notes: Optional[str]

class QuestionSubmissionRequest(BaseModel):
    response: str
    time_taken_seconds: Optional[int] = None
    session_id: Optional[str] = None

@router.get("/resources",
            response_model=List[LearningResourceResponse],
            summary="Get learning resources",
            description="Retrieve learning resources with optional filtering")
async def get_learning_resources(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    difficulty_level: Optional[str] = Query(None, description="Filter by difficulty level"),
    skills: Optional[List[str]] = Query(None, description="Filter by skills"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_premium: Optional[bool] = Query(None, description="Filter by premium status"),
    search_query: Optional[str] = Query(None, description="Search in title and description"),
    limit: int = Query(20, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Get learning resources"""
    try:
        # Build query
        query = select(LearningResource)

        # Apply filters
        if content_type:
            query = query.where(LearningResource.content_type == content_type)

        if difficulty_level:
            query = query.where(LearningResource.difficulty_level == difficulty_level)

        if skills:
            for skill in skills:
                query = query.where(LearningResource.skills_covered.contains([skill]))

        if tags:
            for tag in tags:
                query = query.where(LearningResource.tags.contains([tag]))

        if is_premium is not None:
            query = query.where(LearningResource.is_premium == is_premium)

        if search_query:
            search_term = f"%{search_query.lower()}%"
            query = query.where(or_(
                func.lower(LearningResource.title).like(search_term),
                func.lower(LearningResource.description).like(search_term)
            ))

        # Apply ordering and pagination
        query = query.order_by(LearningResource.view_count.desc(), LearningResource.rating.desc())
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        resources = result.scalars().all()

        return [
            LearningResourceResponse(
                id=str(resource.id),
                title=resource.title,
                description=resource.description,
                content_type=resource.content_type,
                url=resource.url,
                thumbnail_url=resource.thumbnail_url,
                difficulty_level=resource.difficulty_level,
                duration_minutes=resource.duration_minutes,
                skills_covered=resource.skills_covered,
                tags=resource.tags,
                is_premium=resource.is_premium,
                view_count=resource.view_count,
                rating=float(resource.rating),
                created_at=resource.created_at.isoformat()
            )
            for resource in resources
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning resources: {str(e)}"
        )

@router.get("/questions",
            response_model=List[InterviewQuestionResponse],
            summary="Get interview questions",
            description="Retrieve interview questions with optional filtering")
async def get_interview_questions(
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skills: Optional[List[str]] = Query(None, description="Filter by skills"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    search_query: Optional[str] = Query(None, description="Search in question text"),
    limit: int = Query(20, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Get interview questions"""
    try:
        # Build query
        query = select(InterviewQuestion).where(InterviewQuestion.is_active == True)

        # Apply filters
        if question_type:
            query = query.where(InterviewQuestion.question_type == question_type)

        if difficulty:
            query = query.where(InterviewQuestion.difficulty == difficulty)

        if category:
            query = query.where(InterviewQuestion.category == category)

        if skills:
            for skill in skills:
                query = query.where(InterviewQuestion.skills_tested.contains([skill]))

        if companies:
            for company in companies:
                query = query.where(InterviewQuestion.companies_asked_at.contains([company]))

        if search_query:
            search_term = f"%{search_query.lower()}%"
            query = query.where(func.lower(InterviewQuestion.question).like(search_term))

        # Apply ordering and pagination
        query = query.order_by(InterviewQuestion.created_at.desc())
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        questions = result.scalars().all()

        return [
            InterviewQuestionResponse(
                id=str(question.id),
                question=question.question,
                question_type=question.question_type,
                difficulty=question.difficulty,
                category=question.category,
                skills_tested=question.skills_tested,
                companies_asked_at=question.companies_asked_at,
                time_limit_minutes=question.time_limit_minutes,
                created_at=question.created_at.isoformat()
            )
            for question in questions
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get interview questions: {str(e)}"
        )

@router.get("/templates",
            response_model=List[InterviewTemplateResponse],
            summary="Get interview templates",
            description="Retrieve interview templates with optional filtering")
async def get_interview_templates(
    interview_type: Optional[str] = Query(None, description="Filter by interview type"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    is_public: Optional[bool] = Query(True, description="Filter by public status"),
    search_query: Optional[str] = Query(None, description="Search in name and description"),
    limit: int = Query(20, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Get interview templates"""
    try:
        # Build query
        query = select(InterviewTemplate)

        # Apply filters
        if interview_type:
            query = query.where(InterviewTemplate.interview_type == interview_type)

        if difficulty:
            query = query.where(InterviewTemplate.difficulty == difficulty)

        if companies:
            for company in companies:
                query = query.where(InterviewTemplate.companies.contains([company]))

        if is_public is not None:
            query = query.where(InterviewTemplate.is_public == is_public)

        if search_query:
            search_term = f"%{search_query.lower()}%"
            query = query.where(or_(
                func.lower(InterviewTemplate.name).like(search_term),
                func.lower(InterviewTemplate.description).like(search_term)
            ))

        # Apply ordering and pagination
        query = query.order_by(InterviewTemplate.created_at.desc())
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        templates = result.scalars().all()

        return [
            InterviewTemplateResponse(
                id=str(template.id),
                name=template.name,
                description=template.description,
                interview_type=template.interview_type,
                duration_minutes=template.duration_minutes,
                difficulty=template.difficulty,
                companies=template.companies,
                is_public=template.is_public,
                created_at=template.created_at.isoformat()
            )
            for template in templates
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get interview templates: {str(e)}"
        )

@router.get("/resources/{resource_id}/progress",
            response_model=UserProgressResponse,
            summary="Get user progress for resource",
            description="Get user's progress tracking for a specific resource")
async def get_resource_progress(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user progress for resource"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get user progress
        progress_result = await db.execute(
            select(UserProgress)
            .where(UserProgress.user_id == user.id)
            .where(UserProgress.resource_id == uuid.UUID(resource_id))
        )
        progress = progress_result.scalar_one_or_none()

        if not progress:
            # Create default progress
            progress = UserProgress(
                user_id=user.id,
                resource_id=uuid.UUID(resource_id),
                status='not_started'
            )
            db.add(progress)
            await db.commit()

        return UserProgressResponse(
            id=str(progress.id),
            resource_id=str(progress.resource_id),
            status=progress.status,
            progress_percentage=progress.progress_percentage,
            started_at=progress.started_at.isoformat() if progress.started_at else None,
            completed_at=progress.completed_at.isoformat() if progress.completed_at else None,
            time_spent_minutes=progress.time_spent_minutes,
            rating=progress.rating,
            notes=progress.notes
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource progress: {str(e)}"
        )

class ResourceProgressUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Resource status")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    time_spent_minutes: Optional[int] = Field(None, ge=0, description="Time spent in minutes")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating")
    notes: Optional[str] = Field(None, description="User notes")

@router.patch("/resources/{resource_id}/progress",
               response_model=SuccessResponse,
               summary="Update resource progress",
               description="Update user's progress for a specific resource")
async def update_resource_progress(
    resource_id: str,
    request: ResourceProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update resource progress"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get or create progress
        progress_result = await db.execute(
            select(UserProgress)
            .where(UserProgress.user_id == user.id)
            .where(UserProgress.resource_id == uuid.UUID(resource_id))
        )
        progress = progress_result.scalar_one_or_none()

        if not progress:
            progress = UserProgress(
                user_id=user.id,
                resource_id=uuid.UUID(resource_id),
                status='not_started'
            )
            db.add(progress)

        # Update progress
        update_data = {}
        if request.status is not None:
            update_data['status'] = request.status
            if request.status == 'started' and not progress.started_at:
                update_data['started_at'] = datetime.utcnow()
            elif request.status == 'completed' and not progress.completed_at:
                update_data['completed_at'] = datetime.utcnow()

        if request.progress_percentage is not None:
            update_data['progress_percentage'] = request.progress_percentage

        if request.time_spent_minutes is not None:
            update_data['time_spent_minutes'] = progress.time_spent_minutes + request.time_spent_minutes

        if request.rating is not None:
            update_data['rating'] = request.rating

        if request.notes is not None:
            update_data['notes'] = request.notes

        if update_data:
            await db.execute(
                update(UserProgress)
                .where(UserProgress.user_id == user.id)
                .where(UserProgress.resource_id == uuid.UUID(resource_id))
                .values(**update_data)
            )
            await db.commit()

        return SuccessResponse(
            success=True,
            message="Resource progress updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update resource progress: {str(e)}"
        )

@router.post("/questions/{question_id}/submit",
              response_model=SuccessResponse,
              summary="Submit question response",
              description="Submit a response to an interview question")
async def submit_question_response(
    question_id: str,
    submission: QuestionSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit question response"""
    try:
        # Get user data
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if question exists
        question_result = await db.execute(
            select(InterviewQuestion).where(InterviewQuestion.id == uuid.UUID(question_id))
        )
        question = question_result.scalar_one_or_none()

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )

        # Create user response
        user_response = UserResponse(
            user_id=user.id,
            question_id=uuid.UUID(question_id),
            response=submission.response,
            time_taken_seconds=submission.time_taken_seconds,
            session_id=uuid.UUID(submission.session_id) if submission.session_id else None
        )
        db.add(user_response)
        await db.commit()

        return SuccessResponse(
            success=True,
            message="Question response submitted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit question response: {str(e)}"
        )

@router.get("/content/stats",
            response_model=Dict[str, Any],
            summary="Get content statistics",
            description="Get statistics about learning resources and questions")
async def get_content_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get content statistics"""
    try:
        # Get resource counts by type
        resource_counts = await db.execute(
            select(
                LearningResource.content_type,
                func.count(LearningResource.id).label('count')
            )
            .group_by(LearningResource.content_type)
        )

        # Get question counts by type
        question_counts = await db.execute(
            select(
                InterviewQuestion.question_type,
                func.count(InterviewQuestion.id).label('count')
            )
            .where(InterviewQuestion.is_active == True)
            .group_by(InterviewQuestion.question_type)
        )

        # Get template counts by type
        template_counts = await db.execute(
            select(
                InterviewTemplate.interview_type,
                func.count(InterviewTemplate.id).label('count')
            )
            .group_by(InterviewTemplate.interview_type)
        )

        # Get skill distribution
        skill_result = await db.execute(
            select(LearningResource.skills_covered).where(LearningResource.skills_covered.isnot(None))
        )

        all_skills = []
        for skills_tuple in skill_result:
            if skills_tuple[0]:
                all_skills.extend(skills_tuple[0])

        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        return {
            "resources": {
                "total": sum(count for _, count in resource_counts),
                "by_type": {content_type: count for content_type, count in resource_counts}
            },
            "questions": {
                "total": sum(count for _, count in question_counts),
                "by_type": {question_type: count for question_type, count in question_counts}
            },
            "templates": {
                "total": sum(count for _, count in template_counts),
                "by_type": {interview_type: count for interview_type, count in template_counts}
            },
            "top_skills": sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content stats: {str(e)}"
        )