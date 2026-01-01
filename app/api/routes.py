"""
API Routes - FastAPI endpoints for job application agent
"""
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.api.schemas import (
    JobSearchRequest,
    JobSearchResponse,
    JobListing,
    ApproveJobsRequest,
    UpdateStatusRequest,
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
)
from app.orchestrator import run_discovery_phase, run_application_phase, WorkflowState
from app.orchestrator.scheduler import scheduler
from app.agents.job_scoring import scoring_agent
from app.agents.resume_generator import resume_agent, cover_letter_agent
from app.agents.tracking import tracking_agent
from app.tools.utils.logger import get_logger

logger = get_logger("api")
router = APIRouter()

# Store workflow state between requests (in production, use Redis/database)
_workflow_state: WorkflowState = None


@router.get("/health")
async def health_check():
    """Health check endpoint with loop info"""
    import asyncio
    loop = asyncio.get_running_loop()
    return {
        "status": "healthy", 
        "service": "job-application-agent",
        "loop": type(loop).__name__
    }



@router.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """
    Search for jobs across platforms.
    
    This starts the discovery phase and scores jobs.
    Returns jobs ready for human review.
    """
    global _workflow_state
    
    logger.info(f"Starting job search: {request.keywords}")
    
    try:
        # Run discovery phase
        state = await run_discovery_phase(
            keywords=request.keywords,
            locations=request.locations,
            platforms=request.platforms,
            min_score=request.min_score,
        )
        
        _workflow_state = state
        
        # Convert to response format
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


@router.post("/jobs/approve", response_model=APIResponse)
async def approve_jobs(request: ApproveJobsRequest, background_tasks: BackgroundTasks):
    """
    Approve jobs for application.
    
    This triggers resume/cover letter generation for approved jobs.
    """
    global _workflow_state
    
    if not _workflow_state:
        raise HTTPException(status_code=400, detail="No active job search. Run search first.")
    
    logger.info(f"Approving {len(request.job_urls)} jobs")
    
    try:
        # Continue workflow with approved jobs
        _workflow_state = await run_application_phase(
            state=_workflow_state,
            approved_jobs=request.job_urls,
        )
        
        return APIResponse(
            success=True,
            message=f"Processing {len(request.job_urls)} approved jobs",
            data={
                "resume_count": len(_workflow_state.get("resume_optimizations", [])),
                "cover_letter_count": len(_workflow_state.get("cover_letters", [])),
            }
        )
        
    except Exception as e:
        logger.error(f"Approval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume/generate", response_model=ResumeOptimization)
async def generate_resume(request: GenerateContentRequest):
    """Generate optimized resume bullets for a specific job"""
    try:
        result = await resume_agent.generate_optimized_bullets(
            company=request.company,
            role=request.role,
            job_description=request.job_description,
        )
        
        return ResumeOptimization(
            company=request.company,
            role=request.role,
            optimized_bullets=result.get("optimized_bullets", []),
            keywords_included=result.get("keywords_included", []),
            skill_highlights=result.get("skill_highlights", []),
        )
        
    except Exception as e:
        logger.error(f"Resume generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cover-letter/generate", response_model=CoverLetterResponse)
async def generate_cover_letter(request: GenerateContentRequest):
    """Generate a cover letter for a specific job"""
    try:
        letter = await cover_letter_agent.generate_cover_letter(
            company=request.company,
            role=request.role,
            job_description=request.job_description,
        )
        
        return CoverLetterResponse(
            company=request.company,
            role=request.role,
            cover_letter=letter,
        )
        
    except Exception as e:
        logger.error(f"Cover letter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/stats", response_model=ApplicationStats)
async def get_stats():
    """Get application statistics"""
    try:
        stats = await tracking_agent.get_statistics()
        
        return ApplicationStats(
            total_discovered=stats.get("total_discovered", 0),
            total_applied=stats.get("total_applied", 0),
            interviews=stats.get("interviews", 0),
            offers=stats.get("offers", 0),
            rejected=stats.get("rejected", 0),
            no_response=stats.get("no_response", 0),
            success_rate=stats.get("success_rate", 0.0),
        )
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/followups", response_model=FollowUpsResponse)
async def get_followups(days_threshold: int = 7):
    """Get applications needing follow-up"""
    try:
        followups = await tracking_agent.get_pending_followups(days_threshold)
        
        items = [
            FollowUpItem(
                company=f.get("company", ""),
                role=f.get("role", ""),
                applied_date=f.get("applied_date", ""),
                days_since=f.get("days_since", 0),
                status=f.get("status", ""),
            )
            for f in followups
        ]
        
        return FollowUpsResponse(followups=items, count=len(items))
        
    except Exception as e:
        logger.error(f"Followups error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/status", response_model=APIResponse)
async def update_status(request: UpdateStatusRequest):
    """Update application status"""
    try:
        success = await tracking_agent.update_status(
            company=request.company,
            role=request.role,
            new_status=request.status,
            notes=request.notes or "",
        )
        
        return APIResponse(
            success=success,
            message="Status updated" if success else "Failed to update status",
        )
        
    except Exception as e:
        logger.error(f"Status update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications", response_model=ApplicationListResponse)
async def get_all_applications():
    """Get all applications details"""
    try:
        apps = await tracking_agent.get_all_applications()
        
        items = []
        for app in apps:
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
                notes=app.notes,
            ))
            
        return ApplicationListResponse(applications=items, count=len(items))
        
    except Exception as e:
        logger.error(f"Get all applications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    """Get scheduler status"""
    return SchedulerStatus(
        running=scheduler._running,
        interval_minutes=scheduler.settings.check_interval_minutes,
    )


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler"""
    await scheduler.start()
    return {"message": "Scheduler started"}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    await scheduler.stop()
    return {"message": "Scheduler stopped"}


@router.get("/workflow/state")
async def get_workflow_state():
    """Get current workflow state (for debugging)"""
    global _workflow_state
    
    if not _workflow_state:
        return {"state": None, "message": "No active workflow"}
    
    return {
        "state": {
            "current_step": _workflow_state.get("current_step"),
            "discovered_count": len(_workflow_state.get("discovered_jobs", [])),
            "scored_count": len(_workflow_state.get("scored_jobs", [])),
            "approved_count": len(_workflow_state.get("approved_jobs", [])),
            "errors": _workflow_state.get("errors", []),
        }
    }
