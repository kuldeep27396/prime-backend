"""
Security and compliance API endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_admin_user
from app.models.company import User
from app.models.audit import AuditLog, ProctoringEvent, SecurityAlert, ComplianceLog, DataRetentionPolicy
from app.services.security_service import security_service
from app.schemas.security import (
    AuditLogResponse, SecurityEventRequest, SecurityEventResponse,
    BrowserEnvironmentRequest, BrowserEnvironmentResponse,
    SecurityDashboardResponse, DataRetentionPolicyRequest, DataRetentionPolicyResponse,
    ComplianceActionRequest, ComplianceActionResponse, SecurityAlertResponse
)

router = APIRouter()


@router.post("/audit-log", response_model=Dict[str, str])
async def create_audit_log(
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create audit log entry"""
    try:
        audit_log = await security_service.log_user_action(
            db=db,
            user_id=str(current_user.id),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request=request
        )
        
        return {"status": "logged", "audit_log_id": str(audit_log.id)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create audit log: {str(e)}"
        )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get audit logs with filtering"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        audit_logs = await security_service.get_audit_logs(
            db=db,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            limit=limit,
            offset=offset
        )
        
        return [
            AuditLogResponse(
                id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=str(log.ip_address) if log.ip_address else None,
                user_agent=log.user_agent,
                created_at=log.created_at
            )
            for log in audit_logs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.post("/security-event", response_model=SecurityEventResponse)
async def log_security_event(
    event_data: SecurityEventRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log security/proctoring event"""
    try:
        event = await security_service.log_security_event(
            db=db,
            interview_id=event_data.interview_id,
            event_type=event_data.event_type,
            severity=event_data.severity,
            details=event_data.details
        )
        
        return SecurityEventResponse(
            id=str(event.id),
            interview_id=str(event.interview_id),
            event_type=event.event_type,
            severity=event.severity,
            details=event.details,
            timestamp=event.timestamp
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log security event: {str(e)}"
        )


@router.post("/validate-browser-environment", response_model=BrowserEnvironmentResponse)
async def validate_browser_environment(
    environment_data: BrowserEnvironmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate browser environment for security"""
    try:
        validation_result = await security_service.validate_browser_environment(
            db=db,
            interview_id=environment_data.interview_id,
            environment_data=environment_data.environment_data
        )
        
        return BrowserEnvironmentResponse(**validation_result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate browser environment: {str(e)}"
        )


@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get security dashboard data"""
    try:
        dashboard_data = await security_service.get_security_dashboard_data(
            db=db,
            company_id=str(current_user.company_id),
            days=days
        )
        
        return SecurityDashboardResponse(**dashboard_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security dashboard data: {str(e)}"
        )


@router.post("/anonymize-user", response_model=Dict[str, str])
async def anonymize_user_data(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Anonymize user data for GDPR compliance"""
    try:
        result = await security_service.anonymize_user_data(db=db, user_id=user_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to anonymize user data: {str(e)}"
        )


@router.delete("/delete-user/{user_id}", response_model=Dict[str, str])
async def delete_user_data(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete user data for GDPR right to be forgotten"""
    try:
        result = await security_service.delete_user_data(db=db, user_id=user_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user data: {str(e)}"
        )


@router.post("/data-retention-policy", response_model=DataRetentionPolicyResponse)
async def create_data_retention_policy(
    policy_data: DataRetentionPolicyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create data retention policy"""
    try:
        policy = DataRetentionPolicy(
            company_id=current_user.company_id,
            data_type=policy_data.data_type,
            retention_days=policy_data.retention_days,
            auto_delete=policy_data.auto_delete,
            encryption_required=policy_data.encryption_required
        )
        
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        # Log policy creation
        await security_service.log_user_action(
            db=db,
            user_id=str(current_user.id),
            action="create_data_retention_policy",
            resource_type="data_retention_policy",
            resource_id=str(policy.id),
            details={"data_type": policy_data.data_type, "retention_days": policy_data.retention_days}
        )
        
        return DataRetentionPolicyResponse(
            id=str(policy.id),
            data_type=policy.data_type,
            retention_days=policy.retention_days,
            auto_delete=policy.auto_delete,
            encryption_required=policy.encryption_required,
            created_at=policy.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data retention policy: {str(e)}"
        )


@router.post("/apply-retention-policy", response_model=Dict[str, int])
async def apply_data_retention_policy(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Apply data retention policies (background task)"""
    try:
        # Run as background task to avoid timeout
        background_tasks.add_task(security_service.apply_data_retention_policy, db)
        
        return {"status": "scheduled", "message": "Data retention policy application scheduled"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule data retention policy: {str(e)}"
        )


@router.post("/compliance-action", response_model=ComplianceActionResponse)
async def log_compliance_action(
    action_data: ComplianceActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Log compliance action (GDPR/CCPA)"""
    try:
        compliance_log = ComplianceLog(
            company_id=current_user.company_id,
            subject_id=action_data.subject_id,
            action=action_data.action,
            legal_basis=action_data.legal_basis,
            details=action_data.details,
            requested_by=action_data.requested_by,
            processed_by=current_user.id
        )
        
        db.add(compliance_log)
        db.commit()
        db.refresh(compliance_log)
        
        return ComplianceActionResponse(
            id=str(compliance_log.id),
            subject_id=compliance_log.subject_id,
            action=compliance_log.action,
            legal_basis=compliance_log.legal_basis,
            details=compliance_log.details,
            requested_by=compliance_log.requested_by,
            processed_by=str(compliance_log.processed_by),
            created_at=compliance_log.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log compliance action: {str(e)}"
        )


@router.get("/security-alerts", response_model=List[SecurityAlertResponse])
async def get_security_alerts(
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get security alerts"""
    try:
        query = db.query(SecurityAlert).filter(
            SecurityAlert.company_id == current_user.company_id
        )
        
        if resolved is not None:
            query = query.filter(SecurityAlert.resolved == resolved)
        if severity:
            query = query.filter(SecurityAlert.severity == severity)
        
        alerts = query.order_by(SecurityAlert.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            SecurityAlertResponse(
                id=str(alert.id),
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=alert.title,
                description=alert.description,
                details=alert.details,
                resolved=alert.resolved,
                resolved_by=str(alert.resolved_by) if alert.resolved_by else None,
                resolved_at=alert.resolved_at,
                created_at=alert.created_at
            )
            for alert in alerts
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security alerts: {str(e)}"
        )