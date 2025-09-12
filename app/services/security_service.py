"""
Security and compliance service for audit logging, data encryption, and monitoring
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from cryptography.fernet import Fernet
from fastapi import Request
import asyncio
import os

from app.core.database import get_db
from app.models.audit import AuditLog, ProctoringEvent
from app.models.company import User
from app.models.interview import Interview
from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityService:
    """Comprehensive security and compliance service"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for data encryption"""
        key_env = os.getenv("ENCRYPTION_KEY")
        if key_env:
            return key_env.encode()
        
        # Generate new key if not exists (for development)
        key = Fernet.generate_key()
        logger.warning("Generated new encryption key. Set ENCRYPTION_KEY environment variable in production.")
        return key
    
    # Audit Logging System
    async def log_user_action(
        self,
        db: Session,
        user_id: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log user action for audit trail"""
        try:
            ip_address = None
            user_agent = None
            
            if request:
                # Get real IP address (considering proxies)
                ip_address = (
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                    request.headers.get("X-Real-IP") or
                    request.client.host if request.client else None
                )
                user_agent = request.headers.get("User-Agent")
            
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.info(f"Audit log created: {action} by user {user_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            db.rollback()
            raise
    
    async def log_security_event(
        self,
        db: Session,
        interview_id: str,
        event_type: str,
        severity: str,
        details: Dict[str, Any]
    ) -> ProctoringEvent:
        """Log security/proctoring event"""
        try:
            event = ProctoringEvent(
                interview_id=interview_id,
                event_type=event_type,
                severity=severity,
                details=details
            )
            
            db.add(event)
            db.commit()
            db.refresh(event)
            
            # Alert on critical events
            if severity == 'critical':
                await self._alert_critical_security_event(event)
            
            logger.info(f"Security event logged: {event_type} - {severity}")
            return event
            
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
            db.rollback()
            raise
    
    async def get_audit_logs(
        self,
        db: Session,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Retrieve audit logs with filtering"""
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        return query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
    
    # Data Encryption and GDPR Compliance
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            raise
    
    def hash_pii_data(self, data: str) -> str:
        """Hash PII data for anonymization"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def anonymize_user_data(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Anonymize user data for GDPR compliance"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Store original data for audit
            original_data = {
                "email": user.email,
                "name": user.profile.get("name", ""),
                "phone": user.profile.get("phone", "")
            }
            
            # Anonymize data
            anonymized_email = f"anonymized_{self.hash_pii_data(user.email)[:8]}@deleted.com"
            user.email = anonymized_email
            user.profile = {
                **user.profile,
                "name": "Anonymized User",
                "phone": None,
                "anonymized_at": datetime.utcnow().isoformat()
            }
            
            db.commit()
            
            # Log anonymization
            await self.log_user_action(
                db=db,
                user_id=None,  # No user context for system action
                action="anonymize_user_data",
                resource_type="user",
                resource_id=user_id,
                details={"original_email_hash": self.hash_pii_data(original_data["email"])}
            )
            
            return {"status": "anonymized", "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Failed to anonymize user data: {str(e)}")
            db.rollback()
            raise
    
    async def delete_user_data(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Delete user data for GDPR right to be forgotten"""
        try:
            # This would cascade delete related data based on foreign key constraints
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Log deletion before removing user
            await self.log_user_action(
                db=db,
                user_id=None,
                action="delete_user_data",
                resource_type="user",
                resource_id=user_id,
                details={"email_hash": self.hash_pii_data(user.email)}
            )
            
            db.delete(user)
            db.commit()
            
            return {"status": "deleted", "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Failed to delete user data: {str(e)}")
            db.rollback()
            raise
    
    # Data Retention and Deletion Policies
    async def apply_data_retention_policy(self, db: Session) -> Dict[str, int]:
        """Apply data retention policies"""
        try:
            results = {
                "audit_logs_deleted": 0,
                "proctoring_events_deleted": 0,
                "old_interviews_archived": 0
            }
            
            # Delete audit logs older than 7 years (legal requirement)
            retention_date = datetime.utcnow() - timedelta(days=7*365)
            old_audit_logs = db.query(AuditLog).filter(
                AuditLog.created_at < retention_date
            ).count()
            
            db.query(AuditLog).filter(
                AuditLog.created_at < retention_date
            ).delete()
            results["audit_logs_deleted"] = old_audit_logs
            
            # Delete proctoring events older than 2 years
            proctoring_retention_date = datetime.utcnow() - timedelta(days=2*365)
            old_proctoring_events = db.query(ProctoringEvent).filter(
                ProctoringEvent.timestamp < proctoring_retention_date
            ).count()
            
            db.query(ProctoringEvent).filter(
                ProctoringEvent.timestamp < proctoring_retention_date
            ).delete()
            results["proctoring_events_deleted"] = old_proctoring_events
            
            # Archive old interviews (mark as archived instead of deleting)
            archive_date = datetime.utcnow() - timedelta(days=365)
            old_interviews = db.query(Interview).filter(
                and_(
                    Interview.completed_at < archive_date,
                    Interview.metadata.op('->>')('archived') != 'true'
                )
            ).all()
            
            for interview in old_interviews:
                interview.metadata = {
                    **interview.metadata,
                    "archived": True,
                    "archived_at": datetime.utcnow().isoformat()
                }
            
            results["old_interviews_archived"] = len(old_interviews)
            
            db.commit()
            
            logger.info(f"Data retention policy applied: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to apply data retention policy: {str(e)}")
            db.rollback()
            raise
    
    # Browser Environment Monitoring
    async def validate_browser_environment(
        self,
        db: Session,
        interview_id: str,
        environment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate browser environment for security"""
        try:
            security_issues = []
            risk_score = 0
            
            # Check for suspicious extensions
            extensions = environment_data.get("extensions", [])
            suspicious_extensions = [
                "screen_recorder", "remote_desktop", "automation", 
                "developer_tools", "proxy", "vpn"
            ]
            
            for ext in extensions:
                if any(sus in ext.lower() for sus in suspicious_extensions):
                    security_issues.append(f"Suspicious extension detected: {ext}")
                    risk_score += 20
            
            # Check browser integrity
            if environment_data.get("developer_tools_open"):
                security_issues.append("Developer tools detected")
                risk_score += 30
            
            if environment_data.get("multiple_monitors"):
                security_issues.append("Multiple monitors detected")
                risk_score += 10
            
            # Check for automation tools
            if environment_data.get("webdriver_detected"):
                security_issues.append("Automation tools detected")
                risk_score += 50
            
            # Determine severity
            if risk_score >= 50:
                severity = "critical"
            elif risk_score >= 30:
                severity = "high"
            elif risk_score >= 10:
                severity = "medium"
            else:
                severity = "low"
            
            # Log security event if issues found
            if security_issues:
                await self.log_security_event(
                    db=db,
                    interview_id=interview_id,
                    event_type="browser_environment_violation",
                    severity=severity,
                    details={
                        "issues": security_issues,
                        "risk_score": risk_score,
                        "environment_data": environment_data
                    }
                )
            
            return {
                "valid": risk_score < 50,
                "risk_score": risk_score,
                "issues": security_issues,
                "severity": severity
            }
            
        except Exception as e:
            logger.error(f"Failed to validate browser environment: {str(e)}")
            raise
    
    # Security Monitoring and Alerting
    async def _alert_critical_security_event(self, event: ProctoringEvent):
        """Alert administrators about critical security events"""
        try:
            # In a real implementation, this would send alerts via email, Slack, etc.
            logger.critical(
                f"CRITICAL SECURITY EVENT: {event.event_type} in interview {event.interview_id}"
            )
            
            # Could integrate with notification services here
            # await notification_service.send_security_alert(event)
            
        except Exception as e:
            logger.error(f"Failed to send security alert: {str(e)}")
    
    async def get_security_dashboard_data(
        self,
        db: Session,
        company_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get security dashboard data for monitoring"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get security events summary
            security_events = db.query(ProctoringEvent).join(Interview).filter(
                and_(
                    Interview.company_id == company_id,
                    ProctoringEvent.timestamp >= start_date
                )
            ).all()
            
            events_by_severity = {}
            events_by_type = {}
            
            for event in security_events:
                events_by_severity[event.severity] = events_by_severity.get(event.severity, 0) + 1
                events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
            
            # Get audit log summary
            audit_logs = db.query(AuditLog).join(User).filter(
                and_(
                    User.company_id == company_id,
                    AuditLog.created_at >= start_date
                )
            ).all()
            
            actions_summary = {}
            for log in audit_logs:
                actions_summary[log.action] = actions_summary.get(log.action, 0) + 1
            
            return {
                "security_events": {
                    "total": len(security_events),
                    "by_severity": events_by_severity,
                    "by_type": events_by_type
                },
                "audit_logs": {
                    "total": len(audit_logs),
                    "by_action": actions_summary
                },
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get security dashboard data: {str(e)}")
            raise


# Global security service instance
security_service = SecurityService()