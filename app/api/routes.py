"""
API Routes - FastAPI endpoints for job application agent
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.api.schemas import (
    JobSearchRequest,
    JobSearchResponse,
    JobListing,
    ApproveJobsRequest,
    UpdateStatusRequest,
    SettingsUpdateRequest,
    GenerateContentRequest,
    ResumeOptimization,
    CoverLetterResponse,
    ApplicationStats,
    FollowUpsResponse,
    FollowUpItem,
    APIResponse,
    JobApplicationItem,
    ApplicationListResponse,
    SchedulerStatus,
    RemoveApplicationRequest,
    EmailLogResponse,
    EmailLogItem,
)
from app.orchestrator.state_manager import WorkflowState
from app.orchestrator.scheduler import scheduler
from app.tools.utils.logger import get_logger
from app.config.settings import get_settings

logger = get_logger("api")
router = APIRouter()

# Store workflow state between requests
_workflow_state: WorkflowState = None


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "job-application-agent"}


@router.get("/settings")
async def get_app_settings():
    """Get current user settings"""
    settings = get_settings()
    return {
        "user_location": settings.user_location,
        "experience_years": settings.experience_years,
        "target_roles": settings.target_roles,
    }


@router.post("/settings", response_model=APIResponse)
async def update_app_settings(request: SettingsUpdateRequest):
    """Update user settings dynamically"""
    settings = get_settings()
    if request.user_location is not None:
        settings.user_location = request.user_location
    if request.experience_years is not None:
        settings.experience_years = request.experience_years
    if request.target_roles is not None:
        settings.target_roles = request.target_roles
    
    settings.save_dynamic_settings()
    return APIResponse(success=True, message="Settings updated and persisted")


@router.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """Search for jobs across platforms"""
    global _workflow_state
    logger.info(f"Starting job search: {request.keywords}")
    
    try:
        from app.orchestrator import run_discovery_phase
        state = await run_discovery_phase(
            keywords=request.keywords,
            locations=request.locations,
            platforms=request.platforms,
            min_score=request.min_score,
        )
        _workflow_state = state
        
        jobs = []
        for job in state.get("scored_jobs", []):
            jobs.append(JobListing(
                company=job.get("company", ""),
                role=job.get("role", ""),
                location=job.get("location", ""),
                job_url=job.get("job_url", ""),
                platform=job.get("platform", ""),
                experience_required=job.get("experience_required"),
                fit_score=job.get("fit_score"),
                scoring_details=job.get("scoring_details"),
            ))
        
        return JobSearchResponse(
            success=True,
            jobs=jobs,
            total_discovered=len(state.get("discovered_jobs", [])),
            total_scored=len(jobs),
            message=f"Found {len(jobs)} jobs matching your criteria"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications", response_model=ApplicationListResponse)
async def get_all_applications():
    """Get all applications details, sorted by date (newest first)"""
    try:
        from app.agents.tracking import tracking_agent
        apps = await tracking_agent.get_all_applications(today_only=False)
        
        # Determine sort key - prefer date and potentially time if available
        # JobApplication objects have 'date' (YYYY-MM-DD)
        # Sort descending
        apps.sort(key=lambda x: x.date, reverse=True)
        
        items = []
        for app in apps:
            # Skip excluded applications
            if app.status.value == "excluded":
                continue
                
            items.append(JobApplicationItem(
                date=app.date,
                platform=app.platform,
                company=app.company,
                role=app.role,
                location=app.location,
                fit_score=app.fit_score,
                status=app.status.value,
                job_url=app.job_url,
                job_description=app.job_description,
                interview_prep=app.interview_prep,
                skills_to_learn=app.skills_to_learn,
                posted_at=app.posted_at,
                applied_at=app.applied_at,
                notes=app.notes,
            ))
            
        return ApplicationListResponse(applications=items, count=len(items))
    except Exception as e:
        logger.error(f"Get applications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/status", response_model=APIResponse)
async def update_status(request: UpdateStatusRequest):
    """Update application status"""
    try:
        from app.agents.tracking import tracking_agent
        success = await tracking_agent.update_status(
            company=request.company,
            role=request.role,
            new_status=request.status,
            notes=request.notes or "",
        )
        return APIResponse(success=success, message="Status updated")
    except Exception as e:
        logger.error(f"Status update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/remove", response_model=APIResponse)
async def remove_application(request: RemoveApplicationRequest):
    """Remove application by marking it as excluded"""
    try:
        from app.agents.tracking import tracking_agent
        from app.config.constants import ApplicationStatus
        success = await tracking_agent.update_status(
            company=request.company,
            role=request.role,
            new_status=ApplicationStatus.EXCLUDED.value,
            notes="Removed by user from app",
        )
        return APIResponse(success=success, message="Application removed")
    except Exception as e:
        logger.error(f"Remove application error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email/logs", response_model=EmailLogResponse)
async def get_email_logs():
    """Get history of sent emails"""
    try:
        import os
        import json
        log_path = "app/data/email_logs.json"
        
        if not os.path.exists(log_path):
            return EmailLogResponse(logs=[], count=0)
            
        with open(log_path, 'r') as f:
            logs = json.load(f)
            
        return EmailLogResponse(logs=[EmailLogItem(**log) for log in logs], count=len(logs))
    except Exception as e:
        logger.error(f"Get email logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/by-platform/{platform}")
async def get_jobs_by_platform(platform: str):
    """Get all tracked jobs filtered by platform, newest first"""
    try:
        from app.agents.tracking import tracking_agent
        all_apps = await tracking_agent.get_all_applications(today_only=False)
        
        filtered = [app for app in all_apps if app.platform.lower() == platform.lower()]
        filtered.sort(key=lambda x: x.date, reverse=True)
        
        items = [
            {
                "date": app.date,
                "platform": app.platform,
                "company": app.company,
                "role": app.role,
                "location": app.location,
                "fit_score": app.fit_score,
                "status": app.status.value,
                "job_url": app.job_url,
                "job_description": app.job_description,
                "interview_prep": app.interview_prep,
                "skills_to_learn": app.skills_to_learn,
                "posted_at": app.posted_at,
                "applied_at": app.applied_at,
                "notes": app.notes,
            }
            for app in filtered
        ]
        
        return {"platform": platform, "jobs": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Jobs by platform error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/stats", response_model=ApplicationStats)
async def get_stats():
    """Get stats"""
    try:
        from app.agents.tracking import tracking_agent
        stats = await tracking_agent.get_statistics()
        return ApplicationStats(**stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Administrative routes
@router.get("/scheduler/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    return SchedulerStatus(running=scheduler._running, interval_minutes=scheduler.settings.check_interval_minutes)

@router.post("/scheduler/start")
async def start_scheduler():
    await scheduler.start()
    return {"message": "Scheduler started"}

@router.post("/scheduler/stop")
async def stop_scheduler():
    await scheduler.stop()
    return {"message": "Scheduler stopped"}

@router.post("/jobs/scan", response_model=APIResponse)
async def scan_now(background_tasks: BackgroundTasks):
    from app.config.settings import get_settings
    settings = get_settings()
    async def run_scan():
        from app.orchestrator import run_discovery_phase
        await run_discovery_phase(locations=settings.user_location.split(","), keywords=settings.target_roles)
    background_tasks.add_task(run_scan)
    return APIResponse(success=True, message="Job discovery scan started")

@router.get("/supervisor/status")
async def supervisor_status():
    from app.agents.supervisor_agent import supervisor
    return supervisor.get_health_report()

@router.post("/supervisor/re-enable/{platform}")
async def re_enable_platform(platform: str):
    from app.agents.supervisor_agent import supervisor
    supervisor.re_enable_platform(platform)
    return {"success": True, "message": f"{platform} re-enabled"}
