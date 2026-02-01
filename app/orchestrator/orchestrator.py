"""
Orchestrator - LangGraph workflow for job application pipeline
"""
import asyncio
from typing import Dict, Any, List
from app.orchestrator.state_manager import (
    WorkflowState,
    WorkflowStep,
    create_initial_state,
    update_state,
    add_error,
)
# Delayed imports for memory efficiency on Cloud
# Heavy agent imports moved inside functions to prevent OOM on startup
from app.tools.utils.logger import get_logger

logger = get_logger("orchestrator")

# Constants for platform discovery
PLATFORM_AGENTS = {
    "linkedin": "linkedin_agent",
    "indeed": "indeed_agent",
    "naukri": "naukri_agent",
    "glassdoor": "glassdoor_agent",
    "instahyre": "instahyre_agent",
    "cutshort": "cutshort_agent",
    "wellfound": "wellfound_agent",
    "hirist": "hirist_agent",
}

def get_platform_agent(name: str):
    """Lazy load discovery agents to save RAM"""
    from app.agents.job_discovery import (
        linkedin_agent, indeed_agent, naukri_agent,
        glassdoor_agent, instahyre_agent, cutshort_agent,
        wellfound_agent, hirist_agent
    )
    mapping = {
        "linkedin": linkedin_agent,
        "indeed": indeed_agent,
        "naukri": naukri_agent,
        "glassdoor": glassdoor_agent,
        "instahyre": instahyre_agent,
        "cutshort": cutshort_agent,
        "wellfound": wellfound_agent,
        "hirist": hirist_agent,
    }
    return mapping.get(name)


# ============================================================
# NODE FUNCTIONS
# ============================================================

async def discover_jobs(state: WorkflowState) -> WorkflowState:
    """Node: Discover jobs from all platforms in parallel"""
    logger.info("Starting parallel job discovery with persistent deduplication")
    
    from app.config.settings import get_settings
    settings = get_settings()
    
    # Use state values if available, otherwise use defaults from settings
    platforms = state.get("platforms") or list(PLATFORM_AGENTS.keys())
    raw_keywords = state.get("keywords") or settings.target_roles
    
    # Parse multiple keywords
    keywords_list = [k.strip() for k in raw_keywords.split(",")] if "," in raw_keywords else [raw_keywords]
    
    # Get locations (state or settings)
    locations = state.get("locations")
    if not locations:
        locations = [l.strip() for l in settings.user_location.split(",")]
    
    # LOAD PERSISTENT SEEN URLS
    import os, json
    data_dir = "app/data"
    os.makedirs(data_dir, exist_ok=True)
    seen_urls_path = os.path.join(data_dir, "seen_urls.json")
    
    seen_urls = set()
    if os.path.exists(seen_urls_path):
        try:
            with open(seen_urls_path, 'r') as f:
                seen_urls = set(json.load(f))
            logger.info(f"Loaded {len(seen_urls)} already seen URLs from cache")
        except Exception as e:
            logger.warning(f"Could not load seen_urls cache: {e}")

    all_jobs = []
    
    # Limit concurrency to 1 platform at once to avoid OOM on Render Free tier (512MB RAM)
    semaphore = asyncio.Semaphore(1)
    
    # Run for each platform
    async def search_platform(platform_name: str):
        async with semaphore:
            platform_jobs = []
            agent = get_platform_agent(platform_name)

            if not agent:
                logger.warning(f"Unknown platform: {platform_name}")
                return []
                
            for location in locations:
                for keyword in keywords_list:
                    try:
                        logger.info(f"🔍 [{platform_name}] Searching '{keyword}' in {location}...")
                        result = await agent.run(keywords=keyword, location=location)
                        
                        if result.success and result.data:
                            jobs = result.data.get("jobs", [])
                            new_count = 0
                            for job in jobs:
                                url = job.get("job_url")
                                if url and url not in seen_urls:
                                    seen_urls.add(url)
                                    platform_jobs.append(job)
                                    new_count += 1
                            
                            logger.info(f"✅ {platform_name} found {len(jobs)} jobs ({new_count} new) for '{keyword}' in {location}")
                    except Exception as e:
                        logger.error(f"❌ Error on {platform_name} for {keyword} in {location}: {e}")
            
            # Explicitly kill browser after this platform to free all RAM for the next platform
            from app.tools.browser import playwright_manager
            await playwright_manager.close()
            
            return platform_jobs

    logger.info(f"📍 Target Locations: {', '.join(locations)}")
    # Run searches for all platforms - semaphore ensures they run one-by-one
    logger.info(f"🚀 Triggering search on {len(platforms)} platforms: {', '.join(platforms)}")
    search_tasks = [search_platform(p) for p in platforms]
    results = await asyncio.gather(*search_tasks)
    
    # Combined results
    for platform_result in results:
        all_jobs.extend(platform_result)
    
    # SAVE PERSISTENT SEEN URLS
    try:
        with open(seen_urls_path, 'w') as f:
            json.dump(list(seen_urls), f)
        logger.info(f"Saved {len(seen_urls)} seen URLs to cache")
    except Exception as e:
        logger.error(f"Failed to save seen_urls cache: {e}")

    logger.info(f"📊 Total discovery complete: {len(all_jobs)} NEW unique jobs found")
    
    return update_state(state, {
        "discovered_jobs": all_jobs,
        "current_step": WorkflowStep.SCORING.value,
    })



async def score_jobs(state: WorkflowState) -> WorkflowState:
    """Node: Score and filter discovered jobs"""
    logger.info("Scoring jobs")
    
    jobs = state.get("discovered_jobs", [])
    min_score = state.get("min_score", 70)
    
    if not jobs:
        return update_state(state, {
            "current_step": WorkflowStep.COMPLETE.value,
            "errors": state.get("errors", []) + ["No jobs to score"],
        })
    
    try:
        from app.agents.job_scoring import scoring_agent
        result = await scoring_agent.run(jobs=jobs, min_score=min_score)
        
        if result.success:
            scored = result.data.get("jobs", [])
            logger.info(f"Scored {len(jobs)} jobs, {len(scored)} passed filter")
            
            return update_state(state, {
                "scored_jobs": scored,
                "jobs_for_review": scored,  # All scored jobs need review
                "current_step": WorkflowStep.HUMAN_REVIEW.value,
            })
    
    except Exception as e:
        logger.error(f"Scoring error: {e}")
        return add_error(state, f"Scoring: {str(e)}")
    
    return state


async def generate_resume_content(state: WorkflowState) -> WorkflowState:
    """Node: Generate optimized resume content"""
    logger.info("Generating resume content")
    
    approved_urls = state.get("approved_jobs", [])
    scored_jobs = state.get("scored_jobs", [])
    
    # Filter to approved jobs only
    approved_jobs = [j for j in scored_jobs if j.get("job_url") in approved_urls]
    
    if not approved_jobs:
        logger.info("No approved jobs for resume generation")
        return update_state(state, {
            "current_step": WorkflowStep.COMPLETE.value,
        })
    
    try:
        from app.agents.resume_generator import resume_agent
        result = await resume_agent.run(jobs=approved_jobs)
        
        if result.success:
            optimizations = result.data.get("optimizations", [])
            return update_state(state, {
                "resume_optimizations": optimizations,
                "current_step": WorkflowStep.COVER_LETTER_GEN.value,
            })
            
    except Exception as e:
        logger.error(f"Resume generation error: {e}")
        return add_error(state, f"Resume: {str(e)}")
    
    return state


async def generate_cover_letters(state: WorkflowState) -> WorkflowState:
    """Node: Generate cover letters"""
    logger.info("Generating cover letters")
    
    approved_urls = state.get("approved_jobs", [])
    scored_jobs = state.get("scored_jobs", [])
    approved_jobs = [j for j in scored_jobs if j.get("job_url") in approved_urls]
    
    if not approved_jobs:
        return update_state(state, {
            "current_step": WorkflowStep.APPLICATION_PREP.value,
        })
    
    try:
        from app.agents.resume_generator import cover_letter_agent
        result = await cover_letter_agent.run(jobs=approved_jobs)
        
        if result.success:
            letters = result.data.get("cover_letters", [])
            return update_state(state, {
                "cover_letters": letters,
                "current_step": WorkflowStep.APPLICATION_PREP.value,
            })
            
    except Exception as e:
        logger.error(f"Cover letter error: {e}")
        return add_error(state, f"Cover letter: {str(e)}")
    
    return state


async def prepare_applications(state: WorkflowState) -> WorkflowState:
    """Node: Prepare application forms (human review required)"""
    logger.info("Preparing applications")
    
    approved_urls = state.get("approved_jobs", [])
    scored_jobs = state.get("scored_jobs", [])
    approved_jobs = [j for j in scored_jobs if j.get("job_url") in approved_urls]
    
    if not approved_jobs:
        return update_state(state, {
            "current_step": WorkflowStep.TRACKING.value,
        })
    
    try:
        from app.agents.application_assistant import application_agent
        result = await application_agent.run(jobs=approved_jobs)
        
        if result.success:
            preps = result.data.get("preparations", [])
            return update_state(state, {
                "prepared_applications": preps,
                "current_step": WorkflowStep.TRACKING.value,
            })
            
    except Exception as e:
        logger.error(f"Application prep error: {e}")
        return add_error(state, f"Application: {str(e)}")
    
    return state


async def track_applications(state: WorkflowState) -> WorkflowState:
    """Node: Log applications to tracking sheet"""
    logger.info("Tracking applications")
    
    scored_jobs = state.get("scored_jobs", [])
    
    for job in scored_jobs:
        try:
            from app.agents.tracking import tracking_agent
            await tracking_agent.log_application(
                company=job.get("company", ""),
                role=job.get("role", ""),
                platform=job.get("platform", ""),
                job_url=job.get("job_url", ""),
                fit_score=job.get("fit_score", 0),
                location=job.get("location", ""),
                experience_required=job.get("experience_required", ""),
            )
        except Exception as e:
            logger.error(f"Tracking error for {job.get('company')}: {e}")
    
    return update_state(state, {
        "current_step": WorkflowStep.COMPLETE.value,
    })


# ============================================================
# CONDITIONAL EDGES
# ============================================================

def should_continue(state: WorkflowState) -> str:
    """Determine next step based on current state"""
    step = state.get("current_step", WorkflowStep.INIT.value)
    
    if step == WorkflowStep.COMPLETE.value:
        return "end"
    elif step == WorkflowStep.HUMAN_REVIEW.value:
        return "wait_for_review"
    else:
        return "continue"


def route_after_scoring(state: WorkflowState) -> str:
    """Route after scoring: to review or end"""
    scored = state.get("scored_jobs", [])
    if not scored:
        return "end"
    return "human_review"


def route_after_review(state: WorkflowState) -> str:
    """Route after human review"""
    approved = state.get("approved_jobs", [])
    if not approved:
        return "track"  # Still track discovered jobs
    return "resume"


# ============================================================
# BUILD GRAPH
# ============================================================

def create_workflow() -> "StateGraph":
    """
    Create the LangGraph workflow.
    """
    from langgraph.graph import StateGraph, END
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("discover", discover_jobs)
    workflow.add_node("score", score_jobs)
    workflow.add_node("resume", generate_resume_content)
    workflow.add_node("cover_letter", generate_cover_letters)
    workflow.add_node("prepare", prepare_applications)
    workflow.add_node("track", track_applications)
    
    # Set entry point
    workflow.set_entry_point("discover")
    
    workflow.add_edge("discover", "score")
    workflow.add_edge("score", "track")
    workflow.add_edge("resume", "cover_letter")
    workflow.add_edge("cover_letter", "prepare")
    workflow.add_edge("prepare", "track")
    workflow.add_edge("track", END)

    return workflow

# Global for lazy compilation
_job_workflow = None

def get_job_workflow():
    """Lazy compile job workflow to save memory"""
    global _job_workflow
    if _job_workflow is None:
        _job_workflow = create_workflow().compile()
    return _job_workflow


# Compiled workflow (Now lazy)
# job_workflow = get_job_workflow()


async def run_discovery_phase(
    keywords: str = "AI Engineer",
    locations: List[str] = None,
    platforms: List[str] = None,
    min_score: int = 70,
) -> WorkflowState:
    """
    Run the discovery and scoring phase.
    
    Returns state with jobs ready for human review.
    """
    initial_state = create_initial_state(
        keywords=keywords,
        locations=locations,
        platforms=platforms,
        min_score=min_score,
    )
    
    # Run until human review pause
    workflow = get_job_workflow()
    result = await workflow.ainvoke(initial_state)
    
    return result


async def run_application_phase(
    state: WorkflowState,
    approved_jobs: List[str],
) -> WorkflowState:
    """
    Continue workflow after human review.
    
    Args:
        state: State from discovery phase
        approved_jobs: List of job URLs approved by user
        
    Returns:
        Final workflow state
    """
    # Update state with approved jobs
    state = update_state(state, {
        "approved_jobs": approved_jobs,
        "current_step": WorkflowStep.RESUME_GEN.value,
    })
    
    # Run remaining phases manually
    state = await generate_resume_content(state)
    state = await generate_cover_letters(state)
    state = await prepare_applications(state)
    state = await track_applications(state)
    
    return state
