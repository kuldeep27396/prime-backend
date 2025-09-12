"""
Celery configuration for background task processing
"""

from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "prime",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.notification_tasks",
        "app.tasks.interview_tasks",
        "app.tasks.video_processing_tasks",
        "app.tasks.ai_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_routes={
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.tasks.interview_tasks.*": {"queue": "interviews"},
        "app.tasks.video_processing_tasks.*": {"queue": "video_processing"},
        "app.tasks.ai_tasks.*": {"queue": "ai_processing"},
    },
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "send-interview-reminders": {
        "task": "app.tasks.notification_tasks.send_interview_reminders",
        "schedule": 60.0,  # Run every minute
    },
    "process-scheduled-notifications": {
        "task": "app.tasks.notification_tasks.process_scheduled_notifications",
        "schedule": 30.0,  # Run every 30 seconds
    },
    "cleanup-expired-sessions": {
        "task": "app.tasks.interview_tasks.cleanup_expired_sessions",
        "schedule": 300.0,  # Run every 5 minutes
    },
    "process-video-analysis-queue": {
        "task": "app.tasks.video_processing_tasks.process_video_analysis_queue",
        "schedule": 120.0,  # Run every 2 minutes
    },
    "update-ai-model-cache": {
        "task": "app.tasks.ai_tasks.update_model_cache",
        "schedule": 3600.0,  # Run every hour
    },
}

# Error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"


# Task failure handler
@celery_app.task(bind=True)
def handle_task_failure(self, task_id, error, traceback):
    """Handle task failures"""
    logger.error(f"Task {task_id} failed: {error}")
    logger.error(f"Traceback: {traceback}")
    
    # In a production environment, you might want to:
    # 1. Send alerts to monitoring systems
    # 2. Retry the task with exponential backoff
    # 3. Store failure information for debugging
    
    return f"Task {task_id} failure handled"


if __name__ == "__main__":
    celery_app.start()