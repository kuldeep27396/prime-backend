import os
import httpx
from typing import Optional

class EmailService:
    def __init__(self):
        # Resend API Configuration
        self.resend_api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', 'noreply@primeinterviews.info')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Prime Interviews')

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        to_name: Optional[str] = None
    ) -> bool:
        """Send an email using Resend API"""
        try:
            if not self.resend_api_key:
                print("❌ Resend API key not configured")
                return False

            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Email sent via Resend: {result.get('id')}")
                    return True
                else:
                    print(f"❌ Resend API failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.resend_api_key and self.from_email)

    def get_configuration_status(self) -> dict:
        """Get detailed configuration status"""
        return {
            "resend_configured": bool(self.resend_api_key),
            "from_email": self.from_email,
            "from_name": self.from_name,
            "method": "Resend"
        }

# Create a global instance
email_service = EmailService()