"""
Real-time notification service for PRIME platform
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import asyncio
import logging

from app.core.database import get_db
from app.core.websocket import connection_manager, NotificationService as WSNotificationService
from app.models.company import User
from app.models.interview import Interview
from app.models.job import Application

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing real-time notifications"""
    
    @staticmethod
    async def notify_interview_scheduled(
        interview_id: str,
        candidate_id: str,
        interviewer_id: str,
        scheduled_time: datetime,
        db: Session
    ):
        """Notify participants when an interview is scheduled"""
        try:
            # Get interview details
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                logger.error(f"Interview {interview_id} not found")
                return
            
            # Get application and job details
            application = db.query(Application).filter(Application.id == interview.application_id).first()
            if not application:
                logger.error(f"Application for interview {interview_id} not found")
                return
            
            # Notify candidate
            await WSNotificationService.send_notification(
                user_id=candidate_id,
                title="Interview Scheduled",
                message=f"Your interview for {application.job.title} has been scheduled for {scheduled_time.strftime('%B %d, %Y at %I:%M %p')}",
                type="info",
                action_url=f"/interviews/{interview_id}"
            )
            
            # Notify interviewer
            await WSNotificationService.send_notification(
                user_id=interviewer_id,
                title="Interview Scheduled",
                message=f"Interview with candidate for {application.job.title} scheduled for {scheduled_time.strftime('%B %d, %Y at %I:%M %p')}",
                type="info",
                action_url=f"/interviews/{interview_id}"
            )
            
            logger.info(f"Interview scheduled notifications sent for interview {interview_id}")
            
        except Exception as e:
            logger.error(f"Error sending interview scheduled notifications: {e}")
    
    @staticmethod
    async def notify_interview_starting(
        interview_id: str,
        participants: List[str],
        db: Session
    ):
        """Notify participants when an interview is about to start"""
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return
            
            application = db.query(Application).filter(Application.id == interview.application_id).first()
            if not application:
                return
            
            for participant_id in participants:
                await WSNotificationService.send_notification(
                    user_id=participant_id,
                    title="Interview Starting",
                    message=f"Your interview for {application.job.title} is starting now",
                    type="warning",
                    action_url=f"/interviews/{interview_id}/room"
                )
            
            # Also send interview status update
            await WSNotificationService.notify_interview_status_change(
                interview_id=interview_id,
                status="starting",
                participants=participants,
                details={"job_title": application.job.title}
            )
            
        except Exception as e:
            logger.error(f"Error sending interview starting notifications: {e}")
    
    @staticmethod
    async def notify_interview_completed(
        interview_id: str,
        participants: List[str],
        db: Session
    ):
        """Notify participants when an interview is completed"""
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return
            
            application = db.query(Application).filter(Application.id == interview.application_id).first()
            if not application:
                return
            
            for participant_id in participants:
                await WSNotificationService.send_notification(
                    user_id=participant_id,
                    title="Interview Completed",
                    message=f"Interview for {application.job.title} has been completed",
                    type="success",
                    action_url=f"/interviews/{interview_id}/review"
                )
            
            await WSNotificationService.notify_interview_status_change(
                interview_id=interview_id,
                status="completed",
                participants=participants,
                details={"job_title": application.job.title}
            )
            
        except Exception as e:
            logger.error(f"Error sending interview completed notifications: {e}")
    
    @staticmethod
    async def notify_candidate_status_change(
        application_id: str,
        old_status: str,
        new_status: str,
        candidate_id: str,
        recruiter_id: str,
        db: Session
    ):
        """Notify about candidate status changes"""
        try:
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                return
            
            # Notify candidate
            status_messages = {
                "screening": "Your application is being reviewed",
                "interviewing": "You've been selected for an interview",
                "assessed": "Your interview has been completed and is being evaluated",
                "hired": "Congratulations! You've been selected for the position",
                "rejected": "Thank you for your interest. We've decided to move forward with other candidates"
            }
            
            message = status_messages.get(new_status, f"Your application status has been updated to {new_status}")
            notification_type = "success" if new_status == "hired" else "info" if new_status != "rejected" else "warning"
            
            await WSNotificationService.send_notification(
                user_id=candidate_id,
                title="Application Status Update",
                message=f"{message} for {application.job.title}",
                type=notification_type,
                action_url=f"/applications/{application_id}"
            )
            
            # Notify recruiter
            await WSNotificationService.send_notification(
                user_id=recruiter_id,
                title="Candidate Status Updated",
                message=f"Candidate status changed from {old_status} to {new_status} for {application.job.title}",
                type="info",
                action_url=f"/candidates/{candidate_id}"
            )
            
            # Send candidate update via WebSocket
            await WSNotificationService.notify_candidate_update(
                candidate_id=candidate_id,
                update_type="status_change",
                data={
                    "application_id": application_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "job_title": application.job.title
                },
                recipients=[candidate_id, recruiter_id]
            )
            
        except Exception as e:
            logger.error(f"Error sending candidate status change notifications: {e}")
    
    @staticmethod
    async def notify_assessment_completed(
        assessment_id: str,
        candidate_id: str,
        recruiter_id: str,
        score: float,
        db: Session
    ):
        """Notify when an assessment is completed"""
        try:
            # Notify candidate
            await WSNotificationService.send_notification(
                user_id=candidate_id,
                title="Assessment Completed",
                message=f"Your assessment has been submitted successfully. Score: {score:.1f}%",
                type="success",
                action_url=f"/assessments/{assessment_id}/results"
            )
            
            # Notify recruiter
            await WSNotificationService.send_notification(
                user_id=recruiter_id,
                title="Assessment Completed",
                message=f"Candidate has completed their assessment. Score: {score:.1f}%",
                type="info",
                action_url=f"/assessments/{assessment_id}/review"
            )
            
        except Exception as e:
            logger.error(f"Error sending assessment completed notifications: {e}")
    
    @staticmethod
    async def notify_system_maintenance(
        message: str,
        start_time: datetime,
        duration_minutes: int,
        affected_users: Optional[List[str]] = None
    ):
        """Notify users about system maintenance"""
        try:
            maintenance_message = f"System maintenance scheduled: {message}. Start time: {start_time.strftime('%B %d, %Y at %I:%M %p')}. Duration: {duration_minutes} minutes."
            
            if affected_users:
                for user_id in affected_users:
                    await WSNotificationService.send_notification(
                        user_id=user_id,
                        title="System Maintenance",
                        message=maintenance_message,
                        type="warning"
                    )
            else:
                await WSNotificationService.broadcast_system_alert(
                    message=maintenance_message,
                    alert_type="warning"
                )
            
        except Exception as e:
            logger.error(f"Error sending system maintenance notifications: {e}")
    
    @staticmethod
    async def notify_interview_reminder(
        interview_id: str,
        participants: List[str],
        minutes_before: int,
        db: Session
    ):
        """Send interview reminders"""
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return
            
            application = db.query(Application).filter(Application.id == interview.application_id).first()
            if not application:
                return
            
            for participant_id in participants:
                await WSNotificationService.send_notification(
                    user_id=participant_id,
                    title="Interview Reminder",
                    message=f"Your interview for {application.job.title} starts in {minutes_before} minutes",
                    type="warning",
                    action_url=f"/interviews/{interview_id}/room"
                )
            
        except Exception as e:
            logger.error(f"Error sending interview reminder notifications: {e}")
    
    @staticmethod
    async def schedule_interview_reminders(
        interview_id: str,
        participants: List[str],
        scheduled_time: datetime,
        db: Session
    ):
        """Schedule automatic interview reminders"""
        try:
            # Schedule reminders for 24 hours, 1 hour, and 15 minutes before
            reminder_times = [
                (scheduled_time - timedelta(hours=24), 24 * 60),
                (scheduled_time - timedelta(hours=1), 60),
                (scheduled_time - timedelta(minutes=15), 15)
            ]
            
            for reminder_time, minutes_before in reminder_times:
                if reminder_time > datetime.utcnow():
                    # In a real implementation, you would use a task scheduler like Celery
                    # For now, we'll just log the scheduled reminder
                    logger.info(f"Reminder scheduled for interview {interview_id} at {reminder_time} ({minutes_before} minutes before)")
            
        except Exception as e:
            logger.error(f"Error scheduling interview reminders: {e}")


class MessageService:
    """Service for real-time messaging during interviews"""
    
    @staticmethod
    async def send_chat_message(
        room_id: str,
        sender_id: str,
        message: str,
        message_type: str = "text"
    ):
        """Send a chat message to a room"""
        try:
            # Broadcast message to room participants
            room_users = connection_manager.get_room_users(room_id)
            
            for user_id in room_users:
                if user_id != sender_id:  # Don't send back to sender
                    await connection_manager.send_personal_message(
                        user_id,
                        {
                            "type": "chat_message",
                            "data": {
                                "room_id": room_id,
                                "sender_id": sender_id,
                                "message": message,
                                "message_type": message_type,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                    )
            
            logger.info(f"Chat message sent to room {room_id} by user {sender_id}")
            
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
    
    @staticmethod
    async def send_interview_signal(
        interview_id: str,
        sender_id: str,
        signal_type: str,
        signal_data: Any
    ):
        """Send WebRTC signaling data during interviews"""
        try:
            room_id = f"interview_{interview_id}"
            room_users = connection_manager.get_room_users(room_id)
            
            for user_id in room_users:
                if user_id != sender_id:  # Don't send back to sender
                    await connection_manager.send_personal_message(
                        user_id,
                        {
                            "type": "interview_signal",
                            "data": {
                                "interview_id": interview_id,
                                "sender_id": sender_id,
                                "signal_type": signal_type,
                                "signal_data": signal_data,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                    )
            
            logger.debug(f"Interview signal sent: {signal_type} from {sender_id} to interview {interview_id}")
            
        except Exception as e:
            logger.error(f"Error sending interview signal: {e}")
    
    @staticmethod
    async def broadcast_interview_event(
        interview_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        exclude_user: Optional[str] = None
    ):
        """Broadcast interview events to all participants"""
        try:
            room_id = f"interview_{interview_id}"
            
            message = {
                "type": "interview_event",
                "data": {
                    "interview_id": interview_id,
                    "event_type": event_type,
                    "event_data": event_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await connection_manager.broadcast_to_room(room_id, message, exclude_user)
            
            logger.info(f"Interview event broadcasted: {event_type} for interview {interview_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting interview event: {e}")


# Background task for sending scheduled notifications
async def process_scheduled_notifications():
    """Process scheduled notifications (would be run by Celery in production)"""
    try:
        # This would typically be implemented as a Celery task
        # For now, we'll just log that it would process scheduled notifications
        logger.info("Processing scheduled notifications...")
        
        # In a real implementation, you would:
        # 1. Query database for scheduled notifications
        # 2. Send notifications that are due
        # 3. Update notification status
        # 4. Schedule next run
        
    except Exception as e:
        logger.error(f"Error processing scheduled notifications: {e}")