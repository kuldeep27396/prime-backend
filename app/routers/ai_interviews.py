"""
AI Interviews Router
Handles both B2B screening interviews and mock practice interviews
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
import uuid
import secrets
from datetime import datetime, timedelta

from app.database import get_db
from app.database.models import (
    Company, Job, Candidate, User, AIInterviewSession,
    MockInterviewCategory, UserMockProgress, UserAnalytics
)
from app.schemas.ai_interview import (
    AIInterviewCreate, AIInterviewStart, AIInterviewSubmitAnswer, AIInterviewComplete,
    AIInterviewResponse, AIInterviewStartResponse, AIInterviewNextQuestion, AIInterviewAnalysis,
    InterviewQuestion, QuestionEvaluation,
    MockCategoryResponse, MockCategoryListResponse, MockProgressResponse, MockHistoryResponse,
    MockStartRequest,
    ScreeningInterviewCreate, ScreeningInviteResponse, ScreeningValidateToken, ScreeningTokenResponse,
    AIInterviewCreateResponse, AIInterviewCompleteResponse,
    InterviewType, InterviewStatus, DifficultyLevel
)
from app.auth.clerk_auth import get_current_user
from app.services.ai_engine import ai_engine

router = APIRouter(prefix="/api", tags=["AI Interviews"])


# ==========================================
# MOCK INTERVIEW ENDPOINTS (B2C)
# ==========================================

@router.get("/mock/categories",
           response_model=MockCategoryListResponse,
           summary="Get mock interview categories",
           description="Get all available mock interview categories")
async def get_mock_categories(
    db: AsyncSession = Depends(get_db)
):
    """Get all mock interview categories"""
    try:
        result = await db.execute(
            select(MockInterviewCategory)
            .where(MockInterviewCategory.is_active == True)
            .order_by(MockInterviewCategory.order_index)
        )
        categories = result.scalars().all()
        
        return MockCategoryListResponse(
            categories=[
                MockCategoryResponse(
                    id=str(c.id),
                    name=c.name,
                    display_name=c.display_name,
                    description=c.description or "",
                    icon=c.icon or "code",
                    color=c.color or "blue",
                    topics=c.topics or [],
                    difficulty_levels=c.difficulty_levels or ["easy", "medium", "hard"],
                    is_premium=c.is_premium
                )
                for c in categories
            ]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )


@router.post("/mock/start",
            response_model=AIInterviewStartResponse,
            summary="Start a mock interview",
            description="Start a new mock interview session")
async def start_mock_interview(
    request: MockStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Start a mock interview session"""
    try:
        # Get user
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate questions using AI
        questions = await ai_engine.generate_mock_questions(
            category=request.category.value,
            topic=request.topic,
            difficulty=request.difficulty.value,
            question_count=request.question_count
        )
        
        # Create session
        session = AIInterviewSession(
            user_id=user.id,
            interview_type=InterviewType.MOCK.value,
            mock_category=request.category.value,
            topic=request.topic,
            difficulty=request.difficulty.value,
            status=InterviewStatus.IN_PROGRESS.value,
            started_at=datetime.utcnow(),
            duration_minutes=request.question_count * 3,  # ~3 min per question
            questions=questions,
            answers=[]
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return AIInterviewStartResponse(
            success=True,
            session_id=str(session.id),
            message="Mock interview started",
            questions=[InterviewQuestion(**q) for q in questions],
            total_questions=len(questions),
            time_limit_minutes=session.duration_minutes,
            instructions="Answer each question clearly. Take your time to think before responding."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start mock interview: {str(e)}"
        )


@router.post("/mock/{session_id}/answer",
            response_model=AIInterviewNextQuestion,
            summary="Submit mock answer",
            description="Submit an answer during mock interview")
async def submit_mock_answer(
    session_id: str,
    answer: AIInterviewSubmitAnswer,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit an answer during mock interview"""
    try:
        # Get session
        session_result = await db.execute(
            select(AIInterviewSession).where(AIInterviewSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify user owns this session
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or session.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this session"
            )
        
        if session.status != InterviewStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview is not in progress"
            )
        
        # Find the question
        questions = session.questions or []
        question = next((q for q in questions if q["id"] == answer.question_id), None)
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Evaluate answer using AI
        evaluation = await ai_engine.evaluate_answer(
            question=question["question"],
            answer=answer.answer_text,
            expected_points=question.get("expected_points", []),
            category=question.get("category", "general")
        )
        
        # Store answer
        answers = session.answers or []
        answers.append({
            "question_id": answer.question_id,
            "answer_text": answer.answer_text,
            "time_taken_seconds": answer.time_taken_seconds,
            "evaluation": evaluation,
            "timestamp": datetime.utcnow().isoformat()
        })
        session.answers = answers
        
        # Check if more questions remain
        answered_ids = [a["question_id"] for a in answers]
        remaining = [q for q in questions if q["id"] not in answered_ids]
        
        next_question = None
        if remaining:
            next_question = InterviewQuestion(**remaining[0])
        
        await db.commit()
        
        return AIInterviewNextQuestion(
            success=True,
            message="Answer submitted" if remaining else "All questions answered",
            answered_count=len(answers),
            remaining_count=len(remaining),
            next_question=next_question,
            preview_feedback=evaluation.get("feedback", "")[:200]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.post("/mock/{session_id}/complete",
            response_model=AIInterviewCompleteResponse,
            summary="Complete mock interview",
            description="Complete a mock interview session")
async def complete_mock_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Complete mock interview and generate analysis"""
    try:
        # Get session
        session_result = await db.execute(
            select(AIInterviewSession).where(AIInterviewSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify user
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or session.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this session"
            )
        
        # Calculate scores from answers
        answers = session.answers or []
        evaluations = [a.get("evaluation", {}) for a in answers]
        
        total_score = sum(e.get("score", 0) for e in evaluations)
        overall_score = total_score // len(evaluations) if evaluations else 0
        
        # Update session
        session.status = InterviewStatus.COMPLETED.value
        session.completed_at = datetime.utcnow()
        session.actual_duration_seconds = sum(a.get("time_taken_seconds", 0) for a in answers)
        session.overall_score = overall_score
        session.ai_evaluation = evaluations
        session.ai_feedback = f"Completed {len(answers)} questions with an average score of {overall_score}/100."
        
        # Update user progress
        progress_result = await db.execute(
            select(UserMockProgress).where(
                and_(
                    UserMockProgress.user_id == user.id,
                    UserMockProgress.category == session.mock_category
                )
            )
        )
        progress = progress_result.scalar_one_or_none()
        
        if progress:
            progress.total_attempts += 1
            progress.last_score = overall_score
            progress.last_attempt_at = datetime.utcnow()
            progress.best_score = max(progress.best_score or 0, overall_score)
            progress.average_score = ((progress.average_score or 0) * (progress.total_attempts - 1) + overall_score) / progress.total_attempts
            progress.total_time_spent_seconds = (progress.total_time_spent_seconds or 0) + session.actual_duration_seconds
        else:
            progress = UserMockProgress(
                user_id=user.id,
                category=session.mock_category,
                topic=session.topic,
                total_attempts=1,
                best_score=overall_score,
                average_score=overall_score,
                last_score=overall_score,
                last_attempt_at=datetime.utcnow(),
                total_time_spent_seconds=session.actual_duration_seconds
            )
            db.add(progress)
        
        await db.commit()
        
        return AIInterviewCompleteResponse(
            success=True,
            message="Mock interview completed",
            session_id=str(session.id),
            overall_score=overall_score,
            summary=session.ai_feedback,
            analysis_ready=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete interview: {str(e)}"
        )


@router.get("/mock/{session_id}/analysis",
           response_model=AIInterviewAnalysis,
           summary="Get mock interview analysis",
           description="Get detailed AI analysis of a completed mock interview")
async def get_mock_analysis(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed analysis of mock interview"""
    try:
        # Get session
        session_result = await db.execute(
            select(AIInterviewSession).where(AIInterviewSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or session.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this session"
            )
        
        if session.status != InterviewStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview not completed yet"
            )
        
        # Build evaluation list
        answers = session.answers or []
        questions = session.questions or []
        
        question_evaluations = []
        all_strengths = []
        all_improvements = []
        
        for answer in answers:
            eval_data = answer.get("evaluation", {})
            question = next((q for q in questions if q["id"] == answer["question_id"]), {})
            
            question_evaluations.append(QuestionEvaluation(
                question_id=answer["question_id"],
                score=eval_data.get("score", 0),
                feedback=eval_data.get("feedback", ""),
                strengths=eval_data.get("strengths", []),
                improvements=eval_data.get("improvements", []),
                keywords_found=eval_data.get("points_covered", []),
                keywords_missing=eval_data.get("points_missing", [])
            ))
            
            all_strengths.extend(eval_data.get("strengths", []))
            all_improvements.extend(eval_data.get("improvements", []))
        
        return AIInterviewAnalysis(
            session_id=str(session.id),
            interview_type=session.interview_type,
            overall_score=session.overall_score or 0,
            technical_score=session.technical_score,
            communication_score=session.communication_score,
            problem_solving_score=session.problem_solving_score,
            summary=session.ai_feedback or f"You scored {session.overall_score}/100 in this mock interview.",
            strengths=list(set(all_strengths))[:5],
            areas_to_improve=list(set(all_improvements))[:5],
            question_evaluations=question_evaluations,
            percentile=None,  # TODO: Calculate based on other users' scores
            recommended_topics=[],  # TODO: Generate from weak areas
            recommended_resources=[]  # TODO: Link to learning resources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis: {str(e)}"
        )


@router.get("/mock/history",
           response_model=MockHistoryResponse,
           summary="Get mock interview history",
           description="Get user's mock interview history")
async def get_mock_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user's mock interview history"""
    try:
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Build query
        query = select(AIInterviewSession).where(
            and_(
                AIInterviewSession.user_id == user.id,
                AIInterviewSession.interview_type == InterviewType.MOCK.value
            )
        )
        
        if category:
            query = query.where(AIInterviewSession.mock_category == category)
        
        # Count
        count_result = await db.execute(
            select(func.count(AIInterviewSession.id)).where(
                and_(
                    AIInterviewSession.user_id == user.id,
                    AIInterviewSession.interview_type == InterviewType.MOCK.value
                )
            )
        )
        total = count_result.scalar() or 0
        
        # Paginate
        offset = (page - 1) * limit
        query = query.order_by(AIInterviewSession.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        # Calculate stats
        stats_result = await db.execute(
            select(
                func.count(AIInterviewSession.id),
                func.avg(AIInterviewSession.overall_score),
                func.max(AIInterviewSession.overall_score),
                func.sum(AIInterviewSession.actual_duration_seconds)
            ).where(
                and_(
                    AIInterviewSession.user_id == user.id,
                    AIInterviewSession.interview_type == InterviewType.MOCK.value,
                    AIInterviewSession.status == InterviewStatus.COMPLETED.value
                )
            )
        )
        stats = stats_result.first()
        
        return MockHistoryResponse(
            sessions=[
                AIInterviewResponse(
                    id=str(s.id),
                    interview_type=s.interview_type,
                    mock_category=s.mock_category,
                    topic=s.topic,
                    difficulty=s.difficulty,
                    status=s.status,
                    scheduled_at=s.scheduled_at,
                    started_at=s.started_at,
                    completed_at=s.completed_at,
                    duration_minutes=s.duration_minutes,
                    actual_duration_seconds=s.actual_duration_seconds,
                    overall_score=s.overall_score,
                    technical_score=s.technical_score,
                    communication_score=s.communication_score,
                    problem_solving_score=s.problem_solving_score,
                    created_at=s.created_at,
                    questions=None,  # Don't include questions in history
                    current_question_index=0,
                    total_questions=len(s.questions) if s.questions else 0
                )
                for s in sessions
            ],
            total=total,
            page=page,
            limit=limit,
            total_sessions=stats[0] if stats else 0,
            average_score=float(stats[1]) if stats and stats[1] else 0,
            best_score=stats[2] if stats else 0,
            total_time_spent_minutes=(stats[3] or 0) // 60 if stats else 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )


# ==========================================
# SCREENING INTERVIEW ENDPOINTS (B2B)
# ==========================================

@router.post("/screening/create",
            response_model=ScreeningInviteResponse,
            summary="Create screening interview",
            description="Create and send a screening interview invite to a candidate")
async def create_screening_interview(
    request: ScreeningInterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a screening interview for a candidate"""
    try:
        # Get candidate, job, and company
        result = await db.execute(
            select(Candidate, Job, Company)
            .join(Job, Candidate.job_id == Job.id)
            .join(Company, Job.company_id == Company.id)
            .where(Candidate.id == request.candidate_id)
        )
        row = result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        candidate, job, company = row
        
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != str(company.id) and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this candidate"
            )
        
        # Check company credits
        if company.credits_remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="No interview credits remaining"
            )
        
        # Generate questions for this job
        questions = await ai_engine.generate_screening_questions(
            job_title=job.title,
            job_description=job.description or "",
            skills_required=job.skills_required or [],
            question_count=job.question_count or 5,
            difficulty=job.difficulty_level or "medium",
            custom_questions=job.ai_questions
        )
        
        # Create session
        interview_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)
        
        session = AIInterviewSession(
            candidate_id=candidate.id,
            job_id=job.id,
            interview_type=InterviewType.SCREENING.value,
            status=InterviewStatus.PENDING.value,
            scheduled_at=datetime.utcnow(),
            duration_minutes=job.interview_duration or 15,
            questions=questions,
            answers=[]
        )
        
        db.add(session)
        
        # Update candidate
        candidate.interview_token = interview_token
        candidate.interview_link = f"/interview/{interview_token}"
        candidate.interview_expires_at = expires_at
        candidate.status = "invited"
        candidate.interview_sent_at = datetime.utcnow()
        
        # Deduct credit
        company.credits_remaining -= 1
        company.credits_used += 1
        
        await db.commit()
        await db.refresh(session)
        
        # Send email if requested
        email_sent = False
        if request.send_invite_email:
            try:
                from app.email_service import email_service
                if email_service.is_configured():
                    await email_service.send_email(
                        to_email=candidate.email,
                        to_name=candidate.name,
                        subject=f"Interview Invitation - {job.title} at {company.name}",
                        html_content=f"""
                        <h2>You're invited to interview!</h2>
                        <p>Hi {candidate.name},</p>
                        <p>{request.custom_message or f"You've been selected for an AI screening interview for the {job.title} position."}</p>
                        
                        <p><a href="{candidate.interview_link}">Start Interview</a></p>
                        
                        <p>This link expires on {expires_at.strftime('%B %d, %Y')}.</p>
                        
                        <p>Good luck!<br>{company.name}</p>
                        """
                    )
                    email_sent = True
            except Exception as e:
                print(f"Failed to send email: {e}")
        
        return ScreeningInviteResponse(
            success=True,
            message="Screening interview created",
            session_id=str(session.id),
            candidate_id=str(candidate.id),
            interview_link=candidate.interview_link,
            interview_token=interview_token,
            expires_at=expires_at,
            email_sent=email_sent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create screening interview: {str(e)}"
        )


@router.post("/interview/validate",
            response_model=ScreeningTokenResponse,
            summary="Validate interview token",
            description="Validate an interview token (public endpoint)")
async def validate_interview_token(
    request: ScreeningValidateToken,
    db: AsyncSession = Depends(get_db)
):
    """Validate interview token for public access"""
    try:
        # Find candidate by token
        result = await db.execute(
            select(Candidate, Job, Company)
            .join(Job, Candidate.job_id == Job.id)
            .join(Company, Job.company_id == Company.id)
            .where(Candidate.interview_token == request.token)
        )
        row = result.first()
        
        if not row:
            return ScreeningTokenResponse(valid=False, expired=False)
        
        candidate, job, company = row
        
        # Check expiry
        if candidate.interview_expires_at and candidate.interview_expires_at < datetime.utcnow():
            return ScreeningTokenResponse(valid=False, expired=True)
        
        # Get session
        session_result = await db.execute(
            select(AIInterviewSession).where(
                and_(
                    AIInterviewSession.candidate_id == candidate.id,
                    AIInterviewSession.interview_type == InterviewType.SCREENING.value
                )
            ).order_by(AIInterviewSession.created_at.desc())
        )
        session = session_result.scalar_one_or_none()
        
        return ScreeningTokenResponse(
            valid=True,
            expired=False,
            session_id=str(session.id) if session else None,
            candidate_name=candidate.name,
            job_title=job.title,
            company_name=company.name,
            duration_minutes=job.interview_duration or 15,
            question_count=job.question_count or 5
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate token: {str(e)}"
        )


@router.post("/interview/{token}/start",
            response_model=AIInterviewStartResponse,
            summary="Start screening interview",
            description="Start a screening interview (public endpoint)")
async def start_screening_interview(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Start a screening interview (no auth required, uses token)"""
    try:
        # Find candidate by token
        result = await db.execute(
            select(Candidate, Job)
            .join(Job, Candidate.job_id == Job.id)
            .where(Candidate.interview_token == token)
        )
        row = result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid interview link"
            )
        
        candidate, job = row
        
        # Check expiry
        if candidate.interview_expires_at and candidate.interview_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Interview link has expired"
            )
        
        # Get or create session
        session_result = await db.execute(
            select(AIInterviewSession).where(
                and_(
                    AIInterviewSession.candidate_id == candidate.id,
                    AIInterviewSession.interview_type == InterviewType.SCREENING.value
                )
            ).order_by(AIInterviewSession.created_at.desc())
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found"
            )
        
        # Check if already completed
        if session.status == InterviewStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview has already been completed"
            )
        
        # Start the interview
        session.status = InterviewStatus.IN_PROGRESS.value
        session.started_at = datetime.utcnow()
        
        candidate.status = "interview_scheduled"
        
        await db.commit()
        
        questions = session.questions or []
        
        return AIInterviewStartResponse(
            success=True,
            session_id=str(session.id),
            message="Interview started",
            questions=[InterviewQuestion(**q) for q in questions],
            total_questions=len(questions),
            time_limit_minutes=session.duration_minutes or 15,
            instructions=f"Welcome to your interview for {job.title}. Answer each question clearly. You have {session.duration_minutes} minutes total."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/interview/{session_id}/submit",
            response_model=AIInterviewNextQuestion,
            summary="Submit screening answer",
            description="Submit an answer during screening interview")
async def submit_screening_answer(
    session_id: str,
    answer: AIInterviewSubmitAnswer,
    db: AsyncSession = Depends(get_db)
):
    """Submit an answer during screening interview (no auth)"""
    try:
        # Get session with candidate
        result = await db.execute(
            select(AIInterviewSession, Candidate)
            .join(Candidate, AIInterviewSession.candidate_id == Candidate.id)
            .where(AIInterviewSession.id == session_id)
        )
        row = result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session, candidate = row
        
        if session.status != InterviewStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview is not in progress"
            )
        
        # Find question
        questions = session.questions or []
        question = next((q for q in questions if q["id"] == answer.question_id), None)
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Evaluate answer
        evaluation = await ai_engine.evaluate_answer(
            question=question["question"],
            answer=answer.answer_text,
            expected_points=question.get("expected_points", []),
            category=question.get("category", "technical")
        )
        
        # Store answer
        answers = session.answers or []
        answers.append({
            "question_id": answer.question_id,
            "answer_text": answer.answer_text,
            "time_taken_seconds": answer.time_taken_seconds,
            "evaluation": evaluation,
            "timestamp": datetime.utcnow().isoformat()
        })
        session.answers = answers
        
        # Check remaining
        answered_ids = [a["question_id"] for a in answers]
        remaining = [q for q in questions if q["id"] not in answered_ids]
        
        next_question = None
        if remaining:
            next_question = InterviewQuestion(**remaining[0])
        
        await db.commit()
        
        return AIInterviewNextQuestion(
            success=True,
            message="Answer submitted" if remaining else "All questions answered",
            answered_count=len(answers),
            remaining_count=len(remaining),
            next_question=next_question,
            preview_feedback=None  # Don't show feedback during screening
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.post("/interview/{session_id}/complete",
            response_model=AIInterviewCompleteResponse,
            summary="Complete screening interview",
            description="Complete a screening interview")
async def complete_screening_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Complete screening interview and generate report"""
    try:
        # Get session with candidate and job
        result = await db.execute(
            select(AIInterviewSession, Candidate, Job)
            .join(Candidate, AIInterviewSession.candidate_id == Candidate.id)
            .join(Job, AIInterviewSession.job_id == Job.id)
            .where(AIInterviewSession.id == session_id)
        )
        row = result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session, candidate, job = row
        
        # Generate report
        answers = session.answers or []
        questions = session.questions or []
        
        questions_and_answers = []
        evaluations = []
        
        for answer in answers:
            question = next((q for q in questions if q["id"] == answer["question_id"]), {})
            questions_and_answers.append({
                "question": question.get("question", ""),
                "answer": answer.get("answer_text", "")
            })
            eval_data = answer.get("evaluation", {})
            eval_data["question_id"] = answer["question_id"]
            eval_data["category"] = question.get("category", "general")
            evaluations.append(eval_data)
        
        report = await ai_engine.generate_interview_report(
            job_title=job.title,
            candidate_name=candidate.name,
            questions_and_answers=questions_and_answers,
            question_evaluations=evaluations
        )
        
        # Update session
        session.status = InterviewStatus.COMPLETED.value
        session.completed_at = datetime.utcnow()
        session.actual_duration_seconds = sum(a.get("time_taken_seconds", 0) for a in answers)
        session.overall_score = report["overall_score"]
        session.technical_score = report.get("technical_score")
        session.communication_score = report.get("communication_score")
        session.problem_solving_score = report.get("problem_solving_score")
        session.ai_evaluation = report["question_evaluations"]
        session.ai_feedback = report["summary"]
        
        # Update candidate
        candidate.status = "interview_completed"
        candidate.ai_score = report["overall_score"]
        candidate.ai_summary = report["summary"]
        candidate.ai_strengths = report["strengths"]
        candidate.ai_weaknesses = report["areas_to_improve"]
        candidate.ai_recommendation = report["recommendation"]
        candidate.shortlist_reason = report["recommendation_reason"]
        
        # Auto-shortlist if passes threshold
        if report["overall_score"] >= (job.passing_score or 60):
            candidate.shortlisted = True
        
        await db.commit()
        
        return AIInterviewCompleteResponse(
            success=True,
            message="Interview completed. Thank you for your time!",
            session_id=str(session.id),
            overall_score=report["overall_score"],
            summary="Your interview has been submitted successfully. The hiring team will review your responses.",
            analysis_ready=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete interview: {str(e)}"
        )
