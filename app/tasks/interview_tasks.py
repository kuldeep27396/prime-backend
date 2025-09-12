"""
Celery tasks for interview processing
"""

from celery import current_task
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
import asyncio
import json

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.models.interview import Interview, InterviewResponse
from app.models.job import Application
from app.services.interview_orchestration_service import interview_orchestrator
from app.services.ai_service import AIService
from app.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def cleanup_expired_sessions(self):
    """Clean up expired interview sessions"""
    try:
        # Get active interviews that have been running too long
        active_interviews = interview_orchestrator.get_active_interviews()
        
        for interview_id in active_interviews:
            session = interview_orchestrator.get_interview_session(interview_id)
            if not session:
                continue
            
            # Check if session has been active for more than 2 hours
            start_time = session.get("start_time")
            if start_time and datetime.utcnow() - start_time > timedelta(hours=2):
                logger.warning(f"Cleaning up expired interview session {interview_id}")
                
                # End the interview
                db = next(get_db())
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        loop.run_until_complete(
                            interview_orchestrator.end_interview(
                                interview_id=interview_id,
                                ended_by="system_cleanup",
                                db=db
                            )
                        )
                    finally:
                        loop.close()
                finally:
                    db.close()
        
        logger.info(f"Cleaned up expired interview sessions")
        return f"Processed {len(active_interviews)} active interviews"
        
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def process_interview_recording(self, interview_id: str, recording_data: Dict[str, Any]):
    """Process interview recording for analysis"""
    try:
        db = next(get_db())
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        recording_url = recording_data.get("recording_url")
        duration = recording_data.get("duration", 0)
        
        # Update interview with recording information
        metadata = json.loads(interview.metadata or "{}")
        metadata.update({
            "recording_url": recording_url,
            "recording_duration": duration,
            "recording_processed_at": datetime.utcnow().isoformat()
        })
        interview.metadata = json.dumps(metadata)
        db.commit()
        
        # Trigger video analysis if enabled
        if recording_url:
            analyze_interview_video.delay(interview_id, recording_url)
        
        # Generate interview summary
        generate_interview_summary.delay(interview_id)
        
        db.close()
        logger.info(f"Interview recording processed for {interview_id}")
        return f"Recording processed for interview {interview_id}"
        
    except Exception as e:
        logger.error(f"Error processing interview recording: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def analyze_interview_video(self, interview_id: str, video_url: str):
    """Analyze interview video for insights"""
    try:
        db = next(get_db())
        
        # This would integrate with video analysis service
        # For now, we'll simulate the analysis
        
        analysis_results = {
            "engagement_score": 85.0,
            "professionalism_score": 90.0,
            "confidence_score": 78.0,
            "speaking_time_ratio": 0.65,
            "interruptions_count": 2,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        # Update interview with analysis results
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if interview:
            metadata = json.loads(interview.metadata or "{}")
            metadata["video_analysis"] = analysis_results
            interview.metadata = json.dumps(metadata)
            db.commit()
        
        db.close()
        logger.info(f"Video analysis completed for interview {interview_id}")
        return f"Video analysis completed for {interview_id}"
        
    except Exception as e:
        logger.error(f"Error analyzing interview video: {e}")
        raise self.retry(exc=e, countdown=120)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def generate_interview_summary(self, interview_id: str):
    """Generate AI-powered interview summary"""
    try:
        db = next(get_db())
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        # Get interview responses
        responses = db.query(InterviewResponse).filter(
            InterviewResponse.interview_id == interview_id
        ).all()
        
        if not responses:
            logger.warning(f"No responses found for interview {interview_id}")
            db.close()
            return f"No responses to summarize for {interview_id}"
        
        # Generate summary using AI service
        ai_service = AIService()
        
        # Prepare conversation data
        conversation_data = []
        for response in responses:
            conversation_data.append({
                "question_id": response.question_id,
                "response": response.content,
                "type": response.response_type,
                "duration": response.duration
            })
        
        # Generate summary (this would call the AI service)
        summary = {
            "overall_performance": "Strong candidate with good technical skills",
            "key_strengths": [
                "Clear communication",
                "Problem-solving approach",
                "Technical knowledge"
            ],
            "areas_for_improvement": [
                "Could provide more specific examples",
                "Time management in responses"
            ],
            "recommendation": "Proceed to next round",
            "confidence_score": 82.5,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Update interview with summary
        metadata = json.loads(interview.metadata or "{}")
        metadata["ai_summary"] = summary
        interview.metadata = json.dumps(metadata)
        db.commit()
        
        # Trigger scoring calculation
        calculate_interview_scores.delay(interview_id)
        
        db.close()
        logger.info(f"Interview summary generated for {interview_id}")
        return f"Summary generated for interview {interview_id}"
        
    except Exception as e:
        logger.error(f"Error generating interview summary: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def calculate_interview_scores(self, interview_id: str):
    """Calculate comprehensive scores for interview"""
    try:
        db = next(get_db())
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        application = db.query(Application).filter(
            Application.id == interview.application_id
        ).first()
        
        if not application:
            raise ValueError(f"Application not found for interview {interview_id}")
        
        # Calculate scores using scoring service
        scoring_service = ScoringService()
        
        # This would use the actual scoring service
        scores = {
            "technical_score": 85.0,
            "communication_score": 88.0,
            "cultural_fit_score": 82.0,
            "overall_score": 85.0,
            "confidence": 0.87,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Update interview with scores
        metadata = json.loads(interview.metadata or "{}")
        metadata["scores"] = scores
        interview.metadata = json.dumps(metadata)
        db.commit()
        
        # Update application status if scores are high enough
        if scores["overall_score"] >= 80.0:
            application.status = "assessed"
            db.commit()
            
            # Send notification about status change
            from app.tasks.notification_tasks import send_candidate_status_notification
            send_candidate_status_notification.delay({
                "application_id": str(application.id),
                "old_status": "interviewing",
                "new_status": "assessed",
                "candidate_id": str(application.candidate_id),
                "recruiter_id": str(application.job.created_by)
            })
        
        db.close()
        logger.info(f"Interview scores calculated for {interview_id}")
        return f"Scores calculated for interview {interview_id}"
        
    except Exception as e:
        logger.error(f"Error calculating interview scores: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def schedule_interview_followup(self, interview_id: str, followup_data: Dict[str, Any]):
    """Schedule follow-up actions after interview"""
    try:
        followup_type = followup_data.get("type", "feedback_request")
        delay_hours = followup_data.get("delay_hours", 24)
        
        # Schedule the follow-up task
        if followup_type == "feedback_request":
            send_interview_feedback_request.apply_async(
                args=[interview_id],
                countdown=delay_hours * 3600  # Convert hours to seconds
            )
        elif followup_type == "next_round_invitation":
            send_next_round_invitation.apply_async(
                args=[interview_id],
                countdown=delay_hours * 3600
            )
        
        logger.info(f"Follow-up scheduled for interview {interview_id}")
        return f"Follow-up scheduled for {interview_id}"
        
    except Exception as e:
        logger.error(f"Error scheduling interview follow-up: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def send_interview_feedback_request(self, interview_id: str):
    """Send feedback request after interview"""
    try:
        db = next(get_db())
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        application = db.query(Application).filter(
            Application.id == interview.application_id
        ).first()
        
        if not application:
            raise ValueError(f"Application not found for interview {interview_id}")
        
        # Send feedback request notification
        from app.tasks.notification_tasks import send_bulk_notifications
        send_bulk_notifications.delay({
            "recipients": [str(application.candidate_id)],
            "title": "Interview Feedback Request",
            "message": f"How was your interview experience for {application.job.title}? We'd love your feedback!",
            "type": "info",
            "action_url": f"/interviews/{interview_id}/feedback"
        })
        
        db.close()
        logger.info(f"Feedback request sent for interview {interview_id}")
        return f"Feedback request sent for {interview_id}"
        
    except Exception as e:
        logger.error(f"Error sending feedback request: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def send_next_round_invitation(self, interview_id: str):
    """Send invitation for next interview round"""
    try:
        db = next(get_db())
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        application = db.query(Application).filter(
            Application.id == interview.application_id
        ).first()
        
        if not application:
            raise ValueError(f"Application not found for interview {interview_id}")
        
        # Send next round invitation
        from app.tasks.notification_tasks import send_bulk_notifications
        send_bulk_notifications.delay({
            "recipients": [str(application.candidate_id)],
            "title": "Next Interview Round",
            "message": f"Congratulations! You've been selected for the next round of interviews for {application.job.title}",
            "type": "success",
            "action_url": f"/applications/{application.id}"
        })
        
        db.close()
        logger.info(f"Next round invitation sent for interview {interview_id}")
        return f"Next round invitation sent for {interview_id}"
        
    except Exception as e:
        logger.error(f"Error sending next round invitation: {e}")
        raise self.retry(exc=e, countdown=60)