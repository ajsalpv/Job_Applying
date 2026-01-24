"""
Cutshort Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class CutshortAgent(IntelligentJobDiscoveryAgent):
    """Intelligent Cutshort job discovery agent."""
    
    def __init__(self):
        super().__init__(
            platform="cutshort",
            base_url=PLATFORM_URLS.get(JobPlatform.CUTSHORT, "https://cutshort.io/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Cutshort-specific job discovery"""
        self.logger.info(f"Cutshort search: {keywords} in {location}")
        
        await rate_limiter.acquire("cutshort")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                search_url = f"https://cutshort.io/jobs?skill={keywords.replace(' ', '+')}&location={location.replace(' ', '+')}"
                
                await playwright_manager.navigate(page, search_url, wait_for="load")
                await page.wait_for_timeout(5000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('.job-card, [class*="JobCard"], [data-job-id], .job-listing-item');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 30) {
                                const titleEl = card.querySelector('h2, .job-title, [class*="title"], .job-card-title');
                                const companyEl = card.querySelector('.company-name, [class*="company"], .job-card-company');
                                const locationEl = card.querySelector('.location, [class*="location"], .job-card-location');
                                const expEl = card.querySelector('.experience, [class*="exp"], [class*="experience"]');
                                const linkEl = card.querySelector('a[href*="/job/"], a[id^="job-link"]');
                                const descEl = card.querySelector('.job-description, .job-snippet, [class*="description"]');
                                const dateEl = card.querySelector('.posted-time, [class*="time"], [class*="posted"]');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: expEl?.textContent?.trim() || '',
                                        job_url: linkEl?.href || '',
                                        job_description: descEl?.textContent?.trim() || '',
                                        posted_date: dateEl?.textContent?.trim() || 'Today',
                                        platform: 'cutshort',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                self.logger.info(f"Cutshort found {len(raw_jobs)} raw jobs")
                
                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    exp_lower = job.get("experience_required", "").lower()
                    
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower:
                        continue
                    # Refined Junior-Friendly Filter
                    is_junior_friendly = any(kw in exp_lower for kw in ["0", "1", "2", "fresher", "entry", "intern", "junior"])
                    has_high_exp = any(kw in exp_lower for kw in ["5", "6", "7", "8", "9", "5+", "8+", "10+"])
                    
                    if any(kw in role_lower for kw in ["senior", "staff", "principal", "lead", "sr.", "manager"]):
                        continue
                        
                    if has_high_exp and not is_junior_friendly:
                        continue
                    
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "genai", "artificial intelligence", "data scientist"]
                    search_kws = keywords.lower().split()
                    if any(kw in role_lower for kw in ai_keywords) or any(kw in role_lower for kw in search_kws) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Cutshort found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Cutshort search error: {e}")
        
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
                message=f"Found {len(jobs)} jobs on Cutshort",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


cutshort_agent = CutshortAgent()
