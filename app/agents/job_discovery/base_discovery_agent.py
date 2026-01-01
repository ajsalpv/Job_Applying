"""
Intelligent Job Discovery Base - LangGraph-powered job scraping with tools
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool, StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, END
from app.agents.base_agent import AgentResult
from app.config.settings import get_settings
from app.config.constants import (
    EXCLUDED_JOB_TITLES, EXCLUDED_SKILLS, TARGET_JOB_TITLES,
    USER_EXPERIENCE_YEARS, USER_SKILLS,
)
from app.tools.browser import playwright_manager
from app.tools.utils.logger import get_logger
from app.tools.utils.rate_limiter import rate_limiter


class IntelligentJobDiscoveryAgent(ABC):
    """
    Base class for intelligent job discovery agents.
    
    Uses LangGraph with tools for:
    - Smart query optimization
    - Intelligent job filtering
    - Automatic CV role exclusion
    - Experience level matching
    - Quality validation
    """
    
    def __init__(self, platform: str, base_url: str):
        self.platform = platform
        self.base_url = base_url
        self.settings = get_settings()
        self.logger = get_logger(f"agent.discovery.{platform}")
        
        # Initialize LLMs
        self.llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.settings.fast_model,
            temperature=0.1,
        )
        
        self.smart_llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.settings.smart_model,
            temperature=0.3,
        )
        
        # Build tools
        self._tools = self._build_tools()
        
        # Build agent
        self._agent = self._build_agent()
    
    def _build_tools(self) -> List:
        """Build tools for this agent"""
        return [
            self._create_search_tool(),
            self._create_filter_tool(),
            self._create_validate_tool(),
            self._create_extract_jd_tool(),
        ]
    
    def _create_search_tool(self):
        """Create the search tool"""
        platform = self.platform
        base_url = self.base_url
        logger = self.logger
        
        @tool
        async def search_jobs_on_platform(
            keywords: str,
            location: str,
            experience_level: str = "1-3 years",
        ) -> Dict[str, Any]:
            """
            Search for jobs on the platform using browser automation.
            
            Args:
                keywords: Job search keywords
                location: Job location
                experience_level: Experience requirement filter
                
            Returns:
                Raw job listings from the platform
            """
            logger.info(f"Searching {platform}: {keywords} in {location}")
            
            try:
                await rate_limiter.acquire(platform)
                
                async with playwright_manager.get_page() as page:
                    # Build search URL
                    search_url = f"{base_url}?q={keywords}&l={location}"
                    await playwright_manager.navigate(page, search_url)
                    
                    # Wait for job listings
                    await page.wait_for_timeout(3000)
                    
                    # Extract raw job data
                    jobs = await page.evaluate("""
                        () => {
                            const jobs = [];
                            const cards = document.querySelectorAll(
                                '[class*="job"], [class*="Job"], [data-job], .posting'
                            );
                            
                            cards.forEach((card, idx) => {
                                if (idx < 25) {
                                    const titleEl = card.querySelector('h2, h3, [class*="title"]');
                                    const companyEl = card.querySelector('[class*="company"]');
                                    const locationEl = card.querySelector('[class*="location"]');
                                    const linkEl = card.querySelector('a[href*="job"]');
                                    
                                    if (titleEl) {
                                        jobs.push({
                                            role: titleEl.textContent?.trim() || '',
                                            company: companyEl?.textContent?.trim() || '',
                                            location: locationEl?.textContent?.trim() || '',
                                            job_url: linkEl?.href || '',
                                        });
                                    }
                                }
                            });
                            
                            return jobs;
                        }
                    """)
                    
                    return {
                        "success": True,
                        "jobs": jobs,
                        "count": len(jobs),
                        "platform": platform,
                    }
                    
            except Exception as e:
                logger.error(f"Search failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "jobs": [],
                    "count": 0,
                }
        
        return search_jobs_on_platform
    
    def _create_filter_tool(self):
        """Create intelligent filtering tool"""
        
        @tool
        def filter_relevant_jobs(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
            """
            Intelligently filter jobs to remove irrelevant listings.
            
            Filters out:
            - Computer Vision roles
            - Senior roles (5+ years)
            - Non-AI/ML roles
            - Duplicate listings
            
            Args:
                jobs: Raw job listings
                
            Returns:
                Filtered jobs with quality scores
            """
            filtered = []
            excluded_count = 0
            seen_urls = set()
            
            for job in jobs:
                role = job.get("role", "").lower()
                company = job.get("company", "")
                job_url = job.get("job_url", "")
                
                # Skip duplicates
                if job_url in seen_urls:
                    continue
                seen_urls.add(job_url)
                
                # Check for CV exclusion
                is_cv_role = any(
                    ex.lower() in role 
                    for ex in EXCLUDED_JOB_TITLES + EXCLUDED_SKILLS
                )
                if is_cv_role or "computer vision" in role or "opencv" in role:
                    excluded_count += 1
                    continue
                
                # Check for senior roles
                is_senior = any(
                    kw in role 
                    for kw in ["senior", "staff", "principal", "lead", "director", "vp"]
                )
                if is_senior:
                    excluded_count += 1
                    continue
                
                # Check relevance to AI/ML
                ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning",
                              "data scientist", "genai", "generative"]
                is_relevant = any(kw in role for kw in ai_keywords)
                
                if not is_relevant:
                    # Check if it's a generic engineering role
                    if "engineer" in role or "developer" in role:
                        is_relevant = True  # Include generic titles for now
                
                if is_relevant:
                    # Add quality score
                    quality_score = 50  # Base score
                    
                    # Boost for target titles
                    for target in TARGET_JOB_TITLES:
                        if target.lower() in role:
                            quality_score += 30
                            break
                    
                    # Boost for AI keywords
                    if any(kw in role for kw in ["llm", "genai", "langchain"]):
                        quality_score += 20
                    
                    job["quality_score"] = min(quality_score, 100)
                    job["platform"] = job.get("platform", "unknown")
                    filtered.append(job)
            
            # Sort by quality score
            filtered.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            
            return {
                "jobs": filtered,
                "filtered_count": len(filtered),
                "excluded_count": excluded_count,
                "message": f"Filtered to {len(filtered)} relevant jobs, excluded {excluded_count}",
            }
        
        return filter_relevant_jobs
    
    def _create_validate_tool(self):
        """Create job validation tool"""
        
        @tool
        def validate_job_listing(
            role: str,
            company: str,
            location: str,
        ) -> Dict[str, Any]:
            """
            Validate if a job listing is worth pursuing.
            
            Args:
                role: Job title
                company: Company name
                location: Job location
                
            Returns:
                Validation result with recommendation
            """
            issues = []
            score = 100
            
            # Check role
            if not role or len(role) < 3:
                issues.append("Invalid role title")
                score -= 30
            
            # Check company
            if not company or len(company) < 2:
                issues.append("Missing company name")
                score -= 20
            
            # Check for blacklisted patterns
            role_lower = role.lower()
            if any(kw in role_lower for kw in ["intern", "trainee", "fresher only"]):
                issues.append("Position level mismatch")
                score -= 40
            
            # Check location preference
            loc_lower = location.lower() if location else ""
            location_match = any(
                pref in loc_lower 
                for pref in ["remote", "bangalore", "bengaluru", "india", "hybrid"]
            )
            if not location_match and location:
                issues.append("Location may not match preference")
                score -= 10
            
            # Determine recommendation
            if score >= 80:
                recommendation = "apply"
            elif score >= 50:
                recommendation = "review"
            else:
                recommendation = "skip"
            
            return {
                "is_valid": score >= 50,
                "score": max(0, score),
                "issues": issues,
                "recommendation": recommendation,
            }
        
        return validate_job_listing
    
    def _create_extract_jd_tool(self):
        """Create JD extraction tool"""
        logger = self.logger
        
        @tool
        async def extract_job_description(job_url: str) -> Dict[str, Any]:
            """
            Extract full job description from job URL.
            
            Args:
                job_url: URL of the job posting
                
            Returns:
                Extracted job description and details
            """
            if not job_url:
                return {"success": False, "error": "No URL provided"}
            
            try:
                async with playwright_manager.get_page() as page:
                    await playwright_manager.navigate(page, job_url)
                    await page.wait_for_timeout(2000)
                    
                    # Extract job description
                    jd = await page.evaluate("""
                        () => {
                            const selectors = [
                                '[class*="description"]',
                                '[class*="job-details"]',
                                '[class*="jobDescription"]',
                                '.job-description',
                                '#job-description',
                                'article',
                            ];
                            
                            for (const sel of selectors) {
                                const el = document.querySelector(sel);
                                if (el && el.textContent.length > 100) {
                                    return el.textContent.trim().slice(0, 3000);
                                }
                            }
                            
                            return document.body.textContent.slice(0, 2000);
                        }
                    """)
                    
                    # Extract skills
                    skills = []
                    skill_keywords = [
                        "python", "langchain", "pytorch", "tensorflow", "nlp",
                        "llm", "ml", "deep learning", "fastapi", "aws", "docker"
                    ]
                    jd_lower = jd.lower()
                    for skill in skill_keywords:
                        if skill in jd_lower:
                            skills.append(skill.title())
                    
                    return {
                        "success": True,
                        "job_description": jd,
                        "skills_found": skills,
                        "description_length": len(jd),
                    }
                    
            except Exception as e:
                logger.error(f"JD extraction failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "job_description": "",
                }
        
        return extract_job_description
    
    def _build_agent(self):
        """Build the LangGraph ReAct agent"""
        system_prompt = f"""You are an intelligent job discovery agent for {self.platform}.

Your goal is to find the best AI/ML job opportunities for:
- Name: Ajsal PV
- Experience: {USER_EXPERIENCE_YEARS} years
- Target: AI Engineer, ML Engineer, LLM Engineer, NLP Engineer
- Location: Bangalore, India (Remote preferred)
- Skills: {', '.join(USER_SKILLS[:10])}

IMPORTANT RULES:
1. EXCLUDE all Computer Vision roles
2. EXCLUDE Senior positions (5+ years required)
3. PRIORITIZE LLM/GenAI roles
4. VALIDATE each listing before including

Use your tools intelligently to search, filter, and validate jobs."""

        return create_react_agent(
            model=self.llm,
            tools=self._tools,
            prompt=system_prompt,
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Discover jobs using intelligent agent.
        """
        self.logger.info(f"Intelligent discovery: {keywords} in {location}")
        
        # Use tools directly for reliability
        search_tool = self._tools[0]
        filter_tool = self._tools[1]
        
        # Search
        search_result = await search_tool.ainvoke({
            "keywords": keywords,
            "location": location,
            "experience_level": f"{USER_EXPERIENCE_YEARS} years",
        })
        
        if not search_result.get("success"):
            self.logger.error(f"Search failed: {search_result.get('error')}")
            return []
        
        jobs = search_result.get("jobs", [])
        
        # Add platform info
        for job in jobs:
            job["platform"] = self.platform
        
        # Filter
        filter_result = filter_tool.invoke({"jobs": jobs})
        filtered_jobs = filter_result.get("jobs", [])[:max_results]
        
        self.logger.info(
            f"Found {len(jobs)} jobs, filtered to {len(filtered_jobs)} relevant listings"
        )
        
        return filtered_jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        """
        Run the job discovery agent.
        """
        if not keywords:
            keywords = "AI Engineer"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Discovered {len(jobs)} relevant jobs on {self.platform}",
            )
            
        except Exception as e:
            self.logger.error(f"Discovery failed: {e}")
            return AgentResult(
                success=False,
                error=str(e),
                message=f"Failed to discover jobs: {e}",
            )
