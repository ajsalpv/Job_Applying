"""
Google Sheets Client - gspread wrapper for job tracking
"""
import json
from typing import List, Optional, Dict, Any
import gspread
from google.oauth2.service_account import Credentials
from app.config.settings import get_settings
from app.config.constants import SHEETS_COLUMNS
from app.tools.sheets.schema import JobApplication, FollowUp
from app.tools.utils.logger import get_logger
from app.tools.utils.retry import sheets_retry

logger = get_logger("sheets")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsClient:
    """Google Sheets client for job application tracking"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
    
    def _get_client(self) -> gspread.Client:
        """Get or create gspread client"""
        if self._client is None:
            import os
            
            # 1. Try to load from environment variable first (Cloud-friendly)
            # Use manual os.getenv as fallback to Pydantic settings for maximum robustness
            creds_json = self.settings.google_sheets_credentials_json or os.getenv("SHEETS_JSON") or os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
            
            if creds_json:
                try:
                    # Clean the JSON string (strip spaces/newlines)
                    raw_json = creds_json.strip()
                    creds_dict = json.loads(raw_json)
                    creds = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=SCOPES,
                    )
                    logger.info("✅ Google Sheets: Loaded credentials from environment variable")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Google Sheets: JSON error in environment variable: {e}")
                    raise ValueError(f"Invalid JSON in Google Sheets credentials: {e}")
            
            # 2. Fallback to file path (Local development)
            elif os.path.exists(self.settings.google_sheets_credentials_path):
                creds = Credentials.from_service_account_file(
                    self.settings.google_sheets_credentials_path,
                    scopes=SCOPES,
                )
                logger.info(f"✅ Google Sheets: Loaded credentials from file: {self.settings.google_sheets_credentials_path}")
            
            # 3. No credentials found
            else:
                msg = (
                    "❌ Google Sheets Credentials NOT FOUND.\n"
                    "Please set SHEETS_JSON environment variable in Render."
                )
                logger.error(msg)
                raise ValueError(msg)
                
            self._client = gspread.authorize(creds)
            logger.info("🚀 Google Sheets client initialized successfully")
        return self._client
    
    def _get_spreadsheet(self) -> gspread.Spreadsheet:
        """Get or open spreadsheet"""
        if self._spreadsheet is None:
            client = self._get_client()
            if self.settings.google_sheet_id:
                self._spreadsheet = client.open_by_key(self.settings.google_sheet_id)
            else:
                # Create new spreadsheet if none specified
                self._spreadsheet = client.create("AI Job Applications")
                logger.info(f"Created new spreadsheet: {self._spreadsheet.id}")
        return self._spreadsheet
    
    def _ensure_sheet_exists(self, sheet_name: str, headers: List[str]) -> gspread.Worksheet:
        """Ensure worksheet exists with headers"""
        spreadsheet = self._get_spreadsheet()
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=len(headers),
            )
            worksheet.append_row(headers)
            logger.info(f"Created worksheet: {sheet_name}")
        
        return worksheet
    
    @sheets_retry
    def get_applications_sheet(self) -> gspread.Worksheet:
        """Get Applications worksheet"""
        return self._ensure_sheet_exists(
            "Applications",
            SHEETS_COLUMNS["applications"],
        )
    
    @sheets_retry
    def get_followups_sheet(self) -> gspread.Worksheet:
        """Get Follow-ups worksheet"""
        return self._ensure_sheet_exists(
            "Follow-ups",
            SHEETS_COLUMNS["followups"],
        )
    
    @sheets_retry
    def add_application(self, application: JobApplication) -> bool:
        """Add a new application record with duplicate check"""
        try:
            # Check for duplicate URL
            if self.check_duplicate(application.job_url):
                logger.debug(f"Skipping duplicate application: {application.job_url}")
                return False
                
            sheet = self.get_applications_sheet()
            sheet.append_row(application.to_row())
            logger.info(f"Added application: {application.company} - {application.role}")
            return True
        except Exception as e:
            logger.error(f"Failed to add application: {e}")
            raise  # Re-raise to allow caller to handle fallback (e.g. notify anyway)
    
    @sheets_retry
    def get_all_applications(self) -> List[JobApplication]:
        """Get all application records"""
        sheet = self.get_applications_sheet()
        rows = sheet.get_all_values()
        
        # Skip header row
        applications = []
        for row in rows[1:]:
            try:
                applications.append(JobApplication.from_row(row))
            except Exception as e:
                logger.warning(f"Failed to parse row: {e}")
        
        return applications
    
    @sheets_retry
    def get_todays_applications(self) -> List[JobApplication]:
        """Get only today's application records"""
        from datetime import datetime
        
        today = datetime.now().strftime("%Y-%m-%d")
        all_apps = self.get_all_applications()
        
        todays_apps = [app for app in all_apps if app.date == today]
        logger.info(f"Found {len(todays_apps)} applications for today ({today})")
        
        return todays_apps
    
    @sheets_retry
    def update_application_status(
        self,
        company: str,
        role: str,
        new_status: str,
        notes: str = "",
    ) -> bool:
        """Update application status by company and role"""
        try:
            sheet = self.get_applications_sheet()
            rows = sheet.get_all_values()
            
            for i, row in enumerate(rows[1:], start=2):  # 1-indexed, skip header
                if row[2] == company and row[3] == role:
                    sheet.update_cell(i, 8, new_status)  # Status column
                    if notes:
                        sheet.update_cell(i, 15, notes)  # Notes column (Shifted to index 15)
                    
                    # Update applied_at if status is 'applied'
                    if new_status.lower() == "applied":
                        from datetime import datetime
                        applied_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        sheet.update_cell(i, 14, applied_at) # Applied At column
                    
                    logger.info(f"Updated status for {company} - {role}: {new_status}")
                    return True
            
            logger.warning(f"Application not found: {company} - {role}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return False
    
    @sheets_retry
    def check_duplicate(self, job_url: str) -> bool:
        """Check if job URL already exists"""
        sheet = self.get_applications_sheet()
        rows = sheet.get_all_values()
        
        for row in rows[1:]:
            if len(row) > 8 and row[8] == job_url:
                return True
        return False
    
    @sheets_retry
    def get_pending_followups(self, days_threshold: int = 7) -> List[Dict[str, Any]]:
        """Get applications needing follow-up"""
        from datetime import datetime, timedelta
        
        applications = self.get_all_applications()
        pending = []
        
        for app in applications:
            if app.status.value in ["applied", "interview"]:
                try:
                    applied_date = datetime.strptime(app.date, "%Y-%m-%d")
                    days_since = (datetime.now() - applied_date).days
                    
                    if days_since >= days_threshold:
                        pending.append({
                            "company": app.company,
                            "role": app.role,
                            "applied_date": app.date,
                            "days_since": days_since,
                            "status": app.status.value,
                        })
                except:
                    pass
        
        return pending


# Singleton instance
sheets_client = SheetsClient()
