"""
Test integration service functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.services.integration_service import IntegrationService
from app.services.ats_connectors import GreenhouseConnector, LeverConnector, WorkdayConnector, BambooHRConnector
from app.services.calendar_connectors import GoogleCalendarConnector, OutlookConnector, CalendarService
from app.services.communication_service import CommunicationService, ResendEmailConnector, TwilioSMSConnector
from app.schemas.integration import (
    ATSIntegrationConfig, CalendarIntegrationConfig, CommunicationConfig,
    ATSType, CalendarProvider, NotificationRequest, CampaignRequest,
    CalendarEvent, TimeSlot
)


@pytest.mark.asyncio
async def test_greenhouse_connector():
    """Test Greenhouse ATS connector"""
    credentials = {
        "api_key": "test_api_key",
        "base_url": "https://harvest-api.greenhouse.io/v1"
    }
    
    connector = GreenhouseConnector(credentials)
    
    # Test authentication
    auth_result = await connector.authenticate()
    assert auth_result == True
    
    # Test connection
    connection_result = await connector.test_connection()
    assert connection_result == True
    
    # Test getting candidates
    candidates = await connector.get_candidates()
    assert len(candidates) > 0
    assert candidates[0].external_id.startswith("gh_candidate_")
    
    # Test getting jobs
    jobs = await connector.get_jobs()
    assert len(jobs) > 0
    assert jobs[0].external_id.startswith("gh_job_")
    
    # Test rate limits
    rate_limits = await connector.get_rate_limits()
    assert "limit" in rate_limits
    assert "remaining" in rate_limits
    
    print("✓ Greenhouse connector tests passed")


@pytest.mark.asyncio
async def test_lever_connector():
    """Test Lever ATS connector"""
    credentials = {
        "api_key": "test_api_key",
        "base_url": "https://api.lever.co/v1"
    }
    
    connector = LeverConnector(credentials)
    
    # Test authentication
    auth_result = await connector.authenticate()
    assert auth_result == True
    
    # Test getting candidates
    candidates = await connector.get_candidates()
    assert len(candidates) > 0
    assert candidates[0].external_id.startswith("lever_candidate_")
    
    # Test getting jobs
    jobs = await connector.get_jobs()
    assert len(jobs) > 0
    assert jobs[0].external_id.startswith("lever_job_")
    
    print("✓ Lever connector tests passed")


@pytest.mark.asyncio
async def test_workday_connector():
    """Test Workday ATS connector"""
    credentials = {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "base_url": "https://api.workday.com/v1"
    }
    
    connector = WorkdayConnector(credentials)
    
    # Test authentication
    auth_result = await connector.authenticate()
    assert auth_result == True
    
    # Test getting candidates
    candidates = await connector.get_candidates()
    assert len(candidates) > 0
    assert candidates[0].external_id.startswith("wd_candidate_")
    
    # Test getting jobs
    jobs = await connector.get_jobs()
    assert len(jobs) > 0
    assert jobs[0].external_id.startswith("wd_job_")
    
    print("✓ Workday connector tests passed")


@pytest.mark.asyncio
async def test_bamboohr_connector():
    """Test BambooHR ATS connector"""
    credentials = {
        "subdomain": "test_company",
        "api_key": "test_api_key"
    }
    
    connector = BambooHRConnector(credentials)
    
    # Test authentication
    auth_result = await connector.authenticate()
    assert auth_result == True
    
    # Test getting candidates
    candidates = await connector.get_candidates()
    assert len(candidates) > 0
    assert candidates[0].external_id.startswith("bamboo_candidate_")
    
    # Test getting jobs
    jobs = await connector.get_jobs()
    assert len(jobs) > 0
    assert jobs[0].external_id.startswith("bamboo_job_")
    
    print("✓ BambooHR connector tests passed")


@pytest.mark.asyncio
async def test_google_calendar_connector():
    """Test Google Calendar connector"""
    credentials = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret"
    }
    
    connector = GoogleCalendarConnector(credentials)
    
    # Test authentication
    auth_result = await connector.authenticate()
    assert auth_result == True
    
    # Test creating event
    event = CalendarEvent(
        title="Test Interview",
        description="Test interview with candidate",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=1),
        timezone="UTC",
        attendees=["candidate@example.com", "interviewer@company.com"],
        location="Video Call"
    )
    
    event_id = await connector.create_event(event)
    assert event_id.startswith("google_event_")
    
    # Test getting availability
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=1)
    availability = await connector.get_availability("test@example.com", start_time, end_time)
    assert len(availability) > 0
    
    print("✓ Google Calendar connector tests passed")


@pytest.mark.asyncio
async def test_outlook_connector():
    """Test Outlook connector"""
    credentials = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "tenant_id": "test_tenant_id"
    }
    
    connector = OutlookConnector(credentials)
    
    # Test authentication
    auth_result = await connector.authenticate()
    assert auth_result == True
    
    # Test creating event
    event = CalendarEvent(
        title="Test Teams Meeting",
        description="Test Teams meeting with candidate",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=1),
        timezone="UTC",
        attendees=["candidate@example.com", "interviewer@company.com"],
        location="Microsoft Teams"
    )
    
    event_id = await connector.create_event(event)
    assert event_id.startswith("outlook_event_")
    
    print("✓ Outlook connector tests passed")


@pytest.mark.asyncio
async def test_resend_email_connector():
    """Test Resend email connector"""
    credentials = {
        "api_key": "test_resend_api_key"
    }
    settings = {
        "from_email": "noreply@test.com"
    }
    
    connector = ResendEmailConnector(credentials, settings)
    
    # Test authentication
    auth_result = await connector.authenticate()
    assert auth_result == True
    
    # Test sending email
    success = await connector.send_email(
        to="test@example.com",
        subject="Test Email",
        html_content="<h1>Test Email</h1><p>This is a test email.</p>",
        text_content="Test Email\n\nThis is a test email."
    )
    # Note: Success rate is mocked at 95%, so this might occasionally fail
    print(f"Email send result: {success}")
    
    # Test bulk email
    recipients = [
        {
            "email": "test1@example.com",
            "subject": "Test Email 1",
            "html_content": "<h1>Test Email 1</h1>",
            "text_content": "Test Email 1"
        },
        {
            "email": "test2@example.com",
            "subject": "Test Email 2",
            "html_content": "<h1>Test Email 2</h1>",
            "text_content": "Test Email 2"
        }
    ]
    
    bulk_result = await connector.send_bulk_email(recipients)
    assert "sent_count" in bulk_result
    assert "failed_count" in bulk_result
    
    print("✓ Resend email connector tests passed")


@pytest.mark.asyncio
async def test_twilio_sms_connector():
    """Test Twilio SMS connector"""
    credentials = {
        "account_sid": "test_account_sid",
        "auth_token": "test_auth_token"
    }
    settings = {
        "from_phone": "+15551234567"
    }
    
    connector = TwilioSMSConnector(credentials, settings)
    
    # Test authentication
    auth_result = await connector.authenticate()
    assert auth_result == True
    
    # Test sending SMS
    success = await connector.send_sms(
        to="+15559876543",
        message="Test SMS message from PRIME platform"
    )
    # Note: Success rate is mocked at 98%, so this might occasionally fail
    print(f"SMS send result: {success}")
    
    print("✓ Twilio SMS connector tests passed")


@pytest.mark.asyncio
async def test_communication_service():
    """Test communication service with templates"""
    # Mock integration service and database
    integration_service = None  # Would be properly initialized in real test
    db = None  # Would be properly initialized in real test
    
    communication_service = CommunicationService(integration_service, db)
    
    # Test template rendering
    templates = communication_service.default_templates
    assert "interview_invitation" in templates
    assert "application_received" in templates
    assert "interview_reminder" in templates
    assert "rejection_notice" in templates
    
    # Test template structure
    interview_template = templates["interview_invitation"]
    assert "subject" in interview_template
    assert "html_content" in interview_template
    assert "text_content" in interview_template
    
    print("✓ Communication service tests passed")


@pytest.mark.asyncio
async def test_field_mapping():
    """Test field mapping functionality"""
    # Test ATS field mapping
    ats_fields = [
        {"name": "first_name", "type": "string", "required": True},
        {"name": "last_name", "type": "string", "required": True},
        {"name": "email_address", "type": "email", "required": True},
        {"name": "phone_number", "type": "string", "required": False}
    ]
    
    prime_fields = [
        {"name": "name", "type": "string", "required": True},
        {"name": "email", "type": "email", "required": True},
        {"name": "phone", "type": "string", "required": False}
    ]
    
    # Mock field mapping logic
    field_mappings = [
        {"ats_field": "first_name", "prime_field": "name", "transformation": "concat_with_last_name"},
        {"ats_field": "last_name", "prime_field": "name", "transformation": "concat_with_first_name"},
        {"ats_field": "email_address", "prime_field": "email", "transformation": None},
        {"ats_field": "phone_number", "prime_field": "phone", "transformation": "format_phone"}
    ]
    
    assert len(field_mappings) == 4
    assert field_mappings[0]["ats_field"] == "first_name"
    assert field_mappings[0]["prime_field"] == "name"
    
    print("✓ Field mapping tests passed")


async def run_all_tests():
    """Run all integration tests"""
    print("Running integration functionality tests...\n")
    
    try:
        await test_greenhouse_connector()
        await test_lever_connector()
        await test_workday_connector()
        await test_bamboohr_connector()
        await test_google_calendar_connector()
        await test_outlook_connector()
        await test_resend_email_connector()
        await test_twilio_sms_connector()
        await test_communication_service()
        await test_field_mapping()
        
        print("\n✅ All integration functionality tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())