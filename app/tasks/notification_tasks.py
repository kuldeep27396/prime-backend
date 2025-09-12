"""
Celery tasks for notification processing
"""

from celery import current_task
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
import asyncio

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.websocket import NotificationService as WSNotificationService
from app.models.interview import Interview
from app.models.job import Application
from app.models.company import User
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def send_interview_reminders(self):
    """Send interview reminders for upcoming interviews"""
    try:
        db = next(get_db())
        
        # Get interviews starting in the next 24 hours, 1 hour, and 15 minutes
        now = datetime.utcnow()
        reminder_windows = [
            (now + timedelta(hours=24), now + timedelta(hours=24, minutes=5), 24 * 60),
            (now + timedelta(hours=1), now + timedelta(hours=1, minutes=5), 60),
            (now + timedelta(minutes=15), now + timedelta(minutes=20), 15)
        ]
        
        for start_time, end_time, minutes_before in reminder_windows:
            interviews = db.query(Interview).filter(
                Interview.scheduled_at.between(start_time, end_time),
                Interview.status == "scheduled"
            ).all()
            
            for interview in interviews:
                # Get participants
                application = db.query(Application).filter(
                    Application.id == interview.application_id
                ).first()
                
                if not application:
                    continue
                
                participants = [str(application.candidate_id)]
                if interview.interviewer_id:
                    participants.append(str(interview.interviewer_id))
                
                # Send reminder asynchronously
                send_interview_reminder_async.delay(
                    interview_id=str(interview.id),
                    participants=participants,
                    minutes_before=minutes_before
                )
        
        db.close()
        logger.info(f"Interview reminders processed at {now}")
        return f"Processed interview reminders for {len(reminder_windows)} time windows"
        
    except Exception as e:
        logger.error(f"Error processing interview reminders: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def send_interview_reminder_async(self, interview_id: str, participants: List[str], minutes_before: int):
    """Send individual interview reminder"""
    try:
        db = next(get_db())
        
        # Use asyncio to run the async notification function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                NotificationService.notify_interview_reminder(
                    interview_id=interview_id,
                    participants=participants,
                    minutes_before=minutes_before,
                    db=db
                )
            )
        finally:
            loop.close()
        
        db.close()
        logger.info(f"Interview reminder sent for interview {interview_id}")
        return f"Reminder sent for interview {interview_id}"
        
    except Exception as e:
        logger.error(f"Error sending interview reminder: {e}")
        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def process_scheduled_notifications(self):
    """Process scheduled notifications from database"""
    try:
        # In a real implementation, you would have a notifications table
        # with scheduled notifications to be sent
        
        db = next(get_db())
        
        # This is a placeholder for scheduled notification processing
        # You would query a notifications table for pending notifications
        
        logger.debug("Processing scheduled notifications...")
        
        db.close()
        return "Scheduled notifications processed"
        
    except Exception as e:
        logger.error(f"Error processing scheduled notifications: {e}")
        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def send_bulk_notifications(self, notification_data: Dict[str, Any]):
    """Send bulk notifications to multiple users"""
    try:
        recipients = notification_data.get("recipients", [])
        title = notification_data.get("title", "Notification")
        message = notification_data.get("message", "")
        notification_type = notification_data.get("type", "info")
        action_url = notification_data.get("action_url")
        
        # Use asyncio to send notifications
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for recipient_id in recipients:
                loop.run_until_complete(
                    WSNotificationService.send_notification(
                        user_id=recipient_id,
                        title=title,
                        message=message,
                        type=notification_type,
                        action_url=action_url
                    )
                )
        finally:
            loop.close()
        
        logger.info(f"Bulk notifications sent to {len(recipients)} recipients")
        return f"Sent notifications to {len(recipients)} users"
        
    except Exception as e:
        logger.error(f"Error sending bulk notifications: {e}")
        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def send_system_maintenance_alert(self, maintenance_data: Dict[str, Any]):
    """Send system maintenance alerts"""
    try:
        message = maintenance_data.get("message", "System maintenance scheduled")
        start_time = datetime.fromisoformat(maintenance_data.get("start_time"))
        duration_minutes = maintenance_data.get("duration_minutes", 60)
        affected_users = maintenance_data.get("affected_users")
        
        # Use asyncio to send maintenance notifications
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                NotificationService.notify_system_maintenance(
                    message=message,
                    start_time=start_time,
                    duration_minutes=duration_minutes,
                    affected_users=affected_users
                )
            )
        finally:
            loop.close()
        
        logger.info("System maintenance alert sent")
        return "System maintenance alert sent successfully"
        
    except Exception as e:
        logger.error(f"Error sending system maintenance alert: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def send_candidate_status_notification(self, notification_data: Dict[str, Any]):
    """Send candidate status change notification"""
    try:
        application_id = notification_data.get("application_id")
        old_status = notification_data.get("old_status")
        new_status = notification_data.get("new_status")
        candidate_id = notification_data.get("candidate_id")
        recruiter_id = notification_data.get("recruiter_id")
        
        db = next(get_db())
        
        # Use asyncio to send notification
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                NotificationService.notify_candidate_status_change(
                    application_id=application_id,
                    old_status=old_status,
                    new_status=new_status,
                    candidate_id=candidate_id,
                    recruiter_id=recruiter_id,
                    db=db
                )
            )
        finally:
            loop.close()
        
        db.close()
        logger.info(f"Candidate status notification sent for application {application_id}")
        return f"Status notification sent for application {application_id}"
        
    except Exception as e:
        logger.error(f"Error sending candidate status notification: {e}")
        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def cleanup_old_notifications(self):
    """Clean up old notifications from the system"""
    try:
        # In a real implementation, you would clean up old notifications
        # from the database to prevent storage bloat
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        logger.info(f"Cleaning up notifications older than {cutoff_date}")
        
        # This would delete old notifications from the database
        # db.query(Notification).filter(Notification.created_at < cutoff_date).delete()
        
        return "Old notifications cleaned up"
        
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes