from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class MentorBase(BaseModel):
    """Base mentor schema"""
    name: str = Field(..., description="Mentor name", example="John Smith")
    title: str = Field(..., description="Professional title", example="Senior Software Engineer")
    currentCompany: str = Field(..., description="Current company", example="Google")
    previousCompanies: Optional[List[str]] = Field(None, description="Previous companies")
    avatar: Optional[str] = Field(None, description="Avatar URL")
    bio: str = Field(..., description="Professional bio")
    specialties: List[str] = Field(..., description="Areas of specialization")
    skills: List[str] = Field(..., description="Technical skills")
    languages: List[str] = Field(..., description="Spoken languages")
    experience: int = Field(..., description="Years of experience", ge=0)
    hourlyRate: float = Field(..., description="Hourly rate in USD", ge=0)
    responseTime: str = Field(..., description="Average response time", example="Within 2 hours")
    timezone: str = Field(..., description="Timezone", example="America/New_York")
    availability: List[str] = Field(..., description="Available time slots")

class MentorCreate(MentorBase):
    """Mentor creation schema"""
    userId: str = Field(..., description="User ID (from users table)")

class MentorUpdate(BaseModel):
    """Mentor update schema"""
    name: Optional[str] = None
    title: Optional[str] = None
    currentCompany: Optional[str] = None
    previousCompanies: Optional[List[str]] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    experience: Optional[int] = None
    hourlyRate: Optional[float] = None
    responseTime: Optional[str] = None
    timezone: Optional[str] = None
    availability: Optional[List[str]] = None
    isActive: Optional[bool] = None

class MentorResponse(MentorBase):
    """Mentor response schema"""
    id: str = Field(..., description="Mentor ID")
    userId: str = Field(..., description="Associated user ID")
    rating: float = Field(..., description="Average rating", ge=0, le=5)
    reviewCount: int = Field(..., description="Number of reviews", ge=0)
    isActive: bool = Field(..., description="Whether mentor is active")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class ReviewResponse(BaseModel):
    """Review response schema"""
    id: str = Field(..., description="Review ID")
    userId: str = Field(..., description="Reviewer user ID")
    userName: str = Field(..., description="Reviewer name")
    rating: int = Field(..., description="Rating (1-5)", ge=1, le=5)
    comment: Optional[str] = Field(None, description="Review comment")
    date: datetime = Field(..., description="Review date")
    sessionType: str = Field(..., description="Session type")

class MentorDetailResponse(MentorResponse):
    """Detailed mentor response with reviews"""
    reviews: List[ReviewResponse] = Field(default_factory=list, description="Mentor reviews")
    upcomingSlots: List[str] = Field(default_factory=list, description="Upcoming available slots")
    isAvailable: bool = Field(..., description="Current availability status")

class MentorFilters(BaseModel):
    """Mentor search filters"""
    page: int = Field(1, description="Page number", ge=1)
    limit: int = Field(20, description="Items per page", ge=1, le=100)
    skills: Optional[str] = Field(None, description="Comma-separated skills")
    companies: Optional[str] = Field(None, description="Comma-separated companies")
    ratingMin: Optional[float] = Field(None, description="Minimum rating", ge=0, le=5)
    priceMin: Optional[float] = Field(None, description="Minimum price", ge=0)
    priceMax: Optional[float] = Field(None, description="Maximum price", ge=0)
    experienceMin: Optional[int] = Field(None, description="Minimum experience years", ge=0)
    languages: Optional[str] = Field(None, description="Comma-separated languages")
    search: Optional[str] = Field(None, description="Search query")

class PaginationResponse(BaseModel):
    """Pagination response schema"""
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total items")
    totalPages: int = Field(..., description="Total pages")

class FilterOptions(BaseModel):
    """Available filter options"""
    availableSkills: List[str] = Field(..., description="Available skills")
    availableCompanies: List[str] = Field(..., description="Available companies")
    availableLanguages: List[str] = Field(..., description="Available languages")
    priceRange: Dict[str, float] = Field(..., description="Price range (min/max)")
    experienceRange: Dict[str, int] = Field(..., description="Experience range (min/max)")

class MentorListResponse(BaseModel):
    """Mentor list response with pagination and filters"""
    mentors: List[MentorResponse] = Field(..., description="List of mentors")
    pagination: PaginationResponse = Field(..., description="Pagination info")
    filters: FilterOptions = Field(..., description="Available filter options")