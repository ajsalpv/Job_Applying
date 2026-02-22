"""
Google Sheets Schema - Column definitions and data models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.config.constants import ApplicationStatus, JobPlatform


class JobListing(BaseModel):
    """Schema for a job listing"""
    company: str
    role: str
    location: str
    experience_required: Optional[str] = None
    job_url: str
    platform: JobPlatform
    job_description: Optional[str] = None
    salary_range: Optional[str] = None
    skills_required: List[str] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=datetime.now)


class JobApplication(BaseModel):
    """Schema for a job application record in Google Sheets"""
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    platform: str
    company: str
    role: str
    location: str
    experience_required: str = ""
    fit_score: int = 0
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    job_url: str = ""
    job_description: str = ""  # Store full JD
    interview_prep: str = ""   # Interview preparation tips
    skills_to_learn: str = ""  # Skills to learn before interview
    posted_at: str = ""        # When the job was posted
    applied_at: str = ""       # When the user applied
    notes: str = ""
    
    def to_row(self) -> List[str]:
        """Convert to Google Sheets row format"""
        return [
            self.date,
            self.platform,
            self.company,
            self.role,
            self.location,
            self.experience_required,
            str(self.fit_score),
            self.status.value,
            self.job_url,
            self.job_description[:1000] if self.job_description else "",  # Increased limit a bit
            self.interview_prep,
            self.skills_to_learn,
            self.posted_at,
            self.applied_at,
            self.notes,
        ]
    
    @classmethod
    def from_row(cls, row: List[str]) -> "JobApplication":
        """Create from Google Sheets row"""
        # Parsing status with robustness (case-insensitive, default to DISCOVERED)
        sheet_status = row[7].lower().strip() if len(row) > 7 and row[7] else ""
        try:
            status = ApplicationStatus(sheet_status)
        except ValueError:
            # Fallback for manual sheet edits or legacy values
            status_map = {
                "in_progress": ApplicationStatus.APPLIED,
                "interviewing": ApplicationStatus.INTERVIEW,
                "offered": ApplicationStatus.OFFER,
                "archived": ApplicationStatus.EXCLUDED,
            }
            status = status_map.get(sheet_status, ApplicationStatus.DISCOVERED)

        return cls(
            date=row[0] if len(row) > 0 else "",
            platform=row[1] if len(row) > 1 else "",
            company=row[2] if len(row) > 2 else "",
            role=row[3] if len(row) > 3 else "",
            location=row[4] if len(row) > 4 else "",
            experience_required=row[5] if len(row) > 5 else "",
            fit_score=int(row[6]) if len(row) > 6 and row[6].isdigit() else 0,
            status=status,
            job_url=row[8] if len(row) > 8 else "",
            job_description=row[9] if len(row) > 9 else "",
            interview_prep=row[10] if len(row) > 10 else "",
            skills_to_learn=row[11] if len(row) > 11 else "",
            posted_at=row[12] if len(row) > 12 else "",
            applied_at=row[13] if len(row) > 13 else "",
            notes=row[14] if len(row) > 14 else "",
        )


class ScoringResult(BaseModel):
    """Schema for job scoring result"""
    fit_score: int = Field(ge=0, le=100)
    skill_match_score: int = Field(ge=0, le=40)
    experience_match_score: int = Field(ge=0, le=25)
    location_match_score: int = Field(ge=0, le=15)
    role_relevance_score: int = Field(ge=0, le=20)
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    recommendation: str = "maybe"  # apply, maybe, skip
    reason: str = ""


class FollowUp(BaseModel):
    """Schema for follow-up tracking"""
    company: str
    role: str
    applied_date: str
    days_since_applied: int
    status: ApplicationStatus
    action_needed: str = ""
    next_followup: str = ""
    
    def to_row(self) -> List[str]:
        """Convert to Google Sheets row format"""
        return [
            self.company,
            self.role,
            self.applied_date,
            str(self.days_since_applied),
            self.status.value,
            self.action_needed,
            self.next_followup,
        ]
