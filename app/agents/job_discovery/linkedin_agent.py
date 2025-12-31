"""
LinkedIn Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class LinkedInAgent(IntelligentJobDiscoveryAgent):
    """
    Intelligent LinkedIn job discovery agent.
    
    Uses LangGraph with specialized tools for LinkedIn's structure.
    """
    
    def __init__(self):
        super().__init__(
            platform="linkedin",
            base_url=PLATFORM_URLS.get(JobPlatform.LINKEDIN, "https://www.linkedin.com/jobs/search/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        LinkedIn-specific job discovery with intelligent filtering.
        """
        self.logger.info(f"LinkedIn search: {keywords} in {location}")
        
        await rate_limiter.acquire("linkedin")
        
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                # LinkedIn job search URL
                search_url = (
                    f"https://www.linkedin.com/jobs/search/?"
                    f"keywords={keywords.replace(' ', '%20')}"
                    f"&location={location.replace(' ', '%20')}"
                    f"&f_E=2,3"  # Entry + Associate level
                    f"&f_TPR=r604800"  # Last week
                )
                
                await playwright_manager.navigate(page, search_url)
                await page.wait_for_timeout(4000)
                
                # Scroll to load more jobs
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 1000)")
                    await page.wait_for_timeout(1000)
                
                # Extract job listings
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('.job-card-container, .jobs-search-results__list-item');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 30) {
                                const titleEl = card.querySelector('.job-card-list__title, h3');
                                const companyEl = card.querySelector('.job-card-container__primary-description, .job-card-container__company-name');
                                const locationEl = card.querySelector('.job-card-container__metadata-item, .job-card-container__metadata-wrapper');
                                const linkEl = card.querySelector('a.job-card-container__link, a[href*="/jobs/view"]');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        job_url: linkEl?.href || '',
                                        platform: 'linkedin',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                # Intelligent filtering
                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    
                    # Skip CV roles
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower or "opencv" in role_lower:
                        continue
                    
                    # Skip senior roles
                    if any(kw in role_lower for kw in ["senior", "staff", "principal", "lead"]):
                        continue
                    
                    # Check relevance
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", 
                                  "deep learning", "genai", "data scientist"]
                    if any(kw in role_lower for kw in ai_keywords) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"LinkedIn found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"LinkedIn search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        """Run LinkedIn discovery"""
        if not keywords:
            keywords = "AI Engineer"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on LinkedIn",
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                message=f"LinkedIn search failed: {e}",
            )


# Export singleton
linkedin_agent = LinkedInAgent()
