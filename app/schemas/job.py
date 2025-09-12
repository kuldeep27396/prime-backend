"""
Job-related Pydantic schemas
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class ExperienceLevel(str, Enum):
    """Experience level enumeration"""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class EducationLevel(str, Enum):
    """Education level enumeration"""
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    PROFESSIONAL = "professional"


class LocationType(str, Enum):
    """Location type enumeration"""
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


# Base schemas
class SkillRequirement(BaseModel):
    """Skill requirement schema"""
    name: str = Field(..., min_length=1, max_length=100)
    required: bool = True
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    proficiency_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced|expert)$")


class SalaryRange(BaseModel):
    """Salary range schema"""
    min_salary: Optional[int] = Field(None, ge=0)
    max_salary: Optional[int] = Field(None, ge=0)
    currency: str = Field("USD", max_length=3)
    period: str = Field("yearly", pattern="^(hourly|monthly|yearly)$")

    @validator("max_salary")
    def validate_salary_range(cls, v, values):
        if v is not None and values.get("min_salary") is not None:
            if v < values["min_salary"]:
                raise ValueError("max_salary must be greater than or equal to min_salary")
        return v


class LocationRequirement(BaseModel):
    """Location requirement schema"""
    type: LocationType
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = None
    travel_required: bool = False


class JobRequirements(BaseModel):
    """Complete job requirements schema"""
    skills: List[SkillRequirement] = []
    experience_level: Optional[ExperienceLevel] = None
    min_experience_years: Optional[int] = Field(None, ge=0, le=50)
    education_level: Optional[EducationLevel] = None
    location: Optional[LocationRequirement] = None
    salary: Optional[SalaryRange] = None
    additional_requirements: List[str] = []


class JobBase(BaseModel):
    """Base job schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10000)
    requirements: JobRequirements = JobRequirements()
    status: JobStatus = JobStatus.DRAFT


class JobCreate(JobBase):
    """Schema for creating a job"""
    company_id: Optional[UUID] = None  # Will be set from authenticated user if not provided


class JobUpdate(BaseModel):
    """Schema for updating a job"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10000)
    requirements: Optional[JobRequirements] = None
    status: Optional[JobStatus] = None


class JobSearch(BaseModel):
    """Schema for job search"""
    query: Optional[str] = None
    status: Optional[JobStatus] = None
    skills: Optional[List[str]] = None
    experience_level: Optional[ExperienceLevel] = None
    location_type: Optional[LocationType] = None
    location_city: Optional[str] = None
    min_salary: Optional[int] = Field(None, ge=0)
    max_salary: Optional[int] = Field(None, ge=0)
    company_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|updated_at|title|status)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class JobFilters(BaseModel):
    """Schema for job filtering"""
    status: Optional[List[JobStatus]] = None
    company_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    skills: Optional[List[str]] = None
    experience_levels: Optional[List[ExperienceLevel]] = None
    location_types: Optional[List[LocationType]] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# Response schemas
class JobResponse(JobBase):
    """Job response schema"""
    id: UUID
    company_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    application_count: Optional[int] = 0
    active_application_count: Optional[int] = 0

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Paginated job list response"""
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobSearchResult(JobResponse):
    """Job search result with relevance score"""
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    matching_skills: List[str] = []
    matching_keywords: List[str] = []


class JobSearchResponse(BaseModel):
    """Job search response"""
    jobs: List[JobSearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int
    search_query: Optional[str] = None
    filters_applied: Dict[str, Any] = {}


# Analytics schemas
class JobApplicationStats(BaseModel):
    """Job application statistics"""
    total_applications: int = 0
    applications_by_status: Dict[str, int] = {}
    applications_by_date: List[Dict[str, Any]] = []
    avg_applications_per_day: float = 0.0
    conversion_rates: Dict[str, float] = {}


class JobPerformanceMetrics(BaseModel):
    """Job performance metrics"""
    views: int = 0
    applications: int = 0
    application_rate: float = 0.0
    time_to_fill: Optional[int] = None  # days
    quality_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    source_breakdown: Dict[str, int] = {}


class CandidateQualityMetrics(BaseModel):
    """Candidate quality metrics for a job"""
    total_candidates: int = 0
    qualified_candidates: int = 0
    qualification_rate: float = 0.0
    avg_experience_years: Optional[float] = None
    skill_match_distribution: Dict[str, int] = {}
    education_distribution: Dict[str, int] = {}


class JobAnalytics(BaseModel):
    """Complete job analytics"""
    job_id: UUID
    application_stats: JobApplicationStats
    performance_metrics: JobPerformanceMetrics
    candidate_quality: CandidateQualityMetrics
    generated_at: datetime


class JobAnalyticsResponse(BaseModel):
    """Job analytics response"""
    analytics: JobAnalytics
    recommendations: List[str] = []
    insights: List[str] = []


# Bulk operations schemas
class JobBulkUpdate(BaseModel):
    """Schema for bulk job updates"""
    job_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    updates: JobUpdate


class JobBulkUpdateResult(BaseModel):
    """Result of bulk job update"""
    total_processed: int
    successful_updates: int
    failed_updates: int
    errors: List[Dict[str, Any]] = []
    updated_job_ids: List[UUID] = []


class JobStatusChange(BaseModel):
    """Schema for job status change"""
    status: JobStatus
    reason: Optional[str] = Field(None, max_length=500)


class JobStatusChangeResult(BaseModel):
    """Result of job status change"""
    job_id: UUID
    old_status: JobStatus
    new_status: JobStatus
    changed_at: datetime
    changed_by: Optional[UUID] = None
    reason: Optional[str] = None


# Job template schemas
class JobTemplate(BaseModel):
    """Job template schema"""
    id: UUID
    name: str
    description: Optional[str] = None
    template_data: JobCreate
    company_id: UUID
    created_by: UUID
    created_at: datetime
    is_public: bool = False

    class Config:
        from_attributes = True


class JobTemplateCreate(BaseModel):
    """Schema for creating job template"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template_data: JobCreate
    is_public: bool = False


class JobTemplateResponse(BaseModel):
    """Job template response"""
    templates: List[JobTemplate]
    total: int


# Job requirements parsing schemas
class JobRequirementsParseRequest(BaseModel):
    """Request to parse job requirements from text"""
    job_description: str = Field(..., min_length=10, max_length=10000)
    job_title: Optional[str] = Field(None, max_length=200)


class JobRequirementsParseResult(BaseModel):
    """Result of job requirements parsing"""
    success: bool
    parsed_requirements: Optional[JobRequirements] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    extracted_skills: List[str] = []
    suggested_improvements: List[str] = []
    error: Optional[str] = None