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
        self.smtp_port = 587
        self.email_address = self.settings.smtp_email
        self.email_password = self.settings.smtp_password

    def send_application(
        self, 
        to_email: str, 
        position_name: str, 
        resume_path: str = "app/data/Ajsalpv_CV.pdf",
        cover_letter_path: str = "app/data/cover_letter.txt"
    ) -> bool:
        """
        Send job application email with attached resume and customized cover letter.
        
        Args:
            to_email: Recruiter's email address
            position_name: The job title to insert into the cover letter
            resume_path: Path to PDF resume
            cover_letter_path: Path to cover letter text template
            
        Returns:
            True if sent successfully
        """
        if not self.email_address or not self.email_password:
            logger.error("SMTP credentials missing. Please set SMTP_EMAIL and SMTP_PASSWORD in .env")
            return False
            
        if not os.path.exists(resume_path):
            logger.error(f"Resume not found at {resume_path}")
            return False
            
        if not os.path.exists(cover_letter_path):
            logger.error(f"Cover letter template not found at {cover_letter_path}")
            # Fallback could be implemented, but for now strict fail
            return False

        try:
            # 1. Prepare Content
            with open(cover_letter_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Smart Replacement Logic
            # User provided: "Artificial Intelligence Engineer (AI Automation)" is the placeholder phrase logic
            target_phrase = "Artificial Intelligence Engineer (AI Automation)"
            
            if target_phrase in template_content:
                body_content = template_content.replace(target_phrase, position_name)
            else:
                # Fallback: Just try to replace [Position] if they used that, or warn
                body_content = template_content.replace("[Position]", position_name)
                if target_phrase not in template_content:
                    logger.warning(f"Target phrase '{target_phrase}' not found in template. No replacement made or fallbacks used.")
            
            # 2. Setup Message (Support HTML for bold/bullets)
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = f"Application for {position_name} - Ajsal PV"
            
            # Create HTML version of body
            html_content = body_content.replace("\n", "<br>")
            # Convert **bold** to <b>bold</b>
            import re
            html_content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_content)
            
            # Attach both plain and HTML versions
            msg.attach(MIMEText(body_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Create a main container for attachments
            main_msg = MIMEMultipart()
            main_msg['From'] = msg['From']
            main_msg['To'] = msg['To']
            main_msg['Subject'] = msg['Subject']
            main_msg.attach(msg)
            
            # Attach Resume
            with open(resume_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename="Ajsal_PV_Resume.pdf")
                main_msg.attach(attach)
            
            # 3. Send via SMTP with TLS
            logger.info(f"Connecting to SMTP {self.smtp_server}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls() # Secure connection
            server.login(self.email_address, self.email_password)
            
            text = main_msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email} for {position_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

email_sender = EmailSender()
