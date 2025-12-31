"""
Hirist Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class HiristAgent(IntelligentJobDiscoveryAgent):
    """Intelligent Hirist.tech job discovery agent for Indian tech jobs."""
    
    def __init__(self):
        super().__init__(
            platform="hirist",
            base_url=PLATFORM_URLS.get(JobPlatform.HIRIST, "https://www.hirist.tech/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Hirist-specific job discovery"""
        self.logger.info(f"Hirist search: {keywords} in {location}")
        
        await rate_limiter.acquire("hirist")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                search_url = f"https://www.hirist.tech/?q={keywords}&loc={location}"
                
                await playwright_manager.navigate(page, search_url)
                await page.wait_for_timeout(3000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('.job-card, .job-box, [class*="JobCard"]');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 25) {
                                const titleEl = card.querySelector('.job-title, h3, [class*="title"]');
                                const companyEl = card.querySelector('.company, [class*="company"]');
                                const locationEl = card.querySelector('.location, [class*="location"]');
                                const expEl = card.querySelector('.experience, [class*="exp"]');
                                const linkEl = card.querySelector('a');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: expEl?.textContent?.trim() || '',
                                        job_url: linkEl?.href || '',
                                        platform: 'hirist',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower:
                        continue
                    if any(kw in role_lower for kw in ["senior", "staff"]):
                        continue
                    
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning"]
                    if any(kw in role_lower for kw in ai_keywords) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Hirist found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Hirist search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        if not keywords:
            keywords = "machine-learning"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on Hirist",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


hirist_agent = HiristAgent()
