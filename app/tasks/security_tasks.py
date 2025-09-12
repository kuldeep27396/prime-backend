"""
Security and compliance background tasks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from celery import Celery
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.services.security_service import security_service
from app.models.audit import DataRetentionPolicy, SecurityAlert
from app.models.company import Company

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "security_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)


@celery_app.task(name="apply_data_retention_policies")
def apply_data_retention_policies():
    """Apply data retention policies across all companies"""
    try:
        db = next(get_db())
        
        # Get all companies with data retention policies
        companies = db.query(Company).all()
        total_results = {
            "companies_processed": 0,
            "total_audit_logs_deleted": 0,
            "total_proctoring_events_deleted": 0,
            "total_interviews_archived": 0,
            "errors": []
        }
        
        for company in companies:
            try:
                logger.info(f"Applying data retention policies for company: {company.name}")
                
                # Apply retention policy for this company
                result = security_service.apply_data_retention_policy(db)
                
                total_results["companies_processed"] += 1
                total_results["total_audit_logs_deleted"] += result.get("audit_logs_deleted", 0)
                total_results["total_proctoring_events_deleted"] += result.get("proctoring_events_deleted", 0)
                total_results["total_interviews_archived"] += result.get("old_interviews_archived", 0)
                
                logger.info(f"Completed retention policy for {company.name}: {result}")
                
            except Exception as e:
                error_msg = f"Failed to apply retention policy for company {company.name}: {str(e)}"
                logger.error(error_msg)
                total_results["errors"].append(error_msg)
        
        logger.info(f"Data retention policy application completed: {total_results}")
        return total_results
        
    except Exception as e:
        logger.error(f"Failed to apply data retention policies: {str(e)}")
        raise


@celery_app.task(name="generate_security_report")
def generate_security_report(company_id: str, days: int = 30):
    """Generate comprehensive security report for a company"""
    try:
        db = next(get_db())
        
        logger.info(f"Generating security report for company {company_id}")
        
        # Get security dashboard data
        dashboard_data = security_service.get_security_dashboard_data(
            db=db,
            company_id=company_id,
            days=days
        )
        
        # Get recent security alerts
        security_alerts = db.query(SecurityAlert).filter(
            SecurityAlert.company_id == company_id,
            SecurityAlert.created_at >= datetime.utcnow() - timedelta(days=days)
        ).all()
        
        # Compile report
        report = {
            "company_id": company_id,
            "report_period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "dashboard_data": dashboard_data,
            "security_alerts": {
                "total": len(security_alerts),
                "unresolved": len([a for a in security_alerts if not a.resolved]),
                "by_severity": {}
            },
            "recommendations": []
        }
        
        # Analyze security alerts by severity
        for alert in security_alerts:
            severity = alert.severity
            if severity not in report["security_alerts"]["by_severity"]:
                report["security_alerts"]["by_severity"][severity] = 0
            report["security_alerts"]["by_severity"][severity] += 1
        
        # Generate recommendations based on data
        recommendations = []
        
        if report["security_alerts"]["unresolved"] > 0:
            recommendations.append(
                f"You have {report['security_alerts']['unresolved']} unresolved security alerts. "
                "Please review and address them promptly."
            )
        
        critical_events = dashboard_data.get("security_events", {}).get("by_severity", {}).get("critical", 0)
        if critical_events > 0:
            recommendations.append(
                f"There were {critical_events} critical security events in the last {days} days. "
                "Consider reviewing your security policies and monitoring procedures."
            )
        
        if dashboard_data.get("audit_logs", {}).get("total", 0) == 0:
            recommendations.append(
                "No audit logs found. Ensure audit logging is properly configured and functioning."
            )
        
        report["recommendations"] = recommendations
        
        logger.info(f"Security report generated for company {company_id}")
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate security report: {str(e)}")
        raise


@celery_app.task(name="monitor_security_violations")
def monitor_security_violations():
    """Monitor for security violations and create alerts"""
    try:
        db = next(get_db())
        
        logger.info("Starting security violation monitoring")
        
        # This would typically analyze recent security events and create alerts
        # For now, we'll implement basic monitoring logic
        
        from app.models.audit import ProctoringEvent
        from sqlalchemy import and_, func
        
        # Check for multiple critical events in short time period
        recent_time = datetime.utcnow() - timedelta(hours=1)
        
        critical_events = db.query(ProctoringEvent).filter(
            and_(
                ProctoringEvent.severity == 'critical',
                ProctoringEvent.timestamp >= recent_time
            )
        ).all()
        
        if len(critical_events) >= 5:  # 5 or more critical events in 1 hour
            # Group by interview to find problematic interviews
            interview_events = {}
            for event in critical_events:
                interview_id = str(event.interview_id)
                if interview_id not in interview_events:
                    interview_events[interview_id] = []
                interview_events[interview_id].append(event)
            
            # Create alerts for interviews with multiple violations
            for interview_id, events in interview_events.items():
                if len(events) >= 3:  # 3 or more violations per interview
                    # Check if alert already exists
                    existing_alert = db.query(SecurityAlert).filter(
                        and_(
                            SecurityAlert.alert_type == 'multiple_violations',
                            SecurityAlert.details.op('->>')('interview_id') == interview_id,
                            SecurityAlert.resolved == False
                        )
                    ).first()
                    
                    if not existing_alert:
                        # Create new security alert
                        alert = SecurityAlert(
                            company_id=events[0].interview.application.job.company_id,
                            alert_type='multiple_violations',
                            severity='critical',
                            title=f'Multiple Security Violations Detected',
                            description=f'Interview {interview_id} has {len(events)} critical security violations in the last hour',
                            details={
                                'interview_id': interview_id,
                                'violation_count': len(events),
                                'event_types': [e.event_type for e in events],
                                'time_period': '1 hour'
                            }
                        )
                        
                        db.add(alert)
                        db.commit()
                        
                        logger.warning(f"Created security alert for interview {interview_id} with {len(events)} violations")
        
        logger.info("Security violation monitoring completed")
        return {"status": "completed", "critical_events_found": len(critical_events)}
        
    except Exception as e:
        logger.error(f"Failed to monitor security violations: {str(e)}")
        raise


@celery_app.task(name="cleanup_expired_data")
def cleanup_expired_data():
    """Clean up expired data based on retention policies"""
    try:
        db = next(get_db())
        
        logger.info("Starting expired data cleanup")
        
        # Get all data retention policies
        policies = db.query(DataRetentionPolicy).filter(
            DataRetentionPolicy.auto_delete == True
        ).all()
        
        cleanup_results = {
            "policies_processed": 0,
            "items_deleted": 0,
            "errors": []
        }
        
        for policy in policies:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
                
                if policy.data_type == "audit_logs":
                    from app.models.audit import AuditLog
                    
                    # Delete old audit logs
                    deleted_count = db.query(AuditLog).filter(
                        AuditLog.created_at < cutoff_date
                    ).delete()
                    
                    cleanup_results["items_deleted"] += deleted_count
                    logger.info(f"Deleted {deleted_count} expired audit logs for company {policy.company_id}")
                
                elif policy.data_type == "proctoring_events":
                    from app.models.audit import ProctoringEvent
                    
                    # Delete old proctoring events
                    deleted_count = db.query(ProctoringEvent).filter(
                        ProctoringEvent.timestamp < cutoff_date
                    ).delete()
                    
                    cleanup_results["items_deleted"] += deleted_count
                    logger.info(f"Deleted {deleted_count} expired proctoring events for company {policy.company_id}")
                
                # Add more data types as needed
                
                cleanup_results["policies_processed"] += 1
                
            except Exception as e:
                error_msg = f"Failed to cleanup data for policy {policy.id}: {str(e)}"
                logger.error(error_msg)
                cleanup_results["errors"].append(error_msg)
        
        db.commit()
        
        logger.info(f"Expired data cleanup completed: {cleanup_results}")
        return cleanup_results
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired data: {str(e)}")
        raise


@celery_app.task(name="encrypt_sensitive_data")
def encrypt_sensitive_data():
    """Encrypt sensitive data that should be encrypted"""
    try:
        db = next(get_db())
        
        logger.info("Starting sensitive data encryption")
        
        # This would identify and encrypt sensitive data based on policies
        # For now, we'll implement a basic example
        
        from app.models.company import User
        
        # Find users with unencrypted sensitive data
        users_to_encrypt = db.query(User).filter(
            # Add conditions to identify users needing encryption
            User.profile.op('->>')('phone').isnot(None)
        ).all()
        
        encryption_results = {
            "users_processed": 0,
            "fields_encrypted": 0,
            "errors": []
        }
        
        for user in users_to_encrypt:
            try:
                profile = user.profile.copy()
                
                # Encrypt phone number if present and not already encrypted
                if 'phone' in profile and profile['phone']:
                    phone = profile['phone']
                    if not phone.startswith('encrypted:'):  # Simple check for already encrypted
                        encrypted_phone = security_service.encrypt_sensitive_data(phone)
                        profile['phone'] = f"encrypted:{encrypted_phone}"
                        encryption_results["fields_encrypted"] += 1
                
                # Update user profile
                user.profile = profile
                encryption_results["users_processed"] += 1
                
            except Exception as e:
                error_msg = f"Failed to encrypt data for user {user.id}: {str(e)}"
                logger.error(error_msg)
                encryption_results["errors"].append(error_msg)
        
        db.commit()
        
        logger.info(f"Sensitive data encryption completed: {encryption_results}")
        return encryption_results
        
    except Exception as e:
        logger.error(f"Failed to encrypt sensitive data: {str(e)}")
        raise


# Schedule periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic security tasks"""
    
    # Apply data retention policies daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        apply_data_retention_policies.s(),
        name='daily-data-retention'
    )
    
    # Monitor security violations every 15 minutes
    sender.add_periodic_task(
        900.0,  # 15 minutes
        monitor_security_violations.s(),
        name='security-violation-monitoring'
    )
    
    # Clean up expired data weekly on Sunday at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week=0),
        cleanup_expired_data.s(),
        name='weekly-data-cleanup'
    )
    
    # Encrypt sensitive data daily at 4 AM
    sender.add_periodic_task(
        crontab(hour=4, minute=0),
        encrypt_sensitive_data.s(),
        name='daily-data-encryption'
    )