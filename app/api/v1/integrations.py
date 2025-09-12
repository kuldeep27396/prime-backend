"""
Integration API endpoints for ATS, calendar, and communication services
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.company import User
from app.services.integration_service import get_integration_service, IntegrationService
from app.services.ats_connectors import GreenhouseConnector, LeverConnector, WorkdayConnector, BambooHRConnector
from app.services.calendar_connectors import GoogleCalendarConnector, OutlookConnector, CalendarService
from app.services.communication_service import CommunicationService, ResendEmailConnector, TwilioSMSConnector
from app.schemas.integration import (
    IntegrationConfig, ATSIntegrationConfig, CalendarIntegrationConfig, CommunicationConfig,
    IntegrationStatusResponse, IntegrationListResponse, SyncHistoryResponse,
    ATSType, CalendarProvider, NotificationRequest, CampaignRequest, CampaignResult,
    CalendarEvent, TimeSlot
)

router = APIRouter()


@router.on_event("startup")
async def register_connectors():
    """Register all integration connectors"""
    integration_service = get_integration_service()
    
    # Register ATS connectors
    integration_service.register_connector("ats_greenhouse", GreenhouseConnector)
    integration_service.register_connector("ats_lever", LeverConnector)
    integration_service.register_connector("ats_workday", WorkdayConnector)
    integration_service.register_connector("ats_bamboohr", BambooHRConnector)
    
    # Register calendar connectors
    integration_service.register_connector("calendar_google", GoogleCalendarConnector)
    integration_service.register_connector("calendar_outlook", OutlookConnector)
    
    # Register communication connectors
    integration_service.register_connector("communication_resend", ResendEmailConnector)
    integration_service.register_connector("communication_twilio", TwilioSMSConnector)


# ATS Integration Endpoints
@router.post("/ats", response_model=IntegrationStatusResponse)
async def create_ats_integration(
    config: ATSIntegrationConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new ATS integration"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create integrations"
        )
    
    integration_service = get_integration_service(db)
    
    try:
        # Set provider based on ATS type
        config.type = "ats"
        if hasattr(config, 'ats_type'):
            config.provider = config.ats_type.value
        
        integration = await integration_service.create_integration(str(current_user.company_id), config)
        
        return IntegrationStatusResponse(
            integration_id=str(integration.id),
            name=integration.name,
            type=integration.type,
            status=integration.status,
            last_sync=integration.last_sync,
            error_message=integration.error_message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create ATS integration: {str(e)}"
        )


@router.post("/ats/{integration_id}/sync")
async def sync_ats_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger ATS sync operation"""
    if not current_user.is_recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    integration_service = get_integration_service(db)
    
    try:
        result = await integration_service.sync_integration(integration_id, "full_sync")
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sync failed: {str(e)}"
        )


# Calendar Integration Endpoints
@router.post("/calendar", response_model=IntegrationStatusResponse)
async def create_calendar_integration(
    config: CalendarIntegrationConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new calendar integration"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create integrations"
        )
    
    integration_service = get_integration_service(db)
    
    try:
        config.type = "calendar"
        integration = await integration_service.create_integration(str(current_user.company_id), config)
        
        return IntegrationStatusResponse(
            integration_id=str(integration.id),
            name=integration.name,
            type=integration.type,
            status=integration.status,
            last_sync=integration.last_sync,
            error_message=integration.error_message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create calendar integration: {str(e)}"
        )


@router.post("/calendar/schedule-interview")
async def schedule_interview(
    candidate_email: str,
    interviewer_email: str,
    duration_minutes: int = 60,
    preferred_times: Optional[List[TimeSlot]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule an interview using calendar integration"""
    if not current_user.is_recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    integration_service = get_integration_service(db)
    calendar_service = CalendarService(integration_service)
    
    try:
        event = await calendar_service.schedule_interview(
            str(current_user.company_id),
            candidate_email,
            interviewer_email,
            duration_minutes,
            preferred_times
        )
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not find available time slot"
            )
        
        return event
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to schedule interview: {str(e)}"
        )


# Communication Integration Endpoints
@router.post("/communication", response_model=IntegrationStatusResponse)
async def create_communication_integration(
    config: CommunicationConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new communication integration"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create integrations"
        )
    
    integration_service = get_integration_service(db)
    
    try:
        config.type = "communication"
        integration = await integration_service.create_integration(str(current_user.company_id), config)
        
        return IntegrationStatusResponse(
            integration_id=str(integration.id),
            name=integration.name,
            type=integration.type,
            status=integration.status,
            last_sync=integration.last_sync,
            error_message=integration.error_message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create communication integration: {str(e)}"
        )


@router.post("/communication/send-notification")
async def send_notification(
    request: NotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a notification email"""
    if not current_user.is_recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    integration_service = get_integration_service(db)
    communication_service = CommunicationService(integration_service, db)
    
    try:
        success = await communication_service.send_notification(str(current_user.company_id), request)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send notification"
            )
        
        return {"success": True, "message": "Notification sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/communication/send-campaign", response_model=CampaignResult)
async def send_bulk_campaign(
    campaign: CampaignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send bulk email campaign"""
    if not current_user.is_recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    integration_service = get_integration_service(db)
    communication_service = CommunicationService(integration_service, db)
    
    try:
        result = await communication_service.send_bulk_campaign(str(current_user.company_id), campaign)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send campaign: {str(e)}"
        )


# General Integration Management Endpoints
@router.get("/", response_model=IntegrationListResponse)
async def get_integrations(
    integration_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all integrations for the company"""
    integration_service = get_integration_service(db)
    
    try:
        integrations = await integration_service.get_integrations(
            str(current_user.company_id), 
            integration_type
        )
        
        integration_responses = []
        for integration in integrations:
            integration_responses.append(IntegrationStatusResponse(
                integration_id=str(integration.id),
                name=integration.name,
                type=integration.type,
                status=integration.status,
                last_sync=integration.last_sync,
                error_message=integration.error_message
            ))
        
        return IntegrationListResponse(
            integrations=integration_responses,
            total=len(integration_responses)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get integrations: {str(e)}"
        )


@router.put("/{integration_id}")
async def update_integration(
    integration_id: str,
    updates: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an integration"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update integrations"
        )
    
    integration_service = get_integration_service(db)
    
    try:
        integration = await integration_service.update_integration(integration_id, updates)
        
        return IntegrationStatusResponse(
            integration_id=str(integration.id),
            name=integration.name,
            type=integration.type,
            status=integration.status,
            last_sync=integration.last_sync,
            error_message=integration.error_message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update integration: {str(e)}"
        )


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an integration"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete integrations"
        )
    
    integration_service = get_integration_service(db)
    
    try:
        success = await integration_service.delete_integration(integration_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        return {"success": True, "message": "Integration deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete integration: {str(e)}"
        )


@router.get("/{integration_id}/test")
async def test_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test an integration connection"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can test integrations"
        )
    
    integration_service = get_integration_service(db)
    
    try:
        connector = await integration_service.get_connector(integration_id)
        
        if not connector:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not get connector for integration"
            )
        
        success = await connector.test_connection()
        rate_limits = await connector.get_rate_limits()
        
        return {
            "success": success,
            "rate_limits": rate_limits,
            "message": "Connection test successful" if success else "Connection test failed"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {str(e)}"
        )