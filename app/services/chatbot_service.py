"""
Chatbot pre-screening service
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.chatbot import ChatbotTemplate, ChatbotSession, ChatbotMessage
from app.models.job import Application, Job, Candidate
from app.schemas.chatbot import (
    ChatbotTemplateCreate, ChatbotTemplateUpdate, ChatbotTemplateResponse,
    ChatbotSessionStart, CandidateResponse, ChatbotInteractionResponse,
    PreScreeningReport, QuestionSummary, EvaluationResult
)
from app.services.ai_service import ai_service
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service for managing chatbot pre-screening conversations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Template Management
    async def create_template(
        self,
        template_data: ChatbotTemplateCreate,
        company_id: UUID,
        user_id: UUID
    ) -> ChatbotTemplateResponse:
        """Create a new chatbot template"""
        
        # Validate question flow
        self._validate_question_flow([q.dict() for q in template_data.question_flow])
        
        template = ChatbotTemplate(
            company_id=company_id,
            name=template_data.name,
            description=template_data.description,
            job_id=template_data.job_id,
            question_flow=[q.dict() for q in template_data.question_flow],
            settings=template_data.settings.dict(),
            created_by=user_id
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return ChatbotTemplateResponse.from_orm(template)
    
    async def update_template(
        self,
        template_id: UUID,
        template_data: ChatbotTemplateUpdate,
        company_id: UUID
    ) -> ChatbotTemplateResponse:
        """Update an existing chatbot template"""
        
        template = self.db.query(ChatbotTemplate).filter(
            and_(
                ChatbotTemplate.id == template_id,
                ChatbotTemplate.company_id == company_id
            )
        ).first()
        
        if not template:
            raise NotFoundError("Chatbot template not found")
        
        # Update fields
        update_data = template_data.dict(exclude_unset=True)
        
        if "question_flow" in update_data and update_data["question_flow"]:
            question_flow_dicts = [q.dict() for q in update_data["question_flow"]]
            self._validate_question_flow(question_flow_dicts)
            update_data["question_flow"] = question_flow_dicts
        
        if "settings" in update_data:
            update_data["settings"] = update_data["settings"].dict()
        
        for field, value in update_data.items():
            setattr(template, field, value)
        
        self.db.commit()
        self.db.refresh(template)
        
        return ChatbotTemplateResponse.from_orm(template)
    
    async def get_templates(
        self,
        company_id: UUID,
        job_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> List[ChatbotTemplateResponse]:
        """Get chatbot templates for a company"""
        
        query = self.db.query(ChatbotTemplate).filter(
            ChatbotTemplate.company_id == company_id
        )
        
        if job_id:
            query = query.filter(ChatbotTemplate.job_id == job_id)
        
        if active_only:
            query = query.filter(ChatbotTemplate.is_active == True)
        
        templates = query.all()
        return [ChatbotTemplateResponse.from_orm(t) for t in templates]
    
    async def get_template(
        self,
        template_id: UUID,
        company_id: UUID
    ) -> ChatbotTemplateResponse:
        """Get a specific chatbot template"""
        
        template = self.db.query(ChatbotTemplate).filter(
            and_(
                ChatbotTemplate.id == template_id,
                ChatbotTemplate.company_id == company_id
            )
        ).first()
        
        if not template:
            raise NotFoundError("Chatbot template not found")
        
        return ChatbotTemplateResponse.from_orm(template)
    
    # Session Management
    async def start_session(
        self,
        session_data: ChatbotSessionStart,
        is_trial: bool = False
    ) -> Dict[str, Any]:
        """Start a new chatbot session"""
        
        # Validate application exists
        application = self.db.query(Application).filter(
            Application.id == session_data.application_id
        ).first()
        
        if not application:
            raise NotFoundError("Application not found")
        
        # Validate template exists
        template = self.db.query(ChatbotTemplate).filter(
            ChatbotTemplate.id == session_data.template_id
        ).first()
        
        if not template:
            raise NotFoundError("Chatbot template not found")
        
        # Check if session already exists
        existing_session = self.db.query(ChatbotSession).filter(
            and_(
                ChatbotSession.application_id == session_data.application_id,
                ChatbotSession.template_id == session_data.template_id,
                ChatbotSession.status.in_(["started", "in_progress"])
            )
        ).first()
        
        if existing_session:
            return await self._get_session_state(existing_session, is_trial)
        
        # Create new session
        session = ChatbotSession(
            application_id=session_data.application_id,
            template_id=session_data.template_id,
            status="started"
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Send welcome message and first question
        return await self._initialize_conversation(session, template, application, is_trial)
    
    async def process_candidate_response(
        self,
        session_id: UUID,
        response_data: CandidateResponse,
        is_trial: bool = False
    ) -> ChatbotInteractionResponse:
        """Process candidate response and generate next interaction"""
        
        session = self.db.query(ChatbotSession).filter(
            ChatbotSession.id == session_id
        ).first()
        
        if not session:
            raise NotFoundError("Chatbot session not found")
        
        if session.status not in ["started", "in_progress"]:
            raise ValidationError("Session is not active")
        
        # Get template and current question
        template = self.db.query(ChatbotTemplate).filter(
            ChatbotTemplate.id == session.template_id
        ).first()
        
        question_flow = template.question_flow
        current_question = question_flow[session.current_question_index]
        
        # Save candidate response
        await self._save_candidate_message(session, response_data, current_question)
        
        # Evaluate response
        evaluation = await self._evaluate_response(
            session, response_data, current_question, template
        )
        
        # Update session with evaluation
        session.evaluation_results[response_data.question_id] = evaluation
        session.responses[response_data.question_id] = response_data.response
        
        # Check if follow-up is needed
        follow_up = await self._check_follow_up(
            current_question, response_data.response, evaluation
        )
        
        if follow_up:
            # Generate follow-up question
            bot_response = await self._generate_bot_response(
                session, template, follow_up, is_trial
            )
            
            await self._save_bot_message(session, bot_response, current_question["id"])
            
            return ChatbotInteractionResponse(
                message=bot_response,
                question_id=current_question["id"],
                is_final=False,
                session_status="in_progress",
                progress=self._calculate_progress(session, template)
            )
        
        # Move to next question or complete session
        return await self._advance_conversation(session, template, is_trial)
    
    async def get_session_status(self, session_id: UUID) -> Dict[str, Any]:
        """Get current session status and conversation history"""
        
        session = self.db.query(ChatbotSession).filter(
            ChatbotSession.id == session_id
        ).first()
        
        if not session:
            raise NotFoundError("Chatbot session not found")
        
        # Get conversation messages
        messages = self.db.query(ChatbotMessage).filter(
            ChatbotMessage.session_id == session_id
        ).order_by(ChatbotMessage.timestamp).all()
        
        return {
            "session_id": session.id,
            "status": session.status,
            "progress": self._calculate_progress(session, None),
            "conversation_history": [
                {
                    "id": msg.id,
                    "sender": msg.sender,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "question_id": msg.question_id
                }
                for msg in messages
            ],
            "current_question_index": session.current_question_index,
            "overall_score": session.overall_score
        }
    
    async def generate_pre_screening_report(
        self,
        session_id: UUID
    ) -> PreScreeningReport:
        """Generate comprehensive pre-screening report"""
        
        session = self.db.query(ChatbotSession).filter(
            ChatbotSession.id == session_id
        ).first()
        
        if not session:
            raise NotFoundError("Chatbot session not found")
        
        if session.status != "completed":
            raise ValidationError("Session must be completed to generate report")
        
        # Get related data
        application = self.db.query(Application).filter(
            Application.id == session.application_id
        ).first()
        
        candidate = self.db.query(Candidate).filter(
            Candidate.id == application.candidate_id
        ).first()
        
        job = self.db.query(Job).filter(
            Job.id == application.job_id
        ).first()
        
        template = self.db.query(ChatbotTemplate).filter(
            ChatbotTemplate.id == session.template_id
        ).first()
        
        # Calculate metrics
        total_time = self._calculate_session_duration(session)
        completion_rate = len(session.responses) / len(template.question_flow)
        
        # Generate question summaries
        question_summaries = []
        for question_config in template.question_flow:
            question_id = question_config["id"]
            if question_id in session.responses:
                evaluation = session.evaluation_results.get(question_id, {})
                
                summary = QuestionSummary(
                    question_id=question_id,
                    question_text=question_config["text"],
                    candidate_response=str(session.responses[question_id]),
                    evaluation=EvaluationResult(**evaluation) if evaluation else None
                )
                question_summaries.append(summary)
        
        # Generate AI summary
        ai_summary = await ai_service.generate_pre_screening_summary(
            {
                "responses": session.responses,
                "evaluations": session.evaluation_results,
                "overall_score": session.overall_score
            },
            job.requirements
        )
        
        return PreScreeningReport(
            session_id=session.id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            job_title=job.title,
            overall_score=session.overall_score or 0,
            completion_rate=completion_rate,
            total_time_minutes=total_time,
            question_summaries=question_summaries,
            strengths=ai_summary.get("strengths", []),
            concerns=ai_summary.get("concerns", []),
            recommendation=ai_summary.get("recommendation", "needs_review"),
            generated_at=datetime.utcnow()
        )
    
    # Private helper methods
    def _validate_question_flow(self, question_flow: List[Dict[str, Any]]) -> None:
        """Validate question flow configuration"""
        if not question_flow:
            raise ValidationError("Question flow cannot be empty")
        
        question_ids = set()
        for question in question_flow:
            if not question.get("id"):
                raise ValidationError("Each question must have an ID")
            
            if question["id"] in question_ids:
                raise ValidationError(f"Duplicate question ID: {question['id']}")
            
            question_ids.add(question["id"])
            
            if not question.get("text"):
                raise ValidationError("Each question must have text")
    
    async def _initialize_conversation(
        self,
        session: ChatbotSession,
        template: ChatbotTemplate,
        application: Application,
        is_trial: bool
    ) -> Dict[str, Any]:
        """Initialize conversation with welcome message and first question"""
        
        # Get candidate info for context
        candidate = self.db.query(Candidate).filter(
            Candidate.id == application.candidate_id
        ).first()
        
        # Send welcome message
        welcome_message = f"Hello {candidate.name}! I'm here to help with your pre-screening for this position. I'll ask you a few questions to better understand your background and qualifications. Let's get started!"
        
        await self._save_bot_message(session, welcome_message, None, "system")
        
        # Get first question
        first_question = template.question_flow[0]
        
        # Generate contextual question presentation
        question_response = await self._generate_bot_response(
            session, template, first_question["text"], is_trial
        )
        
        await self._save_bot_message(session, question_response, first_question["id"])
        
        # Update session status
        session.status = "in_progress"
        self.db.commit()
        
        return {
            "session_id": session.id,
            "message": question_response,
            "question_id": first_question["id"],
            "is_final": False,
            "session_status": "in_progress",
            "progress": 0.0
        }
    
    async def _save_candidate_message(
        self,
        session: ChatbotSession,
        response_data: CandidateResponse,
        question_config: Dict[str, Any]
    ) -> None:
        """Save candidate message to database"""
        
        message = ChatbotMessage(
            session_id=session.id,
            sender="candidate",
            message_type="response",
            content=str(response_data.response),
            question_id=response_data.question_id,
            message_metadata={
                "response_time": response_data.response_time,
                "question_type": question_config.get("type")
            }
        )
        
        self.db.add(message)
        self.db.commit()
    
    async def _save_bot_message(
        self,
        session: ChatbotSession,
        content: str,
        question_id: Optional[str],
        message_type: str = "question"
    ) -> None:
        """Save bot message to database"""
        
        message = ChatbotMessage(
            session_id=session.id,
            sender="bot",
            message_type=message_type,
            content=content,
            question_id=question_id
        )
        
        self.db.add(message)
        self.db.commit()
    
    async def _evaluate_response(
        self,
        session: ChatbotSession,
        response_data: CandidateResponse,
        question_config: Dict[str, Any],
        template: ChatbotTemplate
    ) -> Dict[str, Any]:
        """Evaluate candidate response using AI"""
        
        # Get job context
        application = self.db.query(Application).filter(
            Application.id == session.application_id
        ).first()
        
        job = self.db.query(Job).filter(
            Job.id == application.job_id
        ).first()
        
        evaluation_criteria = question_config.get("evaluation_criteria", {})
        
        return await ai_service.evaluate_candidate_response(
            question_config["text"],
            str(response_data.response),
            evaluation_criteria,
            {
                "job_title": job.title,
                "job_requirements": job.requirements,
                "job_description": job.description
            }
        )
    
    async def _check_follow_up(
        self,
        question_config: Dict[str, Any],
        candidate_response: str,
        evaluation: Dict[str, Any]
    ) -> Optional[str]:
        """Check if follow-up question is needed"""
        
        follow_up_rules = question_config.get("follow_up_rules", {})
        
        if not follow_up_rules.get("enabled", False):
            return None
        
        # Check if response needs clarification (low score or confidence)
        if evaluation.get("score", 100) < 60 or evaluation.get("confidence", 1) < 0.7:
            return await ai_service.generate_follow_up_question(
                question_config["text"],
                candidate_response,
                follow_up_rules
            )
        
        return None
    
    async def _generate_bot_response(
        self,
        session: ChatbotSession,
        template: ChatbotTemplate,
        content: str,
        is_trial: bool
    ) -> str:
        """Generate contextual bot response"""
        
        # Get conversation history
        messages = self.db.query(ChatbotMessage).filter(
            ChatbotMessage.session_id == session.id
        ).order_by(ChatbotMessage.timestamp.desc()).limit(10).all()
        
        conversation_history = [
            {
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in reversed(messages)
        ]
        
        # Get candidate context
        application = self.db.query(Application).filter(
            Application.id == session.application_id
        ).first()
        
        candidate = self.db.query(Candidate).filter(
            Candidate.id == application.candidate_id
        ).first()
        
        candidate_context = {
            "name": candidate.name,
            "email": candidate.email,
            "parsed_data": candidate.parsed_data
        }
        
        return await ai_service.generate_chatbot_response(
            conversation_history,
            template.settings,
            candidate_context,
            is_trial
        )
    
    async def _advance_conversation(
        self,
        session: ChatbotSession,
        template: ChatbotTemplate,
        is_trial: bool
    ) -> ChatbotInteractionResponse:
        """Advance to next question or complete session"""
        
        session.current_question_index += 1
        
        # Check if we've reached the end
        if session.current_question_index >= len(template.question_flow):
            return await self._complete_session(session, template)
        
        # Get next question
        next_question = template.question_flow[session.current_question_index]
        
        # Generate question presentation
        question_response = await self._generate_bot_response(
            session, template, next_question["text"], is_trial
        )
        
        await self._save_bot_message(session, question_response, next_question["id"])
        
        self.db.commit()
        
        return ChatbotInteractionResponse(
            message=question_response,
            question_id=next_question["id"],
            is_final=False,
            session_status="in_progress",
            progress=self._calculate_progress(session, template)
        )
    
    async def _complete_session(
        self,
        session: ChatbotSession,
        template: ChatbotTemplate
    ) -> ChatbotInteractionResponse:
        """Complete the chatbot session"""
        
        # Calculate overall score
        scores = [
            eval_result.get("score", 0)
            for eval_result in session.evaluation_results.values()
            if isinstance(eval_result, dict) and "score" in eval_result
        ]
        
        overall_score = int(sum(scores) / len(scores)) if scores else 0
        
        # Update session
        session.status = "completed"
        session.overall_score = overall_score
        session.completed_at = datetime.utcnow()
        
        # Send completion message
        completion_message = f"Thank you for completing the pre-screening! Your responses have been recorded and will be reviewed by our team. We'll be in touch soon regarding next steps."
        
        await self._save_bot_message(session, completion_message, None, "system")
        
        self.db.commit()
        
        return ChatbotInteractionResponse(
            message=completion_message,
            is_final=True,
            session_status="completed",
            progress=100.0
        )
    
    def _calculate_progress(
        self,
        session: ChatbotSession,
        template: Optional[ChatbotTemplate]
    ) -> float:
        """Calculate session progress percentage"""
        if not template:
            template = self.db.query(ChatbotTemplate).filter(
                ChatbotTemplate.id == session.template_id
            ).first()
        
        if not template:
            return 0.0
        
        total_questions = len(template.question_flow)
        completed_questions = len(session.responses)
        
        return (completed_questions / total_questions) * 100.0
    
    def _calculate_session_duration(self, session: ChatbotSession) -> int:
        """Calculate session duration in minutes"""
        if not session.completed_at:
            return 0
        
        duration = session.completed_at - session.started_at
        return int(duration.total_seconds() / 60)
    
    async def _get_session_state(
        self,
        session: ChatbotSession,
        is_trial: bool
    ) -> Dict[str, Any]:
        """Get current state of existing session"""
        
        template = self.db.query(ChatbotTemplate).filter(
            ChatbotTemplate.id == session.template_id
        ).first()
        
        if session.current_question_index < len(template.question_flow):
            current_question = template.question_flow[session.current_question_index]
            
            return {
                "session_id": session.id,
                "message": f"Let's continue where we left off. {current_question['text']}",
                "question_id": current_question["id"],
                "is_final": False,
                "session_status": session.status,
                "progress": self._calculate_progress(session, template)
            }
        
        return {
            "session_id": session.id,
            "message": "Your pre-screening session has been completed.",
            "is_final": True,
            "session_status": session.status,
            "progress": 100.0
        }