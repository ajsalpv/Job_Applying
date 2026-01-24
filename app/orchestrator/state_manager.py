"""
State Manager - Application state for LangGraph workflow
"""
from typing import List, Dict, Any, Optional, TypedDict
from enum import Enum
from app.config.constants import ApplicationStatus


class WorkflowState(TypedDict):
    """State for the job application workflow"""
    
    # User input
    keywords: str
    locations: List[str]
    platforms: List[str]
    min_score: int
    
    # Job discovery results
    discovered_jobs: List[Dict[str, Any]]
    
    # Scored jobs
    scored_jobs: List[Dict[str, Any]]
    
    # Generated content
    resume_optimizations: List[Dict[str, Any]]
    cover_letters: List[Dict[str, Any]]
    
    # Application preparations
    prepared_applications: List[Dict[str, Any]]
    
    # Status tracking
    current_step: str
    errors: List[str]
    
    # Human review queue
    jobs_for_review: List[Dict[str, Any]]
    approved_jobs: List[str]  # Job URLs approved by user


class WorkflowStep(str, Enum):
    """Workflow step names"""
    INIT = "init"
    DISCOVERY = "discovery"
    SCORING = "scoring"
    RESUME_GEN = "resume_generation"
    COVER_LETTER_GEN = "cover_letter_generation"
    APPLICATION_PREP = "application_preparation"
    HUMAN_REVIEW = "human_review"
    TRACKING = "tracking"
    COMPLETE = "complete"


def create_initial_state(
    keywords: str = "AI Engineer",
    locations: List[str] = None,
    platforms: List[str] = None,
    min_score: int = 70,
) -> WorkflowState:
    """
    Create initial workflow state.
    
    Args:
        keywords: Job search keywords
        locations: List of preferred locations
        platforms: List of platforms to search
        min_score: Minimum fit score threshold
        
    Returns:
        Initial WorkflowState
    """
    return WorkflowState(
        keywords=keywords,
        locations=locations or ["Bangalore", "Remote"],
        platforms=platforms or ["linkedin", "indeed", "naukri", "hirist", "instahyre", "cutshort", "glassdoor", "wellfound"],
        min_score=min_score,
        discovered_jobs=[],
        scored_jobs=[],
        resume_optimizations=[],
        cover_letters=[],
        prepared_applications=[],
        current_step=WorkflowStep.INIT.value,
        errors=[],
        jobs_for_review=[],
        approved_jobs=[],
    )


def update_state(
    state: WorkflowState,
    updates: Dict[str, Any],
) -> WorkflowState:
    """
    Update workflow state with new values.
    
    Args:
        state: Current state
        updates: Dictionary of updates
        
    Returns:
        Updated state
    """
    new_state = dict(state)
    new_state.update(updates)
    return WorkflowState(**new_state)


def add_error(
    state: WorkflowState,
    error: str,
) -> WorkflowState:
    """Add error to state"""
    errors = list(state.get("errors", []))
    errors.append(error)
    return update_state(state, {"errors": errors})
