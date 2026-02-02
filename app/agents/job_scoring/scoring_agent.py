"""
Job Scoring Agent - LangGraph-based scoring with tool calling
Uses ReAct pattern for intelligent job evaluation
"""
import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.agents.base_agent import LangGraphAgent, AgentResult
from app.config.prompts import (
    JOB_SCORING_SYSTEM, JOB_SCORING_USER,
    JOB_ENRICHMENT_SYSTEM, JOB_ENRICHMENT_USER
)
from app.config.constants import (
    SCORING_WEIGHTS, USER_SKILLS, EXCLUDED_SKILLS,
    TARGET_JOB_TITLES, EXCLUDED_JOB_TITLES,
    USER_EXPERIENCE_YEARS,
)
from app.tools.browser.playwright_manager import playwright_manager

# ... imports ...


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
    
    match_ratio = 0
    for skill in all_job_skills:
        if any(us in skill for us in user_skills_lower) or any(skill in us for us in user_skills_lower):
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
        score = 25  # Default if no skills specified
    
    return {
        "score": score,
        "max_score": 40,
        "matching_skills": matching,
        "missing_skills": missing,
        "match_percentage": round(match_ratio * 100, 1) if len(all_job_skills) > 0 else 60,
    }


@tool
def calculate_experience_match(experience_required: str) -> Dict[str, Any]:
    """
    Calculate if experience level matches candidate's experience (STRICT: 1 year experience - prefers 0-2 years max).
    
    Args:
        experience_required: Experience requirement string (e.g., "2-4 years")
        
    Returns:
        Score and analysis
    """
    import re
    
    user_exp = USER_EXPERIENCE_YEARS  # Now 1 year
    exp_lower = experience_required.lower() if experience_required else ""
    
    score = 0
    analysis = ""
    is_excluded = False
    
    # Extract numbers from experience string (e.g., "2-4 years" -> [2, 4])
    numbers = re.findall(r'\d+', exp_lower)
    min_exp = int(numbers[0]) if numbers else None
    max_exp = int(numbers[1]) if len(numbers) > 1 else min_exp
    
    # Keywords for fresh/entry-level
    is_fresher_role = any(kw in exp_lower for kw in ["fresher", "fresh", "entry", "intern", "trainee", "graduate"])
    is_junior = any(kw in exp_lower for kw in ["junior", "jr", "associate"])
    
    # STRICT FILTERING for 1 year experience:
    if min_exp is not None:
        if min_exp >= 3:
            # Requires 3+ years minimum - EXCLUDE
            score = 0
            analysis = f"Requires {min_exp}+ years minimum - too senior for 1 year exp"
            is_excluded = True
        elif min_exp == 0 and (max_exp is None or max_exp <= 2):
            # 0-2 years - PERFECT
            score = 25
            analysis = "Perfect match (0-2 years)"
        elif min_exp <= 1 and (max_exp is None or max_exp <= 3):
            # 0-1 or 1-2 or 1-3 years - GOOD
            score = 25
            analysis = "Good match for 1 year experience"
        elif min_exp == 2 and (max_exp is None or max_exp <= 4):
            # 2-4 years - STRETCH but acceptable
            score = 15
            analysis = "Stretch role (2+ years preferred)"
        else:
            # Anything else with high experience
            score = 0
            analysis = f"Experience requirement too high ({experience_required})"
            is_excluded = True
    elif is_fresher_role or is_junior:
        score = 25
        analysis = "Entry-level/fresher role"
    elif not exp_lower or "not specified" in exp_lower:
        score = 15
        analysis = "Experience not specified"
    else:
        score = 10
        analysis = "Experience requirement unclear"
    
    return {
        "score": score,
        "max_score": 25,
        "user_experience": user_exp,
        "required": experience_required,
        "analysis": analysis,
        "is_excluded": is_excluded
    }


@tool
def calculate_location_match(job_location: str) -> Dict[str, Any]:
    """
    Calculate if job location matches candidate preferences.
    """
    loc_lower = job_location.lower() if job_location else ""
    
    score = 0
    is_remote = False
    
    # Highest Priority Locations (Score: 15)
    high_priority_cities = [
        "bangalore", "bengaluru", "hyderabad", "chennai", 
        "kochi", "cochin", "calicut", "kozhikode", 
        "trivandrum", "thiruvananthapuram", "mohali",
        "delhi", "gurgaon", "noida", "goa"
    ]
    
    if "remote" in loc_lower or "wfh" in loc_lower or "home" in loc_lower:
        score = 15
        is_remote = True
    elif any(city in loc_lower for city in high_priority_cities):
        score = 15
    elif "hybrid" in loc_lower:
        score = 12
        # If hybrid AND in priority location, it gets 15 (logic above catches it first if city mentioned)
    elif any(city in loc_lower for city in ["mumbai", "pune", "delhi", "gurgaon", "noida", "india"]):
        score = 10
    else:
        score = 5
    
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
    """
    title_lower = job_title.lower()
    
    # Exclusion check
    for excluded in EXCLUDED_JOB_TITLES:
        if excluded.lower() in title_lower:
            return {"score": 0, "max_score": 20, "is_excluded": True, "reason": f"Excluded: {excluded}"}
    
    # CV check
    if any(kw in title_lower for kw in ["computer vision", "opencv", "image", "video"]):
        return {"score": 0, "max_score": 20, "is_excluded": True, "reason": "Computer Vision role"}

    # Relevance
    score = 0
    matched_role = None
    for target in TARGET_JOB_TITLES:
        if target.lower() in title_lower:
            score = 20
            matched_role = target
            break
    
    if score == 0:
        if any(kw in title_lower for kw in ["ai", "ml", "machine learning", "llm", "nlp", "genai"]):
            score = 18
        elif "data scientist" in title_lower:
            score = 15
        elif "engineer" in title_lower or "developer" in title_lower:
            score = 10
        else:
            score = 5
            
    return {"score": score, "max_score": 20, "is_excluded": False, "matched_role": matched_role}


class ScoringAgentLangGraph(LangGraphAgent):
    """LangGraph-based job scoring and enrichment agent."""
    
    def __init__(self):
        system_prompt = JOB_SCORING_SYSTEM.format(
            user_name="Ajsal",
            experience_years=USER_EXPERIENCE_YEARS,
            location="Bangalore/Kerala",
            skills=", ".join(USER_SKILLS[:10])
        )

        super().__init__("scoring", system_prompt)
        
        # Register tools
        self.add_tool(calculate_skill_match)
        self.add_tool(calculate_experience_match)
        self.add_tool(calculate_location_match)
        self.add_tool(calculate_role_relevance)
    
    async def _fetch_full_description(self, url: str) -> str:
        """Fetch full job description from URL if snippet is insufficient."""
        if not url or "linkedin" in url: # LinkedIn direct access often blocked
            return ""
            
        try:
            self.logger.info(f"Fetching full description from: {url}")
            async with playwright_manager.get_page() as page:
                await playwright_manager.navigate(page, url)
                
                # generic selectors for detailed description
                text = await page.evaluate("""() => {
                    const el = document.querySelector('.job-description, #job-description, .description, [class*="description"], article');
                    return el ? el.innerText : document.body.innerText;
                }""")
                return text[:5000] # Limit size
        except Exception as e:
            self.logger.warning(f"Failed to fetch full description: {e}")
            return ""
    
    async def enrich_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to generate interview prep, skills to learn, and notes."""
        try:
            description = job.get("job_description") or f"Role: {job['role']} at {job['company']} in {job['location']}. Experience: {job['experience_required']}."
            
            enrich_system = JOB_ENRICHMENT_SYSTEM.format(
                user_name="Ajsal",
                experience_years=USER_EXPERIENCE_YEARS,
                skills=", ".join(USER_SKILLS[:10])
            )
            
            enrich_user = JOB_ENRICHMENT_USER.format(
                company=job.get("company", "Unknown"),
                role=job.get("role", "Unknown"),
                job_description=description
            )
            
            # Simple LLM call instead of full graph for speed
            response = await self.llm.ainvoke([
                {"role": "system", "content": enrich_system},
                {"role": "user", "content": enrich_user}
            ])
            
            # Parse response with robust fallback
            content = response.content.strip() if response.content else ""
            
            # Skip empty responses
            if not content:
                raise ValueError("Empty LLM response")
            
            # Try multiple parsing strategies
            enrichment = None
            
            # Strategy 1: Extract from code block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                enrichment = json.loads(json_str)
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
                enrichment = json.loads(json_str)
            else:
                # Strategy 2: Find JSON object in text
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    enrichment = json.loads(json_str)
                else:
                    # Strategy 3: Try parsing entire content
                    enrichment = json.loads(content)
            
            return {
                **job,
                "interview_prep": enrichment.get("interview_prep", ""),
                "skills_to_learn": enrichment.get("skills_to_learn", ""),
                "notes": enrichment.get("notes", ""),
                "job_summary": enrichment.get("job_summary", ""),
            }
        except Exception as e:
            self.logger.error(f"Enrichment error: {e}")
            return {
                **job,
                "interview_prep": "Identify core AI concepts and company projects.",
                "skills_to_learn": "Verify skills mentioned in J/D.",
                "notes": "Fast application recommended.",
                "job_summary": job.get("role", ""),
            }

    async def score_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single job posting with strict experience filtering."""
        role = job.get("role", "")
        exp_req = job.get("experience_required", "")
        description = job.get("job_description", "")
        url = job.get("job_url", "")
        
        # 1. Role Relevance & Initial Exclusion
        role_result = calculate_role_relevance.invoke({"job_title": role})
        if role_result.get("is_excluded"):
            return {"fit_score": 0, "is_excluded": True, "reason": role_result.get("reason")}
            
        # 0. FETCH FULL DESCRIPTION if missing or short
        # We skip this for LinkedIn because it's hard to scrape directly
        # But for Indeed/Glassdoor/others it helps catch hidden experience reqs
        if (not description or len(description) < 200) and url and "linkedin" not in url:
             full_desc = await self._fetch_full_description(url)
             if full_desc:
                 description = full_desc
                 job["job_description"] = full_desc # Update job object in place
                 
        # 2. Strict Experience Check (User wants 1 year max)
        # If exp_req is missing or empty, try to find it in the description
        if (not exp_req or exp_req.lower() == "not specified") and description:
            import re
            # Look for explicit "Experience: X Years" or "X-Y Years" in description
            # Simple patterns to catch "Experience: 5 Years" or "5-8 Years experience"
            
            # Pattern 1: "Experience: 5 Years"
            exp_match = re.search(r'experience\s*:\s*(\d+)(?:\s*-\s*(\d+))?\s*y', description.lower())
            
            # Pattern 2: "5 years experience" or "5-7 years experience"
            if not exp_match:
                exp_match = re.search(r'(\d+)(?:\s*-\s*(\d+))?\s*\+?\s*years?\s*experience', description.lower())
                
            if exp_match:
                min_e = int(exp_match.group(1))
                max_e = int(exp_match.group(2)) if exp_match.group(2) else None
                
                if max_e:
                    exp_req = f"{min_e}-{max_e} years"
                else:
                    exp_req = f"{min_e} years"
                
                self.logger.info(f"Extracted experience '{exp_req}' from description for {role}")

        exp_result = calculate_experience_match.invoke({"experience_required": exp_req})
        if exp_result.get("is_excluded"):
            return {"fit_score": 0, "is_excluded": True, "reason": f"Experience too high ({exp_req}): {exp_result.get('analysis')}"}
            
        # 3. Location Match
        loc_result = calculate_location_match.invoke({"job_location": job.get("location", "")})
        
        # 4. Skill Match
        skill_result = calculate_skill_match.invoke({
            "job_skills": job.get("skills_required", []),
            "required_skills": []
        })
        
        total_score = (
            skill_result["score"] +
            exp_result["score"] +
            loc_result["score"] +
            role_result["score"]
        )
        
        recommendation = "apply" if total_score >= 80 else "maybe" if total_score >= 60 else "skip"
        
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
            "reason": f"Breakdown: Skills {skill_result['score']}/40, Exp {exp_result['score']}/25, Loc {loc_result['score']}/15, Role {role_result['score']}/20",
        }
    
    async def run(self, jobs: List[Dict[str, Any]], min_score: int = 50) -> AgentResult:
        """Score, filter, and enrich jobs."""
        self.logger.info(f"Scoring and Enriching {len(jobs)} jobs")
        
        scored_jobs = []
        excluded_count = 0
        
        for job in jobs:
            try:
                result = await self.score_job(job)
                
                if result.get("is_excluded") or result["fit_score"] < min_score:
                    excluded_count += 1
                    continue
                
                # Enrich only passing jobs to save tokens/time
                enriched_job = await self.enrich_job({
                    **job,
                    "fit_score": result["fit_score"],
                    "scoring_details": result
                })
                scored_jobs.append(enriched_job)
                    
            except Exception as e:
                self.logger.error(f"Error processing job: {e}")
                continue
        
        scored_jobs.sort(key=lambda x: x.get("fit_score", 0), reverse=True)
        
        return self._success(
            data={
                "jobs": scored_jobs,
                "total_scored": len(jobs),
                "passed_filter": len(scored_jobs),
                "excluded": excluded_count,
            },
            message=f"Found {len(scored_jobs)} high-quality matches after strict filtering and enrichment."
        )

scoring_agent = ScoringAgentLangGraph()
ScoringAgent = ScoringAgentLangGraph
