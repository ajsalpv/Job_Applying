"""
Job Scoring Agent - LangGraph-based scoring with tool calling
Uses ReAct pattern for intelligent job evaluation
"""
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.agents.base_agent import LangGraphAgent, AgentResult
from app.config.prompts import JOB_SCORING_SYSTEM, JOB_SCORING_USER
from app.config.constants import (
    SCORING_WEIGHTS, USER_SKILLS, EXCLUDED_SKILLS,
    TARGET_JOB_TITLES, EXCLUDED_JOB_TITLES,
    USER_EXPERIENCE_YEARS,
)
from app.config.settings import get_settings


# Define tools for the scoring agent
@tool
def calculate_skill_match(job_skills: List[str], required_skills: List[str]) -> Dict[str, Any]:
    """
    Calculate how well candidate skills match job requirements.
    
    Args:
        job_skills: Skills mentioned in job description
        required_skills: Skills required for the job
        
    Returns:
        Score and matching/missing skills
    """
    user_skills_lower = [s.lower() for s in USER_SKILLS]
    matching = []
    missing = []
    
    all_job_skills = set([s.lower() for s in (job_skills + required_skills)])
    
    for skill in all_job_skills:
        if skill in user_skills_lower:
            matching.append(skill)
        else:
            # Check if it's an excluded skill (Computer Vision)
            if not any(ex.lower() in skill for ex in EXCLUDED_SKILLS):
                missing.append(skill)
    
    # Score out of 40
    if len(all_job_skills) > 0:
        match_ratio = len(matching) / len(all_job_skills)
        score = int(match_ratio * 40)
    else:
        score = 20  # Default if no skills specified
    
    return {
        "score": score,
        "max_score": 40,
        "matching_skills": matching,
        "missing_skills": missing,
        "match_percentage": round(match_ratio * 100, 1) if len(all_job_skills) > 0 else 50,
    }


@tool
def calculate_experience_match(experience_required: str) -> Dict[str, Any]:
    """
    Calculate if experience level matches candidate's experience.
    
    Args:
        experience_required: Experience requirement string (e.g., "2-4 years")
        
    Returns:
        Score and analysis
    """
    user_exp = USER_EXPERIENCE_YEARS
    exp_lower = experience_required.lower() if experience_required else ""
    
    score = 0
    analysis = ""
    
    if not exp_lower or "not specified" in exp_lower:
        score = 15
        analysis = "Experience not specified, assuming moderate fit"
    elif any(x in exp_lower for x in ["0", "fresher", "entry", "graduate"]):
        score = 25  # Perfect for 2 years exp
        analysis = "Entry level - good fit for 2 years experience"
    elif "1" in exp_lower or "1-2" in exp_lower or "0-2" in exp_lower:
        score = 25
        analysis = "Perfect experience match"
    elif "2" in exp_lower or "1-3" in exp_lower or "2-3" in exp_lower:
        score = 23
        analysis = "Excellent experience match"
    elif "3" in exp_lower or "2-4" in exp_lower or "2-5" in exp_lower:
        score = 18
        analysis = "Slightly above experience but can apply"
    elif "4" in exp_lower or "5" in exp_lower or "5+" in exp_lower:
        score = 8
        analysis = "Senior role - may be too experienced requirement"
    else:
        score = 12
        analysis = "Unable to parse experience requirement"
    
    return {
        "score": score,
        "max_score": 25,
        "user_experience": user_exp,
        "required": experience_required,
        "analysis": analysis,
    }


@tool
def calculate_location_match(job_location: str) -> Dict[str, Any]:
    """
    Calculate if job location matches candidate preferences.
    
    Args:
        job_location: Job location string
        
    Returns:
        Score and analysis
    """
    loc_lower = job_location.lower() if job_location else ""
    
    score = 0
    is_remote = False
    
    # Remote - highest priority
    if "remote" in loc_lower or "wfh" in loc_lower or "work from home" in loc_lower:
        score = 15
        is_remote = True
    # Primary cities - full score
    elif "bangalore" in loc_lower or "bengaluru" in loc_lower:
        score = 15
    elif "hyderabad" in loc_lower:
        score = 15
    elif "chennai" in loc_lower:
        score = 15
    # Kerala cities - full score
    elif any(city in loc_lower for city in ["kochi", "cochin", "calicut", "kozhikode", "trivandrum", "thiruvananthapuram"]):
        score = 15
    # Hybrid
    elif "hybrid" in loc_lower:
        score = 12
    # Other Indian cities
    elif any(city in loc_lower for city in ["mumbai", "pune", "delhi", "gurgaon", "noida", "gurugram"]):
        score = 10
    elif "india" in loc_lower:
        score = 10
    else:
        score = 5  # International or unknown
    
    return {
        "score": score,
        "max_score": 15,
        "is_remote": is_remote,
        "location": job_location,
    }


@tool
def calculate_role_relevance(job_title: str) -> Dict[str, Any]:
    """
    Calculate if job title is relevant to target roles.
    
    Args:
        job_title: The job title/role
        
    Returns:
        Score and analysis
    """
    title_lower = job_title.lower()
    
    # Check for excluded roles (Computer Vision)
    for excluded in EXCLUDED_JOB_TITLES:
        if excluded.lower() in title_lower:
            return {
                "score": 0,
                "max_score": 20,
                "is_excluded": True,
                "reason": f"Excluded role type: {excluded}",
            }
    
    # Check for CV keywords
    cv_keywords = ["computer vision", "opencv", "image processing", "video"]
    if any(kw in title_lower for kw in cv_keywords):
        return {
            "score": 0,
            "max_score": 20,
            "is_excluded": True,
            "reason": "Computer Vision role - excluded",
        }
    
    # Score based on target roles
    score = 0
    matched_role = None
    
    for target in TARGET_JOB_TITLES:
        if target.lower() in title_lower:
            score = 20
            matched_role = target
            break
    
    if score == 0:
        # Partial matches
        ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "genai"]
        if any(kw in title_lower for kw in ai_keywords):
            score = 18
        elif "data scientist" in title_lower:
            score = 15
        elif "developer" in title_lower or "engineer" in title_lower:
            score = 10
        else:
            score = 5
    
    return {
        "score": score,
        "max_score": 20,
        "is_excluded": False,
        "matched_role": matched_role,
    }


@tool
def check_cv_exclusion(job_description: str, job_title: str) -> Dict[str, Any]:
    """
    Check if job should be excluded because it's a Computer Vision role.
    
    Args:
        job_description: Full job description text
        job_title: Job title
        
    Returns:
        Whether job should be excluded
    """
    text = f"{job_title} {job_description}".lower()
    
    cv_indicators = [
        "computer vision", "opencv", "image processing",
        "object detection", "yolo", "image recognition",
        "video processing", "image classification", "cnn for images",
        "image segmentation", "visual recognition"
    ]
    
    cv_count = sum(1 for ind in cv_indicators if ind in text)
    
    # If 2+ CV indicators, likely a CV role
    is_cv_role = cv_count >= 2
    
    return {
        "is_excluded": is_cv_role,
        "cv_indicator_count": cv_count,
        "reason": "Computer Vision role detected" if is_cv_role else "Not a CV role",
    }


class ScoringAgentLangGraph(LangGraphAgent):
    """
    LangGraph-based job scoring agent.
    
    Uses tools to:
    - Calculate skill match
    - Calculate experience match
    - Calculate location match
    - Calculate role relevance
    - Check CV exclusion
    """
    
    def __init__(self):
        system_prompt = """You are an expert job matching AI agent.
Your task is to evaluate job postings and calculate fit scores for a candidate.

CANDIDATE PROFILE:
- Experience: 2 years as AI/ML Developer
- Location: Bangalore, India (prefers Remote)
- Skills: Python, LangChain, LLM, RAG, TensorFlow, NLP, FastAPI, Groq
- Target Roles: AI Engineer, ML Engineer, LLM Engineer, NLP Engineer

SCORING RULES:
1. Use the provided tools to calculate each score component
2. EXCLUDE any Computer Vision roles (score = 0)
3. Total score = skill_match + experience_match + location_match + role_relevance
4. Maximum total score is 100

Always use the tools to calculate scores, don't estimate manually."""

        super().__init__("scoring", system_prompt)
        
        # Register tools
        self.add_tool(calculate_skill_match)
        self.add_tool(calculate_experience_match)
        self.add_tool(calculate_location_match)
        self.add_tool(calculate_role_relevance)
        self.add_tool(check_cv_exclusion)
    
    async def score_job(
        self,
        company: str,
        role: str,
        location: str,
        experience_required: str,
        job_description: str,
        skills_required: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Score a single job posting using LangGraph agent.
        """
        # First check CV exclusion
        cv_check = check_cv_exclusion.invoke({
            "job_description": job_description or "",
            "job_title": role,
        })
        
        if cv_check.get("is_excluded"):
            return {
                "fit_score": 0,
                "is_excluded": True,
                "reason": cv_check.get("reason"),
                "recommendation": "skip",
            }
        
        # Calculate individual scores using tools directly (faster than agent)
        skill_result = calculate_skill_match.invoke({
            "job_skills": skills_required or [],
            "required_skills": [],
        })
        
        exp_result = calculate_experience_match.invoke({
            "experience_required": experience_required or "",
        })
        
        loc_result = calculate_location_match.invoke({
            "job_location": location or "",
        })
        
        role_result = calculate_role_relevance.invoke({
            "job_title": role,
        })
        
        # Check if role is excluded
        if role_result.get("is_excluded"):
            return {
                "fit_score": 0,
                "is_excluded": True,
                "reason": role_result.get("reason"),
                "recommendation": "skip",
            }
        
        # Calculate total score
        total_score = (
            skill_result["score"] +
            exp_result["score"] +
            loc_result["score"] +
            role_result["score"]
        )
        
        # Determine recommendation
        if total_score >= 80:
            recommendation = "apply"
        elif total_score >= 60:
            recommendation = "maybe"
        else:
            recommendation = "skip"
        
        return {
            "fit_score": total_score,
            "skill_match_score": skill_result["score"],
            "experience_match_score": exp_result["score"],
            "location_match_score": loc_result["score"],
            "role_relevance_score": role_result["score"],
            "matching_skills": skill_result.get("matching_skills", []),
            "missing_skills": skill_result.get("missing_skills", []),
            "recommendation": recommendation,
            "is_excluded": False,
            "reason": f"Score breakdown: Skills {skill_result['score']}/40, "
                     f"Exp {exp_result['score']}/25, "
                     f"Location {loc_result['score']}/15, "
                     f"Role {role_result['score']}/20",
        }
    
    async def run(
        self,
        jobs: List[Dict[str, Any]],
        min_score: int = 50,
    ) -> AgentResult:
        """
        Score a list of jobs and filter by minimum score.
        """
        self.logger.info(f"Scoring {len(jobs)} jobs (min_score={min_score})")
        
        scored_jobs = []
        excluded_count = 0
        
        for job in jobs:
            try:
                result = await self.score_job(
                    company=job.get("company", ""),
                    role=job.get("role", ""),
                    location=job.get("location", ""),
                    experience_required=job.get("experience_required", ""),
                    job_description=job.get("job_description", ""),
                    skills_required=job.get("skills_required", []),
                )
                
                if result.get("is_excluded"):
                    excluded_count += 1
                    continue
                
                if result["fit_score"] >= min_score:
                    scored_jobs.append({
                        **job,
                        "fit_score": result["fit_score"],
                        "scoring_details": result,
                    })
                    
            except Exception as e:
                self.logger.error(f"Error scoring job: {e}")
                continue
        
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x.get("fit_score", 0), reverse=True)
        
        return self._success(
            data={
                "jobs": scored_jobs,
                "total_scored": len(jobs),
                "passed_filter": len(scored_jobs),
                "excluded_cv": excluded_count,
            },
            message=f"Scored {len(jobs)} jobs, {len(scored_jobs)} passed, {excluded_count} CV roles excluded"
        )


# Export as default scoring agent
scoring_agent = ScoringAgentLangGraph()
