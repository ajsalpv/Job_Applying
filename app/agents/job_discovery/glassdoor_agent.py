"""
Glassdoor India Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class GlassdoorAgent(IntelligentJobDiscoveryAgent):
    """Intelligent Glassdoor job discovery agent."""
    
    def __init__(self):
        super().__init__(
            platform="glassdoor",
            base_url=PLATFORM_URLS.get(JobPlatform.GLASSDOOR, "https://www.glassdoor.co.in/Job/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Glassdoor-specific job discovery"""
        self.logger.info(f"Glassdoor search: {keywords} in {location}")
        
        await rate_limiter.acquire("glassdoor")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                keyword_slug = keywords.lower().replace(" ", "-")
                
                search_url = f"https://www.glassdoor.co.in/Job/india-{keyword_slug}-jobs-SRCH_IL.0,5_IN115.htm"
                
                await playwright_manager.navigate(page, search_url)
                await page.wait_for_timeout(3000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('[data-test="jobListing"], .JobCard, li[data-id]');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 25) {
                                const titleEl = card.querySelector('[data-test="job-title"], .jobTitle');
                                const companyEl = card.querySelector('[data-test="employer-name"], .employerName');
                                const locationEl = card.querySelector('[data-test="emp-location"], .location');
                                const linkEl = card.querySelector('a[data-test="job-title"], a[href*="/job-listing"]');
                                
                                if (titleEl) {
                                    const href = linkEl?.href || '';
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        job_url: href.startsWith('http') ? href : 'https://www.glassdoor.co.in' + href,
                                        platform: 'glassdoor',
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
                    if any(kw in role_lower for kw in ["senior", "staff", "principal"]):
                        continue
                    
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", 
                                  "deep learning", "genai", "data scientist"]
                    if any(kw in role_lower for kw in ai_keywords) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Glassdoor found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Glassdoor search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "India",
        max_results: int = 20,
    ) -> AgentResult:
        if not keywords:
            keywords = "machine learning engineer"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on Glassdoor",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


glassdoor_agent = GlassdoorAgent()
