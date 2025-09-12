"""
Interview service for managing interview templates and interviews
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.interview import InterviewTemplate, Interview, InterviewResponse
from app.models.company import Company, User
from app.models.job import Application
from app.schemas.interview import (
    InterviewTemplateCreate, InterviewTemplateUpdate, InterviewTemplate as InterviewTemplateSchema,
    InterviewCreate, InterviewUpdate, Interview as InterviewSchema,
    InterviewResponseCreate, InterviewResponse as InterviewResponseSchema,
    InterviewTemplateAnalytics, InterviewAnalytics, QuestionBankFilter,
    CalendarEvent, CalendarIntegration, VideoResponseCreate, VideoUploadResponse,
    BatchVideoProcessing
)
import logging

logger = logging.getLogger(__name__)


class InterviewService:
    """Service for managing interview templates and interviews"""

    def __init__(self, db: Session):
        self.db = db

    # Interview Template CRUD Operations
    async def create_template(
        self, 
        template_data: InterviewTemplateCreate, 
        company_id: UUID,
        user_id: UUID
    ) -> InterviewTemplateSchema:
        """Create a new interview template"""
        
        # Verify user has permission to create templates
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.company_id == company_id)
        ).first()
        
        if not user or not user.is_recruiter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create interview templates"
            )

        # Validate template data
        self._validate_template_data(template_data)

        # Create template
        db_template = InterviewTemplate(
            company_id=company_id,
            name=template_data.name,
            description=template_data.description,
            type=template_data.type,
            questions=[q.model_dump() for q in template_data.questions],
            settings=template_data.settings
        )

        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)

        return InterviewTemplateSchema.from_orm(db_template)

    async def get_template(self, template_id: UUID, company_id: UUID) -> InterviewTemplateSchema:
        """Get interview template by ID"""
        
        template = self.db.query(InterviewTemplate).filter(
            and_(
                InterviewTemplate.id == template_id,
                InterviewTemplate.company_id == company_id
            )
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview template not found"
            )

        return InterviewTemplateSchema.from_orm(template)

    async def get_templates(
        self, 
        company_id: UUID,
        template_type: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Get paginated list of interview templates"""
        
        query = self.db.query(InterviewTemplate).filter(
            InterviewTemplate.company_id == company_id
        )

        # Apply filters
        if template_type:
            query = query.filter(InterviewTemplate.type == template_type)
        
        if search:
            query = query.filter(
                or_(
                    InterviewTemplate.name.ilike(f"%{search}%"),
                    InterviewTemplate.type.ilike(f"%{search}%")
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        templates = query.order_by(desc(InterviewTemplate.created_at))\
                        .offset((page - 1) * size)\
                        .limit(size)\
                        .all()

        return {
            "templates": [InterviewTemplateSchema.from_orm(t) for t in templates],
            "total": total,
            "page": page,
            "size": size,
            "has_next": total > page * size
        }

    async def update_template(
        self, 
        template_id: UUID, 
        template_data: InterviewTemplateUpdate,
        company_id: UUID,
        user_id: UUID
    ) -> InterviewTemplateSchema:
        """Update interview template"""
        
        # Verify user has permission
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.company_id == company_id)
        ).first()
        
        if not user or not user.is_recruiter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update interview templates"
            )

        # Get template
        template = self.db.query(InterviewTemplate).filter(
            and_(
                InterviewTemplate.id == template_id,
                InterviewTemplate.company_id == company_id
            )
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview template not found"
            )

        # Update fields
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "questions" and value is not None:
                # Convert Pydantic models to dicts
                value = [q.model_dump() if hasattr(q, 'model_dump') else q for q in value]
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)

        return InterviewTemplateSchema.from_orm(template)

    async def delete_template(
        self, 
        template_id: UUID, 
        company_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete interview template"""
        
        # Verify user has permission
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.company_id == company_id)
        ).first()
        
        if not user or not user.is_recruiter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete interview templates"
            )

        # Get template
        template = self.db.query(InterviewTemplate).filter(
            and_(
                InterviewTemplate.id == template_id,
                InterviewTemplate.company_id == company_id
            )
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview template not found"
            )

        # Check if template is being used
        active_interviews = self.db.query(Interview).filter(
            and_(
                Interview.template_id == template_id,
                Interview.status.in_(["scheduled", "in_progress"])
            )
        ).count()

        if active_interviews > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete template with active interviews"
            )

        self.db.delete(template)
        self.db.commit()
        return True

    # Interview Management
    async def create_interview(
        self, 
        interview_data: InterviewCreate,
        company_id: UUID,
        user_id: UUID
    ) -> InterviewSchema:
        """Create a new interview"""
        
        # Verify user has permission
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.company_id == company_id)
        ).first()
        
        if not user or not user.is_recruiter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create interviews"
            )

        # Verify application exists and belongs to company
        application = self.db.query(Application).join(
            Application.job
        ).filter(
            and_(
                Application.id == interview_data.application_id,
                Application.job.has(company_id=company_id)
            )
        ).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )

        # Verify template if provided
        if interview_data.template_id:
            template = self.db.query(InterviewTemplate).filter(
                and_(
                    InterviewTemplate.id == interview_data.template_id,
                    InterviewTemplate.company_id == company_id
                )
            ).first()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Interview template not found"
                )

        # Create interview
        db_interview = Interview(
            application_id=interview_data.application_id,
            template_id=interview_data.template_id,
            type=interview_data.type,
            scheduled_at=interview_data.scheduled_at,
            interview_metadata=interview_data.interview_metadata
        )

        self.db.add(db_interview)
        self.db.commit()
        self.db.refresh(db_interview)

        return InterviewSchema.from_orm(db_interview)

    async def get_interview(self, interview_id: UUID, company_id: UUID) -> InterviewSchema:
        """Get interview by ID"""
        
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id)
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )

        return InterviewSchema.from_orm(interview)

    async def get_interviews(
        self,
        company_id: UUID,
        application_id: Optional[UUID] = None,
        status: Optional[str] = None,
        interview_type: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Get paginated list of interviews"""
        
        query = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            Application.job.has(company_id=company_id)
        )

        # Apply filters
        if application_id:
            query = query.filter(Interview.application_id == application_id)
        
        if status:
            query = query.filter(Interview.status == status)
            
        if interview_type:
            query = query.filter(Interview.type == interview_type)

        # Get total count
        total = query.count()

        # Apply pagination
        interviews = query.order_by(desc(Interview.created_at))\
                          .offset((page - 1) * size)\
                          .limit(size)\
                          .all()

        return {
            "interviews": [InterviewSchema.from_orm(i) for i in interviews],
            "total": total,
            "page": page,
            "size": size,
            "has_next": total > page * size
        }

    async def update_interview(
        self,
        interview_id: UUID,
        interview_data: InterviewUpdate,
        company_id: UUID,
        user_id: UUID
    ) -> InterviewSchema:
        """Update interview"""
        
        # Verify user has permission
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.company_id == company_id)
        ).first()
        
        if not user or not user.is_interviewer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update interviews"
            )

        # Get interview
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id)
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )

        # Update fields
        update_data = interview_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(interview, field, value)

        interview.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(interview)

        return InterviewSchema.from_orm(interview)

    # Question Bank Management
    async def get_question_bank(
        self,
        company_id: UUID,
        filters: QuestionBankFilter
    ) -> Dict[str, Any]:
        """Get question bank with filtering"""
        
        # Get all templates for the company
        templates = self.db.query(InterviewTemplate).filter(
            InterviewTemplate.company_id == company_id
        ).all()

        # Extract and filter questions
        all_questions = []
        categories = set()
        types = set()
        difficulties = set()
        tags = set()

        for template in templates:
            for question_dict in template.questions:
                # Apply filters
                if filters.type and question_dict.get("type") != filters.type:
                    continue
                if filters.category and question_dict.get("category") != filters.category:
                    continue
                if filters.difficulty and question_dict.get("difficulty") != filters.difficulty:
                    continue
                if filters.tags and not any(tag in question_dict.get("tags", []) for tag in filters.tags):
                    continue
                if filters.search and filters.search.lower() not in question_dict.get("content", "").lower():
                    continue

                all_questions.append(question_dict)
                categories.add(question_dict.get("category", ""))
                types.add(question_dict.get("type", ""))
                difficulties.add(question_dict.get("difficulty", ""))
                tags.update(question_dict.get("tags", []))

        return {
            "questions": all_questions,
            "categories": list(categories),
            "types": list(types),
            "difficulties": list(difficulties),
            "tags": list(tags),
            "total": len(all_questions)
        }

    # Analytics
    async def get_template_analytics(
        self,
        template_id: UUID,
        company_id: UUID
    ) -> InterviewTemplateAnalytics:
        """Get analytics for interview template"""
        
        template = self.db.query(InterviewTemplate).filter(
            and_(
                InterviewTemplate.id == template_id,
                InterviewTemplate.company_id == company_id
            )
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview template not found"
            )

        # Get interview statistics
        interviews = self.db.query(Interview).filter(
            Interview.template_id == template_id
        ).all()

        total_interviews = len(interviews)
        completed_interviews = len([i for i in interviews if i.status == "completed"])
        completion_rate = completed_interviews / total_interviews if total_interviews > 0 else 0

        # Calculate average duration
        completed_with_duration = [
            i for i in interviews 
            if i.status == "completed" and i.started_at and i.completed_at
        ]
        
        avg_duration = None
        if completed_with_duration:
            durations = [
                (i.completed_at - i.started_at).total_seconds() 
                for i in completed_with_duration
            ]
            avg_duration = sum(durations) / len(durations)

        # Question analytics (placeholder - would need more complex analysis)
        question_analytics = []
        for question_dict in template.questions:
            question_analytics.append({
                "question_id": question_dict.get("id"),
                "content": question_dict.get("content"),
                "response_rate": 0.95,  # Placeholder
                "average_score": 7.5,   # Placeholder
                "difficulty_rating": question_dict.get("difficulty", "medium")
            })

        return InterviewTemplateAnalytics(
            template_id=template_id,
            template_name=template.name,
            total_interviews=total_interviews,
            completed_interviews=completed_interviews,
            average_completion_rate=completion_rate,
            average_duration=avg_duration,
            average_score=None,  # Would need scoring system integration
            question_analytics=question_analytics,
            performance_trends={}  # Placeholder for trend data
        )

    # Calendar Integration
    async def schedule_interview_with_calendar(
        self,
        interview_id: UUID,
        calendar_event: CalendarEvent,
        calendar_integration: CalendarIntegration,
        company_id: UUID
    ) -> bool:
        """Schedule interview with calendar integration"""
        
        # Get interview
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id)
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )

        # TODO: Implement actual calendar API integration
        # This would integrate with Google Calendar, Outlook, etc.
        # For now, just update the interview with scheduled time
        
        interview.scheduled_at = calendar_event.start_time
        interview.interview_metadata.update({
            "calendar_event": {
                "title": calendar_event.title,
                "start_time": calendar_event.start_time.isoformat(),
                "end_time": calendar_event.end_time.isoformat(),
                "attendees": calendar_event.attendees,
                "meeting_url": calendar_event.meeting_url
            }
        })
        
        self.db.commit()
        return True

    # Video Interview Methods
    async def create_video_response(
        self,
        interview_id: UUID,
        response_data: InterviewResponseCreate,
        company_id: UUID
    ) -> InterviewResponseSchema:
        """Create a video response for an interview"""
        
        # Verify interview exists and belongs to company
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id)
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )

        # Create response
        db_response = InterviewResponse(
            interview_id=interview_id,
            question_id=response_data.question_id,
            response_type=response_data.response_type,
            content=response_data.content,
            media_url=response_data.media_url,
            duration=response_data.duration,
            response_metadata=response_data.response_metadata
        )

        self.db.add(db_response)
        self.db.commit()
        self.db.refresh(db_response)

        return InterviewResponseSchema.from_orm(db_response)

    async def get_video_upload_url(
        self,
        interview_id: UUID,
        question_id: str,
        file_extension: str,
        company_id: UUID
    ) -> Dict[str, str]:
        """Get pre-signed URL for video upload"""
        
        # Verify interview exists
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id)
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )

        # Import file handler
        from app.utils.file_handler import file_handler
        
        # Generate unique filename
        filename = f"interviews/{interview_id}/{question_id}_{datetime.utcnow().timestamp()}.{file_extension}"
        
        # Get upload URL from file handler
        return await file_handler.generate_upload_url(
            filename=filename,
            content_type=f"video/{file_extension}"
        )

    async def start_one_way_interview(
        self,
        interview_id: UUID,
        company_id: UUID
    ) -> Dict[str, Any]:
        """Start a one-way video interview session"""
        
        # Get interview with template
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id),
                Interview.type == "one_way"
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One-way interview not found"
            )

        if interview.status != "scheduled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview is not in scheduled status"
            )

        # Update interview status
        interview.status = "in_progress"
        interview.started_at = datetime.utcnow()
        self.db.commit()

        # Get template questions
        template = interview.template
        questions = template.questions if template else []

        return {
            "interview_id": interview_id,
            "questions": questions,
            "settings": template.settings if template else {},
            "started_at": interview.started_at.isoformat(),
            "candidate_name": interview.application.candidate.name,
            "job_title": interview.application.job.title
        }

    async def complete_one_way_interview(
        self,
        interview_id: UUID,
        company_id: UUID
    ) -> InterviewSchema:
        """Complete a one-way video interview"""
        
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id)
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )

        interview.status = "completed"
        interview.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(interview)

        return InterviewSchema.from_orm(interview)

    async def get_interview_responses(
        self,
        interview_id: UUID,
        company_id: UUID
    ) -> List[InterviewResponseSchema]:
        """Get all responses for an interview"""
        
        # Verify interview exists
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id)
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )

        responses = self.db.query(InterviewResponse).filter(
            InterviewResponse.interview_id == interview_id
        ).order_by(InterviewResponse.created_at).all()

        return [InterviewResponseSchema.from_orm(r) for r in responses]

    async def process_batch_videos(
        self,
        batch_data: BatchVideoProcessing,
        company_id: UUID
    ) -> Dict[str, Any]:
        """Process multiple video interviews in batch"""
        
        results = []
        
        for interview_id in batch_data.interview_ids:
            try:
                # Verify interview belongs to company
                interview = self.db.query(Interview).join(
                    Interview.application
                ).join(
                    Application.job
                ).filter(
                    and_(
                        Interview.id == interview_id,
                        Application.job.has(company_id=company_id)
                    )
                ).first()

                if not interview:
                    results.append({
                        "interview_id": interview_id,
                        "status": "error",
                        "message": "Interview not found"
                    })
                    continue

                # Get responses for processing
                responses = await self.get_interview_responses(interview_id, company_id)
                
                # TODO: Implement actual video processing (transcription, analysis, etc.)
                # For now, just mark as processed
                interview.interview_metadata.update({
                    "batch_processed": True,
                    "processed_at": datetime.utcnow().isoformat(),
                    "processing_options": batch_data.processing_options
                })
                
                self.db.commit()
                
                results.append({
                    "interview_id": interview_id,
                    "status": "success",
                    "responses_count": len(responses),
                    "processed_at": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                results.append({
                    "interview_id": interview_id,
                    "status": "error",
                    "message": str(e)
                })

        return {
            "batch_id": f"batch_{datetime.utcnow().timestamp()}",
            "total_interviews": len(batch_data.interview_ids),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results
        }

    # Helper methods
    def _validate_template_data(self, template_data: InterviewTemplateCreate):
        """Validate interview template data"""
        
        # Validate interview type
        valid_types = ["one_way", "live_ai", "technical"]
        if template_data.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interview type. Must be one of: {valid_types}"
            )

        # Validate questions
        for question in template_data.questions:
            if not question.id or not question.content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each question must have an id and content"
                )

        return True

    async def start_live_ai_interview(
        self,
        interview_id: UUID,
        company_id: UUID
    ) -> Dict[str, Any]:
        """Start a live AI interview session"""
        
        # Get interview with related data
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).join(
            Application.candidate
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id),
                Interview.type == "live_ai"
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Live AI interview not found"
            )

        if interview.status != "scheduled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview is not in scheduled status"
            )

        # Update interview status
        interview.status = "in_progress"
        interview.started_at = datetime.utcnow()
        self.db.commit()

        # Prepare job context
        job = interview.application.job
        job_context = {
            "title": job.title,
            "company": job.company.name,
            "description": job.description,
            "requirements": job.requirements
        }

        # Prepare candidate context
        candidate = interview.application.candidate
        candidate_context = {
            "name": candidate.name,
            "email": candidate.email,
            "background": candidate.parsed_data
        }

        # Get interview configuration
        interview_config = interview.interview_metadata.get("ai_config", {})
        is_trial = interview_config.get("is_trial", False)

        # Import AI service
        from app.services.ai_service import ai_service

        # Start AI interview session
        try:
            ai_session = await ai_service.start_live_ai_interview(
                job_context=job_context,
                candidate_context=candidate_context,
                interview_config=interview_config,
                is_trial=is_trial
            )

            # Store session state in interview metadata
            interview.interview_metadata.update({
                "ai_session": ai_session["session_state"],
                "session_started_at": datetime.utcnow().isoformat()
            })
            self.db.commit()

            return {
                "interview_id": interview_id,
                "session_id": ai_session["session_state"]["session_id"],
                "opening_question": ai_session["opening_question"],
                "candidate_name": candidate.name,
                "job_title": job.title,
                "interview_config": interview_config,
                "started_at": interview.started_at.isoformat()
            }

        except Exception as e:
            # Revert interview status on error
            interview.status = "scheduled"
            interview.started_at = None
            self.db.commit()
            
            logger.error(f"Failed to start live AI interview: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start AI interview: {str(e)}"
            )

    async def process_live_ai_response(
        self,
        interview_id: UUID,
        candidate_response: str,
        response_metadata: Dict[str, Any],
        company_id: UUID
    ) -> Dict[str, Any]:
        """Process candidate response in live AI interview"""
        
        # Get interview
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id),
                Interview.type == "live_ai"
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Live AI interview not found"
            )

        if interview.status != "in_progress":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview is not in progress"
            )

        # Get current session state
        session_state = interview.interview_metadata.get("ai_session", {})
        if not session_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI session not found"
            )

        # Import AI service
        from app.services.ai_service import ai_service

        try:
            # Process response with AI
            ai_result = await ai_service.process_candidate_response_live(
                session_state=session_state,
                candidate_response=candidate_response,
                response_metadata=response_metadata
            )

            # Store candidate response
            candidate_response_record = InterviewResponse(
                interview_id=interview_id,
                question_id=f"live_ai_q_{session_state.get('question_count', 1)}",
                response_type="text",
                content=candidate_response,
                response_metadata={
                    **response_metadata,
                    "analysis": ai_result["analysis"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            self.db.add(candidate_response_record)

            # Store AI response
            ai_response_record = InterviewResponse(
                interview_id=interview_id,
                question_id=f"live_ai_a_{session_state.get('question_count', 1)}",
                response_type="ai_response",
                content=ai_result["ai_response"],
                response_metadata={
                    "interview_phase": ai_result.get("interview_phase", "ongoing"),
                    "should_continue": ai_result.get("should_continue", True),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            self.db.add(ai_response_record)

            # Update session state in interview metadata
            interview.interview_metadata["ai_session"] = ai_result["session_state"]
            self.db.commit()

            return {
                "ai_response": ai_result["ai_response"],
                "analysis": ai_result["analysis"],
                "should_continue": ai_result["should_continue"],
                "interview_phase": ai_result.get("interview_phase", "ongoing"),
                "session_state": ai_result["session_state"]
            }

        except Exception as e:
            logger.error(f"Failed to process live AI response: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process response: {str(e)}"
            )

    async def complete_live_ai_interview(
        self,
        interview_id: UUID,
        company_id: UUID
    ) -> Dict[str, Any]:
        """Complete a live AI interview and generate summary"""
        
        # Get interview
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id),
                Interview.type == "live_ai"
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Live AI interview not found"
            )

        if interview.status != "in_progress":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview is not in progress"
            )

        # Get session state and job context
        session_state = interview.interview_metadata.get("ai_session", {})
        job = interview.application.job
        job_context = {
            "title": job.title,
            "company": job.company.name,
            "requirements": job.requirements
        }

        # Import AI service
        from app.services.ai_service import ai_service

        try:
            # Generate interview summary
            summary = await ai_service.generate_interview_summary(
                session_state=session_state,
                job_context=job_context
            )

            # Update interview status and metadata
            interview.status = "completed"
            interview.completed_at = datetime.utcnow()
            interview.interview_metadata.update({
                "ai_summary": summary,
                "completed_at": datetime.utcnow().isoformat()
            })
            self.db.commit()

            return {
                "interview_id": interview_id,
                "summary": summary,
                "completed_at": interview.completed_at.isoformat(),
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Failed to complete live AI interview: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to complete interview: {str(e)}"
            )

    async def get_live_ai_session_state(
        self,
        interview_id: UUID,
        company_id: UUID
    ) -> Dict[str, Any]:
        """Get current live AI interview session state"""
        
        interview = self.db.query(Interview).join(
            Interview.application
        ).join(
            Application.job
        ).filter(
            and_(
                Interview.id == interview_id,
                Application.job.has(company_id=company_id),
                Interview.type == "live_ai"
            )
        ).first()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Live AI interview not found"
            )

        session_state = interview.interview_metadata.get("ai_session", {})
        
        return {
            "interview_id": interview_id,
            "session_state": session_state,
            "status": interview.status,
            "started_at": interview.started_at.isoformat() if interview.started_at else None,
            "completed_at": interview.completed_at.isoformat() if interview.completed_at else None
        }

    async def customize_template_for_role(
        self,
        template_id: UUID,
        role_requirements: Dict[str, Any],
        company_id: UUID
    ) -> InterviewTemplateSchema:
        """Customize interview template for specific role"""
        
        template = self.db.query(InterviewTemplate).filter(
            and_(
                InterviewTemplate.id == template_id,
                InterviewTemplate.company_id == company_id
            )
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview template not found"
            )

        # Create customized copy
        customized_questions = []
        for question_dict in template.questions:
            # Customize question based on role requirements
            customized_question = question_dict.copy()
            
            # Add role-specific context or modify difficulty
            if role_requirements.get("seniority_level") == "senior":
                customized_question["difficulty"] = "hard"
            elif role_requirements.get("seniority_level") == "junior":
                customized_question["difficulty"] = "easy"
                
            # Add role-specific tags
            role_tags = role_requirements.get("required_skills", [])
            customized_question["tags"] = list(set(
                customized_question.get("tags", []) + role_tags
            ))
            
            customized_questions.append(customized_question)

        # Create new customized template
        customized_template = InterviewTemplate(
            company_id=company_id,
            name=f"{template.name} - {role_requirements.get('role_name', 'Customized')}",
            description=f"Customized for {role_requirements.get('role_name', 'specific role')}",
            type=template.type,
            questions=customized_questions,
            settings={
                **template.settings,
                "customized_for": role_requirements,
                "base_template_id": str(template_id)
            }
        )

        self.db.add(customized_template)
        self.db.commit()
        self.db.refresh(customized_template)

        return InterviewTemplateSchema.from_orm(customized_template)
        self.db.commit()
        self.db.refresh(customized_template)

        return InterviewTemplateSchema.from_orm(customized_template)