"""
API Schemas - Pydantic models for request/response
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.config.constants import ApplicationStatus, JobPlatform


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class JobSearchRequest(BaseModel):
    """Request for job search"""
    keywords: str = Field(default="AI Engineer", description="Search keywords")
    locations: List[str] = Field(default=["Bangalore", "Remote"], description="Preferred locations")
    platforms: List[str] = Field(default=["linkedin", "indeed", "naukri"], description="Platforms to search")
    min_score: int = Field(default=70, ge=0, le=100, description="Minimum fit score")


class ApproveJobsRequest(BaseModel):
    """Request to approve jobs for application"""
    job_urls: List[str] = Field(..., description="List of job URLs to approve")


class UpdateStatusRequest(BaseModel):
    """Request to update application status"""
    company: str
    role: str
    status: ApplicationStatus
    notes: Optional[str] = ""


class GenerateContentRequest(BaseModel):
    """Request to generate resume/cover letter"""
    company: str
    role: str
    job_description: str


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class JobListing(BaseModel):
    """Job listing in response"""
    company: str
    role: str
    location: str
    job_url: str
    platform: str
    experience_required: Optional[str] = None
    fit_score: Optional[int] = None
    scoring_details: Optional[Dict[str, Any]] = None


class JobSearchResponse(BaseModel):
    """Response for job search"""
    success: bool
    jobs: List[JobListing]
    total_discovered: int
    total_scored: int
    message: str


class ResumeOptimization(BaseModel):
    """Resume optimization response"""
    company: str
    role: str
    optimized_bullets: List[str]
    keywords_included: List[str]
    skill_highlights: List[str]


class CoverLetterResponse(BaseModel):
    """Cover letter response"""
    company: str
    role: str
    cover_letter: str


class ApplicationStats(BaseModel):
    """Application statistics"""
    total_discovered: int
    total_applied: int
    interviews: int
    offers: int
    rejected: int
    no_response: int
    success_rate: float


class FollowUpItem(BaseModel):
    """Follow-up item"""
    company: str
    role: str
    applied_date: str
    days_since: int
    status: str


class FollowUpsResponse(BaseModel):
    """Follow-ups response"""
    followups: List[FollowUpItem]
    count: int


class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
