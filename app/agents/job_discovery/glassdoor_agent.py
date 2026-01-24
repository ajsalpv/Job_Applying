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
                # Use a more generic search URL that accepts parameters
                search_url = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={keywords.replace(' ', '+')}&locT=C&locId=115"
                
                await playwright_manager.navigate(page, search_url, wait_for="load")
                
                try:
                    await page.wait_for_selector("[data-test='jobListing'], .JobCard, .JobsList_jobListItem__", timeout=15000)
                except:
                    self.logger.warning("Glassdoor timeout waiting for job listings.")
                
                # Scroll to load more
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await page.wait_for_timeout(2000)
                
                raw_jobs = await page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('[data-test="jobListing"], .JobCard, li[data-id], [class*="jobListItem"]');
                        
                        cards.forEach((card, idx) => {
                            if (idx < 30) {
                                const titleEl = card.querySelector('[data-test="job-title"], .jobTitle, [class*="jobTitle"]');
                                const companyEl = card.querySelector('[data-test="employer-name"], .employerName, [class*="employerName"]');
                                const locationEl = card.querySelector('[data-test="emp-location"], .location, [class*="location"]');
                                const linkEl = card.querySelector('a[data-test="job-link"], a[href*="/job-listing"], a[class*="JobCard_jobTitle"]');
                                const dateEl = card.querySelector('[data-test="job-age"], [class*="jobAge"]');
                                
                                if (titleEl) {
                                    const href = linkEl?.href || '';
                                    jobs.push({
                                        role: titleEl.textContent?.trim() || '',
                                        company: companyEl?.textContent?.trim() || '',
                                        location: locationEl?.textContent?.trim() || '',
                                        experience_required: '',
                                        job_url: href.startsWith('http') ? href : 'https://www.glassdoor.co.in' + href,
                                        job_description: '', // Desc usually needs click
                                        posted_date: dateEl?.textContent?.trim() || 'Today',
                                        platform: 'glassdoor',
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                self.logger.info(f"Glassdoor found {len(raw_jobs)} raw jobs")
                
                # Standardized intelligent filtering
                for job in raw_jobs:
                    role_lower = job.get("role", "").lower()
                    
                    if any(ex.lower() in role_lower for ex in EXCLUDED_JOB_TITLES):
                        continue
                    if "computer vision" in role_lower or "opencv" in role_lower:
                        continue
                    
                    # Refined Junior-Friendly Filter
                    exp_lower = job.get("experience_required", "").lower()
                    is_junior_friendly = any(kw in exp_lower for kw in ["0", "1", "2", "fresher", "entry", "intern", "junior"])
                    
                    if any(kw in role_lower for kw in ["senior", "staff", "principal", "lead", "sr.", "manager"]):
                        continue
                        
                    # Glassdoor list view mostly doesn't show exp, so we rely on role filter more
                    # but if we have it, we use the refined logic
                    has_high_exp = any(kw in exp_lower for kw in ["5", "6", "7", "8", "9", "5+", "8+", "10+"])
                    if has_high_exp and not is_junior_friendly:
                        continue
                    
                    ai_keywords = ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "genai", "artificial intelligence", "data scientist"]
                    search_kws = keywords.lower().split()
                    if any(kw in role_lower for kw in ai_keywords) or any(kw in role_lower for kw in search_kws) or "engineer" in role_lower:
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
