"""
Security and compliance schemas
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Audit log response schema"""
    id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityEventRequest(BaseModel):
    """Security event request schema"""
    interview_id: str
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(..., regex="^(low|medium|high|critical)$")
    details: Dict[str, Any] = Field(default_factory=dict)


class SecurityEventResponse(BaseModel):
    """Security event response schema"""
    id: str
    interview_id: str
    event_type: str
    severity: str
    details: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True


class BrowserEnvironmentRequest(BaseModel):
    """Browser environment validation request"""
    interview_id: str
    environment_data: Dict[str, Any] = Field(
        ...,
        description="Browser environment data including extensions, developer tools, etc."
    )


class BrowserEnvironmentResponse(BaseModel):
    """Browser environment validation response"""
    valid: bool
    risk_score: int
    issues: List[str]
    severity: str


class SecurityDashboardResponse(BaseModel):
    """Security dashboard data response"""
    security_events: Dict[str, Any]
    audit_logs: Dict[str, Any]
    period_days: int


class DataRetentionPolicyRequest(BaseModel):
    """Data retention policy request schema"""
    data_type: str = Field(..., description="Type of data (audit_logs, interviews, etc.)")
    retention_days: int = Field(..., gt=0, description="Number of days to retain data")
    auto_delete: bool = Field(default=True, description="Whether to automatically delete expired data")
    encryption_required: bool = Field(default=False, description="Whether data must be encrypted")


class DataRetentionPolicyResponse(BaseModel):
    """Data retention policy response schema"""
    id: str
    data_type: str
    retention_days: int
    auto_delete: bool
    encryption_required: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceActionRequest(BaseModel):
    """Compliance action request schema"""
    subject_id: str = Field(..., description="ID of data subject")
    action: str = Field(..., description="Compliance action (data_export, data_deletion, etc.)")
    legal_basis: Optional[str] = Field(None, description="GDPR Article 6 legal basis")
    details: Dict[str, Any] = Field(default_factory=dict)
    requested_by: Optional[str] = Field(None, description="Email or identifier of requester")


class ComplianceActionResponse(BaseModel):
    """Compliance action response schema"""
    id: str
    subject_id: str
    action: str
    legal_basis: Optional[str]
    details: Dict[str, Any]
    requested_by: Optional[str]
    processed_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityAlertResponse(BaseModel):
    """Security alert response schema"""
    id: str
    alert_type: str
    severity: str
    title: str
    description: Optional[str]
    details: Dict[str, Any]
    resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EncryptionRequest(BaseModel):
    """Data encryption request schema"""
    data: str = Field(..., description="Data to encrypt")


class EncryptionResponse(BaseModel):
    """Data encryption response schema"""
    encrypted_data: str
    status: str


class DecryptionRequest(BaseModel):
    """Data decryption request schema"""
    encrypted_data: str = Field(..., description="Encrypted data to decrypt")


class DecryptionResponse(BaseModel):
    """Data decryption response schema"""
    decrypted_data: str
    status: str


class ProctoringEventResponse(BaseModel):
    """Proctoring event response schema"""
    id: str
    interview_id: str
    event_type: str
    severity: str
    details: Dict[str, Any]
    timestamp: datetime
    is_critical: bool
    requires_attention: bool

    class Config:
        from_attributes = True


class SecurityMetricsResponse(BaseModel):
    """Security metrics response schema"""
    total_audit_logs: int
    total_security_events: int
    critical_events_count: int
    unresolved_alerts_count: int
    compliance_actions_count: int
    data_retention_policies_count: int
    period_start: datetime
    period_end: datetime