"""
Indeed India Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class IndeedAgent(IntelligentJobDiscoveryAgent):
    """
    Intelligent Indeed India job discovery agent.
    """
    
    def __init__(self):
        super().__init__(
            platform="indeed",
            base_url=PLATFORM_URLS.get(JobPlatform.INDEED, "https://in.indeed.com/jobs"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Indeed-specific job discovery"""
        self.logger.info(f"Indeed search: {keywords} in {location}")
        
        await rate_limiter.acquire("indeed")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                search_url = (
                    f"https://in.indeed.com/jobs?"
                    f"q={keywords.replace(' ', '+')}"
                    f"&l={location.replace(' ', '+')}"
                    f"&fromage=7"  # Last 7 days
                )
                
                await playwright_manager.navigate(page, search_url)
                await page.wait_for_timeout(3000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('.job_seen_beacon, .jobCard, [data-jk]');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 30) {
                                const titleEl = card.querySelector('h2.jobTitle, .jobTitle');
                                const companyEl = card.querySelector('.companyName, [data-testid="company-name"]');
                                const locationEl = card.querySelector('.companyLocation, [data-testid="text-location"]');
                                const linkEl = card.querySelector('a[href*="/viewjob"], a.jcs-JobTitle');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        job_url: linkEl?.href || '',
                                        platform: 'indeed',
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
                    
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower or "opencv" in role_lower:
                        continue
                    if any(kw in role_lower for kw in ["senior", "staff", "principal", "lead"]):
                        continue
                    
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", 
                                  "deep learning", "genai", "data scientist"]
                    if any(kw in role_lower for kw in ai_keywords) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Indeed found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Indeed search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        if not keywords:
            keywords = "AI Engineer"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on Indeed",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


indeed_agent = IndeedAgent()
