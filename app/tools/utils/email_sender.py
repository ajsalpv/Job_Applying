import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
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
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465 # Switch to Port 465 for SSL (more stable on Render)
        self.email_address = self.settings.smtp_email
        self.email_password = self.settings.smtp_password
        self.timeout = 30 # 30 second timeout for network operations

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
            
            # Smart Replacement Logic
            target_phrase = "Artificial Intelligence Engineer (AI Automation)"
            
            if target_phrase in template_content:
                body_content = template_content.replace(target_phrase, position_name)
            else:
                body_content = template_content.replace("[Position]", position_name)
                if target_phrase not in template_content:
                    logger.warning(f"Target phrase '{target_phrase}' not found in template.")
            
            # 2. Setup Message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = f"Application for {position_name} - Ajsal PV"
            
            html_content = body_content.replace("\n", "<br>")
            import re
            html_content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_content)
            
            msg.attach(MIMEText(body_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            main_msg = MIMEMultipart()
            main_msg['From'] = msg['From']
            main_msg['To'] = msg['To']
            main_msg['Subject'] = msg['Subject']
            main_msg.attach(msg)
            
            with open(resume_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename="Ajsalpv_CV.pdf")
                main_msg.attach(attach)
            
            # 3. Send with Retries
            import time
            max_retries = 3
            retry_delay = 5 # seconds
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Connecting to SMTP {self.smtp_server}:{self.smtp_port} (SSL)... Attempt {attempt + 1}")
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=self.timeout)
                    server.login(self.email_address, self.email_password)
                    
                    text = main_msg.as_string()
                    server.sendmail(self.email_address, to_email, text)
                    server.quit()
                    
                    success_msg = f"Email sent successfully to {to_email} for {position_name}"
                    logger.info(success_msg)
                    return True, success_msg
                    
                except smtplib.SMTPAuthenticationError:
                    msg = "SMTP Authentication failed. Check if your App Password is correct."
                    logger.error(msg)
                    return False, msg
                except (os.error, smtplib.SMTPException, Exception) as e:
                    logger.warning(f"SMTP attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    raise # Re-raise to be caught by outer except
            
            return False, "Failed to send email after retries"

        except Exception as e:
            msg = f"Failed to send email: {str(e)}"
            logger.error(msg)
            return False, msg

email_sender = EmailSender()
