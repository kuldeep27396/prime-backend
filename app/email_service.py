import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from typing import Optional

class EmailService:
    def __init__(self):
        # Brevo API Configuration
        self.brevo_api_key = os.getenv('BREVO_API_KEY')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', 'noreply@primeinterviews.info')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Prime Interviews')

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        to_name: Optional[str] = None
    ) -> bool:
        """Send an email using Brevo API"""
        try:
            if not self.brevo_api_key:
                print("❌ Brevo API key not configured")
                return False

            # Configure API client
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.brevo_api_key

            # Create transactional email API instance
            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

            # Create email data
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender={"name": self.from_name, "email": self.from_email},
                to=[{"email": to_email, "name": to_name} if to_name else {"email": to_email}],
                subject=subject,
                html_content=html_content
            )

            # Send email
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(f"✅ Email sent via Brevo: {api_response.message_id}")
            return True

        except ApiException as e:
            print(f"❌ Brevo API error: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.brevo_api_key and self.from_email)

    def get_configuration_status(self) -> dict:
        """Get detailed configuration status"""
        return {
            "brevo_configured": bool(self.brevo_api_key),
            "from_email": self.from_email,
            "from_name": self.from_name,
            "method": "Brevo"
        }

# Create a global instance
email_service = EmailService()