"""
Candidate-related Pydantic schemas
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID


# Base schemas
class CandidateBase(BaseModel):
    """Base candidate schema"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


class CandidateCreate(CandidateBase):
    """Schema for creating a candidate"""
    resume_file: Optional[bytes] = None
    resume_filename: Optional[str] = None
    cover_letter: Optional[str] = None


class CandidateUpdate(BaseModel):
    """Schema for updating a candidate"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None


class CandidateSearch(BaseModel):
    """Schema for candidate search"""
    query: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_min: Optional[int] = Field(None, ge=0)
    experience_max: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    education_level: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class CandidateBulkImport(BaseModel):
    """Schema for bulk candidate import"""
    file_data: bytes
    filename: str
    file_type: str = Field(..., pattern="^(csv|xlsx|json)$")


# Parsed resume data schemas
class ExtractedSkill(BaseModel):
    """Extracted skill from resume"""
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    category: Optional[str] = None


class WorkExperience(BaseModel):
    """Work experience entry"""
    company: str
    position: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    description: Optional[str] = None
    skills_used: List[str] = []


class Education(BaseModel):
    """Education entry"""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)


class Certification(BaseModel):
    """Certification entry"""
    name: str
    issuer: str
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None


class Language(BaseModel):
    """Language proficiency"""
    language: str
    proficiency: str = Field(..., pattern="^(beginner|intermediate|advanced|native)$")


class ParsedResumeData(BaseModel):
    """Complete parsed resume data"""
    skills: List[ExtractedSkill] = []
    experience: List[WorkExperience] = []
    education: List[Education] = []
    certifications: List[Certification] = []
    languages: List[Language] = []
    total_experience_years: Optional[float] = None
    summary: Optional[str] = None
    contact_info: Dict[str, Any] = {}


# Response schemas
class CandidateResponse(CandidateBase):
    """Candidate response schema"""
    id: UUID
    resume_url: Optional[str] = None
    parsed_data: ParsedResumeData
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CandidateListResponse(BaseModel):
    """Paginated candidate list response"""
    candidates: List[CandidateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CandidateSearchResult(CandidateResponse):
    """Candidate search result with similarity score"""
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    matching_skills: List[str] = []
    matching_keywords: List[str] = []


class CandidateSearchResponse(BaseModel):
    """Candidate search response"""
    candidates: List[CandidateSearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int
    search_query: Optional[str] = None


class BulkImportResult(BaseModel):
    """Bulk import result"""
    total_processed: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, Any]] = []
    imported_candidate_ids: List[UUID] = []


class ResumeParseResult(BaseModel):
    """Resume parsing result"""
    success: bool
    parsed_data: Optional[ParsedResumeData] = None
    error: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


# Application-related schemas
class ApplicationCreate(BaseModel):
    """Schema for creating an application"""
    job_id: UUID
    candidate_id: UUID
    cover_letter: Optional[str] = None
    application_data: Dict[str, Any] = {}


class ApplicationUpdate(BaseModel):
    """Schema for updating an application"""
    status: Optional[str] = Field(None, pattern="^(applied|screening|interviewing|assessed|hired|rejected)$")
    cover_letter: Optional[str] = None
    application_data: Optional[Dict[str, Any]] = None


class ApplicationResponse(BaseModel):
    """Application response schema"""
    id: UUID
    job_id: UUID
    candidate_id: UUID
    status: str
    cover_letter: Optional[str] = None
    application_data: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CandidateWithApplications(CandidateResponse):
    """Candidate with their applications"""
    applications: List[ApplicationResponse] = []