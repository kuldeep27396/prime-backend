"""
Application management schemas
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class ApplicationStatus(str, Enum):
    """Application status enum"""
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    ASSESSED = "assessed"
    HIRED = "hired"
    REJECTED = "rejected"


class SortDirection(str, Enum):
    """Sort direction enum"""
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    """Available sort fields"""
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    CANDIDATE_NAME = "candidate_name"
    JOB_TITLE = "job_title"
    OVERALL_SCORE = "overall_score"


# Request schemas

class ApplicationCreate(BaseModel):
    """Schema for creating an application"""
    job_id: UUID
    candidate_id: UUID
    cover_letter: Optional[str] = None
    application_data: Optional[Dict[str, Any]] = {}


class ApplicationUpdate(BaseModel):
    """Schema for updating an application"""
    status: Optional[ApplicationStatus] = None
    cover_letter: Optional[str] = None
    application_data: Optional[Dict[str, Any]] = None


class PipelineStatusUpdate(BaseModel):
    """Schema for updating pipeline status with notes"""
    status: ApplicationStatus
    notes: Optional[str] = None
    changed_by: Optional[str] = None  # User ID or system identifier


class ApplicationFilters(BaseModel):
    """Schema for filtering applications"""
    job_id: Optional[UUID] = None
    candidate_id: Optional[UUID] = None
    status: Optional[Union[ApplicationStatus, List[ApplicationStatus]]] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    updated_from: Optional[datetime] = None
    updated_to: Optional[datetime] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    has_cover_letter: Optional[bool] = None
    min_score: Optional[float] = Field(None, ge=0, le=100)


class ApplicationSort(BaseModel):
    """Schema for sorting applications"""
    field: SortField = SortField.CREATED_AT
    direction: SortDirection = SortDirection.DESC


class RankingWeights(BaseModel):
    """Schema for customizable ranking weights"""
    technical_weight: float = Field(0.3, ge=0, le=1)
    communication_weight: float = Field(0.2, ge=0, le=1)
    cultural_fit_weight: float = Field(0.2, ge=0, le=1)
    cognitive_weight: float = Field(0.15, ge=0, le=1)
    behavioral_weight: float = Field(0.15, ge=0, le=1)

    @validator('*', pre=True)
    def validate_weights_sum(cls, v, values):
        """Validate that all weights sum to 1.0"""
        if len(values) == 4:  # All weights are set
            total = sum(values.values()) + v
            if abs(total - 1.0) > 0.01:  # Allow small floating point errors
                raise ValueError("All weights must sum to 1.0")
        return v


# Response schemas

class ApplicationResponse(BaseModel):
    """Application response schema"""
    id: UUID
    job_id: UUID
    candidate_id: UUID
    status: ApplicationStatus
    cover_letter: Optional[str] = None
    application_data: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    
    # Related data
    candidate_name: str
    candidate_email: str
    job_title: str
    company_id: UUID
    
    # Computed fields
    overall_score: Optional[float] = None
    score_summary: Dict[str, Any] = {}
    interview_count: int = 0
    assessment_count: int = 0
    days_in_pipeline: int = 0

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """Paginated application list response"""
    applications: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    filters: ApplicationFilters
    sort: ApplicationSort


class CandidateRanking(BaseModel):
    """Candidate ranking with scores"""
    application_id: UUID
    candidate_id: UUID
    candidate_name: str
    candidate_email: str
    job_id: UUID
    job_title: str
    overall_score: float
    category_scores: Dict[str, float]
    status: ApplicationStatus
    applied_at: datetime
    last_updated: datetime
    interview_count: int
    assessment_count: int
    rank: int


class FunnelData(BaseModel):
    """Funnel stage data"""
    stage: ApplicationStatus
    count: int
    percentage: float


class PipelineMetrics(BaseModel):
    """Pipeline performance metrics"""
    total_applications: int = 0
    active_applications: int = 0
    hired_count: int = 0
    rejected_count: int = 0
    hire_rate: float = 0.0
    rejection_rate: float = 0.0
    average_stage_times: Dict[str, float] = {}


class ApplicationAnalytics(BaseModel):
    """Complete application analytics"""
    total_applications: int
    funnel_data: List[FunnelData]
    pipeline_metrics: PipelineMetrics
    applications_by_date: List[Dict[str, Any]]
    conversion_rates: Dict[str, float]
    average_time_in_pipeline: Optional[float] = None


# Bulk operations schemas

class BulkStatusUpdate(BaseModel):
    """Schema for bulk status updates"""
    application_ids: List[UUID]
    status: ApplicationStatus
    notes: Optional[str] = None
    changed_by: Optional[str] = None


class BulkStatusUpdateResult(BaseModel):
    """Result of bulk status update"""
    updated_count: int
    failed_count: int
    errors: List[Dict[str, Any]] = []


# Search and filter schemas

class ApplicationSearchQuery(BaseModel):
    """Advanced application search query"""
    query: Optional[str] = None  # Free text search
    filters: ApplicationFilters = ApplicationFilters()
    sort: ApplicationSort = ApplicationSort()
    include_scores: bool = True
    include_interviews: bool = False
    include_assessments: bool = False


class ApplicationSearchResult(ApplicationResponse):
    """Application search result with relevance score"""
    relevance_score: Optional[float] = None
    matching_keywords: List[str] = []


class ApplicationSearchResponse(BaseModel):
    """Application search response"""
    applications: List[ApplicationSearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int
    search_query: Optional[str] = None
    filters: ApplicationFilters
    sort: ApplicationSort


# Dashboard schemas

class DashboardMetrics(BaseModel):
    """Dashboard overview metrics"""
    total_applications_today: int = 0
    total_applications_week: int = 0
    total_applications_month: int = 0
    active_applications: int = 0
    applications_in_review: int = 0
    applications_pending_interview: int = 0
    recent_hires: int = 0
    conversion_rate_week: float = 0.0
    average_time_to_hire: Optional[float] = None


class StatusDistribution(BaseModel):
    """Application status distribution"""
    status: ApplicationStatus
    count: int
    percentage: float
    trend: Optional[str] = None  # "up", "down", "stable"


class DashboardData(BaseModel):
    """Complete dashboard data"""
    metrics: DashboardMetrics
    status_distribution: List[StatusDistribution]
    recent_applications: List[ApplicationResponse]
    top_performing_jobs: List[Dict[str, Any]]
    funnel_data: List[FunnelData]