"""
Mock calendar connector implementations for Google Calendar and Outlook
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from app.services.integration_service import CalendarConnector
from app.schemas.integration import CalendarEvent as CalendarEventSchema, TimeSlot

logger = logging.getLogger(__name__)


class GoogleCalendarConnector(CalendarConnector):
    """Mock Google Calendar connector"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
    
    async def authenticate(self) -> bool:
        """Mock authentication with Google"""
        await asyncio.sleep(0.1)
        if not self.access_token:
            return False
        self.is_authenticated = True
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Google Calendar"""
        if not self.is_authenticated:
            return False
        await asyncio.sleep(0.1)
        return True
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get Google Calendar rate limits"""
        return {
            "limit": 1000,
            "remaining": random.randint(500, 1000),
            "reset_time": datetime.utcnow() + timedelta(hours=1)
        }
    
    async def create_event(self, event: CalendarEventSchema) -> str:
        """Create Google Calendar event"""
        await asyncio.sleep(0.2)
        
        event_id = f"google_event_{random.randint(1000, 9999)}"
        logger.info(f"Created Google Calendar event {event_id}: {event.title}")
        
        # Mock event creation
        return event_id
    
    async def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """Update Google Calendar event"""
        await asyncio.sleep(0.1)
        logger.info(f"Updated Google Calendar event {event_id} with {updates}")
        return True
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete Google Calendar event"""
        await asyncio.sleep(0.1)
        logger.info(f"Deleted Google Calendar event {event_id}")
        return True
    
    async def get_availability(self, email: str, start_time: datetime, end_time: datetime) -> List[TimeSlot]:
        """Get available time slots from Google Calendar"""
        await asyncio.sleep(0.2)
        
        # Mock availability - generate some free slots
        available_slots = []
        current_time = start_time
        
        while current_time < end_time:
            # Randomly decide if this hour is available
            if random.choice([True, False, True]):  # 66% chance of being available
                slot_end = min(current_time + timedelta(hours=1), end_time)
                available_slots.append(TimeSlot(
                    start_time=current_time,
                    end_time=slot_end,
                    timezone="UTC"
                ))
            current_time += timedelta(hours=1)
        
        return available_slots
    
    async def get_events(self, start_time: datetime, end_time: datetime) -> List[CalendarEventSchema]:
        """Get events from Google Calendar"""
        await asyncio.sleep(0.2)
        
        # Mock events
        events = []
        for i in range(random.randint(2, 5)):
            event_start = start_time + timedelta(hours=random.randint(0, 24))
            event_end = event_start + timedelta(hours=random.randint(1, 3))
            
            events.append(CalendarEventSchema(
                id=f"google_event_{i}",
                title=f"Meeting {i}",
                description=f"Mock meeting {i}",
                start_time=event_start,
                end_time=event_end,
                timezone="UTC",
                attendees=[f"attendee{i}@example.com"],
                location="Conference Room A"
            ))
        
        return events


class OutlookConnector(CalendarConnector):
    """Mock Outlook/Microsoft Graph connector"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.tenant_id = credentials.get("tenant_id")
    
    async def authenticate(self) -> bool:
        """Mock authentication with Microsoft Graph"""
        await asyncio.sleep(0.1)
        if not self.access_token or not self.tenant_id:
            return False
        self.is_authenticated = True
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Outlook"""
        if not self.is_authenticated:
            return False
        await asyncio.sleep(0.1)
        return True
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get Microsoft Graph rate limits"""
        return {
            "limit": 2000,
            "remaining": random.randint(1000, 2000),
            "reset_time": datetime.utcnow() + timedelta(hours=1)
        }
    
    async def create_event(self, event: CalendarEventSchema) -> str:
        """Create Outlook calendar event"""
        await asyncio.sleep(0.2)
        
        event_id = f"outlook_event_{random.randint(1000, 9999)}"
        logger.info(f"Created Outlook event {event_id}: {event.title}")
        
        return event_id
    
    async def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """Update Outlook calendar event"""
        await asyncio.sleep(0.1)
        logger.info(f"Updated Outlook event {event_id} with {updates}")
        return True
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete Outlook calendar event"""
        await asyncio.sleep(0.1)
        logger.info(f"Deleted Outlook event {event_id}")
        return True
    
    async def get_availability(self, email: str, start_time: datetime, end_time: datetime) -> List[TimeSlot]:
        """Get available time slots from Outlook"""
        await asyncio.sleep(0.2)
        
        # Mock availability
        available_slots = []
        current_time = start_time
        
        while current_time < end_time:
            # Different availability pattern than Google
            if random.choice([True, True, False]):  # 66% chance of being available
                slot_end = min(current_time + timedelta(minutes=30), end_time)
                available_slots.append(TimeSlot(
                    start_time=current_time,
                    end_time=slot_end,
                    timezone="UTC"
                ))
            current_time += timedelta(minutes=30)
        
        return available_slots
    
    async def get_events(self, start_time: datetime, end_time: datetime) -> List[CalendarEventSchema]:
        """Get events from Outlook"""
        await asyncio.sleep(0.2)
        
        # Mock events
        events = []
        for i in range(random.randint(1, 4)):
            event_start = start_time + timedelta(hours=random.randint(0, 24))
            event_end = event_start + timedelta(hours=random.randint(1, 2))
            
            events.append(CalendarEventSchema(
                id=f"outlook_event_{i}",
                title=f"Teams Meeting {i}",
                description=f"Mock Teams meeting {i}",
                start_time=event_start,
                end_time=event_end,
                timezone="UTC",
                attendees=[f"participant{i}@company.com"],
                location="Microsoft Teams",
                meeting_url=f"https://teams.microsoft.com/l/meetup-join/{random.randint(100000, 999999)}"
            ))
        
        return events
    
    async def create_teams_meeting(self, event: CalendarEventSchema) -> str:
        """Create Teams meeting with Outlook event"""
        await asyncio.sleep(0.3)
        
        event_id = await self.create_event(event)
        meeting_url = f"https://teams.microsoft.com/l/meetup-join/{random.randint(100000, 999999)}"
        
        logger.info(f"Created Teams meeting for event {event_id}: {meeting_url}")
        return meeting_url


class CalendarService:
    """Service for managing calendar integrations"""
    
    def __init__(self, integration_service):
        self.integration_service = integration_service
    
    async def schedule_interview(self, company_id: str, candidate_email: str, interviewer_email: str, 
                               duration_minutes: int = 60, preferred_times: List[TimeSlot] = None) -> Optional[CalendarEventSchema]:
        """Schedule an interview using available calendar integrations"""
        
        # Get calendar integrations for the company
        integrations = await self.integration_service.get_integrations(company_id, "calendar")
        if not integrations:
            logger.warning(f"No calendar integrations found for company {company_id}")
            return None
        
        # Try each integration until we find availability
        for integration in integrations:
            if not integration.enabled:
                continue
                
            connector = await self.integration_service.get_connector(str(integration.id))
            if not connector:
                continue
            
            try:
                # Get availability for the next 7 days
                start_time = datetime.utcnow()
                end_time = start_time + timedelta(days=7)
                
                availability = await connector.get_availability(interviewer_email, start_time, end_time)
                if not availability:
                    continue
                
                # Find a suitable time slot
                for slot in availability:
                    if (slot.end_time - slot.start_time).total_seconds() >= duration_minutes * 60:
                        # Create the interview event
                        event = CalendarEventSchema(
                            title=f"Interview with {candidate_email}",
                            description=f"Technical interview scheduled via PRIME platform",
                            start_time=slot.start_time,
                            end_time=slot.start_time + timedelta(minutes=duration_minutes),
                            timezone="UTC",
                            attendees=[candidate_email, interviewer_email],
                            location="Video Call"
                        )
                        
                        event_id = await connector.create_event(event)
                        event.id = event_id
                        
                        logger.info(f"Scheduled interview {event_id} for {candidate_email}")
                        return event
                        
            except Exception as e:
                logger.error(f"Failed to schedule with integration {integration.id}: {e}")
                continue
        
        logger.warning(f"Could not schedule interview for {candidate_email}")
        return None
    
    async def reschedule_interview(self, event_id: str, new_start_time: datetime, 
                                 duration_minutes: int = 60) -> bool:
        """Reschedule an existing interview"""
        # Implementation would find the integration that created the event and update it
        logger.info(f"Rescheduling interview {event_id} to {new_start_time}")
        return True
    
    async def cancel_interview(self, event_id: str) -> bool:
        """Cancel an interview"""
        # Implementation would find the integration that created the event and delete it
        logger.info(f"Cancelling interview {event_id}")
        return True