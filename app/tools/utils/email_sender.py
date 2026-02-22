import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import json
import base64
from app.config.settings import get_settings
from app.tools.utils.logger import get_logger

logger = get_logger("email_sender")

class EmailSender:
    """
    Secure Email Sender utility using SMTP (App Passwords recommended).
    Handles attachment of resume and dynamic cover letter generation.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.smtp_server = self.settings.smtp_server
        self.smtp_port = self.settings.smtp_port
        self.email_address = self.settings.smtp_email
        self.email_password = self.settings.smtp_password
        self.timeout = 60 # Extended timeout for slow cloud networks

    from typing import Tuple

    def send_application(
        self, 
        to_email: str, 
        position_name: str, 
        resume_path: str = "app/data/Ajsalpv_CV.pdf",
        cover_letter_path: str = "app/data/cover_letter.txt"
    ) -> Tuple[bool, str]:
        """
        Send job application email with attached resume and customized cover letter.
        
        Args:
            to_email: Recruiter's email address
            position_name: The job title to insert into the cover letter
            resume_path: Path to PDF resume
            cover_letter_path: Path to cover letter text template
            
        Returns:
            (Success boolean, Error or success message string)
        """
        if not self.email_address or not self.email_password:
            msg = "SMTP credentials missing. Please set SMTP_EMAIL and SMTP_PASSWORD in .env"
            logger.error(msg)
            return False, msg
            
        if not os.path.exists(resume_path):
            msg = f"Resume not found at {resume_path}. Make sure to commit it to Git."
            logger.error(msg)
            return False, msg
            
        if not os.path.exists(cover_letter_path):
            msg = f"Cover letter template not found at {cover_letter_path}. Make sure to commit it to Git."
            logger.error(msg)
            return False, msg

        try:
            # 1. Prepare Content
            with open(cover_letter_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            target_phrase = "Artificial Intelligence Engineer (AI Automation)"
            body_content = template_content.replace(target_phrase, position_name) if target_phrase in template_content else template_content.replace("[Position]", position_name)
            
            # --- METHOD 1: Official Gmail API (HTTP - Recommended for Render + Google Only) ---
            # --- METHOD 1: Official Gmail API (HTTP - Recommended for Render + Google Only) ---
            creds = None
            
            # 1. Try Environment Variable (Cloud / Render Fix)
            if self.settings.gmail_token_json:
                try:
                    logger.info("Using Gmail Token from environment variable")
                    token_info = json.loads(self.settings.gmail_token_json)
                    from google.oauth2.credentials import Credentials
                    creds = Credentials.from_authorized_user_info(token_info)
                except Exception as e:
                    logger.error(f"Failed to load Gmail Token from env: {e}")

            # 2. Try Local File (Fallback)
            if not creds and os.path.exists(self.settings.gmail_token_path):
                token_abs_path = os.path.abspath(self.settings.gmail_token_path)
                logger.info(f"✅ Found Gmail Token at: {token_abs_path}")
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(self.settings.gmail_token_path)

            if creds:
                # AUTO-REFRESH: If token is expired, refresh it automatically
                if creds.expired and creds.refresh_token:
                    try:
                        from google.auth.transport.requests import Request
                        logger.info("🔄 Gmail token expired, auto-refreshing...")
                        creds.refresh(Request())
                        logger.info("✅ Gmail token refreshed successfully!")
                        
                        # Save refreshed token back to env-compatible format
                        refreshed_token = {
                            "token": creds.token,
                            "refresh_token": creds.refresh_token,
                            "token_uri": creds.token_uri,
                            "client_id": creds.client_id,
                            "client_secret": creds.client_secret,
                            "scopes": creds.scopes,
                        }
                        logger.info("💾 Refreshed token ready (update GMAIL_TOKEN_JSON env var for persistence)")
                    except Exception as e:
                        logger.error(f"Token refresh failed: {e}. User must re-authenticate.")
                        creds = None
                
                if not creds or not creds.valid:
                    logger.error("❌ Gmail credentials invalid even after refresh attempt")
                    # Fall through to SMTP
                else:
                    logger.info(f"Using Official Gmail API (HTTP) for 100% Google Security...")
                    from googleapiclient.discovery import build
                    service = build('gmail', 'v1', credentials=creds)
                
                    # Build Message
                    msg = MIMEMultipart()
                    msg['To'] = to_email
                    msg['Subject'] = f"Application for {position_name} - {self.settings.user_name}"
                    
                    # HTML Body
                    html_content = body_content.replace("\n", "<br>")
                    import re
                    html_content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_content)
                    msg.attach(MIMEText(html_content, 'html'))
                    
                    # Attachment
                    with open(resume_path, "rb") as f:
                        attach = MIMEApplication(f.read(), _subtype="pdf")
                        attach.add_header('Content-Disposition', 'attachment', filename="Ajsalpv_CV.pdf")
                        msg.attach(attach)
                    
                    raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                    sent_msg = service.users().messages().send(userId='me', body={'raw': raw_msg}).execute()
                    
                    logger.info(f"Email sent via Gmail API: {sent_msg['id']}")
                    self._log_email(to_email, position_name)
                    return True, "Email sent successfully via Official Gmail API (Safe & Free)!"

            # --- METHOD 2: SMTP (Fallback for Local) ---
            # Setup Message for SMTP
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = f"Application for {position_name} - {self.settings.user_name}"
            
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if self.smtp_port == 465:
                        logger.info(f"Connecting to SMTP {self.smtp_server}:{self.smtp_port} (SSL)... Attempt {attempt + 1}")
                        server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=self.timeout)
                    else:
                        logger.info(f"Connecting to SMTP {self.smtp_server}:{self.smtp_port} (STARTTLS)... Attempt {attempt + 1}")
                        server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout)
                        server.starttls()
                    
                    server.login(self.email_address, self.email_password)
                    
                    # Construct message for SMTP
                    smtp_msg = MIMEMultipart()
                    smtp_msg['From'] = self.email_address
                    smtp_msg['To'] = to_email
                    smtp_msg['Subject'] = f"Application for {position_name} - {self.settings.user_name}"
                    smtp_msg.attach(MIMEText(body_content, 'plain'))
                    with open(resume_path, "rb") as f:
                        attach = MIMEApplication(f.read(), _subtype="pdf")
                        attach.add_header('Content-Disposition', 'attachment', filename="Ajsalpv_CV.pdf")
                        smtp_msg.attach(attach)

                    server.sendmail(self.email_address, to_email, smtp_msg.as_string())
                    server.quit()
                    self._log_email(to_email, position_name)
                    return True, f"Email sent via SMTP ({self.smtp_server})"
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    raise e
            
            return False, f"Failed after {max_retries} SMTP attempts."

        except Exception as e:
            msg = f"Critical Error in Email Bot: {str(e)}"
            logger.error(msg)
            return False, msg

    def _log_email(self, to_email: str, job_name: str):
        """Log sent email to local JSON file for tracking"""
        try:
            from datetime import datetime
            log_dir = "app/data"
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "email_logs.json")
            
            logs = []
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    logs = json.load(f)
            
            new_log = {
                "recipient": to_email,
                "job_name": job_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "timestamp": datetime.now().isoformat()
            }
            logs.insert(0, new_log) # Newest first
            
            with open(log_path, 'w') as f:
                json.dump(logs[:500], f, indent=2) # Keep last 500 logs
        except Exception as e:
            logger.error(f"Failed to log email: {e}")

email_sender = EmailSender()
