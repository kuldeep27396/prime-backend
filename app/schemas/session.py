from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SessionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MeetingType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IN_PERSON = "in-person"

class SessionCreate(BaseModel):
    """Session creation schema"""
    mentorId: str = Field(..., description="Mentor ID")
    sessionType: str = Field(..., description="Type of session", example="Mock Technical Interview")
    scheduledAt: datetime = Field(..., description="Session date/time")
    duration: int = Field(..., description="Duration in minutes", ge=15, le=480)
    meetingType: MeetingType = Field(..., description="Meeting type")
    recordSession: bool = Field(False, description="Whether to record the session")
    specialRequests: Optional[str] = Field(None, description="Special requests")
    meetingLink: Optional[str] = Field(None, description="Meeting link (auto-generated if not provided)")
    participantEmail: Optional[str] = Field(None, description="Participant email for notifications")
    participantName: Optional[str] = Field(None, description="Participant name")

    @validator('scheduledAt')
    def validate_future_date(cls, v):
        if v <= datetime.now():
            raise ValueError('Session must be scheduled for a future date/time')
        return v

class SessionUpdate(BaseModel):
    """Session update schema"""
    status: Optional[SessionStatus] = None
    rating: Optional[int] = Field(None, description="Session rating (1-5)", ge=1, le=5)
    feedback: Optional[str] = Field(None, description="Session feedback")
    cancellationReason: Optional[str] = Field(None, description="Reason for cancellation")

class SessionResponse(BaseModel):
    """Session response schema"""
    id: str = Field(..., description="Session ID")
    userId: str = Field(..., description="User ID")
    mentorId: str = Field(..., description="Mentor ID")
    sessionType: str = Field(..., description="Session type")
    scheduledAt: datetime = Field(..., description="Scheduled date/time")
    duration: int = Field(..., description="Duration in minutes")
    meetingType: str = Field(..., description="Meeting type")
    meetingLink: Optional[str] = Field(None, description="Meeting link")
    status: str = Field(..., description="Session status")
    recordSession: bool = Field(..., description="Recording enabled")
    specialRequests: Optional[str] = Field(None, description="Special requests")
    rating: Optional[int] = Field(None, description="Session rating")
    feedback: Optional[str] = Field(None, description="Session feedback")
    cancellationReason: Optional[str] = Field(None, description="Cancellation reason")
    recordingUrl: Optional[str] = Field(None, description="Recording URL")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class SessionWithMentorResponse(SessionResponse):
    """Session response with mentor details"""
    mentorName: str = Field(..., description="Mentor name")
    mentorAvatar: Optional[str] = Field(None, description="Mentor avatar URL")
    mentorCompany: str = Field(..., description="Mentor company")

class SessionListResponse(BaseModel):
    """Session list response"""
    sessions: List[SessionWithMentorResponse] = Field(..., description="List of sessions")
    stats: Dict[str, Any] = Field(..., description="Session statistics")

class SessionStats(BaseModel):
    """Session statistics schema"""
    totalSessions: int = Field(..., description="Total number of sessions", ge=0)
    completedSessions: int = Field(..., description="Completed sessions", ge=0)
    upcomingSessions: int = Field(..., description="Upcoming sessions", ge=0)
    averageRating: float = Field(0, description="Average rating", ge=0, le=5)
    totalHours: int = Field(0, description="Total hours spent", ge=0)

class SessionCreateResponse(BaseModel):
    """Response for session creation"""
    success: bool = Field(..., description="Whether session was created successfully")
    session: SessionResponse = Field(..., description="Created session details")
    emailSent: bool = Field(..., description="Whether confirmation email was sent")

# Video room schemas
class VideoRoomCreate(BaseModel):
    """Video room creation schema"""
    sessionId: str = Field(..., description="Session ID")
    duration: int = Field(..., description="Duration in minutes", ge=15, le=480)
    participantName: str = Field(..., description="Participant name")
    mentorName: str = Field(..., description="Mentor name")
    recordSession: bool = Field(False, description="Whether to record")

class VideoRoomResponse(BaseModel):
    """Video room response schema"""
    roomId: str = Field(..., description="Room ID")
    roomUrl: str = Field(..., description="Room URL")
    participantToken: str = Field(..., description="Participant token")
    mentorToken: Optional[str] = Field(None, description="Mentor token")
    expiresAt: datetime = Field(..., description="Token expiration time")

class ParticipantInfo(BaseModel):
    """Participant information schema"""
    name: str = Field(..., description="Participant name")
    role: str = Field(..., description="Participant role")
    joinedAt: datetime = Field(..., description="Join time")
    isActive: bool = Field(..., description="Whether participant is active")

class VideoRoomStatusResponse(BaseModel):
    """Video room status response"""
    roomId: str = Field(..., description="Room ID")
    status: str = Field(..., description="Room status")
    participants: List[ParticipantInfo] = Field(..., description="Room participants")
    recordingUrl: Optional[str] = Field(None, description="Recording URL if available")
    duration: Optional[int] = Field(None, description="Actual session duration")

# Analytics schemas
class ProgressDataItem(BaseModel):
    """Progress data item schema"""
    month: str = Field(..., description="Month", example="2024-01")
    score: float = Field(..., description="Average score", ge=0, le=5)
    interviews: int = Field(..., description="Number of interviews", ge=0)

class UpcomingInterview(BaseModel):
    """Upcoming interview schema"""
    id: str = Field(..., description="Session ID")
    mentorName: str = Field(..., description="Mentor name")
    company: str = Field(..., description="Mentor company")
    title: str = Field(..., description="Session title/type")
    scheduledAt: datetime = Field(..., description="Scheduled time")
    type: str = Field(..., description="Interview type")
    difficulty: Optional[str] = Field(None, description="Difficulty level")

class ActivityItem(BaseModel):
    """Activity item schema"""
    type: str = Field(..., description="Activity type")
    description: str = Field(..., description="Activity description")
    date: datetime = Field(..., description="Activity date")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class UserAnalyticsResponse(BaseModel):
    """User analytics response schema"""
    stats: Dict[str, Any] = Field(..., description="User statistics")
    progressData: List[ProgressDataItem] = Field(..., description="Progress over time")
    skillAssessments: List[Dict[str, Any]] = Field(..., description="Skill assessments")
    upcomingInterviews: List[UpcomingInterview] = Field(..., description="Upcoming interviews")
    recentActivity: List[ActivityItem] = Field(..., description="Recent activity")