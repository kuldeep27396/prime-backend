"""
Jobs API endpoints
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.company import User
from app.services.job_service import JobService
from app.schemas.job import (
    JobCreate, JobUpdate, JobResponse, JobListResponse, JobSearch,
    JobSearchResponse, JobFilters, JobAnalyticsResponse, JobBulkUpdate,
    JobBulkUpdateResult, JobStatusChange, JobStatusChangeResult,
    JobRequirementsParseRequest, JobRequirementsParseResult, JobStatus
)

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job posting"""
    job_service = JobService(db)
    return await job_service.create_job(
        job_data=job_data,
        created_by_user_id=current_user.id,
        company_id=current_user.company_id
    )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List jobs with pagination and filtering"""
    job_service = JobService(db)
    
    # Create filters
    filters = JobFilters()
    if status:
        filters.status = [status]
    
    return await job_service.list_jobs(
        page=page,
        page_size=page_size,
        company_id=current_user.company_id,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/search", response_model=JobSearchResponse)
async def search_jobs(
    query: Optional[str] = Query(None, description="Search query"),
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    skills: Optional[List[str]] = Query(None, description="Filter by skills"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search jobs with advanced filtering"""
    job_service = JobService(db)
    
    search_params = JobSearch(
        query=query,
        status=status,
        skills=skills or [],
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return await job_service.search_jobs(
        search_params=search_params,
        company_id=current_user.company_id
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job by ID"""
    job_service = JobService(db)
    return await job_service.get_job(
        job_id=job_id,
        company_id=current_user.company_id
    )


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update job information"""
    job_service = JobService(db)
    return await job_service.update_job(
        job_id=job_id,
        job_data=job_data,
        updated_by_user_id=current_user.id,
        company_id=current_user.company_id
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete job (soft delete by setting status to closed)"""
    job_service = JobService(db)
    await job_service.delete_job(
        job_id=job_id,
        company_id=current_user.company_id
    )


@router.patch("/{job_id}/status", response_model=JobStatusChangeResult)
async def change_job_status(
    job_id: UUID,
    status_change: JobStatusChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change job status with audit trail"""
    job_service = JobService(db)
    return await job_service.change_job_status(
        job_id=job_id,
        status_change=status_change,
        changed_by_user_id=current_user.id,
        company_id=current_user.company_id
    )


@router.get("/{job_id}/analytics", response_model=JobAnalyticsResponse)
async def get_job_analytics(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive job analytics and reporting"""
    job_service = JobService(db)
    return await job_service.get_job_analytics(
        job_id=job_id,
        company_id=current_user.company_id
    )


@router.post("/bulk-update", response_model=JobBulkUpdateResult)
async def bulk_update_jobs(
    bulk_update: JobBulkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk update multiple jobs"""
    job_service = JobService(db)
    return await job_service.bulk_update_jobs(
        bulk_update=bulk_update,
        updated_by_user_id=current_user.id,
        company_id=current_user.company_id
    )


@router.post("/parse-requirements", response_model=JobRequirementsParseResult)
async def parse_job_requirements(
    parse_request: JobRequirementsParseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Parse job requirements from job description using AI"""
    job_service = JobService(db)
    return await job_service.parse_job_requirements(parse_request)