"""
Integration schemas for ATS, calendar, and communication services
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class ATSType(str, Enum):
    """Supported ATS systems"""
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    BAMBOOHR = "bamboohr"


class IntegrationStatus(str, Enum):
    """Integration connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class CandidateStatus(str, Enum):
    """Candidate status for ATS sync"""
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    ASSESSED = "assessed"
    HIRED = "hired"
    REJECTED = "rejected"


# ATS Integration Schemas
class ATSCredentials(BaseModel):
    """ATS authentication credentials"""
    api_key: str
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    additional_config: Dict[str, Any] = Field(default_factory=dict)


class ATSField(BaseModel):
    """ATS field definition"""
    name: str
    type: str
    required: bool = False
    options: Optional[List[str]] = None


class PrimeField(BaseModel):
    """PRIME field definition"""
    name: str
    type: str
    required: bool = False


class FieldMapping(BaseModel):
    """Field mapping between ATS and PRIME"""
    ats_field: str
    prime_field: str
    transformation: Optional[str] = None  # e.g., "uppercase", "date_format"


class ATSCandidate(BaseModel):
    """ATS candidate data"""
    external_id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    status: str
    job_id: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ATSJob(BaseModel):
    """ATS job data"""
    external_id: str
    title: str
    description: str
    status: str
    department: Optional[str] = None
    location: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class SyncResult(BaseModel):
    """Result of ATS sync operation"""
    success: bool
    candidates_synced: int
    jobs_synced: int
    errors: List[str] = Field(default_factory=list)
    sync_timestamp: datetime


class ATSCandidateUpdate(BaseModel):
    """Update data for ATS candidate"""
    status: Optional[CandidateStatus] = None
    notes: Optional[str] = None
    stage: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


# Calendar Integration Schemas
class CalendarProvider(str, Enum):
    """Supported calendar providers"""
    GOOGLE = "google"
    OUTLOOK = "outlook"


class TimeSlot(BaseModel):
    """Time slot for scheduling"""
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"


class CalendarEvent(BaseModel):
    """Calendar event data"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    attendees: List[EmailStr] = Field(default_factory=list)
    location: Optional[str] = None
    meeting_url: Optional[str] = None


class CalendarCredentials(BaseModel):
    """Calendar authentication credentials"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    provider: CalendarProvider


# Communication Schemas
class EmailTemplate(BaseModel):
    """Email template definition"""
    id: Optional[str] = None
    name: str
    subject: str
    html_content: str
    text_content: str
    variables: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class SMSTemplate(BaseModel):
    """SMS template definition"""
    id: Optional[str] = None
    name: str
    content: str
    variables: List[str] = Field(default_factory=list)


class NotificationRequest(BaseModel):
    """Notification request"""
    recipient: EmailStr
    template_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None


class CampaignRequest(BaseModel):
    """Bulk campaign request"""
    name: str
    template_id: str
    recipients: List[EmailStr]
    variables: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # per-recipient variables
    scheduled_at: Optional[datetime] = None


class CampaignResult(BaseModel):
    """Campaign execution result"""
    campaign_id: str
    total_recipients: int
    sent_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None


# Integration Configuration Schemas
class IntegrationConfig(BaseModel):
    """Base integration configuration"""
    name: str
    type: str
    enabled: bool = True
    credentials: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    field_mappings: List[FieldMapping] = Field(default_factory=list)


class ATSIntegrationConfig(IntegrationConfig):
    """ATS integration configuration"""
    ats_type: ATSType
    sync_frequency: int = 3600  # seconds
    auto_sync_enabled: bool = True
    sync_candidates: bool = True
    sync_jobs: bool = True


class CalendarIntegrationConfig(IntegrationConfig):
    """Calendar integration configuration"""
    provider: CalendarProvider
    default_duration: int = 3600  # seconds
    buffer_time: int = 900  # 15 minutes
    auto_schedule: bool = False


class CommunicationConfig(IntegrationConfig):
    """Communication service configuration"""
    email_provider: str = "resend"
    sms_provider: str = "twilio"
    default_sender: EmailStr
    templates: List[EmailTemplate] = Field(default_factory=list)


# Response Schemas
class IntegrationStatusResponse(BaseModel):
    """Integration status response"""
    integration_id: str
    name: str
    type: str
    status: IntegrationStatus
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None


class IntegrationListResponse(BaseModel):
    """List of integrations response"""
    integrations: List[IntegrationStatusResponse]
    total: int


class SyncHistoryResponse(BaseModel):
    """Sync history response"""
    sync_id: str
    integration_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    candidates_synced: int
    jobs_synced: int
    errors: List[str] = Field(default_factory=list)