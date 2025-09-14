import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.usesend.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '465'))
        self.smtp_user = os.getenv('SMTP_USER', 'usesend')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', 'noreply@prime-interviews.com')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Prime Interviews')
        self.smtp_secure = os.getenv('SMTP_SECURE', 'true').lower() == 'true'

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        to_name: Optional[str] = None
    ) -> bool:
        """Send an email using SMTP"""
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = f"{to_name} <{to_email}>" if to_name else to_email
            message['Subject'] = subject

            # Add HTML part
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            # Connect and send email
            if self.smtp_secure:
                # SSL connection
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    use_tls=True,
                )
            else:
                # STARTTLS connection
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    start_tls=True,
                )

            return True

        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

    def is_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return bool(
            self.smtp_host and
            self.smtp_password and
            self.smtp_user and
            self.from_email
        )

# Create a global instance
email_service = EmailService()