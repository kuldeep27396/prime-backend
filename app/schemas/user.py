from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    """User creation/update schema"""
    userId: str = Field(..., description="Clerk user ID", example="user_123")
    email: EmailStr = Field(..., description="User email address", example="user@example.com")
    firstName: Optional[str] = Field(None, description="First name", example="John")
    lastName: Optional[str] = Field(None, description="Last name", example="Doe")
    profileImage: Optional[str] = Field(None, description="Profile image URL", example="https://example.com/avatar.jpg")
    role: str = Field("candidate", description="User role", example="candidate")
    experience: Optional[str] = Field(None, description="Experience level", example="5 years")
    skills: Optional[List[str]] = Field(None, description="List of skills", example=["Python", "JavaScript", "React"])
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences", example={
        "recentSearches": ["React", "Python"],
        "favoriteTopics": ["Web Development", "Machine Learning"],
        "timezone": "America/New_York"
    })

    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['candidate', 'mentor', 'admin']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v

class UserResponse(BaseModel):
    """User response schema"""
    id: str = Field(..., description="User ID", example="550e8400-e29b-41d4-a716-446655440000")
    userId: str = Field(..., description="Clerk user ID", example="user_123")
    email: EmailStr = Field(..., description="User email", example="user@example.com")
    firstName: Optional[str] = Field(None, description="First name", example="John")
    lastName: Optional[str] = Field(None, description="Last name", example="Doe")
    profileImage: Optional[str] = Field(None, description="Profile image URL", example="https://example.com/avatar.jpg")
    role: str = Field(..., description="User role", example="candidate")
    experience: Optional[str] = Field(None, description="Experience level", example="5 years")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")

class UserProfileResponse(BaseModel):
    """Complete user profile response schema"""
    profile: UserResponse
    sessionHistory: List[Dict[str, Any]] = Field(default_factory=list)
    skillAssessments: List[Dict[str, Any]] = Field(default_factory=list)
    favorites: List[str] = Field(default_factory=list)
    preferences: Optional[Dict[str, Any]] = None

class UserAnalytics(BaseModel):
    """User analytics response schema"""
    stats: Dict[str, Any] = Field(..., description="User statistics")
    progressData: List[Dict[str, Any]] = Field(default_factory=list)
    skillAssessments: List[Dict[str, Any]] = Field(default_factory=list)
    upcomingInterviews: List[Dict[str, Any]] = Field(default_factory=list)
    recentActivity: List[Dict[str, Any]] = Field(default_factory=list)

class SessionHistoryItem(BaseModel):
    """Session history item schema"""
    id: str = Field(..., description="Session ID", example="550e8400-e29b-41d4-a716-446655440000")
    mentorId: str = Field(..., description="Mentor ID", example="550e8400-e29b-41d4-a716-446655440001")
    date: datetime = Field(..., description="Session date")
    duration: int = Field(..., description="Session duration in minutes", example=60)
    type: str = Field(..., description="Session type", example="Mock Technical Interview")
    rating: Optional[int] = Field(None, description="Session rating (1-5)", example=5)
    feedback: Optional[str] = Field(None, description="Session feedback", example="Great session!")

class SkillAssessment(BaseModel):
    """Skill assessment schema"""
    skill: str = Field(..., description="Skill name", example="Python")
    score: int = Field(..., description="Assessment score (0-100)", example=85)
    assessedAt: datetime = Field(..., description="Assessment timestamp")

class UserPreference(BaseModel):
    """User preference schema"""
    recentSearches: List[str] = Field(default_factory=list)
    favoriteTopics: List[str] = Field(default_factory=list)
    favoriteMentors: List[str] = Field(default_factory=list)
    timezone: Optional[str] = Field(None, description="User timezone", example="America/New_York")
    notificationSettings: Optional[Dict[str, Any]] = None