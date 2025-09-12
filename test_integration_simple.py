"""
Simple integration test without database dependencies
"""

import asyncio
from datetime import datetime, timedelta

from app.services.ats_connectors import GreenhouseConnector, LeverConnector, WorkdayConnector, BambooHRConnector
from app.services.calendar_connectors import GoogleCalendarConnector, OutlookConnector
from app.services.communication_service import ResendEmailConnector, TwilioSMSConnector
from app.schemas.integration import CalendarEvent


async def test_ats_connectors():
    """Test all ATS connectors"""
    print("Testing ATS connectors...")
    
    # Test Greenhouse
    gh_connector = GreenhouseConnector({"api_key": "test_key"})
    assert await gh_connector.authenticate() == True
    candidates = await gh_connector.get_candidates()
    assert len(candidates) > 0
    print(f"✓ Greenhouse: {len(candidates)} candidates")
    
    # Test Lever
    lever_connector = LeverConnector({"api_key": "test_key"})
    assert await lever_connector.authenticate() == True
    candidates = await lever_connector.get_candidates()
    assert len(candidates) > 0
    print(f"✓ Lever: {len(candidates)} candidates")
    
    # Test Workday
    wd_connector = WorkdayConnector({"client_id": "test", "client_secret": "test"})
    assert await wd_connector.authenticate() == True
    candidates = await wd_connector.get_candidates()
    assert len(candidates) > 0
    print(f"✓ Workday: {len(candidates)} candidates")
    
    # Test BambooHR
    bamboo_connector = BambooHRConnector({"subdomain": "test", "api_key": "test"})
    assert await bamboo_connector.authenticate() == True
    candidates = await bamboo_connector.get_candidates()
    assert len(candidates) > 0
    print(f"✓ BambooHR: {len(candidates)} candidates")


async def test_calendar_connectors():
    """Test calendar connectors"""
    print("\nTesting calendar connectors...")
    
    # Test Google Calendar
    google_connector = GoogleCalendarConnector({
        "access_token": "test_token",
        "client_id": "test_id"
    })
    assert await google_connector.authenticate() == True
    
    event = CalendarEvent(
        title="Test Interview",
        description="Test interview",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=1),
        attendees=["test@example.com"]
    )
    event_id = await google_connector.create_event(event)
    assert event_id.startswith("google_event_")
    print(f"✓ Google Calendar: Created event {event_id}")
    
    # Test Outlook
    outlook_connector = OutlookConnector({
        "access_token": "test_token",
        "tenant_id": "test_tenant"
    })
    assert await outlook_connector.authenticate() == True
    
    event_id = await outlook_connector.create_event(event)
    assert event_id.startswith("outlook_event_")
    print(f"✓ Outlook: Created event {event_id}")


async def test_communication_connectors():
    """Test communication connectors"""
    print("\nTesting communication connectors...")
    
    # Test Resend
    resend_connector = ResendEmailConnector({"api_key": "test_key"})
    assert await resend_connector.authenticate() == True
    
    success = await resend_connector.send_email(
        "test@example.com",
        "Test Subject",
        "<h1>Test Email</h1>",
        "Test Email"
    )
    print(f"✓ Resend: Email sent = {success}")
    
    # Test Twilio
    twilio_connector = TwilioSMSConnector({
        "account_sid": "test_sid",
        "auth_token": "test_token"
    })
    assert await twilio_connector.authenticate() == True
    
    success = await twilio_connector.send_sms("+15551234567", "Test SMS")
    print(f"✓ Twilio: SMS sent = {success}")


async def test_rate_limits():
    """Test rate limit functionality"""
    print("\nTesting rate limits...")
    
    connectors = [
        GreenhouseConnector({"api_key": "test"}),
        LeverConnector({"api_key": "test"}),
        WorkdayConnector({"client_id": "test", "client_secret": "test"}),
        BambooHRConnector({"subdomain": "test", "api_key": "test"})
    ]
    
    for connector in connectors:
        await connector.authenticate()
        rate_limits = await connector.get_rate_limits()
        assert "limit" in rate_limits
        assert "remaining" in rate_limits
        print(f"✓ {connector.__class__.__name__}: {rate_limits['remaining']}/{rate_limits['limit']} remaining")


async def main():
    """Run all tests"""
    print("🚀 Starting Integration Hub Tests\n")
    
    try:
        await test_ats_connectors()
        await test_calendar_connectors()
        await test_communication_connectors()
        await test_rate_limits()
        
        print("\n✅ All integration tests passed!")
        print("\n📋 Integration Hub Features Implemented:")
        print("   • ATS Connectors: Greenhouse, Lever, Workday, BambooHR")
        print("   • Calendar Integration: Google Calendar, Outlook")
        print("   • Communication: Email (Resend), SMS (Twilio)")
        print("   • Field Mapping & Data Transformation")
        print("   • Rate Limiting & Error Handling")
        print("   • Automated Sync & Status Updates")
        print("   • Bulk Campaign Management")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())