"""
Application management API endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.company import User
from app.services.application_service import ApplicationService
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    ApplicationListResponse, ApplicationFilters, ApplicationSort,
    PipelineStatusUpdate, CandidateRanking, RankingWeights,
    ApplicationAnalytics, BulkStatusUpdate, BulkStatusUpdateResult,
    ApplicationSearchQuery, ApplicationSearchResponse,
    DashboardData, DashboardMetrics, StatusDistribution
)

router = APIRouter()


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job application"""
    service = ApplicationService(db)
    return await service.create_application(application_data)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application by ID"""
    service = ApplicationService(db)
    return await service.get_application(application_id)


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: UUID,
    application_data: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update application information"""
    service = ApplicationService(db)
    return await service.update_application(application_id, application_data)


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_pipeline_status(
    application_id: UUID,
    status_update: PipelineStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update application pipeline status with notes"""
    # Set the user who made the change
    if not status_update.changed_by:
        status_update.changed_by = str(current_user.id)
    
    service = ApplicationService(db)
    return await service.update_pipeline_status(application_id, status_update)


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    
    # Filters
    job_id: Optional[UUID] = None,
    candidate_id: Optional[UUID] = None,
    status: Optional[str] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    updated_from: Optional[datetime] = None,
    updated_to: Optional[datetime] = None,
    candidate_name: Optional[str] = None,
    job_title: Optional[str] = None,
    has_cover_letter: Optional[bool] = None,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    
    # Sorting
    sort_field: str = Query("created_at"),
    sort_direction: str = Query("desc"),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List applications with filtering and sorting"""
    
    # Parse status filter (can be comma-separated)
    status_list = None
    if status:
        status_list = [s.strip() for s in status.split(",")]
    
    filters = ApplicationFilters(
        job_id=job_id,
        candidate_id=candidate_id,
        status=status_list,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
        candidate_name=candidate_name,
        job_title=job_title,
        has_cover_letter=has_cover_letter,
        min_score=min_score
    )
    
    sort = ApplicationSort(
        field=sort_field,
        direction=sort_direction
    )
    
    service = ApplicationService(db)
    return await service.list_applications(filters, sort, page, page_size)


@router.get("/jobs/{job_id}/rankings", response_model=List[CandidateRanking])
async def get_candidate_rankings(
    job_id: UUID,
    # Customizable weights
    technical_weight: float = Query(0.3, ge=0, le=1),
    communication_weight: float = Query(0.2, ge=0, le=1),
    cultural_fit_weight: float = Query(0.2, ge=0, le=1),
    cognitive_weight: float = Query(0.15, ge=0, le=1),
    behavioral_weight: float = Query(0.15, ge=0, le=1),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ranked candidates for a job with customizable weights"""
    
    # Validate weights sum to 1.0
    total_weight = (technical_weight + communication_weight + 
                   cultural_fit_weight + cognitive_weight + behavioral_weight)
    
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All weights must sum to 1.0"
        )
    
    weights = RankingWeights(
        technical_weight=technical_weight,
        communication_weight=communication_weight,
        cultural_fit_weight=cultural_fit_weight,
        cognitive_weight=cognitive_weight,
        behavioral_weight=behavioral_weight
    )
    
    service = ApplicationService(db)
    return await service.get_candidate_rankings(job_id, weights)


@router.get("/analytics/overview", response_model=ApplicationAnalytics)
async def get_application_analytics(
    job_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application analytics and funnel data"""
    
    # If no company_id provided, use current user's company
    if not company_id:
        company_id = current_user.company_id
    
    service = ApplicationService(db)
    return await service.get_application_analytics(
        job_id=job_id,
        company_id=company_id,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/bulk/status-update", response_model=BulkStatusUpdateResult)
async def bulk_update_status(
    bulk_update: BulkStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update application statuses"""
    
    # Set the user who made the change
    if not bulk_update.changed_by:
        bulk_update.changed_by = str(current_user.id)
    
    service = ApplicationService(db)
    
    result = BulkStatusUpdateResult(
        updated_count=0,
        failed_count=0,
        errors=[]
    )
    
    for app_id in bulk_update.application_ids:
        try:
            status_update = PipelineStatusUpdate(
                status=bulk_update.status,
                notes=bulk_update.notes,
                changed_by=bulk_update.changed_by
            )
            
            await service.update_pipeline_status(app_id, status_update)
            result.updated_count += 1
            
        except Exception as e:
            result.failed_count += 1
            result.errors.append({
                "application_id": str(app_id),
                "error": str(e)
            })
    
    return result


@router.post("/search", response_model=ApplicationSearchResponse)
async def search_applications(
    search_query: ApplicationSearchQuery,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advanced application search with full-text search capabilities"""
    
    service = ApplicationService(db)
    
    # Use the list_applications method with search filters
    response = await service.list_applications(
        filters=search_query.filters,
        sort=search_query.sort,
        page=page,
        page_size=page_size
    )
    
    # Convert to search response format
    search_results = []
    for app in response.applications:
        # Calculate relevance score based on query match
        relevance_score = None
        matching_keywords = []
        
        if search_query.query:
            query_lower = search_query.query.lower()
            app_text = f"{app.candidate_name} {app.candidate_email} {app.job_title}".lower()
            
            # Simple relevance scoring
            query_words = set(query_lower.split())
            app_words = set(app_text.split())
            
            if query_words:
                intersection = len(query_words.intersection(app_words))
                relevance_score = intersection / len(query_words)
                matching_keywords = list(query_words.intersection(app_words))
        
        search_result = ApplicationSearchResult(
            **app.dict(),
            relevance_score=relevance_score,
            matching_keywords=matching_keywords
        )
        search_results.append(search_result)
    
    # Sort by relevance if query provided
    if search_query.query:
        search_results.sort(key=lambda x: x.relevance_score or 0, reverse=True)
    
    return ApplicationSearchResponse(
        applications=search_results,
        total=response.total,
        page=page,
        page_size=page_size,
        total_pages=response.total_pages,
        search_query=search_query.query,
        filters=search_query.filters,
        sort=search_query.sort
    )


@router.get("/dashboard/metrics", response_model=DashboardData)
async def get_dashboard_data(
    company_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard overview data"""
    
    # If no company_id provided, use current user's company
    if not company_id:
        company_id = current_user.company_id
    
    service = ApplicationService(db)
    
    # Get current date ranges
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    
    # Get analytics for different time periods
    today_analytics = await service.get_application_analytics(
        company_id=company_id,
        date_from=today_start,
        date_to=now
    )
    
    week_analytics = await service.get_application_analytics(
        company_id=company_id,
        date_from=week_start,
        date_to=now
    )
    
    month_analytics = await service.get_application_analytics(
        company_id=company_id,
        date_from=month_start,
        date_to=now
    )
    
    all_time_analytics = await service.get_application_analytics(
        company_id=company_id
    )
    
    # Build dashboard metrics
    metrics = DashboardMetrics(
        total_applications_today=today_analytics.total_applications,
        total_applications_week=week_analytics.total_applications,
        total_applications_month=month_analytics.total_applications,
        active_applications=all_time_analytics.pipeline_metrics.active_applications,
        applications_in_review=sum(
            stage.count for stage in all_time_analytics.funnel_data
            if stage.stage in ["screening", "interviewing"]
        ),
        applications_pending_interview=sum(
            stage.count for stage in all_time_analytics.funnel_data
            if stage.stage == "interviewing"
        ),
        recent_hires=sum(
            stage.count for stage in week_analytics.funnel_data
            if stage.stage == "hired"
        ),
        conversion_rate_week=week_analytics.pipeline_metrics.hire_rate,
        average_time_to_hire=all_time_analytics.average_time_in_pipeline
    )
    
    # Build status distribution
    status_distribution = []
    for stage in all_time_analytics.funnel_data:
        status_distribution.append(StatusDistribution(
            status=stage.stage,
            count=stage.count,
            percentage=stage.percentage,
            trend="stable"  # TODO: Calculate trend based on historical data
        ))
    
    # Get recent applications (last 10)
    recent_response = await service.list_applications(
        filters=ApplicationFilters(),
        sort=ApplicationSort(field="created_at", direction="desc"),
        page=1,
        page_size=10
    )
    
    return DashboardData(
        metrics=metrics,
        status_distribution=status_distribution,
        recent_applications=recent_response.applications,
        top_performing_jobs=[],  # TODO: Implement job performance ranking
        funnel_data=all_time_analytics.funnel_data
    )


# Import the missing ApplicationSearchResult class
from app.schemas.application import ApplicationSearchResult