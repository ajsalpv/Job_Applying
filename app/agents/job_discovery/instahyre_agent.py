"""
Instahyre Intelligent Job Discovery Agent
"""
from typing import List, Dict, Any, Optional
from app.agents.job_discovery.base_discovery_agent import IntelligentJobDiscoveryAgent
from app.agents.base_agent import AgentResult
from app.config.constants import JobPlatform, PLATFORM_URLS, EXCLUDED_JOB_TITLES
from app.tools.browser import playwright_manager
from app.tools.utils.rate_limiter import rate_limiter


class InstahyreAgent(IntelligentJobDiscoveryAgent):
    """Intelligent Instahyre job discovery agent for Indian startups."""
    
    def __init__(self):
        super().__init__(
            platform="instahyre",
            base_url=PLATFORM_URLS.get(JobPlatform.INSTAHYRE, "https://www.instahyre.com/"),
        )
    
    async def discover(
        self,
        keywords: str = "AI Engineer",
        location: str = "Bangalore",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Instahyre-specific job discovery"""
        self.logger.info(f"Instahyre search: {keywords} in {location}")
        
        await rate_limiter.acquire("instahyre")
        jobs = []
        
        try:
            async with playwright_manager.get_page() as page:
                # Instahyre search URL
                search_url = f"https://www.instahyre.com/search-jobs/?job_title={keywords.replace(' ', '+')}&location={location.replace(' ', '+')}"
                
                await playwright_manager.navigate(page, search_url, wait_for="load")
                
                # Instahyre often redirects or loads lazily
                try:
                    await page.wait_for_selector(".opportunity-card, .employer-job-name, [id^='employer-profile-opportunity']", timeout=15000)
                except:
                    self.logger.warning(f"Instahyre timeout waiting for selectors. Attempting extraction anyway.")
                
                await page.evaluate("window.scrollBy(0, 500)")
                await page.wait_for_timeout(3000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        // Instahyre uses these specific selectors according to inspection
                        const cards = document.querySelectorAll('.opportunity-card, [id^="employer-profile-opportunity"], .job-card');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 30) {
                                const titleEl = card.querySelector('.employer-job-name, .opportunity-title, h3, [class*="Title"]');
                                const companyEl = card.querySelector('.company-name, [class*="company"], .employer-name');
                                const locationEl = card.querySelector('.location, [class*="location"], .city');
                                const expEl = card.querySelector('.experience, [class*="exp"]');
                                const linkEl = card.querySelector('a[href*="/job/"], a[id^="view-job"], a.opportunity-title');
                                const dateEl = card.querySelector('.posted-date, .job-posted, .ng-binding[ng-if*="posted"]');
                                
                                if (titleEl) {
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: expEl?.textContent?.trim() || '',
                                        job_url: linkEl?.href || '',
                                        posted_date: dateEl?.textContent?.trim() || 'Today',
                                        platform: 'instahyre',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                self.logger.info(f"Instahyre found {len(raw_jobs)} raw jobs")
                
                # Standardized intelligent filtering
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
                    
                    if any(kw in role_lower for kw in ["senior", "staff", "lead", "principal", "manager"]):
                        continue
                        
                    if has_high_exp and not is_junior_friendly:
                        continue
                            
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "genai", "artificial intelligence", "data scientist"]
                    search_kws = keywords.lower().split()
                    if any(kw in role_lower for kw in ai_keywords) or any(kw in role_lower for kw in search_kws) or "engineer" in role_lower:
                        jobs.append(job)
                
                jobs = jobs[:max_results]
                self.logger.info(f"Instahyre found {len(jobs)} relevant jobs")
                
        except Exception as e:
            self.logger.error(f"Instahyre search error: {e}")
        
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
                message=f"Found {len(jobs)} jobs on Instahyre",
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))


instahyre_agent = InstahyreAgent()
