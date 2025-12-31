"""
Naukri.com Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class NaukriAgent(IntelligentJobDiscoveryAgent):
    """
    Intelligent Naukri.com job discovery agent.
    India's largest job portal.
    """
    
    def __init__(self):
        super().__init__(
            platform="naukri",
            base_url=PLATFORM_URLS.get(JobPlatform.NAUKRI, "https://www.naukri.com/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Naukri-specific job discovery"""
        self.logger.info(f"Naukri search: {keywords} in {location}")
        
        await rate_limiter.acquire("naukri")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                keyword_slug = keywords.lower().replace(" ", "-")
                location_slug = location.lower().replace(" ", "-")
                
                search_url = (
                    f"https://www.naukri.com/{keyword_slug}-jobs-in-{location_slug}"
                    f"?experience=1-3"  # 1-3 years experience
                )
                
                await playwright_manager.navigate(page, search_url)
                await page.wait_for_timeout(3000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('.jobTuple, .cust-job-tuple, article.jobTuple');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 30) {
                                const titleEl = card.querySelector('.title, .jobTitle, a.title');
                                const companyEl = card.querySelector('.companyInfo a, .comp-name');
                                const locationEl = card.querySelector('.location, .locWdth');
                                const expEl = card.querySelector('.experience, .expwdth');
                                const linkEl = card.querySelector('a.title, a[href*="job-listings"]');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: expEl?.textContent?.trim() || '',
                                        job_url: linkEl?.href || '',
                                        platform: 'naukri',
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
                self.logger.info(f"Naukri found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Naukri search error: {e}")
        
        return jobs
    
    async def run(
        self,
        keywords: Optional[str] = None,
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> AgentResult:
        if not keywords:
            keywords = "machine learning"
        
        try:
            jobs = await self.discover(keywords, location, max_results)
            return AgentResult(
                success=True,
                data={"jobs": jobs, "count": len(jobs)},
                message=f"Found {len(jobs)} jobs on Naukri",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


naukri_agent = NaukriAgent()
