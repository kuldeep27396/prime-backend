"""
Communication service for email and SMS notifications
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from jinja2 import Template

from app.services.integration_service import CommunicationConnector
from app.schemas.integration import (
    EmailTemplate as EmailTemplateSchema, 
    CampaignRequest, 
    CampaignResult,
    NotificationRequest
)

logger = logging.getLogger(__name__)


class ResendEmailConnector(CommunicationConnector):
    """Mock Resend email service connector"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        super().__init__(credentials, settings)
        self.api_key = credentials.get("api_key")
        self.from_email = settings.get("from_email", "noreply@prime-recruitment.com")
    
    async def authenticate(self) -> bool:
        """Mock authentication with Resend"""
        await asyncio.sleep(0.1)
        if not self.api_key:
            return False
        self.is_authenticated = True
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Resend"""
        if not self.is_authenticated:
            return False
        await asyncio.sleep(0.1)
        return True
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get Resend rate limits"""
        return {
            "limit": 100,  # Free tier limit
            "remaining": random.randint(50, 100),
            "reset_time": datetime.utcnow() + timedelta(hours=24)
        }
    
    async def send_email(self, to: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email via Resend"""
        await asyncio.sleep(0.1)
        
        logger.info(f"Sending email to {to}: {subject}")
        
        # Mock email sending - simulate occasional failures
        success = random.random() > 0.05  # 95% success rate
        
        if success:
            logger.info(f"Email sent successfully to {to}")
        else:
            logger.error(f"Failed to send email to {to}")
        
        return success
    
    async def send_bulk_email(self, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send bulk email campaign"""
        await asyncio.sleep(0.5)  # Bulk operations take longer
        
        sent_count = 0
        failed_count = 0
        errors = []
        
        for recipient in recipients:
            try:
                success = await self.send_email(
                    recipient["email"],
                    recipient["subject"],
                    recipient["html_content"],
                    recipient.get("text_content")
                )
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Failed to send to {recipient['email']}")
            except Exception as e:
                failed_count += 1
                errors.append(f"Error sending to {recipient['email']}: {e}")
        
        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
            "errors": errors
        }


class TwilioSMSConnector(CommunicationConnector):
    """Mock Twilio SMS connector"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        super().__init__(credentials, settings)
        self.account_sid = credentials.get("account_sid")
        self.auth_token = credentials.get("auth_token")
        self.from_phone = settings.get("from_phone", "+15551234567")
    
    async def authenticate(self) -> bool:
        """Mock authentication with Twilio"""
        await asyncio.sleep(0.1)
        if not self.account_sid or not self.auth_token:
            return False
        self.is_authenticated = True
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Twilio"""
        if not self.is_authenticated:
            return False
        await asyncio.sleep(0.1)
        return True
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get Twilio rate limits"""
        return {
            "limit": 1000,
            "remaining": random.randint(500, 1000),
            "reset_time": datetime.utcnow() + timedelta(hours=1)
        }
    
    async def send_email(self, to: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Not applicable for SMS connector"""
        return False
    
    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS via Twilio"""
        await asyncio.sleep(0.2)
        
        logger.info(f"Sending SMS to {to}: {message[:50]}...")
        
        # Mock SMS sending - simulate occasional failures
        success = random.random() > 0.02  # 98% success rate
        
        if success:
            logger.info(f"SMS sent successfully to {to}")
        else:
            logger.error(f"Failed to send SMS to {to}")
        
        return success
    
    async def send_bulk_email(self, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Not applicable for SMS connector"""
        return {"sent_count": 0, "failed_count": 0, "errors": ["SMS connector does not support email"]}


class CommunicationService:
    """Service for managing communication integrations"""
    
    def __init__(self, integration_service, db):
        self.integration_service = integration_service
        self.db = db
        
        # Default email templates
        self.default_templates = {
            "interview_invitation": {
                "subject": "Interview Invitation - {{job_title}} at {{company_name}}",
                "html_content": """
                <h2>Interview Invitation</h2>
                <p>Dear {{candidate_name}},</p>
                <p>We are pleased to invite you for an interview for the {{job_title}} position at {{company_name}}.</p>
                <p><strong>Interview Details:</strong></p>
                <ul>
                    <li>Date: {{interview_date}}</li>
                    <li>Time: {{interview_time}}</li>
                    <li>Duration: {{duration}} minutes</li>
                    <li>Type: {{interview_type}}</li>
                </ul>
                {% if meeting_link %}
                <p><strong>Meeting Link:</strong> <a href="{{meeting_link}}">Join Interview</a></p>
                {% endif %}
                <p>Please confirm your attendance by replying to this email.</p>
                <p>Best regards,<br>{{recruiter_name}}<br>{{company_name}}</p>
                """,
                "text_content": """
                Interview Invitation
                
                Dear {{candidate_name}},
                
                We are pleased to invite you for an interview for the {{job_title}} position at {{company_name}}.
                
                Interview Details:
                - Date: {{interview_date}}
                - Time: {{interview_time}}
                - Duration: {{duration}} minutes
                - Type: {{interview_type}}
                
                {% if meeting_link %}Meeting Link: {{meeting_link}}{% endif %}
                
                Please confirm your attendance by replying to this email.
                
                Best regards,
                {{recruiter_name}}
                {{company_name}}
                """
            },
            "application_received": {
                "subject": "Application Received - {{job_title}}",
                "html_content": """
                <h2>Application Received</h2>
                <p>Dear {{candidate_name}},</p>
                <p>Thank you for your interest in the {{job_title}} position at {{company_name}}.</p>
                <p>We have received your application and will review it carefully. You can expect to hear from us within {{response_time}} business days.</p>
                <p>In the meantime, feel free to learn more about our company at {{company_website}}.</p>
                <p>Best regards,<br>{{company_name}} Recruitment Team</p>
                """,
                "text_content": """
                Application Received
                
                Dear {{candidate_name}},
                
                Thank you for your interest in the {{job_title}} position at {{company_name}}.
                
                We have received your application and will review it carefully. You can expect to hear from us within {{response_time}} business days.
                
                In the meantime, feel free to learn more about our company at {{company_website}}.
                
                Best regards,
                {{company_name}} Recruitment Team
                """
            },
            "interview_reminder": {
                "subject": "Interview Reminder - Tomorrow at {{interview_time}}",
                "html_content": """
                <h2>Interview Reminder</h2>
                <p>Dear {{candidate_name}},</p>
                <p>This is a friendly reminder about your upcoming interview:</p>
                <p><strong>Interview Details:</strong></p>
                <ul>
                    <li>Position: {{job_title}}</li>
                    <li>Date: {{interview_date}}</li>
                    <li>Time: {{interview_time}}</li>
                    <li>Duration: {{duration}} minutes</li>
                </ul>
                {% if meeting_link %}
                <p><strong>Meeting Link:</strong> <a href="{{meeting_link}}">Join Interview</a></p>
                {% endif %}
                <p>Please ensure you have a stable internet connection and test your camera/microphone beforehand.</p>
                <p>Looking forward to speaking with you!</p>
                <p>Best regards,<br>{{recruiter_name}}</p>
                """,
                "text_content": """
                Interview Reminder
                
                Dear {{candidate_name}},
                
                This is a friendly reminder about your upcoming interview:
                
                Interview Details:
                - Position: {{job_title}}
                - Date: {{interview_date}}
                - Time: {{interview_time}}
                - Duration: {{duration}} minutes
                
                {% if meeting_link %}Meeting Link: {{meeting_link}}{% endif %}
                
                Please ensure you have a stable internet connection and test your camera/microphone beforehand.
                
                Looking forward to speaking with you!
                
                Best regards,
                {{recruiter_name}}
                """
            },
            "rejection_notice": {
                "subject": "Update on Your Application - {{job_title}}",
                "html_content": """
                <h2>Application Update</h2>
                <p>Dear {{candidate_name}},</p>
                <p>Thank you for your interest in the {{job_title}} position at {{company_name}} and for taking the time to interview with us.</p>
                <p>After careful consideration, we have decided to move forward with other candidates whose experience more closely matches our current needs.</p>
                <p>We were impressed by your background and encourage you to apply for future opportunities that align with your skills and experience.</p>
                <p>We wish you the best of luck in your job search.</p>
                <p>Best regards,<br>{{company_name}} Recruitment Team</p>
                """,
                "text_content": """
                Application Update
                
                Dear {{candidate_name}},
                
                Thank you for your interest in the {{job_title}} position at {{company_name}} and for taking the time to interview with us.
                
                After careful consideration, we have decided to move forward with other candidates whose experience more closely matches our current needs.
                
                We were impressed by your background and encourage you to apply for future opportunities that align with your skills and experience.
                
                We wish you the best of luck in your job search.
                
                Best regards,
                {{company_name}} Recruitment Team
                """
            }
        }
    
    async def send_notification(self, company_id: str, request: NotificationRequest) -> bool:
        """Send a notification using available communication integrations"""
        
        # Get email integrations for the company
        integrations = await self.integration_service.get_integrations(company_id, "communication")
        email_integration = None
        
        for integration in integrations:
            if integration.enabled and "email" in integration.settings.get("providers", []):
                email_integration = integration
                break
        
        if not email_integration:
            logger.warning(f"No email integration found for company {company_id}")
            return False
        
        connector = await self.integration_service.get_connector(str(email_integration.id))
        if not connector:
            logger.error(f"Could not get connector for integration {email_integration.id}")
            return False
        
        try:
            # Get template
            template_data = self.default_templates.get(request.template_id)
            if not template_data:
                logger.error(f"Template {request.template_id} not found")
                return False
            
            # Render template with variables
            subject_template = Template(template_data["subject"])
            html_template = Template(template_data["html_content"])
            text_template = Template(template_data["text_content"])
            
            subject = subject_template.render(**request.variables)
            html_content = html_template.render(**request.variables)
            text_content = text_template.render(**request.variables)
            
            # Send email
            success = await connector.send_email(request.recipient, subject, html_content, text_content)
            
            if success:
                logger.info(f"Notification sent to {request.recipient} using template {request.template_id}")
            else:
                logger.error(f"Failed to send notification to {request.recipient}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    async def send_bulk_campaign(self, company_id: str, campaign: CampaignRequest) -> CampaignResult:
        """Send bulk email campaign"""
        
        # Get email integrations
        integrations = await self.integration_service.get_integrations(company_id, "communication")
        email_integration = None
        
        for integration in integrations:
            if integration.enabled and "email" in integration.settings.get("providers", []):
                email_integration = integration
                break
        
        if not email_integration:
            return CampaignResult(
                campaign_id=f"campaign_{random.randint(1000, 9999)}",
                total_recipients=len(campaign.recipients),
                sent_count=0,
                failed_count=len(campaign.recipients),
                errors=["No email integration available"],
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
        
        connector = await self.integration_service.get_connector(str(email_integration.id))
        if not connector:
            return CampaignResult(
                campaign_id=f"campaign_{random.randint(1000, 9999)}",
                total_recipients=len(campaign.recipients),
                sent_count=0,
                failed_count=len(campaign.recipients),
                errors=["Could not get email connector"],
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
        
        campaign_id = f"campaign_{random.randint(1000, 9999)}"
        started_at = datetime.utcnow()
        
        try:
            # Get template
            template_data = self.default_templates.get(campaign.template_id)
            if not template_data:
                return CampaignResult(
                    campaign_id=campaign_id,
                    total_recipients=len(campaign.recipients),
                    sent_count=0,
                    failed_count=len(campaign.recipients),
                    errors=[f"Template {campaign.template_id} not found"],
                    started_at=started_at,
                    completed_at=datetime.utcnow()
                )
            
            # Prepare bulk email data
            bulk_recipients = []
            for recipient in campaign.recipients:
                recipient_variables = campaign.variables.get(recipient, {})
                
                # Render templates
                subject_template = Template(template_data["subject"])
                html_template = Template(template_data["html_content"])
                text_template = Template(template_data["text_content"])
                
                subject = subject_template.render(**recipient_variables)
                html_content = html_template.render(**recipient_variables)
                text_content = text_template.render(**recipient_variables)
                
                bulk_recipients.append({
                    "email": recipient,
                    "subject": subject,
                    "html_content": html_content,
                    "text_content": text_content
                })
            
            # Send bulk email
            result = await connector.send_bulk_email(bulk_recipients)
            
            return CampaignResult(
                campaign_id=campaign_id,
                total_recipients=len(campaign.recipients),
                sent_count=result["sent_count"],
                failed_count=result["failed_count"],
                errors=result["errors"],
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error sending bulk campaign: {e}")
            return CampaignResult(
                campaign_id=campaign_id,
                total_recipients=len(campaign.recipients),
                sent_count=0,
                failed_count=len(campaign.recipients),
                errors=[str(e)],
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
    
    async def send_interview_invitation(self, company_id: str, candidate_email: str, 
                                      interview_details: Dict[str, Any]) -> bool:
        """Send interview invitation email"""
        request = NotificationRequest(
            recipient=candidate_email,
            template_id="interview_invitation",
            variables=interview_details
        )
        return await self.send_notification(company_id, request)
    
    async def send_application_confirmation(self, company_id: str, candidate_email: str, 
                                          application_details: Dict[str, Any]) -> bool:
        """Send application received confirmation"""
        request = NotificationRequest(
            recipient=candidate_email,
            template_id="application_received",
            variables=application_details
        )
        return await self.send_notification(company_id, request)
    
    async def send_interview_reminder(self, company_id: str, candidate_email: str, 
                                    interview_details: Dict[str, Any]) -> bool:
        """Send interview reminder email"""
        request = NotificationRequest(
            recipient=candidate_email,
            template_id="interview_reminder",
            variables=interview_details
        )
        return await self.send_notification(company_id, request)
    
    async def send_rejection_notice(self, company_id: str, candidate_email: str, 
                                  rejection_details: Dict[str, Any]) -> bool:
        """Send rejection notice email"""
        request = NotificationRequest(
            recipient=candidate_email,
            template_id="rejection_notice",
            variables=rejection_details
        )
        return await self.send_notification(company_id, request)