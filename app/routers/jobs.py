"""
Jobs Management Router
Job posting and management for B2B companies
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from typing import Optional, List
import uuid
from datetime import datetime

from app.database import get_db
from app.database.models import Company, Job, Candidate, User, AIInterviewSession
from app.schemas.company import (
    JobCreate, JobUpdate, JobResponse, JobWithStats, JobStats,
    JobListResponse, JobPublicResponse, JobCreateResponse, SuccessResponse
)
from app.auth.clerk_auth import get_current_user

router = APIRouter(prefix="/api", tags=["Jobs"])


@router.post("/companies/{company_id}/jobs",
            response_model=JobCreateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new job posting",
            description="Create a new job posting for AI candidate screening")
async def create_job(
    company_id: str,
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new job posting"""
    try:
        # Verify user has access to this company
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != company_id and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )
        
        # Verify company exists
        company_result = await db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Create job
        job = Job(
            company_id=uuid.UUID(company_id),
            title=job_data.title,
            description=job_data.description,
            requirements=job_data.requirements,
            skills_required=job_data.skills_required,
            experience_min=job_data.experience_min,
            experience_max=job_data.experience_max,
            location=job_data.location,
            job_type=job_data.job_type.value if job_data.job_type else None,
            department=job_data.department,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
            ai_questions=[q.model_dump() for q in job_data.ai_questions] if job_data.ai_questions else None,
            question_count=job_data.question_count,
            interview_duration=job_data.interview_duration,
            difficulty_level=job_data.difficulty_level.value,
            passing_score=job_data.passing_score,
            status=job_data.status.value,
            is_public=job_data.is_public,
            application_deadline=job_data.application_deadline
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        return JobCreateResponse(
            success=True,
            message="Job created successfully",
            job=JobResponse(
                id=str(job.id),
                company_id=str(job.company_id),
                title=job.title,
                description=job.description,
                requirements=job.requirements,
                skills_required=job.skills_required,
                experience_min=job.experience_min,
                experience_max=job.experience_max,
                location=job.location,
                job_type=job.job_type,
                department=job.department,
                salary_min=float(job.salary_min) if job.salary_min else None,
                salary_max=float(job.salary_max) if job.salary_max else None,
                ai_questions=job.ai_questions,
                question_count=job.question_count,
                interview_duration=job.interview_duration,
                difficulty_level=job.difficulty_level,
                passing_score=job.passing_score,
                status=job.status,
                is_public=job.is_public,
                application_deadline=job.application_deadline,
                created_at=job.created_at,
                updated_at=job.updated_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/companies/{company_id}/jobs",
           response_model=JobListResponse,
           summary="List company jobs",
           description="Get paginated list of jobs for a company")
async def list_company_jobs(
    company_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List jobs for a company"""
    try:
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != company_id and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )
        
        # Build query
        query = select(Job).where(Job.company_id == company_id)
        
        if status_filter:
            query = query.where(Job.status == status_filter)
        
        # Get total count
        count_result = await db.execute(
            select(func.count(Job.id)).where(Job.company_id == company_id)
        )
        total = count_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(Job.created_at.desc()).offset(offset).limit(limit)
        
        # Execute
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        # Get company info
        company_result = await db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        
        # Build response with stats for each job
        jobs_with_stats = []
        for job in jobs:
            stats = await _get_job_stats(db, job.id)
            jobs_with_stats.append(JobWithStats(
                id=str(job.id),
                company_id=str(job.company_id),
                title=job.title,
                description=job.description,
                requirements=job.requirements,
                skills_required=job.skills_required,
                experience_min=job.experience_min,
                experience_max=job.experience_max,
                location=job.location,
                job_type=job.job_type,
                department=job.department,
                salary_min=float(job.salary_min) if job.salary_min else None,
                salary_max=float(job.salary_max) if job.salary_max else None,
                ai_questions=job.ai_questions,
                question_count=job.question_count,
                interview_duration=job.interview_duration,
                difficulty_level=job.difficulty_level,
                passing_score=job.passing_score,
                status=job.status,
                is_public=job.is_public,
                application_deadline=job.application_deadline,
                created_at=job.created_at,
                updated_at=job.updated_at,
                stats=stats,
                company_name=company.name if company else None,
                company_logo=company.logo_url if company else None
            ))
        
        return JobListResponse(
            jobs=jobs_with_stats,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}",
           response_model=JobWithStats,
           summary="Get job details",
           description="Get detailed job information with statistics")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get job by ID"""
    try:
        # Get job with company
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
        
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != str(job.company_id) and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this job"
            )
        
        stats = await _get_job_stats(db, job.id)
        
        return JobWithStats(
            id=str(job.id),
            company_id=str(job.company_id),
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            skills_required=job.skills_required,
            experience_min=job.experience_min,
            experience_max=job.experience_max,
            location=job.location,
            job_type=job.job_type,
            department=job.department,
            salary_min=float(job.salary_min) if job.salary_min else None,
            salary_max=float(job.salary_max) if job.salary_max else None,
            ai_questions=job.ai_questions,
            question_count=job.question_count,
            interview_duration=job.interview_duration,
            difficulty_level=job.difficulty_level,
            passing_score=job.passing_score,
            status=job.status,
            is_public=job.is_public,
            application_deadline=job.application_deadline,
            created_at=job.created_at,
            updated_at=job.updated_at,
            stats=stats,
            company_name=company.name,
            company_logo=company.logo_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job: {str(e)}"
        )


@router.get("/jobs/{job_id}/public",
           response_model=JobPublicResponse,
           summary="Get public job details",
           description="Get public job information for application page (no auth required)")
async def get_job_public(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get public job details (no auth required)"""
    try:
        # Get job with company
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
        
        # Check if deadline passed
        if job.application_deadline and job.application_deadline < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Application deadline has passed"
            )
        
        return JobPublicResponse(
            id=str(job.id),
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            skills_required=job.skills_required,
            experience_min=job.experience_min,
            experience_max=job.experience_max,
            location=job.location,
            job_type=job.job_type,
            department=job.department,
            company_name=company.name,
            company_logo=company.logo_url,
            company_website=company.website,
            application_deadline=job.application_deadline
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job: {str(e)}"
        )


@router.patch("/jobs/{job_id}",
             response_model=SuccessResponse,
             summary="Update job details",
             description="Update job posting details")
async def update_job(
    job_id: str,
    update_data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update job details"""
    try:
        # Get job
        job_result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != str(job.company_id) and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this job"
            )
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == 'job_type' and value:
                value = value.value if hasattr(value, 'value') else value
            if key == 'difficulty_level' and value:
                value = value.value if hasattr(value, 'value') else value
            if key == 'status' and value:
                value = value.value if hasattr(value, 'value') else value
            if key == 'ai_questions' and value:
                value = [q.model_dump() if hasattr(q, 'model_dump') else q for q in value]
            if hasattr(job, key):
                setattr(job, key, value)
        
        await db.commit()
        
        return SuccessResponse(
            success=True,
            message="Job updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job: {str(e)}"
        )


@router.delete("/jobs/{job_id}",
              response_model=SuccessResponse,
              summary="Delete job",
              description="Delete a job posting and all associated data")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete job"""
    try:
        # Get job
        job_result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Verify access
        user_result = await db.execute(
            select(User).where(User.user_id == current_user["sub"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user or (str(user.company_id) != str(job.company_id) and user.role != "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this job"
            )
        
        await db.delete(job)
        await db.commit()
        
        return SuccessResponse(
            success=True,
            message="Job deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )


# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def _get_job_stats(db: AsyncSession, job_id: uuid.UUID) -> JobStats:
    """Get statistics for a job"""
    # Get candidate counts by status
    stats_result = await db.execute(
        select(
            func.count(Candidate.id).label('total'),
            func.count(Candidate.id).filter(Candidate.status == 'applied').label('pending'),
            func.count(Candidate.id).filter(Candidate.status == 'interview_completed').label('interviewed'),
            func.count(Candidate.id).filter(Candidate.shortlisted == True).label('shortlisted'),
            func.count(Candidate.id).filter(Candidate.status == 'rejected').label('rejected')
        ).where(Candidate.job_id == job_id)
    )
    stats = stats_result.first()
    
    return JobStats(
        total_candidates=stats.total if stats else 0,
        pending_candidates=stats.pending if stats else 0,
        interviewed_candidates=stats.interviewed if stats else 0,
        shortlisted_candidates=stats.shortlisted if stats else 0,
        rejected_candidates=stats.rejected if stats else 0
    )
