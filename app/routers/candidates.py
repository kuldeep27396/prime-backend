"""
Candidates Management Router
Candidate applications and management for B2B screening
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from typing import Optional, List, Dict
import uuid
import secrets
from datetime import datetime, timedelta

from app.database import get_db
from app.database.models import Company, Job, Candidate, User, AIInterviewSession
from app.schemas.candidate import (
    CandidateApply, CandidateCreate, CandidateUpdate, CandidateStatusUpdate,
    CandidateResponse, CandidateListResponse, CandidateDetailResponse,
    ApplicationResponse, BulkUploadResponse, SendInviteResponse,
    ShortlistRequest, ShortlistResponse, ShortlistCandidate, CandidateReportResponse,
    AIEvaluation, AIRecommendation
)
from app.auth.clerk_auth import get_current_user
from app.email_service import email_service

router = APIRouter(prefix="/api", tags=["Candidates"])


# ==========================================
# PUBLIC ENDPOINTS (No Auth Required)
# ==========================================

@router.post("/jobs/{job_id}/apply",
            response_model=ApplicationResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Apply to a job",
            description="Submit a job application (public, no auth required)")
async def apply_to_job(
    job_id: str,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    cover_letter: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Apply to a job (public endpoint)"""
    try:
        # Get job
        job_result = await db.execute(
            select(Job, Company)
            .join(Company, Job.company_id == Company.id)
            .where(and_(Job.id == job_id, Job.is_public == True, Job.status == 'active'))
        )
        row = job_result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or not accepting applications"
            )
        
        job, company = row
        
        # Check deadline
        if job.application_deadline and job.application_deadline < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Application deadline has passed"
            )
        
        # Check if already applied
        existing = await db.execute(
            select(Candidate).where(
                and_(Candidate.job_id == job_id, Candidate.email == email)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied to this job"
            )
        
        # Handle resume upload
        resume_url = None
        resume_text = None
        if resume:
            # TODO: Upload to storage service (S3, etc.)
            # For now, just store the filename
            resume_url = f"/uploads/resumes/{uuid.uuid4()}_{resume.filename}"
            # TODO: Parse resume text for AI processing
        
        # Generate interview token
        interview_token = secrets.token_urlsafe(32)
        interview_expires = datetime.utcnow() + timedelta(hours=72)  # 3 days
        
        # Create candidate
        candidate = Candidate(
            job_id=uuid.UUID(job_id),
            email=email,
            name=name,
            phone=phone,
            linkedin_url=linkedin_url,
            resume_url=resume_url,
            resume_text=resume_text,
            status='applied',
            interview_token=interview_token,
            interview_link=f"/interview/{interview_token}",
            interview_expires_at=interview_expires
        )
        
        db.add(candidate)
        await db.commit()
        await db.refresh(candidate)
        
        # Send confirmation email
        try:
            if email_service.is_configured():
                await email_service.send_email(
                    to_email=email,
                    to_name=name,
                    subject=f"Application Received - {job.title} at {company.name}",
                    html_content=f"""
                    <h2>Application Received</h2>
                    <p>Hi {name},</p>
                    <p>Thank you for applying to <strong>{job.title}</strong> at <strong>{company.name}</strong>.</p>
                    <p>We have received your application and will review it shortly.</p>
                    <p>You may be invited for an AI screening interview. Please check your email for further instructions.</p>
                    <p>Best regards,<br>{company.name} Hiring Team</p>
                    """
                )
        except Exception as e:
            print(f"Failed to send confirmation email: {e}")
        
        return ApplicationResponse(
            success=True,
            message="Application submitted successfully",
            candidate_id=str(candidate.id),
            interview_link=None,  # Will be sent via email when invited
            interview_scheduled=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {str(e)}"
        )


# ==========================================
# AUTHENTICATED ENDPOINTS
# ==========================================

@router.get("/jobs/{job_id}/candidates",
           response_model=CandidateListResponse,
           summary="List candidates for a job",
           description="Get paginated list of candidates for a job")
async def list_candidates(
    job_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    shortlisted_only: bool = Query(False, description="Show only shortlisted"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum AI score"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List candidates for a job"""
    try:
        # Get job and verify access
        job_result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != str(job.company_id) and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this job"
            )
        
        # Build query
        query = select(Candidate).where(Candidate.job_id == job_id)
        
        if status_filter:
            query = query.where(Candidate.status == status_filter)
        
        if shortlisted_only:
            query = query.where(Candidate.shortlisted == True)
        
        if min_score is not None:
            query = query.where(Candidate.ai_score >= min_score)
        
        # Count total
        count_query = select(func.count(Candidate.id)).where(Candidate.job_id == job_id)
        if status_filter:
            count_query = count_query.where(Candidate.status == status_filter)
        if shortlisted_only:
            count_query = count_query.where(Candidate.shortlisted == True)
        if min_score is not None:
            count_query = count_query.where(Candidate.ai_score >= min_score)
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get status counts
        status_counts_result = await db.execute(
            select(Candidate.status, func.count(Candidate.id))
            .where(Candidate.job_id == job_id)
            .group_by(Candidate.status)
        )
        status_counts = {row[0]: row[1] for row in status_counts_result.all()}
        
        # Paginate and sort
        offset = (page - 1) * limit
        query = query.order_by(Candidate.ai_score.desc().nullslast(), Candidate.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        candidates = result.scalars().all()
        
        # Build response
        candidate_responses = []
        for c in candidates:
            candidate_responses.append(CandidateResponse(
                id=str(c.id),
                job_id=str(c.job_id),
                email=c.email,
                name=c.name,
                phone=c.phone,
                linkedin_url=c.linkedin_url,
                resume_url=c.resume_url,
                resume_parsed=c.resume_parsed,
                status=c.status,
                ai_score=c.ai_score,
                ai_summary=c.ai_summary,
                ai_strengths=c.ai_strengths,
                ai_weaknesses=c.ai_weaknesses,
                ai_recommendation=c.ai_recommendation,
                shortlisted=c.shortlisted,
                shortlist_reason=c.shortlist_reason,
                interview_link=c.interview_link,
                interview_sent_at=c.interview_sent_at,
                interview_expires_at=c.interview_expires_at,
                created_at=c.created_at,
                updated_at=c.updated_at
            ))
        
        return CandidateListResponse(
            candidates=candidate_responses,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit,
            status_counts=status_counts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list candidates: {str(e)}"
        )


@router.get("/candidates/{candidate_id}",
           response_model=CandidateDetailResponse,
           summary="Get candidate details",
           description="Get detailed candidate information with interview history")
async def get_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get candidate details"""
    try:
        # Get candidate with job and company
        result = await db.execute(
            select(Candidate, Job, Company)
            .join(Job, Candidate.job_id == Job.id)
            .join(Company, Job.company_id == Company.id)
            .where(Candidate.id == candidate_id)
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
        
        # Get interview sessions
        sessions_result = await db.execute(
            select(AIInterviewSession).where(AIInterviewSession.candidate_id == candidate_id)
            .order_by(AIInterviewSession.created_at.desc())
        )
        sessions = sessions_result.scalars().all()
        
        interview_sessions = []
        for s in sessions:
            interview_sessions.append({
                "id": str(s.id),
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "overall_score": s.overall_score,
                "ai_feedback": s.ai_feedback
            })
        
        return CandidateDetailResponse(
            id=str(candidate.id),
            job_id=str(candidate.job_id),
            email=candidate.email,
            name=candidate.name,
            phone=candidate.phone,
            linkedin_url=candidate.linkedin_url,
            resume_url=candidate.resume_url,
            resume_parsed=candidate.resume_parsed,
            status=candidate.status,
            ai_score=candidate.ai_score,
            ai_summary=candidate.ai_summary,
            ai_strengths=candidate.ai_strengths,
            ai_weaknesses=candidate.ai_weaknesses,
            ai_recommendation=candidate.ai_recommendation,
            shortlisted=candidate.shortlisted,
            shortlist_reason=candidate.shortlist_reason,
            interview_link=candidate.interview_link,
            interview_sent_at=candidate.interview_sent_at,
            interview_expires_at=candidate.interview_expires_at,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            job_title=job.title,
            company_name=company.name,
            interview_sessions=interview_sessions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidate: {str(e)}"
        )


@router.patch("/candidates/{candidate_id}/status",
             response_model=dict,
             summary="Update candidate status",
             description="Update candidate status (e.g., mark as hired, rejected)")
async def update_candidate_status(
    candidate_id: str,
    status_update: CandidateStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update candidate status"""
    try:
        # Get candidate with job
        result = await db.execute(
            select(Candidate, Job)
            .join(Job, Candidate.job_id == Job.id)
            .where(Candidate.id == candidate_id)
        )
        row = result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        candidate, job = row
        
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != str(job.company_id) and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this candidate"
            )
        
        candidate.status = status_update.status.value
        await db.commit()
        
        return {"success": True, "message": f"Candidate status updated to {status_update.status.value}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}"
        )


@router.post("/candidates/{candidate_id}/send-invite",
            response_model=SendInviteResponse,
            summary="Send interview invite",
            description="Send AI interview invite to candidate")
async def send_interview_invite(
    candidate_id: str,
    expires_in_hours: int = Query(72, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send interview invite to candidate"""
    try:
        # Get candidate with job and company
        result = await db.execute(
            select(Candidate, Job, Company)
            .join(Job, Candidate.job_id == Job.id)
            .join(Company, Job.company_id == Company.id)
            .where(Candidate.id == candidate_id)
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
                detail="No interview credits remaining. Please upgrade your plan."
            )
        
        # Generate new token if expired or not set
        if not candidate.interview_token or (candidate.interview_expires_at and candidate.interview_expires_at < datetime.utcnow()):
            candidate.interview_token = secrets.token_urlsafe(32)
        
        candidate.interview_expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        candidate.interview_link = f"/interview/{candidate.interview_token}"
        candidate.status = "invited"
        candidate.interview_sent_at = datetime.utcnow()
        
        await db.commit()
        
        # Send email
        try:
            if email_service.is_configured():
                await email_service.send_email(
                    to_email=candidate.email,
                    to_name=candidate.name,
                    subject=f"Interview Invitation - {job.title} at {company.name}",
                    html_content=f"""
                    <h2>You're invited to interview!</h2>
                    <p>Hi {candidate.name},</p>
                    <p>Great news! You've been selected for an AI screening interview for the <strong>{job.title}</strong> position at <strong>{company.name}</strong>.</p>
                    
                    <h3>Interview Details:</h3>
                    <ul>
                        <li><strong>Duration:</strong> {job.interview_duration} minutes</li>
                        <li><strong>Questions:</strong> {job.question_count} questions</li>
                        <li><strong>Expires:</strong> {candidate.interview_expires_at.strftime('%B %d, %Y at %I:%M %p')} UTC</li>
                    </ul>
                    
                    <p><a href="{candidate.interview_link}" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">Start Interview</a></p>
                    
                    <p><em>Please ensure you have a working camera and microphone before starting.</em></p>
                    
                    <p>Good luck!<br>{company.name} Hiring Team</p>
                    """
                )
        except Exception as e:
            print(f"Failed to send interview invite email: {e}")
        
        return SendInviteResponse(
            success=True,
            message="Interview invite sent successfully",
            candidate_id=str(candidate.id),
            interview_link=candidate.interview_link,
            expires_at=candidate.interview_expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invite: {str(e)}"
        )


@router.post("/jobs/{job_id}/shortlist",
            response_model=ShortlistResponse,
            summary="Run AI shortlisting",
            description="Run AI shortlisting on all interviewed candidates")
async def run_shortlisting(
    job_id: str,
    shortlist_request: ShortlistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Run AI shortlisting on candidates"""
    try:
        # Get job and verify access
        job_result = await db.execute(
            select(Job, Company)
            .join(Company, Job.company_id == Company.id)
            .where(Job.id == job_id)
        )
        row = job_result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job, company = row
        
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != str(company.id) and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this job"
            )
        
        # Get candidates with completed interviews
        threshold = shortlist_request.threshold if shortlist_request.threshold else job.passing_score
        
        candidates_result = await db.execute(
            select(Candidate)
            .where(and_(
                Candidate.job_id == job_id,
                Candidate.status == 'interview_completed',
                Candidate.ai_score.isnot(None)
            ))
            .order_by(Candidate.ai_score.desc())
        )
        candidates = candidates_result.scalars().all()
        
        shortlisted = []
        rejected_count = 0
        
        for candidate in candidates:
            if shortlist_request.limit and len(shortlisted) >= shortlist_request.limit:
                break
            
            if candidate.ai_score >= threshold:
                candidate.shortlisted = True
                candidate.status = 'shortlisted'
                candidate.shortlist_reason = f"AI score of {candidate.ai_score} meets threshold of {threshold}"
                
                shortlisted.append(ShortlistCandidate(
                    id=str(candidate.id),
                    name=candidate.name,
                    email=candidate.email,
                    ai_score=candidate.ai_score,
                    ai_recommendation=candidate.ai_recommendation or "recommend",
                    shortlist_reason=candidate.shortlist_reason,
                    interview_link=candidate.interview_link
                ))
            else:
                candidate.status = 'rejected'
                candidate.shortlist_reason = f"AI score of {candidate.ai_score} below threshold of {threshold}"
                rejected_count += 1
        
        await db.commit()
        
        return ShortlistResponse(
            success=True,
            message=f"Shortlisted {len(shortlisted)} candidates out of {len(candidates)}",
            job_id=job_id,
            total_candidates=len(candidates),
            shortlisted_count=len(shortlisted),
            shortlisted_candidates=shortlisted,
            rejected_count=rejected_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run shortlisting: {str(e)}"
        )
