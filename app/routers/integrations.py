from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations"])

# Schemas for calendar integration
class PreferredTime(BaseModel):
    date: str = Field(..., description="Preferred date (YYYY-MM-DD)", example="2024-01-15")
    time: str = Field(..., description="Preferred time (HH:MM)", example="14:00")
    timezone: str = Field("UTC", description="Timezone", example="America/New_York")

class ScheduleInterviewRequest(BaseModel):
    candidate_email: EmailStr = Field(..., description="Candidate email address")
    interviewer_email: EmailStr = Field(..., description="Interviewer email address")
    duration_minutes: int = Field(..., description="Duration in minutes", example=60)
    preferred_times: List[PreferredTime] = Field(..., description="List of preferred time slots")
    interview_type: str = Field("Technical Interview", description="Type of interview")
    notes: Optional[str] = Field(None, description="Additional notes")

class ScheduleInterviewResponse(BaseModel):
    success: bool = Field(..., description="Whether scheduling was successful")
    message: str = Field(..., description="Status message")
    calendar_event_id: Optional[str] = Field(None, description="Calendar event ID if successful")
    scheduled_time: Optional[str] = Field(None, description="Scheduled time if successful")

class NotificationTemplate(BaseModel):
    template_id: str = Field(..., description="Template identifier")
    variables: Dict[str, Any] = Field(..., description="Template variables")

class SendNotificationRequest(BaseModel):
    recipient: EmailStr = Field(..., description="Recipient email address")
    template_id: str = Field(..., description="Template identifier")
    variables: Dict[str, Any] = Field(..., description="Template variables for the template")

class SendNotificationResponse(BaseModel):
    success: bool = Field(..., description="Whether notification was sent successfully")
    message: str = Field(..., description="Status message")
    notification_id: Optional[str] = Field(None, description="Notification ID if successful")

# Calendar integration endpoints
@router.post("/calendar/schedule-interview",
            response_model=ScheduleInterviewResponse,
            status_code=status.HTTP_200_OK,
            summary="Schedule interview with calendar integration",
            description="Schedule an interview and create calendar events for both candidate and interviewer")
async def schedule_interview(request: ScheduleInterviewRequest):
    """Schedule interview with calendar integration"""
    try:
        # Mock calendar integration - in production, this would integrate with Google Calendar, Outlook, etc.
        # For now, we'll simulate the calendar integration

        # Find the best available time slot (simplified logic)
        best_time = request.preferred_times[0] if request.preferred_times else None

        if not best_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No preferred times provided"
            )

        # Simulate calendar event creation
        event_id = f"cal_{uuid.uuid4().hex[:8]}"
        scheduled_datetime = f"{best_time.date}T{best_time.time}:00"

        # In a real implementation, you would:
        # 1. Check availability in calendar systems
        # 2. Create calendar events for both parties
        # 3. Send calendar invitations
        # 4. Handle timezone conversions

        return ScheduleInterviewResponse(
            success=True,
            message="Interview scheduled successfully and calendar events created",
            calendar_event_id=event_id,
            scheduled_time=scheduled_datetime
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule interview: {str(e)}"
        )

@router.post("/communication/send-notification",
            response_model=SendNotificationResponse,
            status_code=status.HTTP_200_OK,
            summary="Send communication notification",
            description="Send notifications using various communication channels")
async def send_notification(request: SendNotificationRequest):
    """Send communication notification"""
    try:
        # Mock notification system - in production, this would integrate with email, SMS, push notifications, etc.

        # Available templates (simplified)
        available_templates = {
            "interview_scheduled": "Interview Scheduled",
            "interview_reminder": "Interview Reminder",
            "interview_cancelled": "Interview Cancelled",
            "interview_rescheduled": "Interview Rescheduled",
            "welcome_email": "Welcome Email"
        }

        if request.template_id not in available_templates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template '{request.template_id}' not found. Available templates: {list(available_templates.keys())}"
            )

        # Simulate notification sending
        notification_id = f"notif_{uuid.uuid4().hex[:8]}"

        # In a real implementation, you would:
        # 1. Render the template with variables
        # 2. Send via appropriate channel (email, SMS, push)
        # 3. Track delivery status
        # 4. Handle bounces and retries

        return SendNotificationResponse(
            success=True,
            message=f"Notification sent successfully using template '{request.template_id}'",
            notification_id=notification_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

# Calendar availability endpoints
@router.get("/calendar/availability/{email}",
            summary="Get calendar availability",
            description="Get availability for a user's calendar")
async def get_calendar_availability(email: str, start_date: str, end_date: str):
    """Get calendar availability for a user"""
    try:
        # Mock availability data - in production, this would query actual calendar systems
        # For demonstration, return some sample availability

        availability = [
            {
                "date": "2024-01-15",
                "slots": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
            },
            {
                "date": "2024-01-16",
                "slots": ["09:00", "10:00", "14:00", "15:00"]
            }
        ]

        return {
            "success": True,
            "email": email,
            "start_date": start_date,
            "end_date": end_date,
            "availability": availability
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar availability: {str(e)}"
        )

# Calendar sync endpoints
@router.post("/calendar/sync/{user_id}",
            summary="Sync calendar",
            description="Sync user's calendar with the system")
async def sync_calendar(user_id: str, calendar_type: str = "google"):
    """Sync user's calendar"""
    try:
        # Mock calendar sync - in production, this would sync with Google Calendar, Outlook, etc.

        sync_id = f"sync_{uuid.uuid4().hex[:8]}"

        return {
            "success": True,
            "message": f"Calendar synced successfully for {calendar_type}",
            "sync_id": sync_id,
            "synced_events": 5  # Mock number of synced events
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync calendar: {str(e)}"
        )