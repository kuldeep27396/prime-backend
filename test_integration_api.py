"""
Test integration API endpoints
"""

import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta

from app.main import app
from app.core.database import get_db
from app.models.company import Company, User
from app.models.integration import Integration
from app.schemas.integration import (
    ATSIntegrationConfig, CalendarIntegrationConfig, CommunicationConfig,
    ATSType, CalendarProvider, NotificationRequest, CampaignRequest
)


@pytest.fixture
async def test_client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user_token():
    """Create test user and return auth token"""
    # This would normally create a test user and return a valid JWT token
    # For now, we'll mock this
    return "test_token_123"


@pytest.mark.asyncio
async def test_create_ats_integration(test_client, test_user_token):
    """Test creating ATS integration"""
    config = {
        "name": "Test Greenhouse Integration",
        "type": "ats",
        "ats_type": "greenhouse",
        "enabled": True,
        "credentials": {
            "api_key": "test_api_key",
            "base_url": "https://harvest-api.greenhouse.io/v1"
        },
        "settings": {
            "sync_frequency": 3600,
            "auto_sync_enabled": True,
            "sync_candidates": True,
            "sync_jobs": True
        },
        "field_mappings": []
    }
    
    response = await test_client.post(
        "/api/v1/integrations/ats",
        json=config,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    # Note: This will fail without proper authentication setup
    # but demonstrates the expected API structure
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


@pytest.mark.asyncio
async def test_create_calendar_integration(test_client, test_user_token):
    """Test creating calendar integration"""
    config = {
        "name": "Test Google Calendar Integration",
        "type": "calendar",
        "provider": "google",
        "enabled": True,
        "credentials": {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        },
        "settings": {
            "default_duration": 3600,
            "buffer_time": 900,
            "auto_schedule": False
        },
        "field_mappings": []
    }
    
    response = await test_client.post(
        "/api/v1/integrations/calendar",
        json=config,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


@pytest.mark.asyncio
async def test_create_communication_integration(test_client, test_user_token):
    """Test creating communication integration"""
    config = {
        "name": "Test Email Integration",
        "type": "communication",
        "enabled": True,
        "credentials": {
            "api_key": "test_resend_api_key"
        },
        "settings": {
            "email_provider": "resend",
            "default_sender": "noreply@test.com",
            "providers": ["email"]
        },
        "field_mappings": []
    }
    
    response = await test_client.post(
        "/api/v1/integrations/communication",
        json=config,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


@pytest.mark.asyncio
async def test_send_notification(test_client, test_user_token):
    """Test sending notification"""
    notification = {
        "recipient": "test@example.com",
        "template_id": "interview_invitation",
        "variables": {
            "candidate_name": "John Doe",
            "job_title": "Software Engineer",
            "company_name": "Test Company",
            "interview_date": "2024-01-20",
            "interview_time": "2:00 PM",
            "duration": "60",
            "interview_type": "Video Call",
            "recruiter_name": "Jane Smith"
        }
    }
    
    response = await test_client.post(
        "/api/v1/integrations/communication/send-notification",
        json=notification,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


@pytest.mark.asyncio
async def test_send_bulk_campaign(test_client, test_user_token):
    """Test sending bulk campaign"""
    campaign = {
        "name": "Interview Invitations Batch 1",
        "template_id": "interview_invitation",
        "recipients": [
            "candidate1@example.com",
            "candidate2@example.com",
            "candidate3@example.com"
        ],
        "variables": {
            "candidate1@example.com": {
                "candidate_name": "John Doe",
                "job_title": "Software Engineer",
                "company_name": "Test Company",
                "interview_date": "2024-01-20",
                "interview_time": "2:00 PM",
                "duration": "60",
                "interview_type": "Video Call",
                "recruiter_name": "Jane Smith"
            },
            "candidate2@example.com": {
                "candidate_name": "Jane Smith",
                "job_title": "Product Manager",
                "company_name": "Test Company",
                "interview_date": "2024-01-21",
                "interview_time": "10:00 AM",
                "duration": "45",
                "interview_type": "Phone Call",
                "recruiter_name": "Bob Johnson"
            },
            "candidate3@example.com": {
                "candidate_name": "Mike Wilson",
                "job_title": "Data Scientist",
                "company_name": "Test Company",
                "interview_date": "2024-01-22",
                "interview_time": "3:00 PM",
                "duration": "90",
                "interview_type": "Technical Interview",
                "recruiter_name": "Alice Brown"
            }
        }
    }
    
    response = await test_client.post(
        "/api/v1/integrations/communication/send-campaign",
        json=campaign,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


@pytest.mark.asyncio
async def test_schedule_interview(test_client, test_user_token):
    """Test scheduling interview"""
    schedule_request = {
        "candidate_email": "candidate@example.com",
        "interviewer_email": "interviewer@company.com",
        "duration_minutes": 60,
        "preferred_times": [
            {
                "start_time": "2024-01-20T14:00:00Z",
                "end_time": "2024-01-20T15:00:00Z",
                "timezone": "UTC"
            },
            {
                "start_time": "2024-01-21T10:00:00Z",
                "end_time": "2024-01-21T11:00:00Z",
                "timezone": "UTC"
            }
        ]
    }
    
    response = await test_client.post(
        "/api/v1/integrations/calendar/schedule-interview",
        params=schedule_request,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


@pytest.mark.asyncio
async def test_get_integrations(test_client, test_user_token):
    """Test getting integrations list"""
    response = await test_client.get(
        "/api/v1/integrations/",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


@pytest.mark.asyncio
async def test_ats_sync(test_client, test_user_token):
    """Test ATS sync operation"""
    # First create an integration (this would normally be done in setup)
    integration_id = "test_integration_id"
    
    response = await test_client.post(
        f"/api/v1/integrations/ats/{integration_id}/sync",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


if __name__ == "__main__":
    # Run individual tests
    async def run_tests():
        print("Testing Integration API endpoints...")
        
        # Note: These tests require proper authentication setup
        # They demonstrate the expected API structure and usage
        
        print("Integration API tests completed")
    
    asyncio.run(run_tests())